import os

from dotenv import load_dotenv
from google import genai
from google.genai import types


load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY is missing from the environment.")

client = genai.Client(api_key=API_KEY)

EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSIONS = 768


def generate_embedding(text: str, task_type="RETRIEVAL_DOCUMENT") -> list[float]:

    if not text or not text.strip():
        raise ValueError("Cannot generate an embedding for empty text.")

    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(
            task_type=task_type,
            output_dimensionality=EMBEDDING_DIMENSIONS
        )
    )

    return response.embeddings[0].values


def generate_embeddings(texts: list[str]) -> list[list[float]]:

    if not texts:
        return []

    if any(not text.strip() for text in texts):
        raise ValueError("Input contains an empty text chunk.")

    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=texts,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT",
            output_dimensionality=EMBEDDING_DIMENSIONS
        )
    )

    return [
        embedding.values
        for embedding in response.embeddings
    ]


if __name__ == "__main__":

    sample_text = (
        "Veloxa Technologies is a B2B SaaS company "
        "with engineering, finance, HR and marketing teams."
    )

    embedding = generate_embedding(sample_text)

    print("Embedding generated successfully!")
    print(f"Model: {EMBEDDING_MODEL}")
    print(f"Vector dimensions: {len(embedding)}")
    print(f"First five values: {embedding[:5]}")
