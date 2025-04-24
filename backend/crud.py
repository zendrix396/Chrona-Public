import firebase_admin
from firebase_admin import auth
from firebase_admin import credentials
from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from datetime import datetime, timedelta
import models
import schemas
from typing import List, Dict, Any, Optional
import os
import traceback
import time
import json
import uuid
import bcrypt

# Initialize Firebase Admin SDK
try:
    if not firebase_admin._apps:
        cred_path = os.path.join(os.path.dirname(__file__), "firebase-credentials.json")
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
except Exception as e:
    print(f"Error initializing Firebase Admin SDK: {e}")

# User CRUD operations
async def create_user(db, user: schemas.UserCreate) -> models.User:
    """Create a new user"""
    try:
        # Check if user already exists
        users_ref = db.collection('users')
        query = users_ref.where(filter=FieldFilter("email", "==", user.email))
        existing_users = query.get()
        
        if len(existing_users) > 0:
            raise ValueError("User with this email already exists")
        
        # Hash the password
        hashed_password = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt())
        
        # Create Firebase Auth user
        try:
            print(f"Attempting to create Firebase Auth user with email: {user.email}")
            firebase_user = auth.create_user(
                email=user.email,
                password=user.password
            )
            print(f"Firebase Auth user created with UID: {firebase_user.uid}")
        except Exception as e:
            print(f"Error creating Firebase Auth user: {e}")
            print(traceback.format_exc())
            raise ValueError(f"Failed to create Firebase Auth user: {str(e)}")
        
        # Create user in Firestore
        user_data = {
            "email": user.email,
            "name": user.name or "",
            "firebase_uid": firebase_user.uid,
            "created_at": datetime.now()
        }
        
        # Add user to Firestore
        print(f"Adding user to Firestore: {user_data}")
        user_ref = users_ref.document()
        user_ref.set(user_data)
        
        # Return user data
        user_data["id"] = user_ref.id
        print(f"User created successfully with ID: {user_ref.id}")
        return user_data
    except Exception as e:
        print(f"Unexpected error in create_user: {e}")
        print(traceback.format_exc())
        raise

async def get_user_by_email(db, email: str) -> Optional[Dict[str, Any]]:
    """Get user by email"""
    users_ref = db.collection('users')
    query = users_ref.where(filter=FieldFilter("email", "==", email))
    users = query.get()
    
    if len(users) == 0:
        return None
    
    user_doc = users[0]
    user_data = models.User.from_dict(user_doc.to_dict(), user_doc.id)
    return user_data

async def get_user_by_id(db, user_id: str) -> Optional[Dict[str, Any]]:
    """Get user by ID"""
    user_ref = db.collection('users').document(user_id)
    user_doc = user_ref.get()
    
    if not user_doc.exists:
        return None
    
    user_data = models.User.from_dict(user_doc.to_dict(), user_doc.id)
    return user_data

