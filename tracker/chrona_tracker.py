import sys
import os
import json
import time
import logging
import queue
import threading
import requests
from datetime import datetime, timedelta
import traceback
import keyboard
import pystray
from PIL import Image, ImageDraw
try:
    from win10toast import ToastNotifier
except ImportError:
    ToastNotifier = None
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QComboBox, QSystemTrayIcon, QMenu, 
    QFrame, QSizePolicy, QDialog, QTextEdit, QScrollArea
)
from PyQt6.QtCore import (
    Qt, QSize, QPoint, QTimer, QObject, pyqtSignal, pyqtSlot,
    QRect, QPropertyAnimation, QEasingCurve
)
from PyQt6.QtGui import (
    QIcon, QFont, QFontDatabase, QColor, QPalette, QPixmap, 
    QImage, QPainter, QBrush, QPen, QAction, QCursor
)

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("chrona_tracker.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Chrona")

# Configuration
CONFIG_FILE = os.path.join(os.path.expanduser('~'), '.chrona_config.json')
API_URL = os.environ.get('CHRONA_API_URL', 'https://chrona-backend.onrender.com')
HOTKEY = 'ctrl+shift+alt+k'

# Theme Colors
class ChronaTheme:
    # Colors
    DARK_BG = "#121212"
    DARK_SECONDARY = "#1E1E1E"
    DARK_TERTIARY = "#252525" 
    GREEN_ACCENT = "#00C853"
    GREEN_DARK = "#009624"
    GREEN_LIGHT = "#5EFC82"
    TEXT_COLOR = "#FFFFFF"
    SUBTLE_TEXT = "#B0B0B0"
    TIMER_COLOR = "#00E676"
    ERROR_COLOR = "#FF5252"
    WARNING_COLOR = "#FFD740"
    INFO_COLOR = "#82B1FF"
    
    # Fonts
    FONT_PRIMARY = "Segoe UI"
    FONT_MONOSPACE = "Consolas"
    
    # Dimensions
    BORDER_RADIUS = 4
    BUTTON_HEIGHT = 36
    PADDING = 12
    
    @staticmethod
    def setup_qss():
        """Generate QSS (Qt Style Sheets) for the application"""
        return f"""
            QWidget {{
                background-color: {ChronaTheme.DARK_BG};
                color: {ChronaTheme.TEXT_COLOR};
                font-family: "{ChronaTheme.FONT_PRIMARY}";
                font-size: 10pt;
            }}
            
            QLabel {{
                background-color: transparent;
                color: {ChronaTheme.TEXT_COLOR};
            }}
            
            QLabel#HeaderLabel {{
                font-size: 16pt;
                font-weight: bold;
            }}
            
            QLabel#SubHeaderLabel {{
                font-size: 12pt;
            }}
            
            QLabel#TaskLabel {{
                color: {ChronaTheme.SUBTLE_TEXT};
            }}
            
            QLabel#TimerLabel {{
                font-size: 24pt;
                font-weight: bold;
                color: {ChronaTheme.TIMER_COLOR};
                min-height: 40px;
                padding: 5px 0px;
            }}
            
            QLabel#MiniTimerLabel {{
                font-size: 20pt;
                font-weight: bold;
                color: {ChronaTheme.TIMER_COLOR};
                min-height: 35px;
                padding: 5px 0px;
            }}
            
            QLabel#UrlLabel {{
                color: {ChronaTheme.SUBTLE_TEXT};
                font-size: 9pt;
            }}
            
            QLabel#SectionLabel {{
                font-weight: bold;
                margin-top: 10px;
            }}
            
            QPushButton {{
                background-color: {ChronaTheme.GREEN_ACCENT};
                color: {ChronaTheme.DARK_BG};
                border: none;
                border-radius: {ChronaTheme.BORDER_RADIUS}px;
                padding: 8px 16px;
                font-weight: bold;
                height: {ChronaTheme.BUTTON_HEIGHT}px;
            }}
            
            QPushButton:hover {{
                background-color: {ChronaTheme.GREEN_LIGHT};
            }}
            
            QPushButton:pressed {{
                background-color: {ChronaTheme.GREEN_DARK};
            }}
            
            QPushButton:disabled {{
                background-color: {ChronaTheme.DARK_TERTIARY};
                color: {ChronaTheme.SUBTLE_TEXT};
            }}
            
            QPushButton#SecondaryButton {{
                background-color: {ChronaTheme.DARK_SECONDARY};
                color: {ChronaTheme.TEXT_COLOR};
            }}
            
            QPushButton#SecondaryButton:hover {{
                background-color: {ChronaTheme.DARK_TERTIARY};
            }}
            
            QPushButton#IconButton {{
                background-color: transparent;
                padding: 4px;
                border-radius: 16px;
            }}
            
            QPushButton#IconButton:hover {{
                background-color: {ChronaTheme.DARK_TERTIARY};
            }}
            
            QComboBox {{
                background-color: {ChronaTheme.DARK_SECONDARY};
                color: {ChronaTheme.TEXT_COLOR};
                border: none;
                border-radius: {ChronaTheme.BORDER_RADIUS}px;
                padding: 8px 16px;
                height: {ChronaTheme.BUTTON_HEIGHT}px;
                selection-background-color: {ChronaTheme.GREEN_ACCENT};
                selection-color: {ChronaTheme.DARK_BG};
            }}
            
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            
            QComboBox::down-arrow {{
                image: url(:/images/dropdown_arrow.png);
                width: 12px;
                height: 12px;
            }}
            
            QComboBox QAbstractItemView {{
                background-color: {ChronaTheme.DARK_SECONDARY};
                color: {ChronaTheme.TEXT_COLOR};
                border: none;
                selection-background-color: {ChronaTheme.GREEN_ACCENT};
                selection-color: {ChronaTheme.DARK_BG};
                outline: none;
            }}
            
            QFrame#SeparatorLine {{
                background-color: {ChronaTheme.DARK_TERTIARY};
                max-height: 1px;
                min-height: 1px;
            }}
            
            QTextEdit {{
                background-color: {ChronaTheme.DARK_SECONDARY};
                color: {ChronaTheme.TEXT_COLOR};
                border: none;
                border-radius: {ChronaTheme.BORDER_RADIUS}px;
                padding: 8px;
                font-family: "{ChronaTheme.FONT_MONOSPACE}";
                font-size: 9pt;
            }}
            
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            
            QScrollBar:vertical {{
                background: {ChronaTheme.DARK_BG};
                width: 10px;
                margin: 0px;
            }}
            
            QScrollBar::handle:vertical {{
                background: {ChronaTheme.DARK_TERTIARY};
                min-height: 20px;
                border-radius: 5px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background: {ChronaTheme.GREEN_DARK};
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
            
            QFrame#RoundedContainerLight {{
                background-color: {ChronaTheme.DARK_SECONDARY};
                border-radius: {ChronaTheme.BORDER_RADIUS}px;
            }}
            
            QFrame#RoundedContainerDark {{
                background-color: {ChronaTheme.DARK_TERTIARY};
                border-radius: {ChronaTheme.BORDER_RADIUS}px;
            }}
            
            QFrame#SuccessFrame {{
                background-color: {ChronaTheme.GREEN_DARK};
                border-radius: {ChronaTheme.BORDER_RADIUS}px;
                padding: 8px;
            }}
            
            QFrame#ErrorFrame {{
                background-color: {ChronaTheme.ERROR_COLOR};
                border-radius: {ChronaTheme.BORDER_RADIUS}px;
                padding: 8px;
            }}
        """
    
    @staticmethod
    def create_icon(size=64):
        """Create a clock icon for the application"""
        # Create a QPixmap
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        # Create painter
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Define colors
        green_color = QColor(ChronaTheme.GREEN_ACCENT)
        dark_color = QColor(30, 30, 30, 220)
        
        # Draw a clock face
        painter.setBrush(QBrush(dark_color))
        painter.setPen(QPen(green_color, 2))
        painter.drawEllipse(4, 4, size-8, size-8)
        
        # Draw clock hands
        center_x, center_y = size // 2, size // 2
        painter.setPen(QPen(green_color, 3))
        
        # Hour hand
        painter.drawLine(center_x, center_y, center_x - 15, center_y + 10)
        
        # Minute hand
        painter.drawLine(center_x, center_y, center_x + 5, center_y - 20)
        
        painter.end()
        return pixmap


