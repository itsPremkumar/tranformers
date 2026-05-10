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
        """Saves a new interaction to the robot's history."""
        session = Session()
        robot = session.query(RobotMemory).filter_by(robot_name=name).first()
        if robot:
            history = json.loads(robot.history)
            history.append(f"User: {user_msg}")
            history.append(f"Robot: {ai_msg}")
            
            # Keep last 10 interactions for context
            robot.history = json.dumps(history[-10:])
            robot.last_seen = datetime.datetime.utcnow()
            session.commit()
        session.close()

    def update_knowledge(self, name: str, key: str, value: str):
        """Stores a specific fact about the robot or user."""
        session = Session()
        robot = session.query(RobotMemory).filter_by(robot_name=name).first()
        if robot:
            knowledge = json.loads(robot.knowledge)
            knowledge[key] = value
            robot.knowledge = json.dumps(knowledge)
            session.commit()
        session.close()

memory_manager = MemoryManager()
