import os
import json
import numpy as np
import logging
import google.generativeai as genai
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class VectorMemoryManager:
    def __init__(self, memory_file_path: str = "app/data/vector_memory.json"):
        """
        Initialize the Vector Memory Manager using Gemini Cloud Embeddings.
        
        Args:
            memory_file_path: The local path to save persistent vector memories.
        """
        self.memory_file_path = memory_file_path
        self.memories: List[Dict[str, Any]] = []
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.memory_file_path), exist_ok=True)
        self.load_memories()
        
    def load_memories(self):
        """Load stored memories from local JSON file."""
        if os.path.exists(self.memory_file_path):
            try:
                with open(self.memory_file_path, "r", encoding="utf-8") as f:
                    self.memories = json.load(f)
                logger.info(f"[MEMORY] Loaded {len(self.memories)} long-term memories successfully!")
            except Exception as e:
                logger.error(f"[MEMORY] Error loading memories: {e}")
                self.memories = []
        else:
            self.memories = []

    def save_memories(self):
        """Persist current memory database to local JSON file."""
        try:
            with open(self.memory_file_path, "w", encoding="utf-8") as f:
                json.dump(self.memories, f, indent=4, ensure_ascii=False)
            logger.info(f"[MEMORY] Saved {len(self.memories)} memories to {self.memory_file_path}")
        except Exception as e:
            logger.error(f"[MEMORY] Error saving memories: {e}")

    def get_gemini_embedding(self, text: str) -> Optional[List[float]]:
        """
        Call Gemini API to generate a high-quality embedding vector.
        
        Args:
            text: Text block to encode.
        """
        try:
            # We call genai.embed_content which is standard for google-generativeai API
            response = genai.embed_content(
                model="models/embedding-001",
                content=text,
                task_type="retrieval_document"
            )
            if 'embedding' in response:
                return response['embedding']
            elif isinstance(response, dict) and 'embedding' in response:
                return response['embedding']
            return None
        except Exception as e:
            logger.error(f"[MEMORY] Failed to get Gemini embedding: {e}")
            return None

    def add_memory(self, text: str, metadata: Dict[str, Any] = None):
        """
        Embed a memory and store it with its vector, timestamp, and metadata.
        
        Args:
            text: The visual observation, landmark description, or dialogue turn.
            metadata: Associated structured info (e.g. robot mode, location coordinate).
        """
        if not text or not text.strip():
            return
            
        logger.info(f"[MEMORY] Indexing new memory: {text[:50]}...")
        embedding = self.get_gemini_embedding(text)
        
        if embedding is None:
            logger.warning("[MEMORY] Skipping save due to missing embedding vectors.")
            return

        memory_item = {
            "text": text,
            "embedding": embedding,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }
        
        self.memories.append(memory_item)
        self.save_memories()

    def search_memory(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """
        Perform a semantic similarity search across long-term stored memories.
        
        Args:
            query: The natural language search query.
            k: Number of relevant context matches to retrieve.
        """
        if not self.memories or not query or not query.strip():
            return []
            
        query_vector = self.get_gemini_embedding(query)
        if query_vector is None:
            return []

        scored_memories = []
        q_vec = np.array(query_vector)
        q_norm = np.linalg.norm(q_vec)

        for memory in self.memories:
            m_vec = np.array(memory["embedding"])
            m_norm = np.linalg.norm(m_vec)
            
            if q_norm == 0 or m_norm == 0:
                similarity = 0.0
            else:
                # Cosine similarity dot product calculation
                similarity = float(np.dot(q_vec, m_vec) / (q_norm * m_norm))
                
            scored_memories.append((similarity, memory))

        # Sort descending by similarity score
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        
        # Grab top K items
        results = []
        for score, memory in scored_memories[:k]:
            # Clean copy to avoid modifying the core DB
            item = {
                "text": memory["text"],
                "metadata": memory["metadata"],
                "timestamp": memory["timestamp"],
                "similarity": score
            }
            results.append(item)
            
        logger.info(f"[MEMORY] Vector search for '{query}' returned {len(results)} matches.")
        return results

# Global thread-safe singleton instantiation
vector_memory = VectorMemoryManager()