# Signal class for thread-safe communication
class ChronaSignals(QObject):
    toggle_tracking = pyqtSignal()
    show_task_window = pyqtSignal()
    refresh_tasks = pyqtSignal()
    test_api = pyqtSignal()
    exit_app = pyqtSignal()
    stop_tracking = pyqtSignal()
    update_timer = pyqtSignal(str)
    task_refresh_complete = pyqtSignal(list)
    api_test_result = pyqtSignal(bool, str)
    show_error = pyqtSignal(str, str)
    show_info = pyqtSignal(str, str)


# Custom QFrame for rounded containers
class RoundedFrame(QFrame):
    def __init__(self, is_dark=False, parent=None):
        super().__init__(parent)
        self.setObjectName("RoundedContainerDark" if is_dark else "RoundedContainerLight")


# Custom Line Separator
class HorizontalLine(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SeparatorLine")
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFixedHeight(1)


# Utility Functions
def format_duration(seconds):
    """Format duration in seconds as HH:MM:SS"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


# Task Selection Window
class TaskSelectionWindow(QMainWindow):
    def __init__(self, app, tasks, parent=None):
        super().__init__(parent, Qt.WindowType.Window)
        self.chrona_app = app
        self.tasks = tasks
        
        # Set window properties
        self.setWindowTitle("Chrona Time Tracker")
        self.setMinimumSize(420, 400)  # Reduced height since we're removing sections
        self.setWindowIcon(QIcon(ChronaTheme.create_icon()))
        
        # Create the central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(ChronaTheme.PADDING, ChronaTheme.PADDING, 
                                       ChronaTheme.PADDING, ChronaTheme.PADDING)
        main_layout.setSpacing(ChronaTheme.PADDING)
        
        # Header
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Logo image (using a clock icon)
        logo_label = QLabel()
        logo_label.setPixmap(ChronaTheme.create_icon(32))
        logo_label.setFixedSize(32, 32)
        header_layout.addWidget(logo_label)
        
        # App name
        header_label = QLabel("CHRONA")
        header_label.setObjectName("HeaderLabel")
        header_layout.addWidget(header_label)
        
        header_layout.addStretch(1)
        main_layout.addLayout(header_layout)
        
        # Description
        desc_label = QLabel("Track your time efficiently")
        desc_label.setObjectName("SubHeaderLabel")
        main_layout.addWidget(desc_label)
        
        main_layout.addWidget(HorizontalLine())
        main_layout.addSpacing(ChronaTheme.PADDING)
        
        # Task Selection Section
        task_section_label = QLabel("SELECT TASK")
        task_section_label.setObjectName("SectionLabel")
        main_layout.addWidget(task_section_label)
        
        # Task dropdown
        self.task_combo = QComboBox()
        for task in tasks:
            self.task_combo.addItem(task["name"], task["id"])
        main_layout.addWidget(self.task_combo)
        
        main_layout.addSpacing(ChronaTheme.PADDING * 2)
        
        # Actions section
        actions_section_label = QLabel("ACTIONS")
        actions_section_label.setObjectName("SectionLabel")
        main_layout.addWidget(actions_section_label)
        
        # Refresh Tasks button (kept for convenience)
        self.refresh_button = QPushButton("Refresh Tasks")
        self.refresh_button.setObjectName("SecondaryButton")
        self.refresh_button.clicked.connect(app.signals.refresh_tasks.emit)
        main_layout.addWidget(self.refresh_button)
        
        main_layout.addSpacing(ChronaTheme.PADDING)
        
        # Start button
        self.start_button = QPushButton("START TRACKING")
        self.start_button.clicked.connect(self.handle_start_button)
        main_layout.addWidget(self.start_button)
        
        # Cancel button
        self.cancel_button = QPushButton("CANCEL")
        self.cancel_button.setObjectName("SecondaryButton")
        self.cancel_button.clicked.connect(self.close)
        main_layout.addWidget(self.cancel_button)
        
        # Add stretch to push everything up
        main_layout.addStretch(1)
    
    def handle_start_button(self):
        """Handle start tracking button click"""
        task_id = self.task_combo.currentData()
        task_name = self.task_combo.currentText()
        
        if not task_id:
            self.chrona_app.signals.show_error.emit("Error", "Please select a task first")
            return
        
        # Notify the app to start tracking this task
        self.chrona_app.start_tracking(task_id, task_name)
        self.close()
    
    def update_tasks(self, tasks):
        """Update the task dropdown with new task list"""
        if not tasks:
            return
            
        self.tasks = tasks
        
        # Save current selection if possible
        current_id = self.task_combo.currentData() if self.task_combo.count() > 0 else None
        
        # Clear and repopulate
        self.task_combo.clear()
        for task in tasks:
            self.task_combo.addItem(task["name"], task["id"])
            
        # Try to restore previous selection
        if current_id:
            for i in range(self.task_combo.count()):
                if self.task_combo.itemData(i) == current_id:
                    self.task_combo.setCurrentIndex(i)
                    break


# Floating Mini Timer Window
class MiniTimer(QMainWindow):
    def __init__(self, app, task_name, parent=None):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.chrona_app = app
        self.task_name = task_name
        self.dragging = False
        self.drag_position = None
        self.opacity = 0.95
        
        # Set size and position
        self.resize(240, 100)  # Adjusted size for better visibility
        desktop = QApplication.primaryScreen().availableGeometry()
        self.move(desktop.width() - self.width() - 20, 40)
        
        # Main container
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Configure main layout with a border
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(1, 1, 1, 1)  # Thin 1px margin for the border
        
        # Create a container with a border
        border_container = QFrame()
        border_container.setStyleSheet(f"background-color: {ChronaTheme.GREEN_ACCENT}; border-radius: {ChronaTheme.BORDER_RADIUS}px;")
        main_layout.addWidget(border_container)
        
        # Inside container
        inner_layout = QVBoxLayout(border_container)
        inner_layout.setContentsMargins(1, 1, 1, 1)  # 1px padding for border effect
        
        # Content container
        content_container = QFrame()
        content_container.setStyleSheet(f"background-color: {ChronaTheme.DARK_BG}; border-radius: {ChronaTheme.BORDER_RADIUS - 1}px;")
        inner_layout.addWidget(content_container)
        
        # Content layout
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(10, 8, 10, 8)
        content_layout.setSpacing(0)
        
        # Header with task name and close button
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Truncate task name if too long
        display_name = task_name
        if len(display_name) > 25:
            display_name = display_name[:22] + "..."
            
        # Task name label
        self.task_label = QLabel(display_name)
        self.task_label.setObjectName("TaskLabel")
        self.task_label.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))  # Hint that this is draggable
        header_layout.addWidget(self.task_label)
        
        # Close button
        self.close_button = QPushButton("✕")
        self.close_button.setObjectName("IconButton")
        self.close_button.setFixedSize(16, 16)
        self.close_button.clicked.connect(app.signals.stop_tracking.emit)
        header_layout.addWidget(self.close_button)
        
        content_layout.addLayout(header_layout)
        
        # Timer label
        self.timer_label = QLabel("00:00:00")
        self.timer_label.setObjectName("MiniTimerLabel")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_label.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))  # Hint that this is draggable
        content_layout.addWidget(self.timer_label)
        
        # Connect signals for dragging
        for widget in [self.task_label, self.timer_label, content_container]:
            widget.installEventFilter(self)
        
        # Set a tooltip
        self.setToolTip("Drag to move - Press 'P' to pause - Press 'O' to change opacity")
        
        # Configure window transparency
        self.setWindowOpacity(self.opacity)
        
        # Connect to timer update signal
        app.signals.update_timer.connect(self.update_timer)
        
    def update_timer(self, time_text):
        """Update the timer display"""
        self.timer_label.setText(time_text)
    
    def cycle_opacity(self):
        """Cycle through opacity levels"""
        opacity_levels = [0.95, 0.8, 0.6, 0.4]
        current_index = opacity_levels.index(self.opacity) if self.opacity in opacity_levels else 0
        next_index = (current_index + 1) % len(opacity_levels)
        self.opacity = opacity_levels[next_index]
        self.setWindowOpacity(self.opacity)
    
    def eventFilter(self, obj, event):
        """Handle events for dragging the window"""
        if event.type() == event.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_position = event.position().toPoint()
            return True
        
        elif event.type() == event.Type.MouseMove and self.dragging:
            self.move(self.mapToGlobal(event.position().toPoint()) - self.drag_position)
            return True
            
        elif event.type() == event.Type.MouseButtonRelease:
            self.dragging = False
            return True
            
        return super().eventFilter(obj, event)
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        if event.key() == Qt.Key.Key_O:
            self.cycle_opacity()
        elif event.key() == Qt.Key.Key_P:
            self.chrona_app.signals.toggle_tracking.emit()
        else:
            super().keyPressEvent(event) 


# Main application class
class ChronaApp:
    def __init__(self):
        # Create application
        self.app = QApplication(sys.argv)
        self.app.setStyleSheet(ChronaTheme.setup_qss())
        
        # Initialize variables
        self.signals = ChronaSignals()
        self.tasks = []
        self.task_window = None
        self.mini_timer = None
        self.result_window = None
        self.tracking = False
        self.current_task_id = None
        self.current_task_name = None
        self.start_time = None
        self.entry_id = None
        self.config = {}
        self.command_queue = queue.Queue()
        self.icon = None  # System tray icon
        
        # Set application icon
        self.app_icon = QIcon(ChronaTheme.create_icon())
        self.app.setWindowIcon(self.app_icon)
        
        # Connect signals
        self.connect_signals()
        
        # Register global hotkey
        self.initialize_hotkey()
        
        # Load config and test API
        self.load_config()
        self.fetch_tasks()
        
        # Create system tray in a separate thread
        self.setup_system_tray()
        
        # Start processing commands
        QTimer.singleShot(100, self.process_command_queue)
        
        logger.info(f"Chrona Time Tracker started. Press {HOTKEY} to start/stop tracking.")
    
    def initialize_hotkey(self):
        """Initialize or reinitialize the global hotkey"""
        try:
            # First unhook all existing hotkeys to avoid duplicates
            keyboard.unhook_all()
            # Register the hotkey
            keyboard.add_hotkey(HOTKEY, self.queue_command, args=('toggle_tracker',))
            logger.info(f"Hotkey {HOTKEY} registered successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to register hotkey: {e}")
            logger.error(traceback.format_exc())
            return False
        finally:
            # Log the current state of hotkeys
            logger.debug(f"Current hotkeys: {keyboard.get_hotkey_name()}")
    
    def queue_command(self, command, *args):
        """Add a command to the queue to be executed in the main thread"""
        logger.debug(f"Queuing command: {command}")
        self.command_queue.put((command, args))
    
    def process_command_queue(self):
        """Process commands from the queue in the main thread"""
        try:
            while not self.command_queue.empty():
                command, args = self.command_queue.get_nowait()
                logger.debug(f"Processing command: {command}")
                
                if command == 'toggle_tracker':
                    self.toggle_tracking()
                elif command == 'refresh_tasks':
                    self.fetch_tasks()
                elif command == 'test_api':
                    self.test_api_connection()
                elif command == 'show_tracker':
                    self.show_task_window()
                elif command == 'exit_app':
                    self.exit_app()
                elif command == 'stop_tracking':
                    self.stop_tracking()
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            logger.error(traceback.format_exc())
        
        # Schedule the next check
        QTimer.singleShot(100, self.process_command_queue)
    
    def create_tray_image(self):
        """Create a clock icon for the system tray"""
        width = 64
        height = 64
        color1 = (0, 200, 83)  # Green color
        
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        dc = ImageDraw.Draw(image)
        
        # Draw a clock face
        dc.ellipse((4, 4, width-4, height-4), fill=(30, 30, 30, 220), outline=color1, width=2)
        
        # Draw clock hands
        center_x, center_y = width // 2, height // 2
        # Hour hand
        dc.line((center_x, center_y, center_x - 15, center_y + 10), fill=color1, width=3)
        # Minute hand
        dc.line((center_x, center_y, center_x + 5, center_y - 20), fill=color1, width=3)
        
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
            icon_image = self.create_tray_image()
            
            def on_show_tracker(icon, item):
                # Queue the command and also reset keyboard hooks
                self.queue_command('show_tracker')
                self.initialize_hotkey()
            
            menu = (
                pystray.MenuItem('Show Tracker', on_show_tracker),
                pystray.MenuItem('Refresh Tasks', 
                            lambda: self.queue_command('refresh_tasks')),
                pystray.MenuItem('Test API Connection', 
                            lambda: self.queue_command('test_api')),
                pystray.MenuItem('Exit', 
                            lambda: self.queue_command('exit_app'))
            )
            
            self.icon = pystray.Icon("chrona_tracker", icon_image, "Chrona Time Tracker", menu)
            
            # Set the icon's on_click method to show the tracker
            self.icon.on_click = lambda icon: on_show_tracker(icon, None)
            
            # Show a notification that the app is running
            if ToastNotifier:
                try:
                    toaster = ToastNotifier()
                    toaster.show_toast("Chrona Time Tracker", 
                                    "Running in system tray...",
                                    icon_path=None,
                                    duration=3,
                                    threaded=True)
                except Exception as e:
                    logger.error(f"Toast notification error: {e}")
            
            # Start the icon - this blocks until icon.stop() is called
            self.icon.run()
            
        except Exception as e:
            logger.error(f"Error running system tray: {e}")
            logger.error(traceback.format_exc())
    
    def connect_signals(self):
        """Connect signal handlers"""
        self.signals.toggle_tracking.connect(self.toggle_tracking)
        self.signals.show_task_window.connect(self.show_task_window)
        self.signals.refresh_tasks.connect(self.fetch_tasks)
        self.signals.test_api.connect(self.test_api_connection)
        self.signals.exit_app.connect(self.exit_app)
        self.signals.stop_tracking.connect(self.stop_tracking)
        self.signals.show_error.connect(self.show_error_dialog)
        self.signals.show_info.connect(self.show_info_dialog)
    
    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    self.config = json.load(f)
                logger.info(f"Configuration loaded from {CONFIG_FILE}")
            else:
                # Create default config
                self.config = {
                    'api_url': API_URL
                }
                self.save_config()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self.config = {
                'api_url': API_URL
            }
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Configuration saved to {CONFIG_FILE}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def test_api_connection(self):
        """Test API connection"""
        def _test_api():
            try:
                logger.info(f"Testing API connection to {API_URL}...")
                response = requests.get(f"{API_URL}/")
                
                if response.status_code == 200:
                    logger.info("API connection successful")
                    self.signals.api_test_result.emit(True, "Connection successful")
                    return True
                else:
                    logger.error(f"API returned non-200 status: {response.status_code}")
                    self.signals.api_test_result.emit(False, f"API returned status {response.status_code}")
                    return False
            except requests.RequestException as e:
                logger.error(f"API connection error: {e}")
                self.signals.api_test_result.emit(False, f"Connection error: {str(e)}")
                return False
        
        # Run in a separate thread
        threading.Thread(target=_test_api).start()
    
    def fetch_tasks(self):
        """Fetch tasks from the API"""
        def _fetch_tasks():
            try:
                logger.info(f"Fetching tasks from {API_URL}/tasks/")
                response = requests.get(f"{API_URL}/tasks/")
                
                if response.status_code == 200:
                    tasks = response.json()
                    logger.info(f"Fetched {len(tasks)} tasks")
                    self.tasks = tasks
                    self.signals.task_refresh_complete.emit(tasks)
                    return tasks
                else:
                    logger.error(f"Error fetching tasks: Status {response.status_code}")
                    self.signals.show_error.emit("Error", f"Failed to fetch tasks (Error {response.status_code})")
                    return []
            except Exception as e:
                logger.error(f"Error fetching tasks: {e}")
                self.signals.show_error.emit("Error", f"Failed to fetch tasks: {str(e)}")
                return []
        
        # Run in a separate thread
        threading.Thread(target=_fetch_tasks).start()
    
    def create_time_entry(self, task_id):
        """Create a new time entry in the API"""
        try:
            # Format the datetime as ISO 8601 string without timezone
            start_time = datetime.now().replace(microsecond=0).isoformat()
            
            data = {
                'task_id': task_id,
                'start_time': start_time,
                'end_time': None,
                'duration': None,
                'notes': None
            }
            
            logger.info(f"Creating time entry for task ID {task_id}")
            
            # Headers for JSON content
            headers = {'Content-Type': 'application/json'}
            
            response = requests.post(
                f"{API_URL}/time-entries/", 
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
                error_message = "Unknown error"
                try:
                    error_data = response.json()
                    error_message = error_data.get("detail", str(error_data))
                except Exception:
                    error_message = response.text[:500]
                
                logger.error(f"Error creating time entry: {error_message}")
                self.signals.show_error.emit("API Error", f"Failed to create time entry: {error_message}")
                return None
        except Exception as e:
            logger.error(f"Error creating time entry: {e}")
            self.signals.show_error.emit("Error", f"Failed to create time entry: {str(e)}")
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
            
            # Headers for JSON content
            headers = {'Content-Type': 'application/json'}
            
            response = requests.put(
                f"{API_URL}/time-entries/{entry_id}", 
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
                error_message = "Unknown error"
                try:
                    error_data = response.json()
                    error_message = error_data.get("detail", str(error_data))
                except Exception:
                    error_message = response.text[:500]
                
                logger.error(f"Error updating time entry: {error_message}")
                self.signals.show_error.emit("API Error", f"Failed to update time entry: {error_message}")
                return None
        except Exception as e:
            logger.error(f"Error updating time entry: {e}")
            self.signals.show_error.emit("Error", f"Failed to update time entry: {str(e)}")
            return None
    
    def calculate_duration(self):
        """Calculate duration in seconds"""
        if self.start_time:
            now = datetime.now()
            duration = (now - self.start_time).total_seconds()
            return int(duration)
        return 0
    
    def toggle_tracking(self):
        """Toggle time tracking"""
        if self.tracking:
            # Stop tracking
            self.stop_tracking()
        else:
            # Show task selection to start tracking
            self.show_task_window()
        
        # Ensure hotkey is active regardless of what happened
        QTimer.singleShot(500, self.initialize_hotkey)
    
    def show_task_window(self):
        """Show the task selection window"""
        # If already tracking, stop first
        if self.tracking:
            self.stop_tracking()
            return
            
        # If a task window already exists, close it first to prevent duplicates
        if hasattr(self, 'task_window') and self.task_window:
            try:
                self.task_window.close()
                self.task_window.deleteLater()
            except Exception as e:
                logger.error(f"Error closing existing task window: {e}")
            self.task_window = None
        
        # Create and show task window if it doesn't exist
        logger.info("Creating new task selection window")
        self.task_window = TaskSelectionWindow(self, self.tasks)
        self.task_window.show()
        self.task_window.activateWindow()
        self.task_window.raise_()
    
    def start_tracking(self, task_id, task_name):
        """Start tracking time for a task"""
        # Create time entry in the API
        entry = self.create_time_entry(task_id)
        if entry:
            # Store tracking info
            self.current_task_id = task_id
            self.current_task_name = task_name
            self.start_time = datetime.now()
            self.entry_id = entry.get('id')
            self.tracking = True
            
            # Update tray icon tooltip
            if self.icon:
                self.icon.title = f"Chrona - {task_name}: 00:00:00"
            
            # Create and show mini timer
            self.show_mini_timer()
            
            # Start timer to update display
            self.update_timer()
            
            logger.info(f"Started tracking task '{task_name}' with entry ID {self.entry_id}")
    
    def stop_tracking(self):
        """Stop tracking time"""
        if not self.tracking or not self.entry_id:
            return
        
        # Update time entry in the API
        entry = self.update_time_entry(self.entry_id)
        if entry:
            duration = self.calculate_duration()
            formatted = format_duration(duration)
            
            # Update tracking state
            self.tracking = False
            
            logger.info(f"Tracking stopped. Duration: {formatted}")
            
            # Close the mini timer window
            if self.mini_timer:
                self.mini_timer.close()
                self.mini_timer.deleteLater()
                self.mini_timer = None
            
            # Reset the tray icon tooltip
            if self.icon:
                self.icon.title = "Chrona Time Tracker"
            
            # Store the task name and formatted duration for use in the result window
            task_name = self.current_task_name
            self.task_duration = formatted
            
            # Close any existing result window first
            if hasattr(self, 'result_window') and self.result_window:
                try:
                    self.result_window.close()
                    self.result_window.deleteLater()
                except Exception as e:
                    logger.error(f"Error closing existing result window: {e}")
                self.result_window = None
            
            # Show the result window - direct call instead of using timer
            logger.info(f"Showing result window for task: {task_name} with duration: {formatted}")
            self.show_result_window(task_name, formatted)
    
    def show_mini_timer(self):
        """Show the mini timer window"""
        # Close any existing mini timer first
        if self.mini_timer:
            try:
                self.mini_timer.close()
                self.mini_timer.deleteLater()
            except Exception as e:
                logger.error(f"Error closing existing mini timer: {e}")
            self.mini_timer = None
        
        logger.info("Creating new mini timer window")
        self.mini_timer = MiniTimer(self, self.current_task_name)
        self.mini_timer.show()
        self.mini_timer.activateWindow()
        self.mini_timer.raise_()
    
    def show_result_window(self, task_name, duration):
        """Show the result window with final duration"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel
        
        logger.info("Creating result window")
        
        # Create dialog
        dialog = QDialog(None, Qt.WindowType.WindowStaysOnTopHint)
        dialog.setWindowTitle("Time Tracked")
        dialog.resize(350, 200)
        dialog.setWindowIcon(self.app_icon)
        
        # Layout
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(ChronaTheme.PADDING * 2, ChronaTheme.PADDING * 2, 
                                 ChronaTheme.PADDING * 2, ChronaTheme.PADDING * 2)
        
        # Checkmark icon
        checkmark = QLabel("✓")
        checkmark.setObjectName("HeaderLabel")
        checkmark.setStyleSheet(f"color: {ChronaTheme.GREEN_ACCENT}; font-size: 36pt;")
        checkmark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(checkmark)
        
        # Success message
        success_label = QLabel("TIME TRACKED SUCCESSFULLY")
        success_label.setObjectName("HeaderLabel")
        success_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(success_label)
        
        layout.addSpacing(ChronaTheme.PADDING)
        
        # Task name
        task_container = RoundedFrame()
        task_layout = QHBoxLayout(task_container)
        
        task_label = QLabel("Task:")
        task_layout.addWidget(task_label)
        
        task_value = QLabel(task_name)
        task_value.setStyleSheet("font-weight: bold;")
        task_layout.addWidget(task_value)
        
        layout.addWidget(task_container)
        
        # Duration
        duration_container = RoundedFrame()
        duration_layout = QHBoxLayout(duration_container)
        
        duration_label = QLabel("Duration:")
        duration_layout.addWidget(duration_label)
        
        duration_value = QLabel(duration)
        duration_value.setObjectName("TimerLabel")
        duration_layout.addWidget(duration_value)
        
        layout.addWidget(duration_container)
        
        layout.addSpacing(ChronaTheme.PADDING)
        
        # Close button with custom handler to ensure proper cleanup
        def on_close_button():
            dialog.close()
            # Re-register hotkey after dialog closes
            self.initialize_hotkey()
            # Ensure proper cleanup
            self.result_window = None
        
        # Add option to start another task
        def on_next_task_button():
            dialog.close()
            # Re-register hotkey after dialog closes
            self.initialize_hotkey()
            # Ensure proper cleanup
            self.result_window = None
            # Show task selection
            QTimer.singleShot(100, self.show_task_window)
            
        button_layout = QHBoxLayout()
        
        # Close button
        close_button = QPushButton("CLOSE")
        close_button.clicked.connect(on_close_button)
        button_layout.addWidget(close_button)
        
        # Next task button
        next_task_button = QPushButton("START ANOTHER TASK")
        next_task_button.clicked.connect(on_next_task_button)
        button_layout.addWidget(next_task_button)
        
        layout.addLayout(button_layout)
        
        # Also handle dialog's finished signal - ensure proper cleanup
        dialog.finished.connect(lambda: 
            QTimer.singleShot(100, lambda: (self.initialize_hotkey(), setattr(self, 'result_window', None)))
        )
        
        # Center the window on screen
        screen = QApplication.primaryScreen().geometry()
        dialog_size = dialog.size()
        dialog.move(
            (screen.width() - dialog_size.width()) // 2,
            (screen.height() - dialog_size.height()) // 2
        )
        
        # Make sure it stays on top and has focus
        dialog.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.WindowTitleHint | 
            Qt.WindowType.CustomizeWindowHint
        )
        
        # Store a reference to prevent garbage collection
        self.result_window = dialog
        
        dialog.show()
        dialog.activateWindow()
        dialog.raise_()
        
        logger.info("Result window created and shown")
        
        # Force processing of events to make sure window is shown
        self.app.processEvents()
    
    def update_timer(self):
        """Update the timer display"""
        if self.tracking and self.start_time:
            duration = self.calculate_duration()
            formatted = format_duration(duration)
            
            # Update tray icon tooltip
            if self.icon:
                self.icon.title = f"Chrona - {self.current_task_name}: {formatted}"
            
            # Update mini timer if visible
            self.signals.update_timer.emit(formatted)
            
            # Schedule next update
            QTimer.singleShot(1000, self.update_timer)
    
    def show_error_dialog(self, title, message):
        """Show an error dialog"""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(None, title, message)
    
    def show_info_dialog(self, title, message):
        """Show an info dialog"""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(None, title, message)
    
    def exit_app(self):
        """Exit the application"""
        logger.info("Preparing to exit application")
        
        # Stop tracking if active
        if self.tracking:
            self.stop_tracking()
        
        # Close any open windows
        for window_name in ['task_window', 'mini_timer', 'result_window', 'keep_alive_widget']:
            if hasattr(self, window_name) and getattr(self, window_name) is not None:
                try:
                    window = getattr(self, window_name)
                    logger.info(f"Closing {window_name}")
                    window.close()
                    window.deleteLater()
                    setattr(self, window_name, None)
                except Exception as e:
                    logger.error(f"Error closing {window_name}: {e}")
        
        # Save configuration
        self.save_config()
        
        # Stop the system tray icon in a separate thread to avoid blocking
        if self.icon:
            def stop_icon():
                try:
                    self.icon.stop()
                except Exception as e:
                    logger.error(f"Error stopping icon: {e}")
            
            threading.Thread(target=stop_icon).start()
        
        # Unhook all keyboard hooks
        try:
            keyboard.unhook_all()
            logger.info("Unhooked all keyboard hooks")
        except Exception as e:
            logger.error(f"Error unhooking keyboard: {e}")
        
        # Quit the application after a short delay to ensure tray icon is stopped
        logger.info("Quitting application")
        QTimer.singleShot(500, self.app.quit)
    
    def run(self):
        """Run the application main loop"""
        logger.info("Starting Chrona application main loop")
        
        # Create a hidden QWidget to keep the application running
        # This prevents the main loop from exiting when all windows are closed
        self.keep_alive_widget = QWidget()
        self.keep_alive_widget.setWindowTitle("ChronaKeepAlive")
        self.keep_alive_widget.resize(0, 0)
        self.keep_alive_widget.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.keep_alive_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.keep_alive_widget.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.keep_alive_widget.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.keep_alive_widget.move(-1000, -1000)  # Move off-screen
        self.keep_alive_widget.show()
        
        # Set QuitOnLastWindowClosed to False to prevent app from quitting
        # when all visible windows are closed
        self.app.setQuitOnLastWindowClosed(False)
        
        return self.app.exec()


