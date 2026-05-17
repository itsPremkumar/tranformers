from sqlalchemy import create_engine, Column, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import json

Base = declarative_base()

class RobotMemory(Base):
    __tablename__ = 'robot_memory'
    robot_name = Column(String, primary_key=True)
    history = Column(Text, default="[]") # JSON list of strings
    knowledge = Column(Text, default="{}") # JSON object of key-value pairs
    last_seen = Column(DateTime, default=datetime.datetime.utcnow)

engine = create_engine('sqlite:///robot_brain.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

class MemoryManager:
    def get_robot_memory(self, name: str):
        """Retrieves history and knowledge for a specific robot."""
        session = Session()
        robot = session.query(RobotMemory).filter_by(robot_name=name).first()
        if not robot:
            robot = RobotMemory(robot_name=name)
            session.add(robot)
            session.commit()
        
        history = json.loads(robot.history)
        knowledge = json.loads(robot.knowledge)
        session.close()
        return history, knowledge

    def save_interaction(self, name: str, user_msg: str, ai_msg: str):
        """Saves a new interaction to the robot's history and profiles user preferences."""
        session = Session()
        robot = session.query(RobotMemory).filter_by(robot_name=name).first()
        if robot:
            history = json.loads(robot.history)
            history.append(f"User: {user_msg}")
            history.append(f"Robot: {ai_msg}")
            
            # Keep last 10 interactions for context
            robot.history = json.dumps(history[-10:])
            robot.last_seen = datetime.datetime.utcnow()
            
            # 1. Topic Frequency Profiling
            try:
                knowledge = json.loads(robot.knowledge) if robot.knowledge else {}
                frequent_topics = knowledge.get("frequent_topics", {})
                words = user_msg.lower().split()
                stop_words = {"the", "a", "an", "and", "or", "but", "if", "then", "of", "to", "in", "on", "at", "for", "with", "about", "your", "my", "you", "me", "is", "are", "was", "were", "am", "be", "been"}
                for word in words:
                    # Strip punctuation
                    word = ''.join(char for char in word if char.isalnum())
                    if len(word) > 3 and word not in stop_words:
                        frequent_topics[word] = frequent_topics.get(word, 0) + 1
                
                # Sort and keep top 20 topics to prevent memory bloat
                sorted_topics = dict(sorted(frequent_topics.items(), key=lambda x: x[1], reverse=True)[:20])
                knowledge["frequent_topics"] = sorted_topics
                
                # 2. Preferred Swarm Modes tracking
                preferred_modes = knowledge.get("preferred_modes", {})
                msg_lower = user_msg.lower()
                if "transform" in msg_lower or "car" in msg_lower:
                    preferred_modes["car"] = preferred_modes.get("car", 0) + 1
                elif "walk" in msg_lower or "robot" in msg_lower:
                    preferred_modes["robot"] = preferred_modes.get("robot", 0) + 1
                knowledge["preferred_modes"] = preferred_modes
                
                robot.knowledge = json.dumps(knowledge)
            except Exception as e:
                print(f"[COGNITIVE ERROR] Preference profiling failed: {e}")
                
            session.commit()
        session.close()

    def update_knowledge(self, name: str, key: str, value: str):
        """Stores a specific fact about the robot or user."""
        session = Session()
        robot = session.query(RobotMemory).filter_by(robot_name=name).first()
        if robot:
            knowledge = json.loads(robot.knowledge) if robot.knowledge else {}
            knowledge[key] = value
            robot.knowledge = json.dumps(knowledge)
            session.commit()
        session.close()

    # --- Next-Gen Swarm Task & TODO Tracker ---
    def add_todo_task(self, name: str, description: str, due_date: str = "", priority: str = "medium") -> str:
        """Dynamically add a new persistent todo task inside SQL knowledge store."""
        session = Session()
        robot = session.query(RobotMemory).filter_by(robot_name=name).first()
        if robot:
            knowledge = json.loads(robot.knowledge) if robot.knowledge else {}
            tasks = knowledge.get("tasks", [])
            
            next_id = max([t['id'] for t in tasks], default=0) + 1
            new_task = {
                'id': next_id,
                'description': description,
                'due_date': due_date,
                'priority': priority,
                'status': 'pending',
                'created_at': datetime.datetime.utcnow().isoformat()
            }
            tasks.append(new_task)
            knowledge["tasks"] = tasks
            robot.knowledge = json.dumps(knowledge)
            session.commit()
            session.close()
            return f"Task '{description}' successfully added with ID {next_id}."
        session.close()
        return "Failed to find active robot profile."
        
    def get_todo_tasks(self, name: str, status: str = "all") -> list:
        """Retrieve persistent tasks filtered by status."""
        session = Session()
        robot = session.query(RobotMemory).filter_by(robot_name=name).first()
        tasks = []
        if robot:
            knowledge = json.loads(robot.knowledge) if robot.knowledge else {}
            tasks = knowledge.get("tasks", [])
            if status != "all":
                tasks = [t for t in tasks if t.get("status") == status]
        session.close()
        return tasks
        
    def update_todo_status(self, name: str, task_id: int, new_status: str) -> str:
        """Update active task status inside SQL store."""
        session = Session()
        robot = session.query(RobotMemory).filter_by(robot_name=name).first()
        if robot:
            knowledge = json.loads(robot.knowledge) if robot.knowledge else {}
            tasks = knowledge.get("tasks", [])
            found = False
            for t in tasks:
                if t.get("id") == task_id:
                    t["status"] = new_status
                    t["updated_at"] = datetime.datetime.utcnow().isoformat()
                    found = True
                    break
            if found:
                knowledge["tasks"] = tasks
                robot.knowledge = json.dumps(knowledge)
                session.commit()
                session.close()
                return f"Task {task_id} status updated to '{new_status}' successfully."
            session.close()
            return f"Task ID {task_id} not found."
        session.close()
        return "Failed to find active robot profile."

memory_manager = MemoryManager()
