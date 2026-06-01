from sentence_transformers import SentenceTransformer
import chromadb
import os
import json

# Load the embedding model
# This model converts text/code into 384-dimensional vectors
print("Loading embedding model...")
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
print("Model loaded!")

# Setup ChromaDB — this is our vector database
client = chromadb.PersistentClient(path="./vectorstore")

def get_or_create_collection(repo_name):
    """Create a collection (like a table) for each repository."""
    # ChromaDB collection names must be clean
    clean_name = repo_name.replace(" ", "_").replace("/", "_").lower()
    collection = client.get_or_create_collection(
        name=clean_name,
        metadata={"hnsw:space": "cosine"}
    )
    return collection

def embed_code_chunks(parsed_files, repo_name):
    """
    Take parsed code (functions, classes) and:
    1. Convert each to a vector using the AI model
    2. Store in ChromaDB for later semantic search
    """
    collection = get_or_create_collection(repo_name)
    
    documents = []  # the actual code text
    embeddings = []  # the vectors
    metadatas = []  # extra info
    ids = []        # unique IDs
    
    chunk_id = 0
    
    for file_result in parsed_files:
        file_path = file_result["file"]
        
        # Embed each function
        for func in file_result["functions"]:
            code_text = f"Function: {func['name']}\n{func['code']}"
            
            # This is the magic line — converts code to numbers
            embedding = model.encode(code_text).tolist()
            
            documents.append(code_text)
            embeddings.append(embedding)
            metadatas.append({
                "type": "function",
                "name": func["name"],
                "file": file_path,
                "start_line": func["start_line"],
                "end_line": func["end_line"],
            })
            ids.append(f"chunk_{chunk_id}")
            chunk_id += 1
        
        # Embed each class
        for cls in file_result["classes"]:
            code_text = f"Class: {cls['name']}\n{cls['code']}"
            embedding = model.encode(code_text).tolist()
            
            documents.append(code_text)
            embeddings.append(embedding)
            metadatas.append({
                "type": "class",
                "name": cls["name"],
                "file": file_path,
                "start_line": cls["start_line"],
                "end_line": cls["end_line"],
            })
            ids.append(f"chunk_{chunk_id}")
            chunk_id += 1
    
    if documents:
        collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )
        print(f"Stored {len(documents)} code chunks in vector database!")
    
    return len(documents)

def search_code(query, repo_name, top_k=3):
    """
    Search code semantically — finds code by MEANING not keywords.
    Example: searching 'multiply numbers' finds the multiply() function
    even if you never typed that word.
    """
    collection = get_or_create_collection(repo_name)
    
    # Convert search query to vector
    query_embedding = model.encode(query).tolist()
    
    # Find most similar code chunks
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
    )
    
    matches = []
    if results["documents"]:
        for i, doc in enumerate(results["documents"][0]):
            matches.append({
                "code": doc,
                "metadata": results["metadatas"][0][i],
                "similarity": 1 - results["distances"][0][i],
            })
    
    return matches

if __name__ == "__main__":
    import sys
    sys.path.append(".")
    from parser.code_parser import parse_file
    
    # Parse main.py
    print("\nParsing main.py...")
    parsed = [parse_file("main.py")]
    
    # Embed it
    print("\nGenerating embeddings...")
    count = embed_code_chunks(parsed, "test_repo")
    
    # Now search semantically
    print("\nSearching for 'add two numbers'...")
    results = search_code("add two numbers", "test_repo")
    for r in results:
        print(f"\nFound: {r['metadata']['name']} (similarity: {r['similarity']:.2f})")
        print(f"Code: {r['code'][:100]}...")
    
    print("\nSearching for 'math operations'...")
    results = search_code("math operations", "test_repo")
    for r in results:
        print(f"\nFound: {r['metadata']['name']} (similarity: {r['similarity']:.2f})")