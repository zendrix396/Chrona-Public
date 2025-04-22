import keyboard
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import json
import os
import time
import requests
from datetime import datetime
import sys
import ctypes
import pystray
from PIL import Image, ImageDraw, ImageTk
from io import BytesIO
import traceback
import logging
import queue

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("time_tracker.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TimeTracker")

# Configuration
CONFIG_FILE = os.path.join(os.path.expanduser('~'), '.time_tracker_config.json')
API_URL = os.environ.get('TIME_TRACKER_API_URL', 'https://chrona-backend.onrender.com')
HOTKEY = 'ctrl+shift+alt+k'  # Changed from 'ctrl+shift+u' to 'ctrl+shift+alt+k'

class TimeTrackerApp:
    def __init__(self):
        self.root = None
        self.tracking = False
        self.current_task_id = None
        self.start_time = None
        self.tasks = []
        self.entry_id = None
        self.timer_thread = None
        self.stop_thread = False
        self.icon = None  # System tray icon
        self.command_queue = queue.Queue()  # Queue for thread-safe command execution
        
        # Load config
        self.load_config()
        
        # Test API connection on startup
        self.test_api_connection()
        
        # Register global hotkey
        keyboard.add_hotkey(HOTKEY, self.queue_command, args=('toggle_tracker',))
        
        logger.info(f"Time Tracker started. Press {HOTKEY} to start/stop tracking.")
        print(f"Time Tracker started. Press {HOTKEY} to start/stop tracking.")
        
        # Start tkinter main window (hidden)
        self.setup_root_window()
        
        # Create system tray icon in a separate thread
        self.setup_system_tray()
    
    def queue_command(self, command, *args):
        """Add a command to the queue to be executed in the main thread"""
        logger.debug(f"Queuing command: {command}")
        self.command_queue.put((command, args))
        
        # Schedule command processing in the Tkinter main thread
        if hasattr(self, 'root') and self.root is not None:
            self.root.after(10, self.process_command_queue)
    
    def process_command_queue(self):
        """Process commands from the queue in the main thread"""
        try:
            while not self.command_queue.empty():
                command, args = self.command_queue.get_nowait()
                logger.debug(f"Processing command: {command}")
                
                if command == 'toggle_tracker':
                    self.toggle_tracker()
                elif command == 'refresh_tasks':
                    self.refresh_tasks()
                elif command == 'test_api':
                    self.test_and_show_api_status()
                elif command == 'show_tracker':
                    self.show_tracker_window()
                elif command == 'exit_app':
                    self.exit_app()
                elif command == 'stop_tracking':
                    self.stop_tracking()
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            logger.error(traceback.format_exc())
        
        # Schedule the next check if root exists
        if hasattr(self, 'root') and self.root:
            self.root.after(100, self.process_command_queue)
    
    def setup_root_window(self):
        """Setup the main root window"""
        self.root = tk.Tk()
        self.root.title("Time Tracker")
        
        # Make window invisible (0x0 size and positioned off-screen)
        self.root.geometry("1x1+0+0")
        self.root.withdraw()
        
        # Make it impossible to show this window again
        self.root.attributes('-alpha', 0.0)  # Fully transparent
        
        # Prevent the application from exiting when the root window is closed
        self.root.protocol("WM_DELETE_WINDOW", self.hide_root_window)
        
        # Set icon if available
        try:
            icon_img = self.create_tray_icon()
            icon_tk = ImageTk.PhotoImage(icon_img)
            self.root.iconphoto(False, icon_tk)
        except Exception as e:
            logger.error(f"Error setting icon: {e}")
        
        # Start processing commands
        self.root.after(100, self.process_command_queue)
        
        # Start main thread Timer to keep a background timer running
        self.root.after(1000, self.update_timer)
    
    def hide_root_window(self):
        """Hide the root window instead of closing it"""
        self.root.withdraw()
        # This prevents the window from being closed and keeps the app running
    
    def update_timer(self):
        """Update the timer if it's active"""
        try:
            if self.tracking and self.start_time:
                duration = self.calculate_duration()
                formatted = self.format_duration(duration)
                
                # Update timer label if it exists and is valid
                if hasattr(self, 'timer_label') and self.timer_label.winfo_exists():
                    self.timer_label.config(text=formatted)
                
                # Update system tray tooltip with current time
                if self.icon and hasattr(self, 'current_task_name'):
                    self.icon.title = f"Time Tracker - {self.current_task_name}: {formatted}"
        except Exception as e:
            logger.error(f"Error updating timer: {e}")
        
        # Schedule the next update
        if hasattr(self, 'root') and self.root:
            self.root.after(1000, self.update_timer)
    
    def test_api_connection(self):
        """Test the API connection and log details"""
        try:
            logger.info(f"Testing API connection to {self.api_url}...")
            response = requests.get(f"{self.api_url}/")
            logger.info(f"API status code: {response.status_code}")
            if response.status_code == 200:
                logger.info("API connection successful!")
                return True
            else:
                logger.error(f"API returned non-200 status: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
        except requests.RequestException as e:
            logger.error(f"API connection error: {e}")
            return False
    
    def create_tray_icon(self):
        """Create a simple clock icon for the system tray"""
        width = 64
        height = 64
        color1 = (66, 133, 244)  # Blue color
        color2 = (234, 67, 53)   # Red color
        
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        dc = ImageDraw.Draw(image)
        
        # Draw a clock face
        dc.ellipse((4, 4, width-4, height-4), fill=(255, 255, 255, 220), outline=color1, width=2)
        
        # Draw clock hands
        center_x, center_y = width // 2, height // 2
        # Hour hand
        dc.line((center_x, center_y, center_x - 15, center_y + 10), fill=color1, width=3)
        # Minute hand
        dc.line((center_x, center_y, center_x + 5, center_y - 20), fill=color2, width=3)
        
        return image
    
    def setup_system_tray(self):
        """Setup the system tray icon and menu"""
        # Create a separate thread for the system tray icon
        tray_thread = threading.Thread(target=self.run_system_tray)
        tray_thread.daemon = True
        tray_thread.start()
    
    def run_system_tray(self):
        """Run the system tray icon in a separate thread"""
        try:
            icon_image = self.create_tray_icon()
            
            menu = (
                pystray.MenuItem('Show Tracker', 
                            lambda: self.queue_command('show_tracker')),
                pystray.MenuItem('Refresh Tasks', 
                            lambda: self.queue_command('refresh_tasks')),
                pystray.MenuItem('Test API Connection', 
                            lambda: self.queue_command('test_api')),
                pystray.MenuItem('Exit', 
                            lambda: self.queue_command('exit_app'))
            )
            
            self.icon = pystray.Icon("time_tracker", icon_image, "Time Tracker", menu)
            
            # Start the icon
            self.icon.run()
        except Exception as e:
            logger.error(f"Error running system tray: {e}")
            logger.error(traceback.format_exc())
    
    def test_and_show_api_status(self):
        """Test API connection and show the result"""
        if self.test_api_connection():
            messagebox.showinfo("API Connection", "Successfully connected to the API!")
        else:
            messagebox.showerror("API Connection Error", 
                               f"Failed to connect to the API at {self.api_url}. Please check that the backend is running.")
    
    def exit_app(self):
        """Safely exit the application"""
        try:
            # Stop any tracking if active
            if self.tracking:
                self.stop_tracking()
            
            # Stop the system tray icon
            if self.icon:
                try:
                    self.icon.stop()
                except Exception as e:
                    logger.error(f"Error stopping icon: {e}")
            
            # Ensure all threads are terminated
            self.stop_thread = True
            
            # Destroy root window
            if hasattr(self, 'root') and self.root:
                self.root.quit()
                self.root.destroy()
            
            # Exit the application
            logger.info("Application exiting...")
            os._exit(0)
        except Exception as e:
            logger.error(f"Error during exit: {e}")
            os._exit(1)
    
    def refresh_tasks(self):
        """Refresh tasks from the database"""
        tasks = self.fetch_tasks()
        if tasks:
            logger.info(f"Successfully loaded {len(tasks)} tasks")
            messagebox.showinfo("Tasks Refreshed", f"Successfully loaded {len(tasks)} tasks from the database.")
        else:
            logger.warning("Could not refresh tasks")
            messagebox.showwarning("Refresh Failed", "Could not refresh tasks. Check API connection.")
        
        # If the task window is open, update the dropdown
        if hasattr(self, 'task_window') and self.task_window and self.task_window.winfo_exists():
            try:
                if hasattr(self, 'task_dropdown'):
                    # Update the dropdown values
                    self.task_dropdown['values'] = [task['name'] for task in tasks]
                    # Reset the selection
                    self.task_var.set('')
            except Exception as e:
                logger.error(f"Error updating task dropdown: {e}")
    
    def load_config(self):
        try:
            # Always use production API for deployment
            self.api_url = 'https://chrona-backend.onrender.com'
            
            # Save the config
            self.save_config()
                
            logger.info(f"Using API URL: {self.api_url}")
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self.api_url = API_URL
    
    def save_config(self):
        try:
            config = {
                'api_url': self.api_url
            }
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f)
            logger.info(f"Config saved to {CONFIG_FILE}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def fetch_tasks(self):
        try:
            logger.info(f"Fetching tasks from {self.api_url}/tasks/")
            response = requests.get(f"{self.api_url}/tasks/")
            logger.info(f"Tasks API status code: {response.status_code}")
            
            if response.status_code == 200:
                self.tasks = response.json()
                logger.info(f"Fetched {len(self.tasks)} tasks")
                return self.tasks
            else:
                logger.error(f"Error fetching tasks: Status {response.status_code}, Response: {response.text}")
                return []
        except Exception as e:
            logger.error(f"Error connecting to API: {e}")
            logger.error(traceback.format_exc())
            return []
    
    def create_time_entry(self, task_id):
        try:
            # Format the datetime as ISO 8601 string without timezone information
            # The API expects this format with precision up to seconds only
            start_time = datetime.now().replace(microsecond=0).isoformat()
            
            data = {
                'task_id': task_id,  # Now a string ID for Firebase
                'start_time': start_time,
                'end_time': None,
                'duration': None,
                'notes': None
            }
            
            logger.info(f"Creating time entry for task ID {task_id} at {self.api_url}/time-entries/")
            logger.debug(f"Request data: {data}")
            
            # First verify the task exists in our local tasks list
            task_exists = any(task['id'] == task_id for task in self.tasks)
            if not task_exists:
                logger.error(f"Task with ID {task_id} not found in local task list")
                messagebox.showerror("Error", f"Task with ID {task_id} not found in local task list.")
                return None
            
            # Add headers to indicate JSON content
            headers = {'Content-Type': 'application/json'}
            
            response = requests.post(
                f"{self.api_url}/time-entries/", 
                json=data, 
                headers=headers,
                timeout=10
            )
            
            logger.info(f"Create time entry status code: {response.status_code}")
            
            if response.status_code == 200 or response.status_code == 201:  # Accept both 200 and 201
                try:
                    entry = response.json()
                    logger.info(f"Created time entry with ID {entry.get('id')}")
                    return entry
                except Exception as e:
                    logger.error(f"Error parsing response JSON: {e}")
                    logger.error(f"Response text: {response.text[:500]}")
                    messagebox.showerror("Error", f"Server returned invalid data. Check logs for details.")
                    return None
            else:
                error_message = "Unknown error"
                try:
                    error_data = response.json()
                    if isinstance(error_data, dict):
                        error_message = error_data.get("detail", error_data)
                    else:
                        error_message = str(error_data)
                except Exception:
                    error_message = response.text[:500]  # Limit the length
                
                logger.error(f"Error creating time entry: Status {response.status_code}")
                logger.error(f"Error details: {error_message}")
                
                # More descriptive error message
                error_to_show = f"Failed to create time entry (HTTP {response.status_code}).\n\nDetails: {error_message}"
                messagebox.showerror("API Error", error_to_show)
                return None
        except requests.RequestException as e:
            logger.error(f"Request exception: {e}")
            error_msg = f"Failed to connect to API: {str(e)}"
            messagebox.showerror("Connection Error", error_msg)
            return None
        except Exception as e:
            logger.error(f"Error connecting to API: {e}")
            logger.error(traceback.format_exc())
            return None
    
    def update_time_entry(self, entry_id):
        try:
            # Format end_time as ISO 8601 string without timezone information
            # The API expects this format with precision up to seconds only
            end_time = datetime.now().replace(microsecond=0).isoformat()
            
            # Calculate duration in minutes
            duration_minutes = self.calculate_duration() / 60
            
            data = {
                'end_time': end_time,
                'duration': duration_minutes,
                'notes': None
            }
            
            logger.info(f"Updating time entry ID {entry_id} at {self.api_url}/time-entries/{entry_id}")
            logger.debug(f"Request data: {data}")
            
            # Add headers to indicate JSON content
            headers = {'Content-Type': 'application/json'}
            
            response = requests.put(
                f"{self.api_url}/time-entries/{entry_id}", 
                json=data, 
                headers=headers,
                timeout=10
            )
            
            logger.info(f"Update time entry status code: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    entry = response.json()
                    logger.info(f"Updated time entry with ID {entry.get('id')}")
                    return entry
                except Exception as e:
                    logger.error(f"Error parsing response JSON: {e}")
                    logger.error(f"Response text: {response.text[:500]}")
                    messagebox.showerror("Error", f"Server returned invalid data. Check logs for details.")
                    return None
            else:
                error_message = "Unknown error"
                try:
                    error_data = response.json()
                    if isinstance(error_data, dict):
                        error_message = error_data.get("detail", error_data)
                    else:
                        error_message = str(error_data)
                except Exception:
                    error_message = response.text[:500]
                
                logger.error(f"Error updating time entry: Status {response.status_code}")
                logger.error(f"Error details: {error_message}")
                
                # Show error message
                error_to_show = f"Failed to update time entry (HTTP {response.status_code}).\n\nDetails: {error_message}"
                messagebox.showerror("API Error", error_to_show)
                return None
        except Exception as e:
            logger.error(f"Error connecting to API: {e}")
            logger.error(traceback.format_exc())
            return None
    
    def calculate_duration(self):
        if self.start_time:
            now = datetime.now()
            duration = now - self.start_time
            return int(duration.total_seconds())
        return 0
    
    def format_duration(self, seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def toggle_tracker(self):
        """Toggle time tracking"""
        if self.tracking:
            # Stop tracking
            self.stop_tracking()
        else:
            # Start tracking
            logger.info("Showing tracker window...")
            # Don't show root window, just create the task selection as independent window
            self.show_tracker_window()
    
    def show_tracker_window(self):
        """Show the task selection window"""
        # Safely destroy any existing window
        if hasattr(self, 'task_window') and self.task_window:
            try:
                if self.task_window.winfo_exists():
                    self.task_window.destroy()
            except Exception as e:
                logger.error(f"Error destroying existing task window: {e}")
                pass
        
        # Refresh tasks before showing window
        self.tasks = self.fetch_tasks()
        if not self.tasks:
            logger.error("No tasks fetched, showing error")
            messagebox.showerror("Error", "Failed to fetch tasks. Check API connection and try again.")
            return
        
        logger.info(f"Creating new task window with {len(self.tasks)} tasks")
        
        # Create a new independent Toplevel window
        self.task_window = tk.Toplevel()
        self.task_window.title("Time Tracker")
        self.task_window.geometry("400x400")  # Made slightly taller for the new button
        
        # Make sure it appears on top of other windows
        self.task_window.attributes('-topmost', True)
        
        # Don't make it depend on the root window
        self.task_window.transient()  # Make it independent
        
        # Handle window close - just hide the window
        self.task_window.protocol("WM_DELETE_WINDOW", self.task_window.withdraw)
        
        # Center the window
        self.center_window(self.task_window)
        
        # Create frame
        frame = ttk.Frame(self.task_window, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Add app icon
        icon_img = self.create_tray_icon()
        # Convert PIL image to tkinter PhotoImage
        icon_tk = ImageTk.PhotoImage(icon_img)
        self.task_window.iconphoto(False, icon_tk)
        
        # Header with icon
        header_frame = ttk.Frame(frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Display smaller icon in the header
        small_icon = icon_img.resize((32, 32))
        small_icon_tk = ImageTk.PhotoImage(small_icon)
        icon_label = ttk.Label(header_frame, image=small_icon_tk)
        icon_label.image = small_icon_tk  # Keep a reference
        icon_label.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(header_frame, text="Track Time", font=("Arial", 16, "bold")).pack(side=tk.LEFT)
        
        # Task selection
        ttk.Label(frame, text="Select Task:").pack(anchor="w")
        
        self.task_var = tk.StringVar()
        self.task_dropdown = ttk.Combobox(frame, textvariable=self.task_var, width=40)
        self.task_dropdown['values'] = [task['name'] for task in self.tasks]
        if self.task_dropdown['values']:
            self.task_dropdown.current(0)  # Select first task by default
        self.task_dropdown.pack(pady=(5, 15), fill="x")
        
        # API URL display and testing
        api_frame = ttk.Frame(frame)
        api_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(api_frame, text=f"API: {self.api_url}", font=("Arial", 9)).pack(side=tk.LEFT)
        ttk.Button(api_frame, text="Test", command=self.test_and_show_api_status, width=8).pack(side=tk.RIGHT)
        ttk.Button(api_frame, text="Refresh", command=self.refresh_tasks, width=8).pack(side=tk.RIGHT, padx=(0, 5))
        
        # Add detailed API test button
        ttk.Button(api_frame, text="Debug API", command=self.run_detailed_api_test, width=10).pack(side=tk.RIGHT, padx=(0, 5))
        
        # Timer display
        self.timer_label = ttk.Label(frame, text="00:00:00", font=("Arial", 24))
        self.timer_label.pack(pady=(5, 20))
        
        # Start button
        start_button = ttk.Button(frame, text="Start Tracking", 
                               command=self.handle_start_button)
        start_button.pack(pady=(0, 10), fill="x")
        
        # Cancel button
        cancel_button = ttk.Button(frame, text="Cancel", 
                               command=self.task_window.withdraw)
        cancel_button.pack(fill="x")
        
        # Force update and focus on the dropdown
        self.task_window.update_idletasks()
        self.task_dropdown.focus_set()
        
        # Ensure it's visible
        self.task_window.lift()
        self.task_window.attributes('-topmost', True)
        # Remove topmost after a short delay to avoid it staying on top permanently
        self.task_window.after(2000, lambda: self.task_window.attributes('-topmost', False))
        
        logger.info("Task window created and shown")
    
    def handle_start_button(self):
        """Handle the start tracking button click"""
        selected_task = self.task_var.get()
        
        if not selected_task:
            messagebox.showwarning("Warning", "Please select a task first")
            return
        
        # Find the task ID for the selected task name
        task_id = None
        for task in self.tasks:
            if task['name'] == selected_task:
                task_id = task['id']
                break
        
        if task_id:
            self.start_tracking(task_id)
        else:
            messagebox.showerror("Error", "Task not found")
    
    def center_window(self, window):
        """Center a window on the screen"""
        try:
            window.update_idletasks()
            width = window.winfo_width()
            height = window.winfo_height()
            x = (window.winfo_screenwidth() // 2) - (width // 2)
            y = (window.winfo_screenheight() // 2) - (height // 2)
            window.geometry(f"{width}x{height}+{x}+{y}")
        except Exception as e:
            logger.error(f"Error centering window: {e}")
    
    def start_tracking(self, task_id):
        try:
            # First try to get the task from our local cache
            current_task = None
            for task in self.tasks:
                if task['id'] == task_id:
                    current_task = task
                    break
            
            if not current_task:
                logger.error(f"Task with ID {task_id} not found in tasks list")
                messagebox.showerror("Error", "Selected task could not be found. Please try again.")
                return
            
            # Store task info
            self.current_task_id = task_id
            self.current_task_name = current_task['name']
            self.start_time = datetime.now()
            
            # Create time entry in API
            entry = self.create_time_entry(task_id)
            if entry:
                self.entry_id = entry.get('id')  # Store string ID from Firebase
                logger.info(f"Started tracking task '{current_task['name']}' with entry ID {self.entry_id}")
                
                # Set tracking flag
                self.tracking = True
                
                # Update icon tooltip
                if self.icon:
                    self.icon.title = f"Time Tracker - {current_task['name']}: 00:00:00"
                
                # If task window exists, destroy it
                self.safe_destroy(getattr(self, 'task_window', None))
                
                # Show mini timer
                self.show_mini_timer()
            else:
                logger.error("Failed to create time entry, not starting tracking")
        except Exception as e:
            logger.error(f"Error starting tracking: {e}")
            logger.error(traceback.format_exc())
            messagebox.showerror("Error", f"Failed to start tracking: {str(e)}")
    
    def show_mini_timer(self):
        """Show a small, draggable timer window"""
        # Check if there's an existing mini timer window and destroy it
        if hasattr(self, 'mini_timer_window') and self.mini_timer_window and self.mini_timer_window.winfo_exists():
            try:
                self.mini_timer_window.destroy()
            except Exception:
                pass
        
        # Create mini timer window
        self.mini_timer_window = tk.Toplevel(self.root)
        self.mini_timer_window.title("")
        self.mini_timer_window.geometry("120x35")
        self.mini_timer_window.overrideredirect(True)  # Remove window decorations
        self.mini_timer_window.attributes('-topmost', True)  # Keep on top
        self.mini_timer_window.configure(bg='black')
        
        # Position at the top-right corner initially
        screen_width = self.mini_timer_window.winfo_screenwidth()
        self.mini_timer_window.geometry(f"+{screen_width-130}+10")
        
        # Create frame
        frame = tk.Frame(self.mini_timer_window, bg='black')
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Timer label
        self.mini_timer_label = tk.Label(
            frame, 
            text="00:00:00", 
            font=("Consolas", 14, "bold"), 
            fg="#00FF00", 
            bg="black"
        )
        self.mini_timer_label.pack(fill=tk.BOTH, expand=True)
        
        # Make window draggable
        self.mini_timer_window.bind("<ButtonPress-1>", self.start_drag)
        self.mini_timer_window.bind("<ButtonRelease-1>", self.stop_drag)
        self.mini_timer_window.bind("<B1-Motion>", self.on_drag)
        
        # Add keyboard shortcuts
        self.mini_timer_window.bind("<KeyPress>", self.handle_key_press)
        
        # Set opacity level
        self.opacity = 0.8
        self.update_opacity()
        
        # Start updating the timer
        self.update_mini_timer()
    
    def update_mini_timer(self):
        """Update the mini timer display"""
        if self.tracking and hasattr(self, 'mini_timer_label') and self.mini_timer_label.winfo_exists():
            duration = self.calculate_duration()
            formatted = self.format_duration(duration)
            self.mini_timer_label.config(text=formatted)
            
            # Schedule the next update
            if hasattr(self, 'mini_timer_window') and self.mini_timer_window:
                self.mini_timer_window.after(1000, self.update_mini_timer)
    
    def start_drag(self, event):
        """Start dragging the mini timer window"""
        self.x = event.x
        self.y = event.y
    
    def stop_drag(self, event):
        """Stop dragging the mini timer window"""
        self.x = None
        self.y = None
    
    def on_drag(self, event):
        """Handle dragging the mini timer window"""
        if hasattr(self, 'mini_timer_window') and self.mini_timer_window:
            x = self.mini_timer_window.winfo_x() - self.x + event.x
            y = self.mini_timer_window.winfo_y() - self.y + event.y
            self.mini_timer_window.geometry(f"+{x}+{y}")
    
    def handle_key_press(self, event):
        """Handle keyboard shortcuts for the mini timer"""
        key = event.char.lower()
        
        if key == 'p':
            # Toggle pause
            if self.tracking:
                self.toggle_tracker()
        elif key == 'o':
            # Toggle opacity
            self.cycle_opacity()
    
    def cycle_opacity(self):
        """Cycle through opacity levels"""
        # Cycle through opacity levels: 0.8 -> 0.6 -> 0.4 -> 0.9
        opacity_levels = [0.8, 0.6, 0.4, 0.9]
        current_index = opacity_levels.index(self.opacity) if self.opacity in opacity_levels else 0
        next_index = (current_index + 1) % len(opacity_levels)
        self.opacity = opacity_levels[next_index]
        self.update_opacity()
    
    def update_opacity(self):
        """Update the opacity of the mini timer window"""
        if hasattr(self, 'mini_timer_window') and self.mini_timer_window:
            try:
                self.mini_timer_window.attributes('-alpha', self.opacity)
            except Exception as e:
                logger.error(f"Error setting opacity: {e}")
    
    def debug_api_connection(self):
        """Debug API connection issues"""
        logger.debug("Starting API connection debugging")
        try:
            # Test API root endpoint
            try:
                root_response = requests.get(f"{self.api_url}/", timeout=5)
                logger.debug(f"API root endpoint: Status {root_response.status_code}, Response: {root_response.text[:200]}")
            except requests.RequestException as e:
                logger.debug(f"API root endpoint error: {e}")
            
            # Test tasks endpoint
            try:
                tasks_response = requests.get(f"{self.api_url}/tasks/", timeout=5)
                logger.debug(f"Tasks endpoint: Status {tasks_response.status_code}, Response: {tasks_response.text[:200]}")
            except requests.RequestException as e:
                logger.debug(f"Tasks endpoint error: {e}")
            
            # Test time-entries endpoint
            try:
                entries_response = requests.get(f"{self.api_url}/time-entries/", timeout=5)
                logger.debug(f"Time-entries endpoint: Status {entries_response.status_code}, Response: {entries_response.text[:200]}")
            except requests.RequestException as e:
                logger.debug(f"Time-entries endpoint error: {e}")
                
            # Check if the API URL is correctly formed
            logger.debug(f"API URL format check: {'http' in self.api_url.lower()}")
            
            # Create a test time entry
            try:
                logger.debug("Attempting to create a test time entry...")
                test_data = {
                    'task_id': next((task['id'] for task in self.tasks if len(self.tasks) > 0), None),
                    'start_time': datetime.now().isoformat(),
                    'test': True  # Flag to indicate this is a test entry
                }
                if test_data['task_id']:
                    logger.debug(f"Test data: {test_data}")
                    test_response = requests.post(f"{self.api_url}/time-entries/", json=test_data, timeout=5)
                    logger.debug(f"Test time entry creation: Status {test_response.status_code}")
                    logger.debug(f"Response: {test_response.text[:500]}")
                else:
                    logger.debug("No tasks available for testing time entry creation")
            except requests.RequestException as e:
                logger.debug(f"Test time entry creation error: {e}")
            
            # Test if the server is reachable
            try:
                import socket
                api_host = self.api_url.replace("http://", "").replace("https://", "").split("/")[0]
                if ":" in api_host:
                    host, port = api_host.split(":")
                    port = int(port)
                else:
                    host = api_host
                    port = 80 if "http://" in self.api_url else 443
                
                logger.debug(f"Testing socket connection to {host}:{port}")
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(5)
                result = s.connect_ex((host, port))
                s.close()
                logger.debug(f"Socket connection result: {result} (0 means success)")
            except Exception as e:
                logger.debug(f"Socket connection test error: {e}")
            
        except Exception as e:
            logger.debug(f"Debug API connection error: {e}")
            logger.debug(traceback.format_exc())
    
    def stop_tracking(self):
        """Stop tracking time"""
        if not self.tracking or not self.entry_id:
            return
        
        # Update entry in the API
        entry = self.update_time_entry(self.entry_id)
        if entry:
            duration = self.calculate_duration()
            formatted = self.format_duration(duration)
            
            self.tracking = False
            self.stop_thread = True
            
            logger.info(f"Tracking stopped. Duration: {formatted}")
            
            # Close the mini timer window
            if hasattr(self, 'mini_timer_window') and self.mini_timer_window and self.mini_timer_window.winfo_exists():
                self.mini_timer_window.destroy()
            
            # Reset the system tray icon tooltip
            if self.icon:
                self.icon.title = "Time Tracker"
            
            # Find the task name since it's no longer included in the response
            task_name = self.current_task_name
            
            # Show the final duration
            self.show_final_duration(task_name, formatted)
        else:
            messagebox.showerror("Error", "Failed to stop tracking. Check API connection.")
    
    def show_final_duration(self, task_name, duration):
        """Show the final duration in a window"""
        # Check if there's an existing result window and destroy it
        if hasattr(self, 'result_window') and self.result_window and self.result_window.winfo_exists():
            try:
                self.result_window.destroy()
            except Exception:
                pass
        
        # Create a new window
        self.result_window = tk.Toplevel(self.root)
        self.result_window.title("Time Tracked")
        self.result_window.geometry("300x150")
        self.result_window.protocol("WM_DELETE_WINDOW", lambda: self.safe_destroy(self.result_window))
        
        # Set attributes
        self.result_window.attributes('-topmost', True)
        self.center_window(self.result_window)
        
        # Create frame
        frame = ttk.Frame(self.result_window, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Add labels and button
        ttk.Label(frame, text="Time tracked for:", font=("Arial", 12)).pack(pady=(0, 5))
        ttk.Label(frame, text=task_name, font=("Arial", 14, "bold")).pack(pady=(0, 10))
        ttk.Label(frame, text=duration, font=("Arial", 16)).pack(pady=(0, 15))
        
        ttk.Button(frame, text="Close", command=lambda: self.safe_destroy(self.result_window)).pack()
        
        # Auto-close after 5 seconds
        self.result_window.after(5000, lambda: self.safe_destroy(self.result_window))
    
    def safe_destroy(self, window):
        """Safely destroy a window if it exists"""
        try:
            if window and window.winfo_exists():
                window.destroy()
        except Exception:
            pass
            
    def start(self):
        """Start the main application loop"""
        try:
            logger.info("Starting main Tkinter loop")
            
            # Ensure the window stays hidden
            self.root.withdraw()
            
            # Create a message showing that the app is running in the system tray
            if self.icon:
                # Short delay to make sure system tray icon is visible
                time.sleep(0.5)
                self.icon.notify(
                    "Time Tracker is running in the system tray", 
                    "Time Tracker"
                )
            
            # Start the main event loop
            self.root.mainloop()
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            logger.error(traceback.format_exc())
    
    def run_detailed_api_test(self):
        """Run a detailed API test and show results"""
        results = {}
        test_window = tk.Toplevel(self.root)
        test_window.title("API Endpoint Test Results")
        test_window.geometry("500x400")
        test_window.attributes('-topmost', True)
        self.center_window(test_window)
        
        # Create a text widget to display results
        result_text = tk.Text(test_window, wrap=tk.WORD, font=("Courier", 9))
        result_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add a scroll bar
        scrollbar = ttk.Scrollbar(result_text, command=result_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        result_text.config(yscrollcommand=scrollbar.set)
        
        # Function to append text
        def append_text(text):
            result_text.config(state=tk.NORMAL)
            result_text.insert(tk.END, text + "\n")
            result_text.see(tk.END)
            result_text.config(state=tk.DISABLED)
            test_window.update()
        
        append_text(f"API URL: {self.api_url}")
        append_text("Starting API tests...\n")
        
        # Test root endpoint
        try:
            append_text("Testing root endpoint...")
            response = requests.get(f"{self.api_url}/", timeout=5)
            results['root'] = f"Status: {response.status_code}, Response: {response.text[:100]}"
            append_text(f"✓ Root endpoint: {response.status_code}\n")
        except Exception as e:
            results['root'] = f"Error: {str(e)}"
            append_text(f"❌ Root endpoint error: {str(e)}\n")
        
        # Test tasks endpoint
        try:
            append_text("Testing tasks endpoint...")
            response = requests.get(f"{self.api_url}/tasks/", timeout=5)
            results['tasks'] = f"Status: {response.status_code}, Tasks: {len(response.json())}"
            append_text(f"✓ Tasks endpoint: {response.status_code}, Found {len(response.json())} tasks\n")
        except Exception as e:
            results['tasks'] = f"Error: {str(e)}"
            append_text(f"❌ Tasks endpoint error: {str(e)}\n")
        
        # Test time entries GET endpoint
        try:
            append_text("Testing time-entries GET endpoint...")
            response = requests.get(f"{self.api_url}/time-entries/", timeout=5)
            results['time_entries_get'] = f"Status: {response.status_code}, Entries: {len(response.json()) if response.status_code == 200 else 'N/A'}"
            append_text(f"✓ Time entries GET: {response.status_code}\n")
        except Exception as e:
            results['time_entries_get'] = f"Error: {str(e)}"
            append_text(f"❌ Time entries GET error: {str(e)}\n")
        
        # Test time entries POST endpoint with a test task
        if self.tasks:
            try:
                test_task_id = self.tasks[0]['id']
                append_text(f"Testing time-entries POST endpoint with task ID {test_task_id}...")
                
                # Format the datetime as ISO 8601 string without timezone information
                start_time = datetime.now().isoformat(timespec='seconds')
                
                test_data = {
                    'task_id': test_task_id,
                    'start_time': start_time,
                    'end_time': None,
                    'duration': None,
                    'notes': None
                }
                
                append_text(f"Request data: {json.dumps(test_data)}")
                
                # Add headers to indicate JSON content
                headers = {'Content-Type': 'application/json'}
                
                response = requests.post(
                    f"{self.api_url}/time-entries/", 
                    json=test_data, 
                    headers=headers,
                    timeout=10
                )
                
                results['time_entries_post'] = f"Status: {response.status_code}, Response: {response.text[:100]}"
                
                if response.status_code in [200, 201]:
                    append_text(f"✓ Time entries POST: {response.status_code}, Entry created successfully\n")
                    entry_id = response.json().get('id')
                    
                    # If successful, test the PUT endpoint too to complete the test entry
                    if entry_id:
                        append_text(f"Testing time-entries PUT endpoint with entry ID {entry_id}...")
                        
                        # Format end_time as ISO 8601 string without timezone information
                        end_time = datetime.now().isoformat(timespec='seconds')
                        
                        update_data = {
                            'end_time': end_time,
                            'duration': 1.0,  # 1 minute for test
                            'notes': 'Test entry'
                        }
                        
                        update_response = requests.put(
                            f"{self.api_url}/time-entries/{entry_id}", 
                            json=update_data, 
                            headers=headers,
                            timeout=5
                        )
                        
                        results['time_entries_put'] = f"Status: {update_response.status_code}"
                        
                        if update_response.status_code == 200:
                            append_text(f"✓ Time entries PUT: {update_response.status_code}, Entry updated successfully\n")
                        else:
                            append_text(f"❌ Time entries PUT failed: {update_response.status_code}\n{update_response.text[:200]}\n")
                else:
                    append_text(f"❌ Time entries POST failed: {response.status_code}\n{response.text[:200]}\n")
            except Exception as e:
                results['time_entries_post'] = f"Error: {str(e)}"
                append_text(f"❌ Time entries POST error: {str(e)}\n")
        else:
            append_text("⚠️ Cannot test time entries POST - no tasks available\n")
        
        # Summary
        append_text("\nTest Summary:")
        for endpoint, result in results.items():
            append_text(f"- {endpoint}: {result}")
        
        append_text("\nAPI test complete. Check time_tracker.log for more details.")
        
        # Add a close button
        ttk.Button(test_window, text="Close", command=test_window.destroy).pack(pady=10)
        
        # Log all results
        logger.debug(f"API Test Results: {json.dumps(results, indent=2)}")

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if __name__ == "__main__":
    try:
        if sys.platform == 'win32' and not is_admin():
            # Re-run the program with admin rights on Windows
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        else:
            # Show a notification that the app is starting
            if sys.platform == 'win32':
                from win10toast import ToastNotifier
                try:
                    toaster = ToastNotifier()
                    toaster.show_toast("Time Tracker", 
                                     "Starting in system tray...",
                                     icon_path=None,
                                     duration=3,
                                     threaded=True)
                except Exception:
                    pass  # Silently fail if toast notification fails
            
            # Start the application
            app = TimeTrackerApp()
            app.start()  # Start the main loop
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        logging.error(traceback.format_exc())
        messagebox.showerror("Fatal Error", f"An error occurred: {e}\n\nSee time_tracker.log for details.")
        sys.exit(1) 