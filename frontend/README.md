# Time Tracker Dashboard

A modern React-based dashboard for visualizing and managing time tracking data.

## Features

- Beautiful dashboard with charts and statistics
- Time entry management
- Task management
- Real-time duration tracking
- Responsive design for all devices

## Technologies Used

- React (with TypeScript)
- Material UI for beautiful components
- React Query for data fetching
- Chart.js for visualizations
- Day.js for date/time handling

## Setup

1. Install dependencies:
   ```
   npm install
   ```

2. Set up environment variables:
   Create a `.env` file with:
   ```
   REACT_APP_API_URL=https://chrona-backend.onrender.com
   ```

3. Start the development server:
   ```
   npm start
   ```

4. The application will be available at http://localhost:3000

## Deployment

This application is configured for deployment on Render.com or similar services.

1. Build the production version:
   ```
   npm run build
   ```

2. Deploy the `build` folder to your hosting service.

## Structure

- `src/components`: Reusable UI components
- `src/pages`: Main application pages
- `src/services`: API service layer
- `src/hooks`: Custom React hooks