# Chrona: Advanced Time Tracker System

A comprehensive time tracking system with global hotkey tracking, REST API backend, and beautiful dashboard visualizations.

# Screenshots

![Screenshot 2025-04-22 233418](https://github.com/user-attachments/assets/034b25b3-68b1-4440-a3db-8842bcff1d12)
![Screenshot 2025-04-22 233425](https://github.com/user-attachments/assets/ff40e36e-8025-4125-ab32-8f6b2afe11f0)
![Screenshot 2025-04-22 222432](https://github.com/user-attachments/assets/97174061-c399-4bd0-9782-f92444f00f5b)
![Screenshot 2025-04-22 222504](https://github.com/user-attachments/assets/bf4a6d37-f748-45c5-9e54-9ed91550eef6)
![Screenshot 2025-04-22 222512](https://github.com/user-attachments/assets/07f0d688-d7cf-48e0-ac47-7fc6e62859c7)


## Stack
 - React, React Native (Frontend)
 - FastAPI (Backend)
 - Firebase Firestore (Database)
 - Pyinstaller and other utilities (Windows Executable)

## Components

### 1. Backend API (FastAPI)

A robust REST API that manages time entries, tasks, and generates statistics.

- **Tech Stack**: FastAPI, Firebase Firestore, Pydantic
- **Location**: `/backend`
- **Deployment**: Render.com

### 2. Frontend Dashboard (React)

A beautiful, responsive dashboard for visualizing and managing time tracking data.

- **Tech Stack**: React, TypeScript, Material UI, Chart.js
- **Location**: `/frontend`
- **Deployment**: Render.com

### 3. Keyboard Tracking Utility (Python)

A background utility that tracks time with global hotkey (Ctrl+Alt+Shift+K) triggers.

- **Tech Stack**: Python, keyboard library, Tkinter
- **Location**: `/tracker`
- **Deployment**: Distributed as executable

## Setup and Running

### Firebase Setup

1. Create a Firebase project at [Firebase Console](https://console.firebase.google.com/)
2. Set up Firestore Database in your project
3. Generate service account credentials:
   - Go to Project Settings > Service Accounts
   - Generate a new private key (downloads a JSON file)
   - Rename it to `firebase-credentials.json` and place it in the `/backend` directory

### Backend

```bash
cd backend
pip install -r requirements.txt
# Configure Firebase (see backend/README.md)
uvicorn main:app --reload
```

Backend will be available at https://chrona-backend.onrender.com

### Frontend

```bash
cd frontend
npm install
npm start
```

Frontend will be available at http://localhost:3000

### Tracker Utility

```bash
cd tracker
pip install -r requirements.txt
python time_tracker.py
```

Once running, press `Ctrl+Shift+R` to start/stop time tracking.

## Features

- **Task Management**: Create and manage tasks
- **Time Entry Tracking**: Track time spent on tasks with precise start/end times
- **Global Hotkey Tracking**: Press `Ctrl+Shift+R` from anywhere to start/stop tracking
- **Real-time Dashboard**: Visualize time spent with charts and statistics
- **Daily and Weekly Reports**: Analyze your productivity patterns
- **Cloud Database**: Firebase Firestore for reliable cloud storage

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Tracker   │────▶│   Backend   │◀────│  Frontend   │
│  (Python)   │     │  (FastAPI)  │     │   (React)   │
└─────────────┘     └─────────────┘     └─────────────┘
                          │
                          ▼
                    ┌─────────────┐
                    │   Firebase  │
                    │  Firestore  │
                    └─────────────┘
```

- **Tracker** sends time entries to the Backend API
- **Frontend** retrieves and displays data from the Backend API
- **Backend** stores and retrieves data from Firebase Firestore
- All components can work independently or together
