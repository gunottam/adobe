# run_1b.py
import json
import time
from pathlib import Path
from datetime import datetime
import torch
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import nltk

from pdf_parser import PDFParser

# --- 1. System Overview ---

# Constants
MODEL_NAME = 'sentence-transformers/all-MiniLM-L6-v2'
INPUT_DIR = Path("/app/input")
OUTPUT_DIR = Path("/app/output")
TOP_K_RETRIEVAL = 20  # Retrieve top 20 chunks
TOP_N_SENTENCES = 15 # Re-rank and keep top 15 sentences

def main():
    # Load persona and JBTD from the new input.json format
    config_path = INPUT_DIR / "input.json"
    if not config_path.exists():
        raise FileNotFoundError("input.json not found in the input directory!")
        
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # Extract information from the new nested structure
    persona = config["persona"]["role"]
    job_to_be_done = config["job_to_be_done"]["task"]
    pdf_files = [INPUT_DIR / doc["filename"] for doc in config["documents"]]
    doc_filenames = [doc["filename"] for doc in config["documents"]]

    # --- Preprocessing & Chunking ---
    parser = PDFParser()
    all_chunks = []
    print("Step 1: Parsing and Chunking PDFs...")
    for pdf_file in pdf_files:
        if pdf_file.exists():
            all_chunks.extend(parser.process_pdf(pdf_file))
        else:
            print(f"Warning: Document {pdf_file.name} not found in input directory.")

    if not all_chunks:
        print("No content chunks were extracted. Exiting.")
        return

    # --- Vector Store Construction ---
    print("Step 2: Building Vector Store...")
    # Use GPU if available, otherwise CPU. This will run on CPU in the hackathon env.
    device = "cuda" if torch.cuda.is_available() else "cpu"
    embedding_model = SentenceTransformer(MODEL_NAME, device=device)
    
    chunk_contents = [chunk["content"] for chunk in all_chunks]
    chunk_embeddings = embedding_model.encode(chunk_contents, convert_to_tensor=True, show_progress_bar=True)

    # --- Persona-Augmented Retrieval ---
    print("Step 3: Performing Persona-Augmented Retrieval...")
    retrieval_query = f"Role: {persona}. Task: {job_to_be_done}"
    query_embedding = embedding_model.encode(retrieval_query, convert_to_tensor=True)

    # Calculate cosine similarity
    similarities = cosine_similarity(
        query_embedding.cpu().numpy().reshape(1, -1),
        chunk_embeddings.cpu().numpy()
    )[0]

    # Get top K chunks
    top_k_indices = np.argsort(similarities)[-TOP_K_RETRIEVAL:][::-1]
    retrieved_chunks = [all_chunks[i] for i in top_k_indices]
    retrieved_scores = {i: similarities[i] for i in top_k_indices}
    for chunk_idx, chunk in enumerate(retrieved_chunks):
        chunk['retrieval_score'] = retrieved_scores[top_k_indices[chunk_idx]]


    # --- Sentence-Level Refinement ---
    print("Step 4: Reranking Sentences...")
    sentences = []
    for chunk in retrieved_chunks:
        # Split chunk into sentences
        sents = nltk.sent_tokenize(chunk["content"])
        for sent in sents:
            sentences.append({
                "text": sent,
                "source_chunk": chunk
            })

    sentence_texts = [s["text"] for s in sentences]
    # Re-rank using the same bi-encoder for efficiency
    sentence_embeddings = embedding_model.encode(sentence_texts, convert_to_tensor=True)
    sentence_similarities = cosine_similarity(
        query_embedding.cpu().numpy().reshape(1, -1),
        sentence_embeddings.cpu().numpy()
    )[0]
    
    for i, sent in enumerate(sentences):
        sent["rerank_score"] = sentence_similarities[i]
        
    # Keep top N sentences
    sentences.sort(key=lambda x: x["rerank_score"], reverse=True)
    top_sentences = sentences[:TOP_N_SENTENCES]

    # --- Reconstruction & Final Importance Ranking ---
    print("Step 5: Reconstructing Passages and Ranking...")
    passages = {}
    for sent in top_sentences:
        chunk = sent["source_chunk"]
        chunk_id = (chunk["doc_name"], chunk["page"], chunk["section_title"])
        if chunk_id not in passages:
            passages[chunk_id] = {
                "doc_name": chunk["doc_name"],
                "page": chunk["page"],
                "section_title": chunk["section_title"],
                "retrieval_score": chunk["retrieval_score"],
                "sentences": []
            }
        passages[chunk_id]["sentences"].append(sent)

    ranked_passages = []
    for passage_id, passage_data in passages.items():
        # Sort sentences by their original order within the document
        passage_data["sentences"].sort(key=lambda s: chunk_contents.index(s['source_chunk']['content']))
        
        # Calculate final passage score
        avg_rerank_score = np.mean([s["rerank_score"] for s in passage_data["sentences"]])
        final_score = (passage_data["retrieval_score"] * 0.4) + (avg_rerank_score * 0.6)
        
        ranked_passages.append({
            "document": passage_data["doc_name"],
            "page_number": passage_data["page"] + 1, # Convert to 1-based index for output
            "section_title": passage_data["section_title"],
            "final_score": final_score,
            "refined_text_candidates": passage_data["sentences"]
        })
        
    ranked_passages.sort(key=lambda x: x["final_score"], reverse=True)

    # --- Sub-Section Analysis & Final JSON Output ---
    print("Step 6: Generating Final JSON Output...")
    output_data = {
        "metadata": {
            "input_documents": doc_filenames,
            "persona": persona,
            "job_to_be_done": job_to_be_done,
            "processing_timestamp": datetime.utcnow().isoformat()
        },
        "extracted_sections": [],
        "subsection_analysis": []
    }
    
    for rank, passage in enumerate(ranked_passages):
        output_data["extracted_sections"].append({
            "document": passage["document"],
            "section_title": passage["section_title"],
            "importance_rank": rank + 1,
            "page_number": passage["page_number"]
        })
        
        # For sub-section, take the top 1-2 sentences from this passage
        passage["refined_text_candidates"].sort(key=lambda x: x["rerank_score"], reverse=True)
        refined_text = " ".join([s["text"] for s in passage["refined_text_candidates"][:2]])

        output_data["subsection_analysis"].append({
            "document": passage["document"],
            "refined_text": refined_text,
            "page_number": passage["page_number"]
        })

    output_file = OUTPUT_DIR / "result.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=4)

    print(f"\nProcessing complete. Output saved to {output_file}")

if __name__ == "__main__":
    main()
