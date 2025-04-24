from fastapi import FastAPI, Depends, HTTPException, status, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import List, Optional, Dict, Any
import models, schemas, crud
from database import get_db
from datetime import datetime, timedelta
import traceback
from jose import JWTError, jwt
from firebase_admin import auth as firebase_auth
from pydantic import BaseModel
import time
import json
import os

# JWT configuration
SECRET_KEY = "PLACEHOLDER_SECRET_KEY_REPLACE_IN_PRODUCTION"  # In production, load from env var like: os.environ.get("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 1 week

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI(title="Chrona Time Tracker API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper functions for auth
def create_access_token(data: dict):
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_db)):
    """Verify JWT token and return current user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        # Get user from database
        user = await crud.get_user_by_id(db, user_id)
        if user is None:
            raise credentials_exception
        
        return user
    except JWTError:
        raise credentials_exception

# Optional user authentication - allows API access without auth
async def get_optional_user(request: Request, db=Depends(get_db)):
    """Get the current user if authenticated, otherwise None"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.replace("Bearer ", "")
    try:
        # Decode JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        
        # Get user from database
        user = await crud.get_user_by_id(db, user_id)
        return user
    except JWTError:
        return None

@app.on_event("startup")
async def startup():
    # Initialize Firebase connection
    get_db()

@app.get("/")
async def root():
    return {"message": "Chrona Time Tracker API is running"}

# Auth endpoints
@app.post("/register", response_model=schemas.User)
async def register(user: schemas.UserCreate, db=Depends(get_db)):
    """Register a new user"""
    try:
        new_user = await crud.create_user(db, user)
        return new_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        print(f"Registration error: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during registration"
        )

@app.post("/token", response_model=schemas.TokenData)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    """Login and get access token"""
    # Authenticate user
    user = await crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": user["user_id"]})
    
    # Calculate expiration time
    expires_at = int(time.time()) + ACCESS_TOKEN_EXPIRE_MINUTES * 60
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user["user_id"],
        "expires_at": expires_at
    }

@app.post("/auth/google", response_model=schemas.TokenData)
async def login_with_google(id_token: str = Body(..., embed=True), db=Depends(get_db)):
    """Login with Google ID token"""
    try:
        # Verify the ID token with Firebase
        decoded_token = firebase_auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        email = decoded_token.get('email', '')
        name = decoded_token.get('name', '')
        
        print(f"Google login - UID: {uid}, Email: {email}")
        
        # Check if user exists in Firestore
        user = await crud.get_user_by_firebase_uid(db, uid)
        
        if not user:
            # Create a new user if they don't exist
            print(f"Creating new user for Google login: {email}")
            user_data = {
                "email": email,
                "name": name,
                "firebase_uid": uid,
                "created_at": datetime.now()
            }
            
            # Add user to Firestore
            user_ref = db.collection('users').document()
            user_ref.set(user_data)
            
            # Set the ID
            user_id = user_ref.id
        else:
            user_id = user["id"]
        
        # Create access token
        access_token = create_access_token(data={"sub": user_id})
        
        # Calculate expiration time
        expires_at = int(time.time()) + ACCESS_TOKEN_EXPIRE_MINUTES * 60
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user_id,
            "expires_at": expires_at
        }
    except Exception as e:
        print(f"Google login error: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid ID token: {str(e)}"
        )

