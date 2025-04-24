import asyncio
from database import get_db
import sys

async def reset_db():
    try:
        # Get Firestore database instance
        db = get_db()
        
        # Delete all documents in the tasks collection
        print("Deleting all tasks...")
        tasks_ref = db.collection('tasks')
        tasks_docs = list(tasks_ref.stream())
        
        for doc in tasks_docs:
            print(f"Deleting task: {doc.id}")
            doc.reference.delete()
        
        # Delete all documents in the time_entries collection
        print("Deleting all time entries...")
        entries_ref = db.collection('time_entries')
        entries_docs = list(entries_ref.stream())
        
        for doc in entries_docs:
            print(f"Deleting time entry: {doc.id}")
            doc.reference.delete()
        
        print("Firestore collections have been reset successfully")
    except Exception as e:
        print(f"Error resetting Firestore collections: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("Starting Firestore reset...")
    asyncio.run(reset_db())
    print("Firestore reset complete!") 