FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY process_pdfs.py ./

RUN mkdir -p /app/input /app/output

ENTRYPOINT ["python", "process_pdfs.py"]
