from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import models, schemas, crud
from database import get_db
from datetime import datetime, timedelta
import traceback

app = FastAPI(title="Time Tracker API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    # Initialize Firebase connection
    get_db()

@app.get("/")
async def root():
    return {"message": "Time Tracker API is running"}

@app.post("/time-entries/", response_model=schemas.TimeEntry)
async def create_time_entry(time_entry: schemas.TimeEntryCreate, db=Depends(get_db)):
    try:
        print(f"Received time entry request: {time_entry.dict()}")
        
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
async def read_time_entries(skip: int = 0, limit: int = 100, db=Depends(get_db)):
    try:
        print("Fetching time entries...")
        time_entries = await crud.get_time_entries(db, skip=skip, limit=limit)
        print(f"Retrieved {len(time_entries)} time entries")
        return time_entries
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Error fetching time entries: {e}")
        print(error_trace)
        detail = f"Failed to fetch time entries: {str(e)}\n{error_trace}"
        raise HTTPException(status_code=500, detail=detail)

@app.get("/time-entries/{id}", response_model=schemas.TimeEntry)
async def read_time_entry(id: str, db=Depends(get_db)):
    db_time_entry = await crud.get_time_entry(db, id=id)
    if db_time_entry is None:
        raise HTTPException(status_code=404, detail="Time entry not found")
    return db_time_entry

@app.put("/time-entries/{id}", response_model=schemas.TimeEntry)
async def update_time_entry(id: str, time_entry: schemas.TimeEntryUpdate, db=Depends(get_db)):
    try:
        db_time_entry = await crud.get_time_entry(db, id=id)
        if db_time_entry is None:
            raise HTTPException(status_code=404, detail="Time entry not found")
        
        result = await crud.update_time_entry(db=db, id=id, time_entry=time_entry)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error updating time entry: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to update time entry: {str(e)}")

@app.delete("/time-entries/{id}")
async def delete_time_entry(id: str, db=Depends(get_db)):
    db_time_entry = await crud.get_time_entry(db, id=id)
    if db_time_entry is None:
        raise HTTPException(status_code=404, detail="Time entry not found")
    await crud.delete_time_entry(db=db, id=id)
    return {"message": "Time entry deleted successfully"}

@app.get("/tasks/", response_model=List[schemas.Task])
async def read_tasks(db=Depends(get_db)):
    return await crud.get_tasks(db)

@app.post("/tasks/", response_model=schemas.Task)
async def create_task(task: schemas.TaskCreate, db=Depends(get_db)):
    return await crud.create_task(db=db, task=task)

@app.get("/tasks/{id}", response_model=schemas.Task)
async def read_task(id: str, db=Depends(get_db)):
    db_task = await crud.get_task(db, id=id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task

@app.delete("/tasks/{id}")
async def delete_task(id: str, db=Depends(get_db)):
    try:
        await crud.delete_task(db=db, id=id)
        return {"message": "Task deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error deleting task: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to delete task: {str(e)}")

@app.get("/stats/daily")
async def get_daily_stats(db=Depends(get_db)):
    return await crud.get_daily_stats(db)

@app.get("/stats/weekly")
async def get_weekly_stats(db=Depends(get_db)):
    return await crud.get_weekly_stats(db)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 