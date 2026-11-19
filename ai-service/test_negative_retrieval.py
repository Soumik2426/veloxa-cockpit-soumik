from app.rag.retriever import retrieve_relevant_chunks

question = "What will the weather be in Kolkata tomorrow?"

results = retrieve_relevant_chunks(question, top_k=5)

print("\n========== NEGATIVE RETRIEVAL TEST ==========\n")

for index, result in enumerate(results, start=1):
    print(f"Result: {index}")
    print(f"Source: {result['source_file']}")
    print(f"Similarity: {result['similarity']:.4f}")
    print(f"Content: {result['content'][:180]}")
    print("-" * 60)