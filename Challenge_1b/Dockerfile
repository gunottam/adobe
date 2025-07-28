# Dockerfile for Challenge 1b Solution
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy solution code
COPY run_1b.py ./
COPY pdf_parser.py ./
COPY download_model.py ./

# Copy input/output structure
COPY input/input.json ./input/input.json
COPY PDFs ./input/PDFs
RUN mkdir -p /app/output


# Download model and NLTK data at build time
RUN python download_model.py && python -m nltk.downloader punkt punkt_tab

CMD ["python", "run_1b.py"]
