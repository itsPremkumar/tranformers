import json
import os
import hashlib

SKILLS_DIR = os.path.join(os.path.dirname(__file__), 'skills')

def init_skills_db():
    if not os.path.exists(SKILLS_DIR):
        os.makedirs(SKILLS_DIR)

def get_skill_hash(topic: str) -> str:
    # Normalize the topic to lower case and remove spaces to create a deterministic hash
    normalized = topic.lower().strip().replace(" ", "_")
    return hashlib.md5(normalized.encode()).hexdigest()

def save_skill(topic: str, synthesis_data: str):
    init_skills_db()
    skill_id = get_skill_hash(topic)
    skill_path = os.path.join(SKILLS_DIR, f"{skill_id}.json")
    
    skill_data = {
        "topic": topic,
        "synthesis": synthesis_data
    }
    
    with open(skill_path, 'w', encoding='utf-8') as f:
        json.dump(skill_data, f, indent=4)
        
def load_skill(topic: str) -> str:
    init_skills_db()
    skill_id = get_skill_hash(topic)
    skill_path = os.path.join(SKILLS_DIR, f"{skill_id}.json")
    
    if os.path.exists(skill_path):
        try:
            with open(skill_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('synthesis', None)
        except:
            return None
    return None
