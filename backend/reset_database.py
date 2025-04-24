"""
Script to reset the Firestore database
This will delete all documents in the tasks, time_entries, and users collections
"""

import firebase_admin
from firebase_admin import credentials, firestore, auth
from database import get_db
import traceback

def reset_database():
    """Reset all data in the database"""
    try:
        print("Starting database reset...")
        
        # Get database instance
        db = get_db()
        
        # Collections to reset
        collections = ['tasks', 'time_entries', 'users']
        
        for collection_name in collections:
            # Delete all documents in collection
            print(f"Deleting all documents in {collection_name} collection...")
            
            # Get all documents
            docs = db.collection(collection_name).limit(500).stream()
            
            # Delete each document
            deleted_count = 0
            for doc in docs:
                doc.reference.delete()
                deleted_count += 1
            
            print(f"Deleted {deleted_count} documents from {collection_name}")
        
        # Delete all Firebase Auth users
        try:
            print("Deleting all Firebase Auth users...")
            
            # Get all users
            page = auth.list_users()
            users_to_delete = []
            
            # Collect user UIDs
            for user in page.iterate_all():
                users_to_delete.append(user.uid)
            
            if users_to_delete:
                # Delete users in batches (max 1000 at a time)
                for i in range(0, len(users_to_delete), 1000):
                    batch = users_to_delete[i:i+1000]
                    auth.delete_users(batch)
                print(f"Deleted {len(users_to_delete)} Firebase Auth users")
            else:
                print("No Firebase Auth users to delete")
        except Exception as e:
            print(f"Error deleting Firebase Auth users: {e}")
            print(traceback.format_exc())
        
        print("Database reset completed successfully")
    except Exception as e:
        print(f"Database reset failed: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    reset_database() 