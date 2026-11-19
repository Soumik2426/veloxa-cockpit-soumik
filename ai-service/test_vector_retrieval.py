from app.rag.retriever import retrieve_relevant_chunks


QUESTIONS = [
    "Why were REQ-014 and REQ-015 put on hold?",
    "What was the ARR, customer count, monthly burn and runway in July to September 2026?",
    "What was the original and revised release date of Atlas GA?",
    "What information did the CEO provide in the voice notes?",
]


if __name__ == "__main__":
    for question in QUESTIONS:
        print("\n" + "=" * 90)
        print(f"QUESTION: {question}")
        print("=" * 90)

        results = retrieve_relevant_chunks(question, top_k=10)

        if not results:
            print("No results returned.")
            continue

        for index, result in enumerate(results, start=1):
            print(f"\nResult: {index}")
            print(f"Source: {result.get('source_file')}")
            print(f"Section: {result.get('section')}")
            print(f"Similarity: {result.get('similarity'):.4f}")
            print(f"Content: {result.get('content')}")
