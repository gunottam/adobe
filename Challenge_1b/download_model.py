# download_model.py
from sentence_transformers import SentenceTransformer
import nltk

# Define the model name from the architecture blueprint
MODEL_NAME = 'sentence-transformers/all-MiniLM-L6-v2'
print(f"Downloading model: {MODEL_NAME}")

# Download and cache the sentence transformer model
SentenceTransformer(MODEL_NAME)
print("Model downloaded successfully.")

# Download the 'punkt' tokenizer for sentence splitting
nltk.download('punkt')
print("NLTK 'punkt' downloaded successfully.")
