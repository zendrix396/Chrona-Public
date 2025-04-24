from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import validator

# User authentication schemas
class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None

class UserCreate(UserBase):
    password: str
    
class UserLogin(BaseModel):
    email: EmailStr
    password: str
    
class TokenData(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    expires_at: int

class User(UserBase):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Task schemas
class TaskBase(BaseModel):
    name: str
    description: Optional[str] = None
    user_id: Optional[str] = None  # Added user_id to associate tasks with users

class TaskCreate(TaskBase):
    pass

class Task(TaskBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True

# TimeEntry schemas
class TimeEntryBase(BaseModel):
    task_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    notes: Optional[str] = None
    user_id: Optional[str] = None  # Added user_id to associate time entries with users
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class TimeEntryCreate(TimeEntryBase):
    # Allow string dates and convert to datetime objects (without timezone info)
    @validator('start_time', 'end_time', pre=True)
    def parse_datetime(cls, value):
        if value is None:
            return None
        if isinstance(value, datetime):
            # Remove timezone if present
            if value.tzinfo is not None:
                return value.replace(tzinfo=None)
            return value
        try:
            # Handle various ISO formats by cleaning the string first
            # Remove potential microseconds and timezone info
            cleaned = value.split('.')[0]  # Remove microseconds if present
            if '+' in cleaned:
                cleaned = cleaned.split('+')[0]  # Remove timezone info if present
            if 'Z' in cleaned:
                cleaned = cleaned.split('Z')[0]  # Remove UTC indicator if present
            
            dt = datetime.fromisoformat(cleaned)
            return dt
        except (TypeError, ValueError) as e:
            raise ValueError(f"Invalid datetime format: {value}. Error: {e}")

class TimeEntryUpdate(BaseModel):
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    notes: Optional[str] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    # Allow string dates and convert to datetime objects (without timezone info)
    @validator('end_time', pre=True)
    def parse_datetime(cls, value):
        if value is None:
            return None
        if isinstance(value, datetime):
            # Remove timezone if present
            if value.tzinfo is not None:
                return value.replace(tzinfo=None)
            return value
        try:
            # Handle various ISO formats by cleaning the string first
            # Remove potential microseconds and timezone info
            cleaned = value.split('.')[0]  # Remove microseconds if present
            if '+' in cleaned:
                cleaned = cleaned.split('+')[0]  # Remove timezone info if present
            if 'Z' in cleaned:
                cleaned = cleaned.split('Z')[0]  # Remove UTC indicator if present
            
            dt = datetime.fromisoformat(cleaned)
            return dt
        except (TypeError, ValueError) as e:
            raise ValueError(f"Invalid datetime format: {value}. Error: {e}")

class TimeEntry(TimeEntryBase):
    id: str
    created_at: datetime
    task: Optional[Task] = None

# Stats schemas
class DailyStats(BaseModel):
    date: str
    total_duration: float
    tasks: List[Dict[str, Any]]

class WeeklyStats(BaseModel):
    week_start: str
    week_end: str
    total_duration: float
    daily_breakdown: List[Dict[str, Any]]
    task_breakdown: List[Dict[str, Any]] 