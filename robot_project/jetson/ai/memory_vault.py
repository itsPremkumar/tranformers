#!/usr/bin/env python3
import os
import sqlite3

class LocalMemoryVault:
    def __init__(self, db_path="robot_brain.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        # A simple SQLite-based semantic memory store as a fallback/representation
        # of the ChromaDB parent-child schema
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_vault (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_id INTEGER,
                content TEXT,
                category TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def store_memory(self, content: str, category="general", parent_id=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO memory_vault (content, category, parent_id) VALUES (?, ?, ?)",
            (content, category, parent_id)
        )
        conn.commit()
        conn.close()

    def retrieve_memories(self, query: str, limit=3):
        # In a full deployment, this runs Cosine Similarity against sentence transformer vector embeddings.
        # This SQLite representation selects matches containing query terms as a fallback.
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Simple keyword search mimicking RAG retrieval
        search_term = f"%{query}%"
        cursor.execute(
            "SELECT content, category FROM memory_vault WHERE content LIKE ? ORDER BY id DESC LIMIT ?",
            (search_term, limit)
        )
        results = cursor.fetchall()
        conn.close()
        
        return [{"content": r[0], "category": r[1]} for r in results]

if __name__ == "__main__":
    vault = LocalMemoryVault("test_vault.db")
    vault.store_memory("Omni-Morph robot was upgraded to NVIDIA Jetson Orin architecture in May 2026.", "history")
    memories = vault.retrieve_memories("Jetson")
    print("Retrieved memories:", memories)
    os.remove("test_vault.db")
