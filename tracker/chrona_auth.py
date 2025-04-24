import sys
import os
import requests
import json
import logging
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QApplication, QFrame, QStackedWidget
)
from PyQt6.QtCore import Qt, QSettings, QSize, pyqtSignal, pyqtSlot

# Set up logging
logger = logging.getLogger("Chrona.Auth")

# API URL
API_URL = os.environ.get('CHRONA_API_URL', 'https://chrona-backend.onrender.com')

class AuthManager:
    """Authentication manager for Chrona"""
    
    def __init__(self):
        # Initialize settings storage
        self.settings = QSettings("Chrona", "TimeTracker")
        self.user_id = self.settings.value("auth/user_id", "")
        self.token = self.settings.value("auth/token", "")
        self.token_expiry = self.settings.value("auth/token_expiry", 0)
        self.user_name = self.settings.value("auth/user_name", "")
        self.user_email = self.settings.value("auth/user_email", "")
    
    def is_authenticated(self):
        """Check if the user is authenticated and token is valid"""
        if not self.token:
            return False
        
        # Check if token is expired
        try:
            expiry = int(self.token_expiry)
            now = int(datetime.now().timestamp())
            if now >= expiry:
                # Token expired
                logger.info("Auth token expired")
                return False
        except (ValueError, TypeError):
            # Invalid expiry value
            return False
        
        return True
    
    def get_auth_headers(self):
        """Get authorization headers for API requests"""
        if not self.is_authenticated():
            return {}
        
        return {
            "Authorization": f"Bearer {self.token}"
        }
    
    def save_auth_data(self, token, user_id, expires_at, user_name="", user_email=""):
        """Save authentication data to settings"""
        self.token = token
        self.user_id = user_id
        self.token_expiry = expires_at
        self.user_name = user_name
        self.user_email = user_email
        
        # Save to settings
        self.settings.setValue("auth/user_id", user_id)
        self.settings.setValue("auth/token", token)
        self.settings.setValue("auth/token_expiry", expires_at)
        self.settings.setValue("auth/user_name", user_name)
        self.settings.setValue("auth/user_email", user_email)
        
        logger.info(f"Saved auth data for user {user_id}")
    
    def clear_auth_data(self):
        """Clear authentication data"""
        self.token = ""
        self.user_id = ""
        self.token_expiry = 0
        self.user_name = ""
        self.user_email = ""
        
        # Clear from settings
        self.settings.remove("auth/user_id")
        self.settings.remove("auth/token")
        self.settings.remove("auth/token_expiry")
        self.settings.remove("auth/user_name")
        self.settings.remove("auth/user_email")
        
        logger.info("Cleared auth data")
    
    def login(self, email, password):
        """Login to the API and get a token"""
        try:
            # Prepare form data
            data = {
                'username': email,
                'password': password
            }
            
            # Make login request
            response = requests.post(
                f"{API_URL}/token",
                data=data,
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            )
            
            # Check response
            if response.status_code != 200:
                error_msg = f"Login failed: {response.status_code}"
                try:
                    error_data = response.json()
                    if "detail" in error_data:
                        error_msg = error_data["detail"]
                except:
                    pass
                
                logger.error(f"Login failed: {error_msg}")
                return False, error_msg
            
            # Parse response
            token_data = response.json()
            
            # Make request to get user details
            user_response = requests.get(
                f"{API_URL}/users/me",
                headers={
                    'Authorization': f"Bearer {token_data['access_token']}"
                }
            )
            
            if user_response.status_code != 200:
                logger.error(f"Failed to get user details: {user_response.status_code}")
                return False, "Failed to get user details"
            
            # Parse user data
            user_data = user_response.json()
            
            # Save auth data
            self.save_auth_data(
                token_data["access_token"],
                token_data["user_id"],
                token_data["expires_at"],
                user_data.get("name", ""),
                user_data.get("email", "")
            )
            
            return True, "Login successful"
        
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False, f"Login error: {str(e)}"
    
    def register(self, email, password, name=""):
        """Register a new user"""
        try:
            # Prepare data
            data = {
                'email': email,
                'password': password,
                'name': name
            }
            
            # Make registration request
            response = requests.post(
                f"{API_URL}/register",
                json=data,
                headers={
                    'Content-Type': 'application/json'
                }
            )
            
            # Check response
            if response.status_code not in [200, 201]:
                error_msg = f"Registration failed: {response.status_code}"
                try:
                    error_data = response.json()
                    if "detail" in error_data:
                        error_msg = error_data["detail"]
                except:
                    pass
                
                logger.error(f"Registration failed: {error_msg}")
                return False, error_msg
            
            # Registration successful, now login
            return self.login(email, password)
        
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return False, f"Registration error: {str(e)}"
    
    def logout(self):
        """Logout the user"""
        self.clear_auth_data()
        return True, "Logged out successfully"
    
    def get_current_user(self):
        """Get current user details"""
        if not self.is_authenticated():
            return None
        
        return {
            "id": self.user_id,
            "name": self.user_name,
            "email": self.user_email
        }


