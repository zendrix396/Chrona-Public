import os
import json
import time
import logging
import requests
import traceback
from datetime import datetime
from threading import Thread
from queue import Queue

# Kivy imports
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.utils import platform
from kivy.uix.floatlayout import FloatLayout
from kivy.metrics import dp
from kivy.properties import StringProperty, BooleanProperty
from kivy.graphics import Color, Rectangle

# Android specific imports
if platform == 'android':
    from android.permissions import request_permissions, Permission
    from android import mActivity
    from jnius import autoclass, cast
    
    # Import for notification
    Context = autoclass('android.content.Context')
    Intent = autoclass('android.content.Intent')
    PendingIntent = autoclass('android.app.PendingIntent')
    NotificationBuilder = autoclass('android.app.Notification$Builder')
    NotificationChannel = autoclass('android.app.NotificationChannel')
    NotificationManager = autoclass('android.app.NotificationManager')
    AndroidString = autoclass('java.lang.String')
    NotificationCompat = autoclass('androidx.core.app.NotificationCompat')
    Service = autoclass('android.app.Service')
    
# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("chrona_android.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ChronaAndroid")

# Configuration
CONFIG_FILE = os.path.join(os.path.expanduser('~'), '.time_tracker_config.json')
API_URL = os.environ.get('TIME_TRACKER_API_URL', 'https://chrona-backend.onrender.com')

# Theme colors
DARK_BG = (0.1, 0.1, 0.1, 1)  # Dark background
GREEN_ACCENT = (0, 0.8, 0.2, 1)  # Green accent
GREEN_DARK = (0, 0.6, 0.2, 1)  # Darker green for buttons
TEXT_COLOR = (0.9, 0.9, 0.9, 1)  # Light text
TIMER_COLOR = (0, 1, 0, 1)  # Bright green for timer

class TimeTrackerNotification:
    """Class to handle Android notifications"""
    def __init__(self, app_instance):
        self.app = app_instance
        self.notification_id = 1001
        
        if platform == 'android':
            self.setup_notification_channel()
    
    def setup_notification_channel(self):
        """Setup notification channel for Android 8.0+"""
        if platform != 'android':
            return
            
        channel_id = "chrona_channel"
        channel_name = AndroidString("Chrona".encode('utf-8'))
        channel_description = AndroidString("Chrona time tracking notifications".encode('utf-8'))
        
        # Create the channel
        channel = NotificationChannel(
            channel_id, 
            channel_name,
            NotificationManager.IMPORTANCE_HIGH
        )
        channel.setDescription(channel_description)
        
        # Register the channel
        manager = mActivity.getSystemService(Context.NOTIFICATION_SERVICE)
        manager.createNotificationChannel(channel)
        
        self.channel_id = channel_id
    
    def show_tracking_notification(self, task_name, time_display):
        """Show ongoing notification with current tracking time"""
        if platform != 'android':
            return
            
        # Get the notification manager
        manager = mActivity.getSystemService(Context.NOTIFICATION_SERVICE)
        
        # Create an intent to open the app when notification is tapped
        intent = mActivity.getIntent()
        pending_intent = PendingIntent.getActivity(mActivity, 0, intent, PendingIntent.FLAG_IMMUTABLE)
        
        # Build the notification
        notification_builder = NotificationCompat.Builder(mActivity, self.channel_id)
        notification_builder.setContentTitle(f"Tracking: {task_name}")
        notification_builder.setContentText(f"Time: {time_display}")
        notification_builder.setSmallIcon(mActivity.getApplication().getApplicationInfo().icon)
        notification_builder.setContentIntent(pending_intent)
        notification_builder.setOngoing(True)  # Cannot be dismissed by user
        
        # Show the notification
        manager.notify(self.notification_id, notification_builder.build())
    
    def cancel_notification(self):
        """Cancel the timer notification"""
        if platform != 'android':
            return
            
        manager = mActivity.getSystemService(Context.NOTIFICATION_SERVICE)
        manager.cancel(self.notification_id)

