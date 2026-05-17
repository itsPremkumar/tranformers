import chromadb
import os

class MemoryVault:
    """
    Feature 3: Closed-Loop Skill Reflexion & Persistent Memory Vault (Hermes-inspired)
    Uses ChromaDB to permanently store crawled scientific sentences.
    """
    def __init__(self, db_path: str = None):
        if not db_path:
            db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'vector_store'))
        
        if not os.path.exists(db_path):
            os.makedirs(db_path)
            
        try:
            self.client = chromadb.PersistentClient(path=db_path)
            self.collection = self.client.get_or_create_collection(name="scientific_knowledge")
            print(f"[MEMORY VAULT] Successfully initialized persistent vault at {db_path}")
        except Exception as e:
            print(f"[MEMORY VAULT ERROR] Could not init ChromaDB: {e}")
            self.collection = None

    def store_knowledge(self, url: str, content: str, perspective: str, metadata: dict = None):
        if not self.collection or not content:
            return
            
        try:
            # Parent Chunks (approx 800 characters, overlap 200)
            parent_size = 800
            parent_overlap = 200
            parents = []
            start = 0
            while start < len(content):
                parents.append(content[start:start+parent_size])
                start += (parent_size - parent_overlap)
                
            documents = []
            metadatas = []
            ids = []
            
            for p_idx, parent in enumerate(parents):
                # Child Chunks (approx 150 characters, overlap 50)
                child_size = 150
                child_overlap = 50
                c_idx = 0
                start_c = 0
                while start_c < len(parent):
                    child = parent[start_c:start_c+child_size]
                    documents.append(child)
                    metadatas.append({
                        "source": url, 
                        "perspective": perspective, 
                        "parent_chunk": parent
                    })
                    ids.append(f"{url}_{p_idx}_{c_idx}")
                    c_idx += 1
                    start_c += (child_size - child_overlap)
            
            if documents:
                self.collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                print(f"[MEMORY VAULT] Saved {len(documents)} Child-Parent knowledge pairs from {url}")
        except Exception as e:
            print(f"[MEMORY VAULT ERROR] Failed saving knowledge: {e}")

    def retrieve_knowledge(self, query: str, n_results: int = 3):
        if not self.collection:
            return []
            
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            retrieved_contexts = []
            if results and results['metadatas'] and results['metadatas'][0]:
                for meta in results['metadatas'][0]:
                    if meta and "parent_chunk" in meta:
                        retrieved_contexts.append(meta["parent_chunk"])
                    
                # De-duplicate matching parent paragraphs
                unique_contexts = []
                for ctx in retrieved_contexts:
                    if ctx not in unique_contexts:
                        unique_contexts.append(ctx)
                        
                print(f"[MEMORY VAULT] Retrieved {len(unique_contexts)} unique high-fidelity parent memories.")
                return unique_contexts
            return []
        except Exception as e:
            print(f"[MEMORY VAULT ERROR] Search failed: {e}")
            return []

