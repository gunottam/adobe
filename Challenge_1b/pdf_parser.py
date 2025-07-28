# pdf_parser.py
import re
from pathlib import Path
import fitz  # PyMuPDF
import statistics

class PDFParser:
    """
    An advanced parser that uses the logic from Challenge 1(a) to extract
    structured content chunks based on a document's hierarchical outline.
    """

    def _get_line_objects(self, doc):
        """Extracts all lines of text with their properties."""
        lines = []
        for page_num, page in enumerate(doc):
            blocks = page.get_text("dict", flags=fitz.TEXT_INHIBIT_SPACES)["blocks"]
            for b in blocks:
                if "lines" in b:
                    for l in b["lines"]:
                        if not l["spans"]: continue
                        text = " ".join(s["text"] for s in l["spans"]).strip()
                        if not text: continue
                        span = l["spans"][0]
                        lines.append({
                            "text": text,
                            "size": round(span["size"], 2),
                            "bold": (span["flags"] & 16) != 0,
                            "page_num": page_num,
                            "y0": l["bbox"][1]
                        })
        return lines

    def _get_body_text_size(self, lines):
        """Determines the most common font size (body text)."""
        if not lines: return 10.0
        font_sizes = [l["size"] for l in lines if 8 < l["size"] < 24]
        if not font_sizes: return 10.0
        try:
            return statistics.mode(font_sizes)
        except statistics.StatisticsError:
            return statistics.median(font_sizes)

    def _get_headings(self, lines, body_size):
        """Identifies headings based on font size and boldness."""
        headings = []
        for line in lines:
            if line["size"] > body_size + 1 and len(line["text"].split()) < 20:
                headings.append(line)
        headings.sort(key=lambda x: (x["page_num"], x["y0"]))
        return headings

    def process_pdf(self, pdf_path):
        """
        Processes a single PDF and returns a list of structured content chunks.
        Each chunk represents the text content under a specific heading.
        """
        doc = fitz.open(pdf_path)
        if doc.page_count == 0:
            return []

        lines = self._get_line_objects(doc)
        body_size = self._get_body_text_size(lines)
        headings = self._get_headings(lines, body_size)

        chunks = []
        if not headings:
            # If no headings, treat the whole document as one chunk
            full_text = " ".join([line["text"] for line in lines])
            chunks.append({
                "doc_name": Path(pdf_path).name,
                "page": 0,
                "section_title": doc.metadata.get("title") or Path(pdf_path).stem,
                "content": full_text
            })
            doc.close()
            return chunks

        # Create chunks by associating text with the preceding heading
        for i, heading in enumerate(headings):
            start_page = heading["page_num"]
            start_y = heading["y0"]
            
            end_page = headings[i+1]["page_num"] if i + 1 < len(headings) else doc.page_count
            end_y = headings[i+1]["y0"] if i + 1 < len(headings) else float('inf')

            content = []
            for line in lines:
                is_after_start = (line["page_num"] > start_page) or (line["page_num"] == start_page and line["y0"] > start_y)
                is_before_end = (line["page_num"] < end_page) or (line["page_num"] == end_page and line["y0"] < end_y)
                
                if is_after_start and is_before_end:
                    content.append(line["text"])

            chunks.append({
                "doc_name": Path(pdf_path).name,
                "page": heading["page_num"],
                "section_title": heading["text"],
                "content": " ".join(content)
            })
            
        doc.close()
        return chunks
