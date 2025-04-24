"""
Test script for Firebase connectivity and authentication.
Run this script to check if Firebase is properly configured.
"""

import os
import firebase_admin
from firebase_admin import auth, credentials, firestore
from database import get_db
import traceback

def test_firebase_connection():
    """Test Firebase connectivity and authentication"""
    try:
        print("Testing Firebase connection...")
        
        # Get database instance
        db = get_db()
        
        # Test Firestore connection by listing collections
        collections = db.collections()
        collection_names = [collection.id for collection in collections]
        print(f"Found collections: {collection_names}")
        
        # Test Firebase Auth by listing users (up to 10)
        print("\nTesting Firebase Auth...")
        try:
            list_users = auth.list_users().iterate_all()
            users = []
            for user in list_users:
                users.append(user.email)
                if len(users) >= 10:
                    break
                    
            print(f"Found {len(users)} users: {users}")
        except Exception as e:
            print(f"Error listing users: {e}")
            print(traceback.format_exc())
        
        print("\nFirebase connection test completed successfully")
    except Exception as e:
        print(f"Firebase connection test failed: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    test_firebase_connection() 