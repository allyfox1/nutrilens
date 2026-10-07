from pathlib import Path
import chromadb


def chunk_text(text, max_chars=900):
    """Group whole lines into chunks so nothing is cut mid-word."""
    chunks, current = [], ""
    for line in text.split("\n"):
        if current and len(current) + len(line) > max_chars:
            chunks.append(current.strip())
            current = ""
        current += line + "\n"
    if current.strip():
        chunks.append(current.strip())
    return [c for c in chunks if len(c) > 80]


def get_collection(rebuild=False):
    client = chromadb.PersistentClient(path="chroma_db")
    if rebuild:
        try:
            client.delete_collection("nutrition")
        except Exception:
            pass
    collection = client.get_or_create_collection("nutrition")
    if collection.count() == 0:
        ids, documents, metadatas = [], [], []
        for file in sorted(Path("docs").glob("*.txt")):
            source, slug = file.stem.rsplit("-", 1)
            level = "Health Professional" if slug == "HealthProfessional" else "Consumer"
            url = f"https://ods.od.nih.gov/factsheets/{source}-{slug}/"
            for i, chunk in enumerate(chunk_text(file.read_text())):
                ids.append(f"{file.stem}-{i}")
                documents.append(f"{source}: {chunk}")
                metadatas.append({"source": source, "level": level, "url": url})
        for start in range(0, len(ids), 500):
            end = start + 500
            collection.add(
                ids=ids[start:end],
                documents=documents[start:end],
                metadatas=metadatas[start:end],
            )
    return collection


if __name__ == "__main__":
    collection = get_collection(rebuild=True)
    print("Stored", collection.count(), "chunks")
    results = collection.query(
        query_texts=["What is the upper limit for zinc?"], n_results=3
    )
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        print("\n---", meta["source"], "|", meta["level"])
        print(doc[:300])