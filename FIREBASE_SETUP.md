# Firebase Setup Guide for Chrona

This guide will help you set up Firebase for the Chrona Time Tracker application.

## 1. Create a Firebase Project

1. Go to the [Firebase Console](https://console.firebase.google.com/)
2. Click "Add project"
3. Enter a project name (e.g., "chrona-timetracker")
4. Accept the Firebase terms
5. Choose whether to enable Google Analytics (optional)
6. Click "Create Project"

## 2. Set up Firestore Database

1. In the Firebase console, navigate to your project
2. From the left menu, select "Build > Firestore Database"
3. Click "Create database"
4. Choose "Start in production mode" (recommended) or "Start in test mode" (for development only)
5. Select a location for your Firestore database that's closest to your users
6. Click "Enable"

## 3. Create Service Account Credentials

1. In the Firebase console, navigate to your project
2. Click the gear icon (⚙️) near the top left, then select "Project settings"
3. Go to the "Service accounts" tab
4. Click "Generate new private key"
5. Save the downloaded JSON file securely - this contains sensitive credentials!

## 4. Configure the Backend

1. Rename the downloaded JSON file to `firebase-credentials.json`
2. Place this file in the `/backend` directory of your Chrona project
3. Copy `.env.example` to `.env` in the `/backend` directory
4. Update the `.env` file with:
   ```
   FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json
   ```

Alternative: For production environments, you can set the credentials directly as an environment variable:

```
FIREBASE_CREDENTIALS={"type":"service_account","project_id":"your-project-id",... entire JSON content ...}
```

## 5. Security Rules (Optional but Recommended)

For better security, consider setting up Firestore security rules:

1. In the Firebase console, navigate to your project
2. From the left menu, select "Build > Firestore Database"
3. Click the "Rules" tab
4. Set up rules like:

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /tasks/{taskId} {
      allow read: if true;
      allow write: if request.auth != null;
    }
    match /time_entries/{entryId} {
      allow read: if true;
      allow write: if request.auth != null;
    }
  }
}
```

These rules allow anyone to read data but require authentication for writing. For a production application, you should implement proper authentication.

## 6. Verification

To verify your setup is working correctly:

1. Start the backend server:
   ```
   cd backend
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```

2. Visit http://localhost:8000/docs and try creating a task using the API
3. Check your Firestore database in the Firebase console to see if the task was created

## Troubleshooting

- **Authentication Failed**: Make sure your credentials file is correctly located and has not been modified
- **Permission Denied**: Check your Firestore security rules
- **Connection Issues**: Ensure your network allows outbound connections to Google services
- **Import Errors**: Verify you've installed all required dependencies with `pip install -r requirements.txt` 