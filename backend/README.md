# Time Tracker API

A FastAPI-based REST API for tracking time spent on different tasks.

## Features

- Task management
- Time entry tracking
- Statistics for daily and weekly analysis
- Async SQLAlchemy with SQLite (local) or PostgreSQL (production)

## Technology Stack

- FastAPI - Web framework
- Firebase Firestore - Database
- Pydantic - Data validation

## Setup

1. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Configure Firebase:

### Firebase Configuration

The application uses Firebase Firestore as its database. You need to set up Firebase credentials to use it:

1. Create a Firebase project at [Firebase Console](https://console.firebase.google.com/)
2. Go to Project Settings > Service Accounts
3. Generate a new private key (this will download a JSON file)
4. Rename the downloaded file to `firebase-credentials.json` and place it in the backend directory
   
Alternatively, you can set the credentials via environment variables:

- Copy `.env.example` to `.env`
- Either set `FIREBASE_CREDENTIALS_PATH` to point to your credentials file
- Or set `FIREBASE_CREDENTIALS` to the full JSON content of your credentials file (useful for production environments)

4. Run the development server:
   ```
   uvicorn main:app --reload
   ```

5. Access the API at http://localhost:8000
   - API documentation at http://localhost:8000/docs

## API Endpoints

- **GET /**: API status check
- **GET /tasks/**: List all tasks
- **POST /tasks/**: Create a new task
- **GET /time-entries/**: List all time entries
- **POST /time-entries/**: Create a new time entry
- **GET /time-entries/{id}**: Get a specific time entry
- **PUT /time-entries/{id}**: Update a time entry
- **DELETE /time-entries/{id}**: Delete a time entry
- **GET /stats/daily**: Get daily statistics
- **GET /stats/weekly**: Get weekly statistics

## Deployment

This API is configured for deployment on Render.com using the render.yaml file. 

## Database Schema

The application uses the following collections in Firestore:

- **tasks**: Stores information about tasks
  - id (string, auto-generated)
  - name (string)
  - description (string, optional)
  - created_at (timestamp)

- **time_entries**: Stores time tracking entries
  - id (string, auto-generated)
  - task_id (string, reference to tasks collection)
  - start_time (timestamp)
  - end_time (timestamp, optional)
  - duration (number, optional)
  - notes (string, optional)
  - created_at (timestamp) 