class MiniTimerWidget(BoxLayout):
    """A small widget that shows the current tracking time"""
    time_text = StringProperty("00:00:00")
    
    def __init__(self, app_instance, **kwargs):
        super(MiniTimerWidget, self).__init__(**kwargs)
        self.app = app_instance
        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.height = dp(120)
        
        # Background color
        with self.canvas.before:
            Color(*DARK_BG)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        
        self.bind(pos=self._update_rect, size=self._update_rect)
        
        # Timer label with green text
        self.timer_label = Label(
            text=self.time_text,
            font_size=dp(36),
            color=TIMER_COLOR,
            bold=True,
            size_hint_y=None,
            height=dp(50)
        )
        
        # Create buttons layout
        buttons_layout = BoxLayout(
            orientation='horizontal',
            spacing=dp(10),
            padding=[dp(20), dp(10)],
            size_hint_y=None,
            height=dp(60)
        )
        
        # Stop button
        self.stop_button = Button(
            text="Stop",
            size_hint_x=0.5,
            background_color=GREEN_DARK,
            color=TEXT_COLOR
        )
        self.stop_button.bind(on_press=self.app.stop_tracking)
        
        # Pause button (functionality will be added later)
        self.pause_button = Button(
            text="Pause",
            size_hint_x=0.5,
            background_color=GREEN_DARK,
            color=TEXT_COLOR
        )
        self.pause_button.bind(on_press=self.app.toggle_pause)
        
        # Add widgets
        buttons_layout.add_widget(self.pause_button)
        buttons_layout.add_widget(self.stop_button)
        
        self.add_widget(self.timer_label)
        self.add_widget(buttons_layout)
        
        # Update the display when time_text changes
        self.bind(time_text=self.update_display)
    
    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size
    
    def update_display(self, instance, value):
        self.timer_label.text = value
        
    def update_pause_button(self, is_paused):
        """Update pause button text based on state"""
        self.pause_button.text = "Resume" if is_paused else "Pause"

class ThemeBox(BoxLayout):
    """Base class for themed BoxLayout"""
    def __init__(self, **kwargs):
        super(ThemeBox, self).__init__(**kwargs)
        with self.canvas.before:
            Color(*DARK_BG)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        
        self.bind(pos=self._update_rect, size=self._update_rect)
    
    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

class TaskSelectionScreen(ThemeBox):
    """The main task selection screen"""
    def __init__(self, app_instance, **kwargs):
        super(TaskSelectionScreen, self).__init__(**kwargs)
        self.app = app_instance
        self.orientation = 'vertical'
        self.padding = dp(20)
        self.spacing = dp(10)
        
        # Header
        header = Label(
            text="Chrona", 
            font_size=dp(24),
            size_hint_y=None,
            height=dp(40),
            color=TEXT_COLOR
        )
        self.add_widget(header)
        
        # Task selection
        task_label = Label(
            text="Select Task:",
            halign='left',
            size_hint_y=None, 
            height=dp(30),
            color=TEXT_COLOR
        )
        self.add_widget(task_label)
        
        # Spinner for task selection
        self.task_spinner = Spinner(
            text="Select a task",
            values=[],
            size_hint_y=None,
            height=dp(50),
            background_color=(0.2, 0.2, 0.2, 1),
            color=TEXT_COLOR
        )
        self.add_widget(self.task_spinner)
        
        # API URL display
        api_box = BoxLayout(
            orientation='horizontal',
            size_hint_y=None, 
            height=dp(40)
        )
        
        api_label = Label(
            text=f"API: {self.app.api_url}",
            size_hint_x=0.7,
            color=TEXT_COLOR
        )
        
        test_button = Button(
            text="Test API",
            size_hint_x=0.3,
            background_color=GREEN_DARK,
            color=TEXT_COLOR
        )
        test_button.bind(on_press=self.app.test_api_connection)
        
        api_box.add_widget(api_label)
        api_box.add_widget(test_button)
        self.add_widget(api_box)
        
        # Timer display
        self.timer_label = Label(
            text="00:00:00",
            font_size=dp(36),
            size_hint_y=None,
            height=dp(60),
            color=TIMER_COLOR
        )
        self.add_widget(self.timer_label)
        
        # Spacer
        self.add_widget(BoxLayout(size_hint_y=0.5))
        
        # Start button
        self.start_button = Button(
            text="Start Tracking",
            size_hint_y=None,
            height=dp(60),
            background_color=GREEN_ACCENT,
            color=TEXT_COLOR
        )
        self.start_button.bind(on_press=self.app.start_tracking)
        self.add_widget(self.start_button)
        
        # Refresh button
        refresh_button = Button(
            text="Refresh Tasks",
            size_hint_y=None,
            height=dp(50),
            background_color=GREEN_DARK,
            color=TEXT_COLOR
        )
        refresh_button.bind(on_press=self.app.fetch_tasks)
        self.add_widget(refresh_button)

