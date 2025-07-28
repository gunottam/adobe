# 🧠 Adobe Hackathon: Connecting the Dots — Round 1 Solution

This repository contains the **complete, containerized** solution for **Round 1** of the Adobe Connecting the Dots Hackathon, covering:

✅ **Challenge 1A**: Document Outline Extraction  
✅ **Challenge 1B**: Persona-Driven Document Intelligence  

## 📘 Overview

A two-stage, offline-ready document analysis pipeline optimized for CPU-only environments:

1. **Stage 1: Document Outline Extraction (Challenge 1A)**  
   Parses any PDF to extract:
   - **Title**  
   - **Hierarchical outline** of headings (H1–H4) with page numbers  

2. **Stage 2: Persona-Driven Intelligence (Challenge 1B)**  
   Builds on Stage 1 using a lightweight Retrieval-Augmented Generation (RAG) pipeline to:
   - Extract the **most relevant document sections** based on a user persona and job-to-be-done (JBTD)  
   - Return a **ranked list** of insights  

> **Fully containerized** with Docker, adheres to offline constraints, and requires minimal setup.

## 🚀 Challenge 1A: Document Outline Extraction

### 📌 Problem Statement

Create a system to:
- Accept **any PDF**  
- Output a **structured outline** including title, headings (H1–H4), and page numbers  

### 🛠️ Approach: Multi-Pass, Feature-Driven Pipeline

1. **Logical Block Parsing**  
   Groups text into logical blocks to handle multi-line headings  
2. **Role-Based Filtering**  
   Excludes headers/footers, bulleted lists, and table contents  
3. **Context-Aware Feature Scoring**  
   - **Whitespace Analysis**: Uses vertical gaps  
   - **Typographical Prominence**: Font size, weight, caps  
   - **Structural Cues**: Numbered headings, keywords (e.g., “Appendix”)  
4. **Adaptive Thresholding**  
   Learns each document’s layout to set dynamic scores  
5. **Hierarchical Classification**  
   Clusters font sizes and patterns to assign H1–H4 levels  

## 🧠 Challenge 1B: Persona-Driven Document Intelligence

### 📌 Problem Statement

Given:
- A **user persona**  
- A **job-to-be-done (JBTD)**  
- A collection of **PDFs**  

Build a system to:
- Retrieve the **most relevant document sections**  
- Present a **ranked list** of insights  

### 🛠️ Approach: Lightweight Offline RAG

1. **Preprocessing & Semantic Chunking**  
   Splits PDFs into logical (heading + content) chunks  
2. **Vector Store Construction**  
   - Embeds chunks with `all-MiniLM-L6-v2`  
   - Stores in an efficient vector database  
3. **Persona-Augmented Retrieval**  
   - Embeds persona + JBTD query  
   - Retrieves Top-K chunks via cosine similarity  
4. **Sentence-Level Refinement**  
   Splits chunks into sentences and reranks by relevance  
5. **Reconstruction & Final Ranking**  
   Groups top sentences into coherent passages and returns top 5 insights  

## 📁 Project Structure

```text
├── Challenge_1a/
│   ├── sample_dataset/
│   │   ├── outputs/
│   │   └── schema/
│   ├── Dockerfile
│   ├── process_pdfs.py
│   ├── README.md
│   └── requirements.txt
├── Challenge_1b/
│   ├── input/
│   │   ├── PDFs/
│   │   └── input.json
│   ├── output/
│   │   ├── challenge1b_output.json
│   │   └── result.json
│   ├── Dockerfile
│   ├── download_model.py
│   ├── pdf_parser.py
│   ├── run_1b.py
│   └── requirements.txt
├── README.md
├── pdf_parser.py
├── download_model.py
├── run_1b.py
├── requirements.txt
└── Dockerfile
```

## ⚙️ How to Build & Run

### 🔧 Prerequisites

- Docker installed and running  

### ✅ Step 1: Prepare Input

1. Place your PDF files into `Challenge_1a/sample_dataset/` for Stage 1.  
2. Copy outputs to `input/PDFs/` and edit `input/input.json` for Stage 2:  

```json
{
  "documents": [
    { "filename": "doc1.pdf" },
    { "filename": "doc2.pdf" }
  ],
  "persona": { "role": "Travel Planner" },
  "job_to_be_done": { "task": "Plan a 4-day trip for 10 college friends." }
}
```

### 🧱 Step 2: Build the Docker Image

```bash
docker build -t adobe-hackathon-solution .
```

> ⚠️ First build may take several minutes to download dependencies and models.

### 🏃 Step 3: Run the Container

```bash
docker run --rm \
  -v "$(pwd)/Challenge_1a/sample_dataset:/app/input" \
  -v "$(pwd)/Challenge_1b/output:/app/output" \
  adobe-hackathon-solution
```

### 📤 Step 4: View Outputs

- **Stage 1**: `Challenge_1a/sample_dataset/outputs/`  
- **Stage 2**: `Challenge_1b/output/result.json`  

## 📦 Dependencies

All Python packages are listed in `requirements.txt`, including:

- `PyMuPDF`  
- `sentence-transformers`  
- `scikit-learn`  
- `numpy`  
- `torch`  
- `transformers`  

## 👥 Authors & Credits

- **Gunottam Maini**  
- **Ridhima Kathait**  
- **Abhinav Chand Ramola**  

## 🏷️ Topics

- Document Analysis  
- PDF Parsing  
- Retrieval-Augmented Generation (RAG)  
- Docker  
- NLP  
- Offline AI  
