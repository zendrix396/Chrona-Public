from datetime import datetime
from typing import Optional, List, Dict, Any

# Firebase Firestore doesn't require traditional ORM models
# Instead, we define data structures and helper methods

class User:
    """User model for Firestore"""
    
    @staticmethod
    def from_dict(data: Dict[str, Any], doc_id: str = None) -> Dict[str, Any]:
        """Convert Firestore document to User model"""
        return {
            "id": doc_id,
            "email": data.get("email"),
            "name": data.get("name"),
            "firebase_uid": data.get("firebase_uid"),
            "created_at": data.get("created_at")
        }
    
    @staticmethod
    def to_dict(user: Dict[str, Any]) -> Dict[str, Any]:
        """Convert User model to Firestore document"""
        return {
            "email": user.get("email"),
            "name": user.get("name", ""),
            "firebase_uid": user.get("firebase_uid", ""),
            "created_at": user.get("created_at", datetime.now())
        }

class Task:
    """Task model for Firestore"""
    
    @staticmethod
    def from_dict(data: Dict[str, Any], doc_id: str = None) -> Dict[str, Any]:
        """Convert Firestore document to Task model"""
        return {
            "id": doc_id,
            "name": data.get("name"),
            "description": data.get("description"),
            "user_id": data.get("user_id"),
            "created_at": data.get("created_at")
        }
    
    @staticmethod
    def to_dict(task: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Task model to Firestore document"""
        return {
            "name": task.get("name"),
            "description": task.get("description", ""),
            "user_id": task.get("user_id", ""),
            "created_at": task.get("created_at", datetime.now())
        }


class TimeEntry:
    """TimeEntry model for Firestore"""
    
    @staticmethod
    def from_dict(data: Dict[str, Any], doc_id: str = None) -> Dict[str, Any]:
        """Convert Firestore document to TimeEntry model"""
        return {
            "id": doc_id,
            "task_id": data.get("task_id"),
            "user_id": data.get("user_id"),
            "start_time": data.get("start_time"),
            "end_time": data.get("end_time"),
            "duration": data.get("duration"),
            "notes": data.get("notes"),
            "created_at": data.get("created_at")
        }
    
    @staticmethod
    def to_dict(time_entry: Dict[str, Any]) -> Dict[str, Any]:
        """Convert TimeEntry model to Firestore document"""
        return {
            "task_id": time_entry.get("task_id"),
            "user_id": time_entry.get("user_id", ""),
            "start_time": time_entry.get("start_time"),
            "end_time": time_entry.get("end_time"),
            "duration": time_entry.get("duration"),
            "notes": time_entry.get("notes", ""),
            "created_at": time_entry.get("created_at", datetime.now())
        } 