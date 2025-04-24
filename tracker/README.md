# Time Tracker Utility

A background utility that tracks time spent on tasks with a global hotkey trigger.

## Features

- Global hotkey (Ctrl+Shift+R) to start/stop time tracking
- Minimal UI that doesn't interrupt your workflow
- Task selection from dropdown
- Real-time timer display
- Automatic synchronization with the backend API
- Windows administrator mode for global keyboard hooks

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Set the API URL (optional):
   ```
   # On Windows
   set TIME_TRACKER_API_URL=http://your-api-url
   
   # On macOS/Linux
   export TIME_TRACKER_API_URL=http://your-api-url
   ```

3. Run the tracker:
   ```
   python time_tracker.py
   ```
   
   Note: On Windows, the script will request administrator privileges to properly capture global hotkeys.

## Usage

1. Press `Ctrl+Shift+R` to open the tracker window
2. Select a task from the dropdown
3. Click "Start Tracking" or press Enter
4. The window will disappear, and tracking will begin in the background
5. Press `Ctrl+Shift+R` again to stop tracking
6. A summary window will appear showing the duration tracked

## Configuration

The configuration file is stored at `~/.time_tracker_config.json` and contains:

- `api_url`: The URL of the backend API

## Creating a Windows Executable

1. Install PyInstaller:
   ```
   pip install pyinstaller
   ```

2. Create the executable:
   ```
   pyinstaller --onefile --windowed time_tracker.py
   ```

3. The executable will be in the `dist` folder 