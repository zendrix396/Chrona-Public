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
import socket

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

# Theme Colors
DARK_BG = "#121212"  # Nearly black background
DARK_SECONDARY = "#1E1E1E"  # Slightly lighter dark
GREEN_ACCENT = "#00C853"  # Bright green accent
GREEN_DARK = "#009624"  # Darker green for hover states
TEXT_COLOR = "#FFFFFF"  # White text
SUBTLE_TEXT = "#B0B0B0"  # Subtle gray for secondary text
TIMER_COLOR = "#00E676"  # Bright green for timer

class ChronaTheme:
    """Theme manager for consistent styling across the app"""
    @staticmethod
    def setup_custom_style():
        """Configure custom ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')  # Start with the most configurable theme
        
        # Configure the colors
        style.configure(".",
            background=DARK_BG,
            foreground=TEXT_COLOR,
            fieldbackground=DARK_SECONDARY,
            troughcolor=DARK_SECONDARY,
            bordercolor=DARK_SECONDARY,
            darkcolor=DARK_SECONDARY,
            lightcolor=DARK_SECONDARY)
        
        # TLabel
        style.configure("TLabel",
            background=DARK_BG,
            foreground=TEXT_COLOR,
            font=("Segoe UI", 10))
        
        # Timer Label
        style.configure("Timer.TLabel",
            background=DARK_BG,
            foreground=TIMER_COLOR,
            font=("Segoe UI", 24, "bold"))
        
        # Header Label
        style.configure("Header.TLabel",
            background=DARK_BG,
            foreground=TEXT_COLOR,
            font=("Segoe UI", 16, "bold"))
        
        # Subtle Label
        style.configure("Subtle.TLabel",
            background=DARK_BG,
            foreground=SUBTLE_TEXT,
            font=("Segoe UI", 9))
        
        # TFrame
        style.configure("TFrame",
            background=DARK_BG)
        
        # TButton - Regular
        style.configure("TButton",
            background=GREEN_ACCENT,
            foreground=DARK_BG,
            font=("Segoe UI", 10, "bold"),
            borderwidth=0,
            focusthickness=0,
            padding=(10, 8))
        
        style.map("TButton",
            background=[('active', GREEN_DARK), ('pressed', GREEN_DARK)],
            relief=[('pressed', 'flat'), ('!pressed', 'flat')])
        
        # TButton - Secondary
        style.configure("Secondary.TButton",
            background=DARK_SECONDARY,
            foreground=TEXT_COLOR,
            font=("Segoe UI", 10))
        
        style.map("Secondary.TButton",
            background=[('active', "#2A2A2A"), ('pressed', "#2A2A2A")],
            foreground=[('active', TEXT_COLOR)])
        
        # TButton - Accent
        style.configure("Accent.TButton",
            background=GREEN_ACCENT,
            foreground=DARK_BG,
            font=("Segoe UI", 10, "bold"))
        
        style.map("Accent.TButton",
            background=[('active', GREEN_DARK), ('pressed', GREEN_DARK)])
        
        # TCombobox
        style.configure("TCombobox",
            background=DARK_SECONDARY,
            foreground=TEXT_COLOR,
            fieldbackground=DARK_SECONDARY,
            selectbackground=GREEN_ACCENT,
            selectforeground=DARK_BG,
            arrowcolor=GREEN_ACCENT,
            font=("Segoe UI", 10))
        
        style.map("TCombobox",
            fieldbackground=[('readonly', DARK_SECONDARY)],
            selectbackground=[('readonly', GREEN_ACCENT)],
            selectforeground=[('readonly', DARK_BG)])
        
        # TScrollbar
        style.configure("TScrollbar",
            background=DARK_SECONDARY,
            troughcolor=DARK_BG,
            arrowcolor=GREEN_ACCENT)
            
    @staticmethod
    def configure_widget_styles(root):
        """Apply styling to non-ttk widgets in a window"""
        # Configure window
        root.configure(bg=DARK_BG)
        
        # Update all child widgets
        for child in root.winfo_children():
            widget_class = child.winfo_class()
            
            if widget_class == 'Frame':
                child.configure(bg=DARK_BG)
            elif widget_class == 'Label':
                child.configure(bg=DARK_BG, fg=TEXT_COLOR, font=("Segoe UI", 10))
            elif widget_class == 'Button':
                child.configure(
                    bg=GREEN_ACCENT, 
                    fg=DARK_BG, 
                    activebackground=GREEN_DARK, 
                    activeforeground=DARK_BG,
                    font=("Segoe UI", 10, "bold"),
                    borderwidth=0,
                    highlightthickness=0,
                    padx=10, pady=5
                )
            elif widget_class == 'Entry':
                child.configure(
                    bg=DARK_SECONDARY, 
                    fg=TEXT_COLOR, 
                    insertbackground=GREEN_ACCENT,
                    selectbackground=GREEN_ACCENT,
                    selectforeground=DARK_BG,
                    borderwidth=0,
                    highlightthickness=1,
                    highlightbackground=DARK_SECONDARY,
                    highlightcolor=GREEN_ACCENT,
                    font=("Segoe UI", 10)
                )
            elif widget_class == 'Text':
                child.configure(
                    bg=DARK_SECONDARY, 
                    fg=TEXT_COLOR, 
                    insertbackground=GREEN_ACCENT,
                    selectbackground=GREEN_ACCENT,
                    selectforeground=DARK_BG,
                    borderwidth=0,
                    highlightthickness=1,
                    highlightbackground=DARK_SECONDARY,
                    highlightcolor=GREEN_ACCENT,
                    font=("Consolas", 9)
                )
                
            # Recursively configure any children
            if hasattr(child, 'winfo_children'):
                for grandchild in child.winfo_children():
                    ChronaTheme.configure_widget_styles(grandchild)

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
        
        # Initialize the custom theme
        ChronaTheme.setup_custom_style()
        
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
        """Create a clock icon for the system tray with green theme"""
        width = 64
        height = 64
        green_color = (0, 200, 83)  # GREEN_ACCENT as RGB
        
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        dc = ImageDraw.Draw(image)
        
        # Draw a clock face
        dc.ellipse((4, 4, width-4, height-4), fill=(30, 30, 30, 220), outline=green_color, width=2)
        
        # Draw clock hands
        center_x, center_y = width // 2, height // 2
        # Hour hand
        dc.line((center_x, center_y, center_x - 15, center_y + 10), fill=green_color, width=3)
        # Minute hand
        dc.line((center_x, center_y, center_x + 5, center_y - 20), fill=green_color, width=3)
        
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
        self.task_window.title("Chrona Time Tracker")
        self.task_window.geometry("400x450")
        
        # Configure the window with dark theme
        self.task_window.configure(bg=DARK_BG)
        
        # Set window icon
        icon_img = self.create_tray_icon()
        icon_tk = ImageTk.PhotoImage(icon_img)
        self.task_window.iconphoto(False, icon_tk)
        
        # Make sure it appears on top of other windows
        self.task_window.attributes('-topmost', True)
        
        # Don't make it depend on the root window
        self.task_window.transient()  # Make it independent
        
        # Handle window close - just hide the window
        self.task_window.protocol("WM_DELETE_WINDOW", self.task_window.withdraw)
        
        # Center the window
        self.center_window(self.task_window)
        
        # Create frame with padding
        frame = ttk.Frame(self.task_window, padding="20", style="TFrame")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Header with icon
        header_frame = ttk.Frame(frame, style="TFrame")
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Display smaller icon in the header
        small_icon = icon_img.resize((32, 32))
        small_icon_tk = ImageTk.PhotoImage(small_icon)
        icon_label = ttk.Label(header_frame, image=small_icon_tk, style="TLabel")
        icon_label.image = small_icon_tk  # Keep a reference
        icon_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Header text
        ttk.Label(header_frame, text="CHRONA", style="Header.TLabel").pack(side=tk.LEFT)
        
        # Descriptive text
        ttk.Label(frame, text="Track your time efficiently", style="TLabel").pack(anchor="w", pady=(0, 20))
        
        # Task selection
        ttk.Label(frame, text="SELECT TASK", style="TLabel").pack(anchor="w")
        
        self.task_var = tk.StringVar()
        self.task_dropdown = ttk.Combobox(frame, textvariable=self.task_var, width=40, style="TCombobox")
        self.task_dropdown['values'] = [task['name'] for task in self.tasks]
        if self.task_dropdown['values']:
            self.task_dropdown.current(0)  # Select first task by default
        self.task_dropdown.pack(pady=(5, 20), fill="x")
        
        # Timer display
        timer_frame = ttk.Frame(frame, style="TFrame")
        timer_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(timer_frame, text="TIMER", style="TLabel").pack(anchor="w")
        self.timer_label = ttk.Label(timer_frame, text="00:00:00", style="Timer.TLabel")
        self.timer_label.pack(pady=(5, 0))
        
        # API connection info
        api_frame = ttk.Frame(frame, style="TFrame")
        api_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(api_frame, text="SERVER", style="TLabel").pack(anchor="w")
        ttk.Label(api_frame, text=f"{self.api_url}", style="Subtle.TLabel").pack(anchor="w", pady=(2, 5))
        
        # Buttons row for API actions
        api_buttons = ttk.Frame(api_frame, style="TFrame")
        api_buttons.pack(fill=tk.X)
        
        ttk.Button(api_buttons, text="Test Connection", command=self.test_and_show_api_status, 
                  style="Secondary.TButton").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(api_buttons, text="Refresh Tasks", command=self.refresh_tasks, 
                  style="Secondary.TButton").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(api_buttons, text="Debug API", command=self.run_detailed_api_test, 
                  style="Secondary.TButton").pack(side=tk.LEFT)
        
        # Actions section
        ttk.Label(frame, text="ACTIONS", style="TLabel").pack(anchor="w", pady=(0, 5))
        
        # Buttons
        ttk.Button(frame, text="START TRACKING", command=self.handle_start_button, 
                  style="Accent.TButton").pack(fill="x", pady=(5, 10), ipady=5)
        ttk.Button(frame, text="CANCEL", command=self.task_window.withdraw, 
                  style="Secondary.TButton").pack(fill="x")
        
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
        self.mini_timer_window.geometry("180x80")
        self.mini_timer_window.overrideredirect(True)  # Remove window decorations
        self.mini_timer_window.attributes('-topmost', True)  # Keep on top
        self.mini_timer_window.configure(bg=DARK_BG)
        
        # Add a subtle border
        border_frame = tk.Frame(self.mini_timer_window, bg=GREEN_ACCENT)
        border_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        # Inside frame
        inner_frame = tk.Frame(border_frame, bg=DARK_BG)
        inner_frame.pack(fill=tk.BOTH, expand=True)
        
        # Position at the top-right corner initially
        screen_width = self.mini_timer_window.winfo_screenwidth()
        self.mini_timer_window.geometry(f"+{screen_width-200}+10")
        
        # Task name label with ellipsis if too long
        task_name = self.current_task_name
        if len(task_name) > 20:
            task_name = task_name[:17] + "..."
            
        task_label = tk.Label(
            inner_frame,
            text=task_name,
            font=("Segoe UI", 10),
            fg=TEXT_COLOR,
            bg=DARK_BG,
            anchor="w"
        )
        task_label.pack(fill=tk.X, padx=10, pady=(8, 0))
        
        # Timer label
        self.mini_timer_label = tk.Label(
            inner_frame, 
            text="00:00:00", 
            font=("Segoe UI", 18, "bold"), 
            fg=TIMER_COLOR, 
            bg=DARK_BG
        )
        self.mini_timer_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Add a small stop button
        stop_button = tk.Label(
            inner_frame,
            text="✕",
            font=("Segoe UI", 8),
            fg=SUBTLE_TEXT,
            bg=DARK_BG,
            cursor="hand2"
        )
        stop_button.place(x=160, y=5)
        stop_button.bind("<Button-1>", lambda e: self.stop_tracking())
        
        # Make window draggable
        for widget in [self.mini_timer_label, task_label, inner_frame]:
            widget.bind("<ButtonPress-1>", self.start_drag)
            widget.bind("<ButtonRelease-1>", self.stop_drag)
            widget.bind("<B1-Motion>", self.on_drag)
        
        # Add keyboard shortcuts
        self.mini_timer_window.bind("<KeyPress>", self.handle_key_press)
        
        # Add a helpful tooltip on hover
        task_label.bind("<Enter>", lambda e: self.show_timer_tooltip("Drag to move, press 'O' to adjust opacity"))
        task_label.bind("<Leave>", lambda e: self.hide_timer_tooltip())
        
        # Set opacity level
        self.opacity = 0.9
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
    
    def show_timer_tooltip(self, text):
        """Show a tooltip for the mini timer"""
        if hasattr(self, 'tooltip') and self.tooltip:
            self.tooltip.destroy()
            
        # Create tooltip window
        self.tooltip = tk.Toplevel(self.mini_timer_window)
        self.tooltip.overrideredirect(True)
        self.tooltip.configure(bg=DARK_SECONDARY)
        
        # Add tooltip text
        tip_label = tk.Label(self.tooltip, text=text, bg=DARK_SECONDARY, fg=TEXT_COLOR,
                           font=("Segoe UI", 9), padx=8, pady=2)
        tip_label.pack()
        
        # Position tooltip below the timer
        x = self.mini_timer_window.winfo_x() + 10
        y = self.mini_timer_window.winfo_y() + self.mini_timer_window.winfo_height() + 2
        self.tooltip.geometry(f"+{x}+{y}")
        
        # Auto-hide after 2 seconds
        self.mini_timer_window.after(2000, self.hide_timer_tooltip)
        
    def hide_timer_tooltip(self):
        """Hide the tooltip"""
        if hasattr(self, 'tooltip') and self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
            
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
        self.result_window.geometry("350x250")
        self.result_window.configure(bg=DARK_BG)
        self.result_window.protocol("WM_DELETE_WINDOW", lambda: self.safe_destroy(self.result_window))
        
        # Set attributes
        self.result_window.attributes('-topmost', True)
        self.center_window(self.result_window)
        
        # Create main frame
        frame = ttk.Frame(self.result_window, padding="20", style="TFrame")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Add a completion icon/checkmark
        check_frame = ttk.Frame(frame, style="TFrame")
        check_frame.pack(pady=(0, 20))
        
        check_label = ttk.Label(check_frame, text="✓", font=("Segoe UI", 36), foreground=GREEN_ACCENT, background=DARK_BG)
        check_label.pack()
        
        # Add labels with task info
        ttk.Label(frame, text="TIME TRACKED SUCCESSFULLY", style="Header.TLabel").pack(pady=(0, 10))
        
        task_frame = ttk.Frame(frame, style="TFrame")
        task_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(task_frame, text="Task:", style="TLabel").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(task_frame, text=task_name, style="TLabel").pack(side=tk.LEFT)
        
        duration_frame = ttk.Frame(frame, style="TFrame")
        duration_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(duration_frame, text="Duration:", style="TLabel").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(duration_frame, text=duration, style="Timer.TLabel").pack(side=tk.LEFT)
        
        # Add close button
        ttk.Button(frame, text="CLOSE", command=lambda: self.safe_destroy(self.result_window), 
                  style="Accent.TButton").pack(fill="x", pady=(10, 0))
        
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
        test_window.geometry("550x450")
        test_window.configure(bg=DARK_BG)
        test_window.attributes('-topmost', True)
        self.center_window(test_window)
        
        # Main container
        main_frame = ttk.Frame(test_window, padding="15", style="TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        ttk.Label(main_frame, text="API CONNECTION TEST", style="Header.TLabel").pack(pady=(0, 15))
        ttk.Label(main_frame, text=f"Testing connection to {self.api_url}", style="Subtle.TLabel").pack(pady=(0, 15))
        
        # Create a text widget with scrollbar for results
        results_frame = ttk.Frame(main_frame, style="TFrame")
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        result_text = tk.Text(results_frame, wrap=tk.WORD, bg=DARK_SECONDARY, fg=TEXT_COLOR,
                            font=("Consolas", 9), borderwidth=0, highlightthickness=1,
                            highlightbackground=DARK_SECONDARY, highlightcolor=GREEN_ACCENT)
        result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add a scroll bar
        scrollbar = ttk.Scrollbar(results_frame, command=result_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        result_text.config(yscrollcommand=scrollbar.set)
        
        # Function to append text
        def append_text(text, tag=None):
            result_text.config(state=tk.NORMAL)
            if tag:
                result_text.insert(tk.END, text + "\n", tag)
            else:
                result_text.insert(tk.END, text + "\n")
            result_text.see(tk.END)
            result_text.config(state=tk.DISABLED)
            test_window.update()
        
        # Configure tags for colored text
        result_text.tag_configure("success", foreground="#00E676")  # Green for success
        result_text.tag_configure("error", foreground="#FF5252")    # Red for errors
        result_text.tag_configure("info", foreground="#82B1FF")     # Blue for info
        result_text.tag_configure("header", foreground="#E0E0E0", font=("Consolas", 9, "bold"))  # Bold for headers
        
        append_text(f"API URL: {self.api_url}", "header")
        append_text("Starting API tests...\n", "info")
        
        # Test root endpoint
        try:
            append_text("Testing root endpoint...", "header")
            response = requests.get(f"{self.api_url}/", timeout=5)
            results['root'] = f"Status: {response.status_code}, Response: {response.text[:100]}"
            append_text(f"✓ Root endpoint: {response.status_code}\n", "success")
        except Exception as e:
            results['root'] = f"Error: {str(e)}"
            append_text(f"❌ Root endpoint error: {str(e)}\n", "error")
            
        # Test tasks endpoint
        try:
            append_text("Testing tasks endpoint...", "header")
            response = requests.get(f"{self.api_url}/tasks/", timeout=5)
            results['tasks'] = f"Status: {response.status_code}, Tasks: {len(response.json())}"
            append_text(f"✓ Tasks endpoint: {response.status_code}, Found {len(response.json())} tasks\n", "success")
        except Exception as e:
            results['tasks'] = f"Error: {str(e)}"
            append_text(f"❌ Tasks endpoint error: {str(e)}\n", "error")
        
        # Test time entries GET endpoint
        try:
            append_text("Testing time-entries GET endpoint...", "header")
            response = requests.get(f"{self.api_url}/time-entries/", timeout=5)
            results['time_entries_get'] = f"Status: {response.status_code}, Entries: {len(response.json()) if response.status_code == 200 else 'N/A'}"
            append_text(f"✓ Time entries GET: {response.status_code}\n", "success")
        except Exception as e:
            results['time_entries_get'] = f"Error: {str(e)}"
            append_text(f"❌ Time entries GET error: {str(e)}\n", "error")
        
        # Test time entries POST endpoint with a test task
        if self.tasks:
            try:
                test_task_id = self.tasks[0]['id']
                append_text(f"Testing time-entries POST endpoint with task ID {test_task_id}...", "header")
                
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
                    append_text(f"✓ Time entries POST: {response.status_code}, Entry created successfully\n", "success")
                    entry_id = response.json().get('id')
                    
                    # If successful, test the PUT endpoint too to complete the test entry
                    if entry_id:
                        append_text(f"Testing time-entries PUT endpoint with entry ID {entry_id}...", "header")
                        
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
                            append_text(f"✓ Time entries PUT: {update_response.status_code}, Entry updated successfully\n", "success")
                        else:
                            append_text(f"❌ Time entries PUT failed: {update_response.status_code}\n{update_response.text[:200]}\n", "error")
                else:
                    append_text(f"❌ Time entries POST failed: {response.status_code}\n{response.text[:200]}\n", "error")
            except Exception as e:
                results['time_entries_post'] = f"Error: {str(e)}"
                append_text(f"❌ Time entries POST error: {str(e)}\n", "error")
        else:
            append_text("⚠️ Cannot test time entries POST - no tasks available\n", "info")
        
        # Summary
        append_text("\nTest Summary:")
        for endpoint, result in results.items():
            append_text(f"- {endpoint}: {result}")
        
        append_text("\nAPI test complete. Check time_tracker.log for more details.")
        
        # Add a close button
        ttk.Button(main_frame, text="CLOSE", command=test_window.destroy, 
                  style="Accent.TButton").pack(pady=15)
        
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