class ResultScreen(ThemeBox):
    """Screen shown when tracking is stopped with the final duration"""
    def __init__(self, app_instance, task_name, duration, on_close, **kwargs):
        super(ResultScreen, self).__init__(**kwargs)
        self.app = app_instance
        self.orientation = 'vertical'
        self.padding = dp(20)
        self.spacing = dp(15)
        
        # Result text
        self.add_widget(Label(
            text="Time tracked for:",
            font_size=dp(18),
            size_hint_y=None,
            height=dp(30),
            color=TEXT_COLOR
        ))
        
        self.add_widget(Label(
            text=task_name,
            font_size=dp(24),
            bold=True,
            size_hint_y=None,
            height=dp(40),
            color=TEXT_COLOR
        ))
        
        self.add_widget(Label(
            text=duration,
            font_size=dp(36),
            size_hint_y=None,
            height=dp(60),
            color=TIMER_COLOR
        ))
        
        # Spacer
        self.add_widget(BoxLayout(size_hint_y=0.5))
        
        # Button layout
        button_layout = BoxLayout(
            orientation='horizontal',
            spacing=dp(10),
            size_hint_y=None,
            height=dp(60)
        )
        
        # Back button (returns to task selection)
        back_btn = Button(
            text="Back",
            size_hint_x=0.5,
            background_color=GREEN_DARK,
            color=TEXT_COLOR
        )
        back_btn.bind(on_press=on_close)
        
        # New tracking button (starts a new session)
        new_tracking_btn = Button(
            text="New Tracking",
            size_hint_x=0.5,
            background_color=GREEN_ACCENT,
            color=TEXT_COLOR
        )
        new_tracking_btn.bind(on_press=self.app.return_to_task_selection)
        
        button_layout.add_widget(back_btn)
        button_layout.add_widget(new_tracking_btn)
        self.add_widget(button_layout)

