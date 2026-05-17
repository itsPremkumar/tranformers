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
            # Chunking large content into manageable sentences/blocks
            chunks = [content[i:i+500] for i in range(0, len(content), 500)]
            ids = [f"{url}_{i}" for i in range(len(chunks))]
            metadatas = [{"source": url, "perspective": perspective} for _ in chunks]
            
            self.collection.add(
                documents=chunks,
                metadatas=metadatas,
                ids=ids
            )
            print(f"[MEMORY VAULT] Saved {len(chunks)} knowledge chunks from {url}")
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
            
            if results and results['documents'] and results['documents'][0]:
                print(f"[MEMORY VAULT] Retrieved {len(results['documents'][0])} relevant past memories.")
                return results['documents'][0]
            return []
        except Exception as e:
            print(f"[MEMORY VAULT ERROR] Search failed: {e}")
            return []
