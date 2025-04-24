import asyncio
import sys
from database import get_db
from crud import create_task
from schemas import TaskCreate

async def add_test_task():
    try:
        # Get Firestore database instance
        db = get_db()
        
        # Create a test task
        task = TaskCreate(name="Test Task", description="A task for testing")
        created_task = await create_task(db=db, task=task)
        
        print(f"Created test task with ID: {created_task['id']}")
        print(f"Name: {created_task['name']}")
        print(f"Created at: {created_task['created_at']}")
    except Exception as e:
        print(f"Error creating test task: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("Creating test task...")
    asyncio.run(add_test_task())
    print("Done!") 