class LoginDialog(QDialog):
    """Login dialog for Chrona"""
    
    login_successful = pyqtSignal()
    
    def __init__(self, auth_manager, parent=None):
        super().__init__(parent)
        
        self.auth_manager = auth_manager
        
        # Set window properties
        self.setWindowTitle("Login to Chrona")
        self.setFixedSize(400, 300)
        
        # Create layout
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(20)
        
        # Title
        title_label = QLabel("CHRONA")
        title_label.setObjectName("HeaderLabel")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("Log in to sync your time tracking data")
        subtitle_label.setObjectName("SubHeaderLabel")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(subtitle_label)
        
        # Form container
        form_container = QFrame()
        form_container.setObjectName("RoundedContainerLight")
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(10)
        
        # Email field
        email_label = QLabel("Email:")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email")
        form_layout.addWidget(email_label)
        form_layout.addWidget(self.email_input)
        
        # Password field
        password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addWidget(password_label)
        form_layout.addWidget(self.password_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.login_button = QPushButton("LOGIN")
        self.login_button.clicked.connect(self.handle_login)
        button_layout.addWidget(self.login_button)
        
        self.register_button = QPushButton("REGISTER")
        self.register_button.setObjectName("SecondaryButton")
        self.register_button.clicked.connect(self.switch_to_register)
        button_layout.addWidget(self.register_button)
        
        form_layout.addLayout(button_layout)
        
        # Add form container to layout
        self.layout.addWidget(form_container)
    
    def handle_login(self):
        """Handle login button click"""
        email = self.email_input.text().strip()
        password = self.password_input.text()
        
        if not email or not password:
            QMessageBox.warning(self, "Error", "Please enter both email and password")
            return
        
        # Login
        success, message = self.auth_manager.login(email, password)
        
        if success:
            self.login_successful.emit()
            self.accept()
        else:
            QMessageBox.critical(self, "Login Failed", message)
    
    def switch_to_register(self):
        """Switch to registration dialog"""
        # Hide login dialog
        self.hide()
        
        # Create register dialog
        register_dialog = RegisterDialog(self.auth_manager, self.parent())
        register_dialog.login_successful.connect(self.login_successful.emit)
        register_dialog.login_successful.connect(self.accept)
        
        # Show register dialog
        if register_dialog.exec() == QDialog.DialogCode.Accepted:
            # User logged in through registration
            self.accept()
        else:
            # User cancelled registration, show login again
            self.show()


class RegisterDialog(QDialog):
    """Registration dialog for Chrona"""
    
    login_successful = pyqtSignal()
    
    def __init__(self, auth_manager, parent=None):
        super().__init__(parent)
        
        self.auth_manager = auth_manager
        
        # Set window properties
        self.setWindowTitle("Register for Chrona")
        self.setFixedSize(400, 350)
        
        # Create layout
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(20)
        
        # Title
        title_label = QLabel("CHRONA")
        title_label.setObjectName("HeaderLabel")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("Create a new account")
        subtitle_label.setObjectName("SubHeaderLabel")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(subtitle_label)
        
        # Form container
        form_container = QFrame()
        form_container.setObjectName("RoundedContainerLight")
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(10)
        
        # Name field
        name_label = QLabel("Name:")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter your name (optional)")
        form_layout.addWidget(name_label)
        form_layout.addWidget(self.name_input)
        
        # Email field
        email_label = QLabel("Email:")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email")
        form_layout.addWidget(email_label)
        form_layout.addWidget(self.email_input)
        
        # Password field
        password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addWidget(password_label)
        form_layout.addWidget(self.password_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.register_button = QPushButton("REGISTER")
        self.register_button.clicked.connect(self.handle_register)
        button_layout.addWidget(self.register_button)
        
        self.login_button = QPushButton("BACK TO LOGIN")
        self.login_button.setObjectName("SecondaryButton")
        self.login_button.clicked.connect(self.reject)
        button_layout.addWidget(self.login_button)
        
        form_layout.addLayout(button_layout)
        
        # Add form container to layout
        self.layout.addWidget(form_container)
    
    def handle_register(self):
        """Handle register button click"""
        name = self.name_input.text().strip()
        email = self.email_input.text().strip()
        password = self.password_input.text()
        
        if not email or not password:
            QMessageBox.warning(self, "Error", "Please enter both email and password")
            return
        
        # Register
        success, message = self.auth_manager.register(email, password, name)
        
        if success:
            self.login_successful.emit()
            self.accept()
        else:
            QMessageBox.critical(self, "Registration Failed", message)


class AuthDialog(QDialog):
    """Combined login/register dialog"""
    
    login_successful = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.auth_manager = AuthManager()
        
        # Set window properties
        self.setWindowTitle("Chrona Authentication")
        self.setFixedSize(400, 350)
        
        # Create main layout
        main_layout = QVBoxLayout(self)
        
        # Create stacked widget for login/register
        self.stacked_widget = QStackedWidget()
        
        # Create login widget
        login_widget = QWidget()
        login_layout = QVBoxLayout(login_widget)
        
        # Create login dialog and add to layout
        self.login_dialog = LoginDialog(self.auth_manager)
        self.login_dialog.login_successful.connect(self.login_successful.emit)
        login_layout.addWidget(self.login_dialog)
        
        # Add login widget to stacked widget
        self.stacked_widget.addWidget(login_widget)
        
        # Add stacked widget to main layout
        main_layout.addWidget(self.stacked_widget)

    def exec(self):
        """Show dialog and return result"""
        # Check if already authenticated
        if self.auth_manager.is_authenticated():
            self.login_successful.emit()
            return QDialog.DialogCode.Accepted
        
        # Show dialog
        return super().exec()
    
    def get_auth_manager(self):
        """Get the auth manager"""
        return self.auth_manager


# Test function
def main():
    """Test the auth dialogs"""
    app = QApplication(sys.argv)
    
    # Apply theme
    with open("style.qss", "r") as f:
        app.setStyleSheet(f.read())
    
    # Create auth dialog
    auth_dialog = AuthDialog()
    
    # Show dialog
    if auth_dialog.exec() == QDialog.DialogCode.Accepted:
        print("Authentication successful")
        auth_manager = auth_dialog.get_auth_manager()
        user = auth_manager.get_current_user()
        print(f"User: {user}")
    else:
        print("Authentication cancelled")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 