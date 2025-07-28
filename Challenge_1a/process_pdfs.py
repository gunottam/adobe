# app.py
import json
import re
from pathlib import Path
import fitz  # PyMuPDF
import statistics
from collections import Counter

class PDFOutlineExtractor:
    """
    Extracts a structured outline from a PDF using a multi-stage pipeline
    that combines visual, textual, and structural analysis, based on a
    detailed logic blueprint.
    """

    # --- 1. Preprocessing & Line Object Extraction ---
    def _get_line_objects(self, doc):
        """Extracts all lines with comprehensive metadata for analysis."""
        lines = []
        for page_num, page in enumerate(doc):
            page_width, page_height = page.rect.width, page.rect.height
            for b in page.get_text("dict")["blocks"]:
                for l in b.get("lines", []):
                    for s in l.get("spans", []):
                        text = s["text"].strip()
                        if not text: continue
                        
                        x_center = (s["bbox"][0] + s["bbox"][2]) / 2
                        lines.append({
                            "text": text,
                            "font_size": round(s["size"], 2),
                            "font_flags": s["flags"],
                            "page_num": page_num,
                            "bbox": s["bbox"],
                            "y_rel": s["bbox"][1] / page_height,
                            "is_centered": abs(x_center - page_width / 2) < 20,
                            "is_all_caps": text.isupper() and len(text) > 1,
                            "is_bold": (s["flags"] & 16) != 0,
                        })
        return lines

    # --- 2. Body Font-Size Estimation ---
    def _get_body_size(self, lines):
        """Determines the most common font size (body text)."""
        if not lines: return 10.0
        font_sizes = [l["font_size"] for l in lines if 8 < l["font_size"] < 24]
        if not font_sizes: return 10.0
        try:
            return statistics.mode(font_sizes)
        except statistics.StatisticsError:
            return statistics.median(font_sizes)

    # --- 3. Title Candidate Selection ---
    def _extract_title(self, lines):
        """Implements stricter title extraction heuristics."""
        candidates = [l for l in lines if l["page_num"] == 0 and l["y_rel"] < 0.30]
        if not candidates: return ""

        max_size = max(c["font_size"] for c in candidates)
        title_lines = [c for c in candidates if c["font_size"] >= max_size - 0.5]
        
        # Filter by centered or left-aligned rules
        filtered_lines = [
            l for l in title_lines
            if l["is_centered"] or (len(l["text"].split()) >= 2)
        ]
        if not filtered_lines: filtered_lines = title_lines

        filtered_lines.sort(key=lambda l: l["bbox"][1])

        # Merge contiguous lines
        if not filtered_lines: return ""
        title_text = filtered_lines[0]["text"]
        last_y = filtered_lines[0]["bbox"][3]
        for i in range(1, len(filtered_lines)):
            line = filtered_lines[i]
            if (line["bbox"][1] - last_y) < (1.5 * line["font_size"]):
                title_text += " " + line["text"]
                last_y = line["bbox"][3]
            else:
                break
        return re.sub(r'\s+', ' ', title_text).strip()

    def _process_headings(self, lines, title, body_size):
        """
        Implements the full heading pipeline: filtering, scoring,
        and hierarchy assignment.
        """
        # --- 4. Heading Candidate Filtering ---
        candidates = []
        for line in lines:
            text = line["text"]
            # Basic filters
            if line["font_size"] <= (body_size + 1): continue
            if len(text) > 60: continue
            if text.endswith(('.', '?', '!')): continue
            if (line["y_rel"] < 0.10 or line["y_rel"] > 0.90) and not line["is_centered"]: continue
            if text.lower() == title.lower(): continue

            # Special flyer rule
            if line["is_all_caps"] and line["is_centered"] and line["font_size"] > (body_size + 2):
                line['is_flyer_slogan'] = True
                candidates.append(line)
                continue

            candidates.append(line)

        # --- 5. Scoring & Content-Pattern Boosts ---
        for cand in candidates:
            score = 0
            num_level = 0
            text = cand["text"]

            # Numbering regex
            if re.match(r'^\d+\.\d+\.\d+', text): num_level = 3
            elif re.match(r'^\d+\.\d+', text): num_level = 2
            elif re.match(r'^\d+\.', text): num_level = 1
            elif re.match(r'^Appendix', text, re.IGNORECASE): num_level = 2

            if num_level > 0: score += 5
            if text.endswith(':'): score += 1
            if cand["is_bold"]: score += 1
            
            cand["score"] = score
            cand["num_level"] = num_level

        # --- 6. Candidate Prioritization & Hierarchy Assignment ---
        # Sort by size first, then score, to find visual levels
        candidates.sort(key=lambda c: (-c["font_size"], -c.get("score", 0)))
        unique_sizes = sorted(list(set(c["font_size"] for c in candidates)), reverse=True)
        size_to_visual_level = {size: i + 1 for i, size in enumerate(unique_sizes[:3])}

        outline = []
        for cand in candidates:
            visual_level = size_to_visual_level.get(cand["font_size"], 3)
            
            # Use numbering level if it exists, otherwise use visual level
            final_level_int = cand["num_level"] if cand["num_level"] > 0 else visual_level
            
            # Special flyer rule override
            if cand.get('is_flyer_slogan'):
                final_level_int = 1

            outline.append({
                "level": f"H{final_level_int}",
                "text": cand["text"],
                "page": cand["page_num"], # Keep 0-indexed for now
                "y0": cand["bbox"][1]
            })

        # --- 7. Outline Construction (Sort by document order) ---
        outline.sort(key=lambda x: (x["page"], x["y0"]))
        
        return outline

    # --- 8. Post-Processing & Deduplication ---
    def _post_process(self, title, outline):
        """Applies deduplication and final cleanup."""
        # Drop heading if it matches title
        clean_outline = [h for h in outline if h["text"].lower().strip() != title.lower().strip()]

        if not clean_outline: return []
        
        # Drop consecutive duplicate headings
        final_outline = [clean_outline[0]]
        for i in range(1, len(clean_outline)):
            prev = final_outline[-1]
            curr = clean_outline[i]
            if not (curr["text"] == prev["text"] and curr["page"] <= prev["page"] + 1):
                final_outline.append(curr)
        
        # Remove temporary 'y0' key
        for h in final_outline:
            del h['y0']

        return final_outline

    def process_pdf(self, pdf_path):
        """Main processing pipeline for a single PDF."""
        doc = fitz.open(pdf_path)
        if doc.page_count == 0:
            return {"title": "", "outline": []}

        lines = self._get_line_objects(doc)
        body_size = self._get_body_size(lines)
        title = self._extract_title(lines)
        
        outline = self._process_headings(lines, title, body_size)
        final_outline = self._post_process(title, outline)
        
        doc.close()
        
        # --- 10. Output Formatting ---
        return {"title": title, "outline": final_outline}

def main():
    """Entry point for the Docker container."""
    input_dir = Path("/app/input")
    output_dir = Path("/app/output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    pdf_files = list(input_dir.glob("*.pdf"))
    if not pdf_files: return

    extractor = PDFOutlineExtractor()
    for pdf_file in pdf_files:
        result = extractor.process_pdf(pdf_file)
        
        output_file = output_dir / f"{pdf_file.stem}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    main()
