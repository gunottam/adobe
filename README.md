# 🧠 Adobe Hackathon: Connecting the Dots - Round 1 Solution

This repository contains the **complete solution** for **Round 1** of the Adobe *Connecting the Dots* Hackathon, covering:

* ✅ **Challenge 1A**: Document Outline Extraction
* ✅ **Challenge 1B**: Persona-Driven Document Intelligence

---

## 📘 Overview

This project is built as a **comprehensive two-stage document analysis pipeline**:

### 🔹 Stage 1: Document Outline Extraction (Challenge 1A)

Parses a PDF document and extracts:

* The **title**
* A **hierarchical outline** of headings (H1–H4) with corresponding page numbers.

### 🔹 Stage 2: Persona-Driven Intelligence (Challenge 1B)

Builds on 1A to analyze multiple documents using:

* A **lightweight Retrieval-Augmented Generation (RAG)** pipeline
* Extracts the **most relevant document sections** based on a user’s persona and job-to-be-done (JBTD)

> ✅ The solution is **fully containerized** using Docker, optimized for **CPU-only**, **offline** execution, and adheres to all hackathon constraints.

---

## 🚀 Challenge 1A: Document Outline Extraction

### 📌 Problem Statement

Create a system that:

* Accepts **any PDF**
* Outputs a **structured outline** with:

  * Title
  * Headings (H1, H2, H3, etc.)
  * Page numbers

### 🛠️ Approach: Multi-Pass, Feature-Driven Pipeline

1. **Logical Block Parsing**
   Parses full text blocks instead of fragmented lines (handles multi-line headings properly).

2. **Role-Based Filtering**
   Ignores:

   * Repeating headers/footers
   * Bulleted lists
   * Table contents

3. **Context-Aware Feature Scoring**

   * **Whitespace Analysis**: Uses vertical spacing to separate sections.
   * **Typographical Prominence**: Font size, bold, all-caps.
   * **Structural Cues**: Extra weight for numbered headings (e.g., `1.1 Introduction`) or keywords (`Appendix`).

4. **Adaptive Thresholding**
   Learns layout of each document to dynamically score headings.

5. **Hierarchical Classification**
   Assigns H1–H4 levels using font size clusters and numbering patterns.

---

## 🧠 Challenge 1B: Persona-Driven Document Intelligence

### 📌 Problem Statement

Given:

* A **user persona**
* A **job-to-be-done (JBTD)**
* A collection of **PDFs**

Build a system to:

* Extract the **most relevant document sections**
* Present a **ranked list** of insights

### 🛠️ Approach: Lightweight Offline RAG Architecture

1. **Preprocessing & Semantic Chunking**
   Parses PDFs into logical chunks (heading + content).

2. **Vector Store Construction**

   * Converts each chunk into embeddings using `all-MiniLM-L6-v2`
   * Stores in an efficient **vector store**

3. **Persona-Augmented Retrieval**

   * Embeds the user's query (persona + JBTD)
   * Uses **cosine similarity** to retrieve Top-K relevant chunks

4. **Sentence-Level Refinement**

   * Breaks down chunks into sentences
   * Reranks by relevance to filter noise

5. **Reconstruction & Final Ranking**

   * Groups top-ranked sentences back into coherent passages
   * Scores and returns top 5 most relevant results

---

## 📁 Project Structure

```
├── input/
│   ├── doc1.pdf
│   ├── doc2.pdf
│   └── input.json         # Persona & task definition for 1B
├── output/
│   └── result.json        # Final result for 1B
├── pdf_parser.py          # Core parsing logic (Challenge 1A)
├── download_model.py      # Pre-downloads the sentence-transformer model
├── run_1b.py              # Main script for persona-driven analysis (1B)
├── requirements.txt       # Python dependencies
└── Dockerfile             # Docker container definition
```

---

## ⚙️ How to Build and Run

### 🔧 Prerequisites

* [Docker](https://www.docker.com/) installed and running

---

### ✅ Step 1: Prepare Input

Place your PDF files into the `input/` directory.

Create an `input.json` file in the following format:

```json
{
  "documents": [
    { "filename": "doc1.pdf" },
    { "filename": "doc2.pdf" }
  ],
  "persona": {
    "role": "Travel Planner"
  },
  "job_to_be_done": {
    "task": "Plan a trip of 4 days for a group of 10 college friends."
  }
}
```

---

### 🧱 Step 2: Build the Docker Image

In the root of the project, run:

```bash
docker build -t adobe-hackathon-solution .
```

> ⚠️ First-time build may take a few minutes to download dependencies and models.

---

### 🏃 Step 3: Run the Container

```bash
docker run --rm \
  -v "$(pwd)/input:/app/input" \
  -v "$(pwd)/output:/app/output" \
  adobe-hackathon-solution
```

---

### 📤 Step 4: View the Output

The final results will be saved as:

```
output/result.json
```

---

## 📦 Requirements

All dependencies are listed in `requirements.txt` and include:

* `PyMuPDF`
* `sentence-transformers`
* `scikit-learn`
* `numpy`
* `torch`
* `transformers`
* ...and others required for parsing and similarity scoring.

---

## 👥 Authors & Credits

Gunottam Maini
Ridhima Kathait
Abhinav Chand Ramola

