import os
import json
import firebase_admin
from firebase_admin import auth, credentials, firestore
from fastapi import Depends

# Hardcoded path to credentials
CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), "firebase-credentials.json")

# Global database instance
_db = None
_app = None

# Initialize Firebase and return database instance
def get_db():
    """Get Firestore database instance"""
    global _db, _app
    
    if _db is not None:
        return _db
    
    try:
        # Set environment variable for credentials
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CREDENTIALS_PATH
        
        # Initialize Firebase Admin if not already initialized
        if not firebase_admin._apps:
            cred = credentials.Certificate(CREDENTIALS_PATH)
            _app = firebase_admin.initialize_app(cred)
            print("Firebase Admin SDK initialized successfully")
        else:
            _app = firebase_admin.get_app()
            print("Using existing Firebase Admin SDK app")
        
        # Initialize Firestore client using the same app
        _db = firestore.client()
        print(f"Successfully connected to Firebase project")
        return _db
    except Exception as e:
        print(f"Error initializing Firebase: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise 