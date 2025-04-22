import os
import json
from google.cloud import firestore
from google.oauth2 import service_account
from fastapi import Depends
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Firebase credentials from environment variables
CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH")
CREDENTIALS_JSON = os.getenv("FIREBASE_CREDENTIALS")

# Global database instance
_db = None

# Initialize Firestore and return database instance
def get_db():
    """Get Firestore database instance"""
    global _db
    
    if _db is not None:
        return _db
    
    try:
        # Use credentials from environment variable or file
        if CREDENTIALS_JSON:
            # Use inline JSON credentials
            cred_info = json.loads(CREDENTIALS_JSON)
            credentials = service_account.Credentials.from_service_account_info(cred_info)
        elif CREDENTIALS_PATH and os.path.exists(CREDENTIALS_PATH):
            # Use credentials file
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CREDENTIALS_PATH
            with open(CREDENTIALS_PATH, "r") as f:
                cred_info = json.load(f)
            credentials = service_account.Credentials.from_service_account_info(cred_info)
        else:
            # For development, use a mock database or raise an error
            print("WARNING: No Firebase credentials provided. Using mock database for development.")
            return None  # Replace with mock DB implementation if needed
            
        # Initialize Firestore client
        _db = firestore.Client(
            project=cred_info["project_id"], 
            credentials=credentials
        )
        
        print(f"Successfully connected to Firebase project: {cred_info['project_id']}")
        return _db
    except Exception as e:
        print(f"Error initializing Firestore: {str(e)}")
        raise 