class TimeTrackerApp(App):
    """Main app class for the Time Tracker application"""
    is_tracking = BooleanProperty(False)
    is_paused = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super(TimeTrackerApp, self).__init__(**kwargs)
        self.title = "Chrona"
        self.tasks = []
        self.current_task_id = None
        self.current_task_name = None
        self.start_time = None
        self.entry_id = None
        self.mini_timer = None
        self.task_screen = None
        self.command_queue = Queue()
        self.pause_time = None
        self.paused_duration = 0
        
        # Load config
        self.load_config()
        
        # Initialize notification manager
        self.notification = TimeTrackerNotification(self)
    
    def build(self):
        """Build the application UI"""
        # Set background color
        Window.clearcolor = DARK_BG
        
        # Create root layout
        self.root_layout = FloatLayout()
        
        # Create task selection screen
        self.task_screen = TaskSelectionScreen(self)
        self.root_layout.add_widget(self.task_screen)
        
        # Request permissions if on Android
        if platform == 'android':
            request_permissions([
                Permission.INTERNET,
                Permission.FOREGROUND_SERVICE,
                Permission.POST_NOTIFICATIONS
            ])
        
        # Start timer update
        Clock.schedule_interval(self.update_timer, 1)
        
        # Start command processor
        Clock.schedule_interval(self.process_command_queue, 0.1)
        
        # Fetch tasks
        Clock.schedule_once(lambda dt: self.fetch_tasks(), 0.5)
        
        return self.root_layout
    
    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    self.api_url = config.get('api_url', API_URL)
            else:
                self.api_url = API_URL
                self.save_config()
                
            logger.info(f"Using API URL: {self.api_url}")
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self.api_url = API_URL
    
    def save_config(self):
        """Save configuration to file"""
        try:
            config = {
                'api_url': self.api_url
            }
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f)
            logger.info(f"Config saved to {CONFIG_FILE}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def queue_command(self, command, *args):
        """Add commands to the queue to be processed in the main thread"""
        logger.debug(f"Queuing command: {command}")
        self.command_queue.put((command, args))
    
    def process_command_queue(self, dt):
        """Process commands from the queue"""
        try:
            if not self.command_queue.empty():
                command, args = self.command_queue.get_nowait()
                logger.debug(f"Processing command: {command}")
                
                if command == 'toggle_tracking':
                    self.toggle_tracking()
                elif command == 'update_timer_display':
                    task_name, time_display = args
                    if self.mini_timer:
                        self.mini_timer.time_text = time_display
                    self.notification.show_tracking_notification(task_name, time_display)
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            logger.error(traceback.format_exc())
    
    def fetch_tasks(self, *args):
        """Fetch tasks from the API"""
        try:
            logger.info(f"Fetching tasks from {self.api_url}/tasks/")
            
            # Run in a separate thread to not block UI
            def _fetch_tasks():
                try:
                    response = requests.get(f"{self.api_url}/tasks/")
                    logger.info(f"Tasks API status code: {response.status_code}")
                    
                    if response.status_code == 200:
                        self.tasks = response.json()
                        logger.info(f"Fetched {len(self.tasks)} tasks")
                        
                        # Update UI in main thread
                        def update_ui(dt):
                            if hasattr(self, 'task_screen') and self.task_screen:
                                self.task_screen.task_spinner.values = [task['name'] for task in self.tasks]
                                if self.task_screen.task_spinner.values:
                                    self.task_screen.task_spinner.text = self.task_screen.task_spinner.values[0]
                                self.show_info_popup(f"Successfully fetched {len(self.tasks)} tasks")
                        
                        Clock.schedule_once(update_ui)
                    else:
                        logger.error(f"Error fetching tasks: Status {response.status_code}")
                        Clock.schedule_once(lambda dt: self.show_error_popup(f"Failed to fetch tasks (Error {response.status_code})"))
                except Exception as e:
                    logger.error(f"Error fetching tasks: {e}")
                    Clock.schedule_once(lambda dt: self.show_error_popup(f"Failed to fetch tasks: {e}"))
            
            Thread(target=_fetch_tasks).start()
        except Exception as e:
            logger.error(f"Error scheduling task fetch: {e}")
            self.show_error_popup(f"Error: {e}")
    
    def start_tracking(self, *args):
        """Start tracking time for the selected task"""
        if self.is_tracking:
            return
        
        selected_task = self.task_screen.task_spinner.text
        if selected_task == "Select a task" or not selected_task:
            self.show_error_popup("Please select a task first")
            return
        
        # Find task ID for the selected task
        task_id = None
        for task in self.tasks:
            if task['name'] == selected_task:
                task_id = task['id']
                self.current_task_name = task['name']
                break
        
        if not task_id:
            self.show_error_popup("Task not found")
            return
        
        # Create time entry in a separate thread
        self.current_task_id = task_id
        
        def _create_entry():
            try:
                entry = self.create_time_entry(task_id)
                if entry:
                    self.entry_id = entry['id']
                    self.start_time = datetime.now()
                    self.paused_duration = 0  # Reset paused duration
                    self.is_paused = False
                    
                    # Update UI in main thread
                    def update_ui(dt):
                        self.is_tracking = True
                        self.show_mini_timer()
                        # Show notification if on Android
                        self.notification.show_tracking_notification(
                            self.current_task_name, 
                            "00:00:00"
                        )
                    
                    Clock.schedule_once(update_ui)
                else:
                    Clock.schedule_once(lambda dt: self.show_error_popup("Failed to create time entry"))
            except Exception as e:
                logger.error(f"Error creating time entry: {e}")
                logger.error(traceback.format_exc())
                Clock.schedule_once(lambda dt: self.show_error_popup(f"Error: {e}"))
        
        Thread(target=_create_entry).start()
    
    def toggle_pause(self, *args):
        """Pause or resume the timer"""
        if not self.is_tracking:
            return
            
        if self.is_paused:
            # Resume timer
            paused_time = datetime.now() - self.pause_time
            self.paused_duration += paused_time.total_seconds()
            self.is_paused = False
            if self.mini_timer:
                self.mini_timer.update_pause_button(False)
        else:
            # Pause timer
            self.pause_time = datetime.now()
            self.is_paused = True
            if self.mini_timer:
                self.mini_timer.update_pause_button(True)
    
    def show_mini_timer(self):
        """Show a floating mini timer widget"""
        # Remove previous mini timer if exists
        if self.mini_timer:
            self.root_layout.remove_widget(self.mini_timer)
        
        # Create and add mini timer
        self.mini_timer = MiniTimerWidget(self)
        self.root_layout.add_widget(self.mini_timer)
        
        # Hide the task selection screen
        if self.task_screen:
            self.root_layout.remove_widget(self.task_screen)
    
    def stop_tracking(self, *args):
        """Stop tracking time"""
        if not self.is_tracking or not self.entry_id:
            return
        
        def _stop_tracking():
            try:
                # Calculate final duration
                duration = self.calculate_duration()
                formatted = self.format_duration(duration)
                
                # Update time entry
                entry = self.update_time_entry(self.entry_id)
                
                if entry:
                    def update_ui(dt):
                        self.is_tracking = False
                        self.is_paused = False
                        
                        # Remove mini timer
                        if self.mini_timer:
                            self.root_layout.remove_widget(self.mini_timer)
                            self.mini_timer = None
                        
                        # Cancel notification
                        self.notification.cancel_notification()
                        
                        # Show result screen
                        self.show_result_screen(self.current_task_name, formatted)
                        
                        # Reset tracking state
                        self.entry_id = None
                        self.start_time = None
                        self.current_task_id = None
                        self.paused_duration = 0
                    
                    Clock.schedule_once(update_ui)
                else:
                    Clock.schedule_once(lambda dt: self.show_error_popup("Failed to update time entry"))
            except Exception as e:
                logger.error(f"Error stopping tracking: {e}")
                logger.error(traceback.format_exc())
                Clock.schedule_once(lambda dt: self.show_error_popup(f"Error: {e}"))
        
        Thread(target=_stop_tracking).start()
    
    def toggle_tracking(self, *args):
        """Toggle time tracking on/off"""
        if self.is_tracking:
            self.stop_tracking()
        else:
            # Show task selection
            if self.task_screen not in self.root_layout.children:
                self.root_layout.add_widget(self.task_screen)
    
    def update_timer(self, dt):
        """Update the timer display"""
        if self.is_tracking and self.start_time and not self.is_paused:
            duration = self.calculate_duration()
            formatted = self.format_duration(duration)
            
            # Update mini timer text
            if self.mini_timer:
                self.mini_timer.time_text = formatted
            
            # Update notification
            if platform == 'android' and self.current_task_name:
                self.notification.show_tracking_notification(
                    self.current_task_name, 
                    formatted
                )
    
    def show_result_screen(self, task_name, duration):
        """Show the final duration screen"""
        result_screen = ResultScreen(
            self,
            task_name=task_name,
            duration=duration,
            on_close=self.return_to_task_selection
        )
        
        self.root_layout.add_widget(result_screen)
    
    def return_to_task_selection(self, *args):
        """Return to the task selection screen"""
        # Remove all widgets except task_screen
        self.root_layout.clear_widgets()
        
        # Add back the task selection screen
        self.root_layout.add_widget(self.task_screen)
    
    def calculate_duration(self):
        """Calculate duration in seconds since start time, accounting for pauses"""
        if self.start_time:
            if self.is_paused:
                # If currently paused, calculate up to the pause point
                duration = (self.pause_time - self.start_time).total_seconds() - self.paused_duration
            else:
                # Regular calculation minus total paused time
                duration = (datetime.now() - self.start_time).total_seconds() - self.paused_duration
            return int(duration)
        return 0
    
    def format_duration(self, seconds):
        """Format duration as HH:MM:SS"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def create_time_entry(self, task_id):
        """Create a new time entry in the API"""
        try:
            # Format the datetime as ISO 8601 string
            start_time = datetime.now().replace(microsecond=0).isoformat()
            
            data = {
                'task_id': task_id,
                'start_time': start_time,
                'end_time': None,
                'duration': None,
                'notes': None
            }
            
            logger.info(f"Creating time entry for task ID {task_id}")
            logger.debug(f"Request data: {data}")
            
            # Add headers
            headers = {'Content-Type': 'application/json'}
            
            response = requests.post(
                f"{self.api_url}/time-entries/", 
                json=data, 
                headers=headers,
                timeout=10
            )
            
            logger.info(f"Create time entry status code: {response.status_code}")
            
            if response.status_code in [200, 201]:
                entry = response.json()
                logger.info(f"Created time entry with ID {entry.get('id')}")
                return entry
            else:
                logger.error(f"Error creating time entry: Status {response.status_code}")
                logger.error(f"Response: {response.text[:500]}")
                return None
        except Exception as e:
            logger.error(f"Error creating time entry: {e}")
            logger.error(traceback.format_exc())
            return None
    
    def update_time_entry(self, entry_id):
        """Update a time entry in the API"""
        try:
            # Format end_time as ISO 8601 string
            end_time = datetime.now().replace(microsecond=0).isoformat()
            
            # Calculate duration in minutes
            duration_minutes = self.calculate_duration() / 60
            
            data = {
                'end_time': end_time,
                'duration': duration_minutes,
                'notes': None
            }
            
            logger.info(f"Updating time entry ID {entry_id}")
            logger.debug(f"Request data: {data}")
            
            # Add headers
            headers = {'Content-Type': 'application/json'}
            
            response = requests.put(
                f"{self.api_url}/time-entries/{entry_id}", 
                json=data, 
                headers=headers,
                timeout=10
            )
            
            logger.info(f"Update time entry status code: {response.status_code}")
            
            if response.status_code == 200:
                entry = response.json()
                logger.info(f"Updated time entry with ID {entry.get('id')}")
                return entry
            else:
                logger.error(f"Error updating time entry: Status {response.status_code}")
                logger.error(f"Response: {response.text[:500]}")
                return None
        except Exception as e:
            logger.error(f"Error updating time entry: {e}")
            logger.error(traceback.format_exc())
            return None
    
    def test_api_connection(self, *args):
        """Test the API connection and show result"""
        def _test_api():
            try:
                logger.info(f"Testing API connection to {self.api_url}...")
                response = requests.get(f"{self.api_url}/")
                
                if response.status_code == 200:
                    logger.info("API connection successful!")
                    Clock.schedule_once(lambda dt: self.show_info_popup("API connection successful!"))
                    return True
                else:
                    logger.error(f"API returned non-200 status: {response.status_code}")
                    Clock.schedule_once(lambda dt: self.show_error_popup(f"API error: Status {response.status_code}"))
                    return False
            except requests.RequestException as e:
                logger.error(f"API connection error: {e}")
                Clock.schedule_once(lambda dt: self.show_error_popup(f"API connection error: {e}"))
                return False
        
        # Run test in a separate thread
        Thread(target=_test_api).start()
    
    def show_info_popup(self, message):
        """Show an information popup"""
        content = BoxLayout(orientation='vertical', padding=dp(10))
        content.add_widget(Label(text=message, color=TEXT_COLOR))
        
        popup = Popup(
            title='Information',
            content=content,
            size_hint=(0.8, 0.3),
            background_color=DARK_BG,
            title_color=TEXT_COLOR
        )
        popup.open()
        # Auto-close after 2 seconds
        Clock.schedule_once(popup.dismiss, 2)
    
    def show_error_popup(self, message):
        """Show an error popup"""
        content = BoxLayout(orientation='vertical', padding=dp(10))
        content.add_widget(Label(text=message, color=TEXT_COLOR))
        
        popup = Popup(
            title='Error',
            content=content,
            size_hint=(0.8, 0.3),
            background_color=DARK_BG,
            title_color=(1, 0.3, 0.3, 1)  # Reddish title for errors
        )
        popup.open()

if __name__ == '__main__':
    TimeTrackerApp().run() 