@app.get("/users/me", response_model=schemas.User)
async def read_users_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get the current authenticated user"""
    return current_user

@app.post("/time-entries/", response_model=schemas.TimeEntry)
async def create_time_entry(
    time_entry: schemas.TimeEntryCreate, 
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user),
    db=Depends(get_db)
):
    try:
        print(f"Received time entry request: {time_entry.dict()}")
        
        # Add user_id if authenticated
        if current_user:
            time_entry.user_id = current_user["id"]
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required to create time entries"
            )
        
        # Validate task exists
        task_check = await crud.get_task(db, id=time_entry.task_id)
        print(f"Task check result: {task_check}")
        if not task_check:
            raise HTTPException(
                status_code=404, 
                detail=f"Task with ID {time_entry.task_id} not found"
            )
        
        # Create time entry
        result = await crud.create_time_entry(db=db, time_entry=time_entry)
        return result
    except ValueError as e:
        print(f"ValueError in time entry creation: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        error_msg = f"Error in time entry creation endpoint: {e}"
        error_trace = traceback.format_exc()
        print(error_msg)
        print(error_trace)
        # Return more details about the error
        detail = f"Failed to create time entry: {str(e)}\n{error_trace}"
        raise HTTPException(status_code=500, detail=detail)

@app.get("/time-entries/", response_model=List[schemas.TimeEntry])
async def read_time_entries(
    skip: int = 0, 
    limit: int = 100, 
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user),
    db=Depends(get_db)
):
    try:
        print("Fetching time entries...")
        # Get user-specific entries if authenticated
        user_id = current_user["id"] if current_user else None
        time_entries = await crud.get_time_entries(db, skip=skip, limit=limit, user_id=user_id)
        print(f"Retrieved {len(time_entries)} time entries")
        return time_entries
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Error fetching time entries: {e}")
        print(error_trace)
        detail = f"Failed to fetch time entries: {str(e)}\n{error_trace}"
        raise HTTPException(status_code=500, detail=detail)

@app.get("/time-entries/{id}", response_model=schemas.TimeEntry)
async def read_time_entry(
    id: str, 
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user),
    db=Depends(get_db)
):
    db_time_entry = await crud.get_time_entry(db, id=id)
    if db_time_entry is None:
        raise HTTPException(status_code=404, detail="Time entry not found")
    
    # Check if user has access to this entry
    if current_user and db_time_entry.get("user_id") and db_time_entry["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this time entry")
    
    return db_time_entry

@app.put("/time-entries/{id}", response_model=schemas.TimeEntry)
async def update_time_entry(
    id: str, 
    time_entry: schemas.TimeEntryUpdate, 
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user),
    db=Depends(get_db)
):
    try:
        # Get user_id if authenticated
        user_id = current_user["id"] if current_user else None
        
        db_time_entry = await crud.get_time_entry(db, id=id)
        if db_time_entry is None:
            raise HTTPException(status_code=404, detail="Time entry not found")
        
        # Check if user has access to this entry
        if user_id and db_time_entry.get("user_id") and db_time_entry["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this time entry")
        
        result = await crud.update_time_entry(db=db, id=id, time_entry=time_entry, user_id=user_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error updating time entry: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to update time entry: {str(e)}")

@app.delete("/time-entries/{id}")
async def delete_time_entry(
    id: str, 
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user),
    db=Depends(get_db)
):
    # Get user_id if authenticated
    user_id = current_user["id"] if current_user else None
    
    db_time_entry = await crud.get_time_entry(db, id=id)
    if db_time_entry is None:
        raise HTTPException(status_code=404, detail="Time entry not found")
    
    # Check if user has access to this entry
    if user_id and db_time_entry.get("user_id") and db_time_entry["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this time entry")
    
    await crud.delete_time_entry(db=db, id=id, user_id=user_id)
    return {"message": "Time entry deleted successfully"}

@app.get("/tasks/", response_model=List[schemas.Task])
async def read_tasks(
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user),
    db=Depends(get_db)
):
    # Get user-specific tasks if authenticated
    user_id = current_user["id"] if current_user else None
    return await crud.get_tasks(db, user_id=user_id)

@app.post("/tasks/", response_model=schemas.Task)
async def create_task(
    task: schemas.TaskCreate, 
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user),
    db=Depends(get_db)
):
    # Add user_id if authenticated
    if current_user:
        task.user_id = current_user["id"]
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to create tasks"
        )
    
    return await crud.create_task(db=db, task=task)

@app.get("/tasks/{id}", response_model=schemas.Task)
async def read_task(
    id: str, 
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user),
    db=Depends(get_db)
):
    db_task = await crud.get_task(db, id=id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Check if user has access to this task
    if current_user and db_task.get("user_id") and db_task["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this task")
        
    return db_task

@app.delete("/tasks/{id}")
async def delete_task(
    id: str, 
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user),
    db=Depends(get_db)
):
    try:
        # Get user_id if authenticated
        user_id = current_user["id"] if current_user else None
        
        await crud.delete_task(db=db, id=id, user_id=user_id)
        return {"message": "Task deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error deleting task: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to delete task: {str(e)}")

@app.get("/stats/daily")
async def get_daily_stats(
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user),
    db=Depends(get_db)
):
    # Get user-specific stats if authenticated
    user_id = current_user["id"] if current_user else None
    # If not authenticated, return error
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to access statistics"
        )
    return await crud.get_daily_stats(db, user_id=user_id)

@app.get("/stats/weekly")
async def get_weekly_stats(
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user),
    db=Depends(get_db)
):
    # Get user-specific stats if authenticated
    user_id = current_user["id"] if current_user else None
    # If not authenticated, return error
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to access statistics"
        )
    return await crud.get_weekly_stats(db, user_id=user_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 