async def authenticate_user(db, email: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate user"""
    try:
        # Get user from Firebase
        user = await get_user_by_email(db, email)
        if not user:
            return None
        
        # Verify with Firebase Auth
        firebase_user = auth.get_user_by_email(email)
        
        # Create custom token (normally used for client SDK sign in)
        custom_token = auth.create_custom_token(firebase_user.uid)
        
        # Return user data with token
        return {
            "user_id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "firebase_uid": firebase_user.uid,
            "custom_token": custom_token.decode('utf-8')
        }
    except Exception as e:
        print(f"Authentication error: {e}")
        print(traceback.format_exc())
        return None

async def get_user_by_firebase_uid(db, firebase_uid: str) -> Optional[Dict[str, Any]]:
    """Get user by Firebase UID"""
    users_ref = db.collection('users')
    query = users_ref.where(filter=FieldFilter("firebase_uid", "==", firebase_uid))
    users = query.get()
    
    if len(users) == 0:
        return None
    
    user_doc = users[0]
    user_data = models.User.from_dict(user_doc.to_dict(), user_doc.id)
    return user_data

# Task CRUD operations
async def get_task(db: firestore.Client, id: str):
    doc_ref = db.collection('tasks').document(id)
    doc = doc_ref.get()
    if doc.exists:
        return models.Task.from_dict(doc.to_dict(), doc.id)
    return None

async def get_task_by_name(db: firestore.Client, name: str):
    tasks_ref = db.collection('tasks')
    query = tasks_ref.where('name', '==', name).limit(1)
    docs = query.stream()
    
    for doc in docs:
        return models.Task.from_dict(doc.to_dict(), doc.id)
    return None

async def get_tasks(db: firestore.Client, skip: int = 0, limit: int = 100, user_id: str = None):
    """Get tasks, optionally filtered by user_id"""
    tasks_ref = db.collection('tasks')
    
    # If user_id is provided, filter tasks by user_id
    if user_id:
        tasks_ref = tasks_ref.where('user_id', '==', user_id)
    
    # Apply limits
    query = tasks_ref.limit(limit).offset(skip)
    
    tasks = []
    for doc in query.stream():
        tasks.append(models.Task.from_dict(doc.to_dict(), doc.id))
    return tasks

async def create_task(db: firestore.Client, task: schemas.TaskCreate):
    task_data = {
        "name": task.name,
        "description": task.description if task.description else "",
        "created_at": datetime.now()
    }
    
    # Add to Firestore
    doc_ref = db.collection('tasks').document()
    doc_ref.set(task_data)
    
    # Return the created task with ID
    return models.Task.from_dict(task_data, doc_ref.id)

async def delete_task(db: firestore.Client, id: str):
    # First check if the task exists
    task_ref = db.collection('tasks').document(id)
    task = task_ref.get()
    if not task.exists:
        raise ValueError(f"Task with ID {id} not found")
    
    # Check if there are any time entries associated with this task
    time_entries_ref = db.collection('time_entries')
    query = time_entries_ref.where('task_id', '==', id)
    entries = list(query.stream())
    
    if entries:
        # If there are time entries, we might want to prevent deletion or delete the entries as well
        # For now, let's raise an error to prevent data loss
        raise ValueError(f"Cannot delete task with ID {id} because it has associated time entries. Delete these entries first.")
    
    # Delete the task
    task_ref.delete()
    return {"id": id}

# TimeEntry CRUD operations
async def get_time_entry(db: firestore.Client, id: str):
    doc_ref = db.collection('time_entries').document(id)
    doc = doc_ref.get()
    if doc.exists:
        return models.TimeEntry.from_dict(doc.to_dict(), doc.id)
    return None

async def get_time_entries(db: firestore.Client, skip: int = 0, limit: int = 100, user_id: str = None):
    """Get time entries, optionally filtered by user_id"""
    entries_ref = db.collection('time_entries')
    
    # If user_id is provided, filter entries by user_id
    if user_id:
        entries_ref = entries_ref.where('user_id', '==', user_id)
    
    # Apply ordering and limits
    query = entries_ref.order_by('start_time', direction=firestore.Query.DESCENDING)
    query = query.limit(limit).offset(skip)
    
    entries = []
    for doc in query.stream():
        entry = models.TimeEntry.from_dict(doc.to_dict(), doc.id)
        
        # Optionally fetch the related task
        if entry.get("task_id"):
            task_ref = db.collection('tasks').document(entry.get("task_id"))
            task_doc = task_ref.get()
            if task_doc.exists:
                entry["task"] = models.Task.from_dict(task_doc.to_dict(), task_doc.id)
        
        entries.append(entry)
    
    return entries

async def create_time_entry(db: firestore.Client, time_entry: schemas.TimeEntryCreate):
    # First verify the task exists
    task_ref = db.collection('tasks').document(time_entry.task_id)
    task = task_ref.get()
    if not task.exists:
        raise ValueError(f"Task with ID {time_entry.task_id} does not exist")
    
    # Create the time entry
    entry_data = {
        "task_id": time_entry.task_id,
        "start_time": time_entry.start_time,
        "end_time": time_entry.end_time,
        "duration": time_entry.duration,
        "notes": time_entry.notes if time_entry.notes else "",
        "created_at": datetime.now()
    }
    
    # Add to Firestore
    doc_ref = db.collection('time_entries').document()
    doc_ref.set(entry_data)
    
    # Return the created entry with ID
    return models.TimeEntry.from_dict(entry_data, doc_ref.id)

async def update_time_entry(db: firestore.Client, id: str, time_entry: schemas.TimeEntryUpdate):
    # Get the time entry
    entry_ref = db.collection('time_entries').document(id)
    entry = entry_ref.get()
    if not entry.exists:
        raise ValueError(f"Time entry with ID {id} not found")
    
    # Update only provided fields
    update_data = {}
    
    if time_entry.end_time is not None:
        update_data["end_time"] = time_entry.end_time
    
    if time_entry.duration is not None:
        update_data["duration"] = time_entry.duration
    
    if time_entry.notes is not None:
        update_data["notes"] = time_entry.notes
    
    # Update in Firestore
    entry_ref.update(update_data)
    
    # Get the updated document
    updated_doc = entry_ref.get()
    return models.TimeEntry.from_dict(updated_doc.to_dict(), updated_doc.id)

async def delete_time_entry(db: firestore.Client, id: str):
    entry_ref = db.collection('time_entries').document(id)
    entry = entry_ref.get()
    if not entry.exists:
        raise ValueError(f"Time entry with ID {id} not found")
    
    # Delete from Firestore
    entry_ref.delete()
    return {"id": id}

# Statistics functions
async def get_daily_stats(db: firestore.Client, user_id: str = None):
    """Get daily stats, optionally filtered by user_id"""
    # Get today's date
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    # Get all time entries for today
    entries_ref = db.collection('time_entries')
    query = entries_ref.where('start_time', '>=', today_start).where('start_time', '<=', today_end)
    
    # Filter by user_id if provided
    if user_id:
        # Need to use a different approach since Firestore doesn't allow multiple field filters
        # with different fields in the same query
        entries = []
        for doc in query.stream():
            entry = doc.to_dict()
            if entry.get('user_id') == user_id:
                entries.append(entry)
    else:
        entries = [doc.to_dict() for doc in query.stream()]
    
    # Calculate total duration
    total_duration = 0
    task_durations = {}
    
    for entry in entries:
        if entry.get('duration'):
            duration = entry.get('duration')
            total_duration += duration
            
            task_id = entry.get('task_id')
            if task_id in task_durations:
                task_durations[task_id]["duration"] += duration
            else:
                # Get task name
                task_ref = db.collection('tasks').document(task_id)
                task_doc = task_ref.get()
                task_name = task_doc.to_dict().get('name') if task_doc.exists else "Unknown"
                
                task_durations[task_id] = {
                    "task_id": task_id,
                    "task_name": task_name,
                    "duration": duration
                }
    
    return {
        "date": today.isoformat(),
        "total_duration": total_duration,
        "tasks": list(task_durations.values())
    }

async def get_weekly_stats(db: firestore.Client, user_id: str = None):
    """Get weekly stats, optionally filtered by user_id"""
    # Get the start and end of the current week
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    week_start_dt = datetime.combine(week_start, datetime.min.time())
    week_end_dt = datetime.combine(week_end, datetime.max.time())
    
    # Get all time entries for the week
    entries_ref = db.collection('time_entries')
    query = entries_ref.where('start_time', '>=', week_start_dt).where('start_time', '<=', week_end_dt)
    
    # Filter by user_id if provided
    if user_id:
        # Need to use a different approach since Firestore doesn't allow multiple field filters
        # with different fields in the same query
        entries = []
        for doc in query.stream():
            entry = doc.to_dict()
            if entry.get('user_id') == user_id:
                entries.append(entry)
    else:
        entries = [doc.to_dict() for doc in query.stream()]
    
    # Calculate statistics
    total_duration = 0
    daily_breakdown = {(week_start + timedelta(days=i)).isoformat(): 0 for i in range(7)}
    task_breakdown = {}
    
    for entry in entries:
        if entry.get('duration'):
            duration = entry.get('duration')
            total_duration += duration
            
            # Daily breakdown
            entry_date = entry.get('start_time').date().isoformat()
            if entry_date in daily_breakdown:
                daily_breakdown[entry_date] += duration
            
            # Task breakdown
            task_id = entry.get('task_id')
            if task_id in task_breakdown:
                task_breakdown[task_id]["duration"] += duration
            else:
                # Get task name
                task_ref = db.collection('tasks').document(task_id)
                task_doc = task_ref.get()
                task_name = task_doc.to_dict().get('name') if task_doc.exists else "Unknown"
                
                task_breakdown[task_id] = {
                    "task_id": task_id,
                    "task_name": task_name,
                    "duration": duration
                }
    
    return {
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "total_duration": total_duration,
        "daily_breakdown": [{"date": date, "duration": duration} for date, duration in daily_breakdown.items()],
        "task_breakdown": list(task_breakdown.values())
    } 