if __name__ == "__main__":
    import ctypes
    import platform
    
    def is_admin():
        """Check if the script is running with admin privileges"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    try:
        # Try to run with admin rights on Windows
        if platform.system() == 'Windows' and not is_admin():
            logger.info("Requesting admin privileges...")
            # Re-run the program with admin rights
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        else:
            # Show a notification that the app is starting if possible
            if platform.system() == 'Windows' and ToastNotifier:
                try:
                    toaster = ToastNotifier()
                    toaster.show_toast("Chrona Time Tracker", 
                                     "Starting in system tray...",
                                     icon_path=None,
                                     duration=3,
                                     threaded=True)
                except Exception as e:
                    logger.error(f"Toast notification error: {e}")
            
            # Start the application
            app = ChronaApp()
            
            # Create a global reference to prevent garbage collection
            global_app_reference = app
            
            # Run the application
            exit_code = app.run()
            
            # If the main loop exits but the app should continue running in system tray
            logger.info(f"Application main loop exited with code {exit_code}, but app will continue running")
            
            # This will keep the process alive even if the main loop exits
            if platform.system() == 'Windows':
                # Keep the process alive
                try:
                    # This will block until killed
                    import time
                    while True:
                        # Process any queued commands every second
                        app.process_command_queue()
                        # Sleep but also allow for KeyboardInterrupt
                        time.sleep(1)
                except KeyboardInterrupt:
                    logger.info("Application terminated by user")
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1) 