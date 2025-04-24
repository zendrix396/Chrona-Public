# Chrona - Time Tracking Application

Chrona is a comprehensive time tracking solution with a web frontend and desktop client, designed to help individuals and teams track time spent on tasks efficiently.

## Features

- **Track Time**: Start and stop timers for different tasks
- **Multiple Interfaces**: Web and desktop clients for flexibility
- **Task Management**: Create and manage tasks to track time against
- **Real-time Tracking**: Accurate time tracking with intuitive interface
- **Desktop Mini-timer**: Floating mini-timer for desktop users
- **Reports & Analytics**: View time usage statistics and reports

## Architecture

Chrona is built using a modern tech stack:

### Backend
- **FastAPI**: High-performance Python web framework
- **Firebase Firestore**: NoSQL database for data storage
- **JWT Authentication**: Secure user authentication
- **Pydantic**: Data validation and settings management

### Frontend (Web)
- **React**: JavaScript library for building user interfaces
- **Material-UI**: Modern UI component library
- **React Query**: Data fetching and state management
- **TypeScript**: Type-safe JavaScript

### Desktop Client
- **Python**: Core programming language
- **Tkinter**: GUI toolkit for desktop application
- **PyInstaller**: Packaging the desktop app
- **Firebase SDK**: Communication with backend

## Getting Started

### Prerequisites
- Python 3.8+
- Node.js 14+
- Firebase account

### Backend Setup

1. Clone the repository
2. Set up a virtual environment:
   ```
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Configure Firebase:
   - Create a Firebase project
   - Download Firebase credentials
   - Rename it to `firebase-credentials.json` and place it in the `/backend` directory
   - Or set the `FIREBASE_CREDENTIALS` environment variable with the JSON content

4. Run the backend:
   ```
   uvicorn main:app --reload
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Start the development server:
   ```
   npm start
   ```

### Desktop Client Setup

1. Install the required dependencies:
   ```
   pip install -r tracker/requirements.txt
   ```

2. Run the desktop client:
   ```
   python tracker/time_tracker.py
   ```

## Security Note

This is a public repository of Chrona. The code has been sanitized to remove any sensitive information. If you fork or clone this repository for your own use, make sure to:

1. Generate your own security keys
2. Set up your own Firebase project
3. Never commit any sensitive credentials to your repository

## License

MIT License 