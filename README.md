# Chrona Time Tracking Utility

Streamlined time tracking solution for professionals and teams with intuitive task management and insightful performance analytics.

![Screenshot 2025-04-22 233418](https://github.com/user-attachments/assets/cf6b65dc-4841-4968-a835-f06a2c0fb244)
![Screenshot 2025-04-22 222512](https://github.com/user-attachments/assets/5aef3078-04e6-4086-a19f-501eb8583ede)
![Screenshot 2025-04-22 222432](https://github.com/user-attachments/assets/d6b226d7-df01-4bb4-8e9d-ddfbe46074c2)
![Screenshot 2025-04-22 222504](https://github.com/user-attachments/assets/45572ffc-1d81-4d53-851a-967f3ad224e9)
![WhatsApp Image 2025-04-20 at 15 41 06_19c33fd3](https://github.com/user-attachments/assets/2612bb06-4181-4222-87ed-7e56b107ae49)
![WhatsApp Image 2025-04-20 at 15 41 06_d2e0ee7e](https://github.com/user-attachments/assets/b880ccf0-a720-482b-94da-eb42186826a5)
![WhatsApp Image 2025-04-20 at 15 41 05_96b40f6d](https://github.com/user-attachments/assets/260edcf9-2260-441b-9980-c26fe81377a3)


## The problem it solves

Chrona addresses the challenge of accurate time tracking and productivity management for freelancers, remote workers, and teams. Users can:
- Track time spent on specific tasks with a single click
- Organize work by projects and categories
- Generate detailed reports on productivity and billable hours
- Access their time data across web and desktop platforms
- Maintain accountability with historical time entry records

The solution eliminates manual time logging errors and provides visibility into how time is actually spent, helping professionals optimize their workflows and accurately bill clients.

## Challenges I ran into

Developing Chrona presented several technical hurdles:
1. **Cross-platform compatibility**: Creating a consistent experience across web and desktop required careful architecture design. We used React for the frontend and Flask for the backend to maintain code reusability.
2. **Real-time synchronization**: Ensuring time entries synchronized seamlessly between devices necessitated implementing websockets and a robust state management system.
3. **Authentication security**: We implemented JWT tokens with proper refresh mechanisms to maintain security while providing a seamless user experience.
4. **Performance optimization**: The time tracking component needed to run efficiently without consuming excessive resources, particularly in background mode.
5. **Firestore data modeling**: Designing an efficient database schema in Firestore required rethinking traditional relational models to leverage NoSQL capabilities properly.

## Technologies I used

Python, Flask, React, TypeScript, Firebase, Firestore, Material-UI, JWT, React Query, FastAPI, Docker, Render

## Links

- [API Documentation](https://chrona-backend.onrender.com/docs)
- [Live Demo](https://chrona-app.onrender.com)
- [GitHub Repository](https://github.com/zendrix396/chrona-public)

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
