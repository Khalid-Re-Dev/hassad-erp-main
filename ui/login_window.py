"""
Login window for user authentication.

This module provides the main login interface for the Hassad ERP system.
"""

import sys
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
)

from core.auth import (
    AuthenticationError,
    InactiveUserError,
    InvalidCredentialsError,
    authenticate_user,
)
from core.database import get_db_context
from core.session_manager import session_manager
from models import User


class LoginWindow(QDialog):
    """
    Login window for user authentication.

    Provides username/password input and authentication against database.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize login window.

        Args:
            parent: Parent widget (optional)
        """
        super().__init__(parent)
        self._authenticated_user: Optional[User] = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup user interface components."""
        self.setWindowTitle("Hassad ERP - Login")
        self.setFixedSize(400, 500)
        self.setModal(True)

        # Main layout
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        # Logo/Title section
        title_label = QLabel("Hassad ERP System")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        subtitle_label = QLabel("Point of Sale & Accounting")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_font = QFont()
        subtitle_font.setPointSize(12)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setStyleSheet("color: #666;")
        layout.addWidget(subtitle_label)

        layout.addSpacing(30)

        # Username field
        username_label = QLabel("Username or Email:")
        username_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(username_label)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username or email")
        self.username_input.setMinimumHeight(40)
        self.username_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
            }
        """)
        layout.addWidget(self.username_input)

        # Password field
        password_label = QLabel("Password:")
        password_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(password_label)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(40)
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
            }
        """)
        self.password_input.returnPressed.connect(self._handle_login)
        layout.addWidget(self.password_input)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        layout.addSpacing(10)

        # Login button
        self.login_button = QPushButton("Login")
        self.login_button.setMinimumHeight(45)
        self.login_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.login_button.clicked.connect(self._handle_login)
        layout.addWidget(self.login_button)

        # Info section
        layout.addStretch()
        info_label = QLabel("Default credentials:\nUsername: admin\nPassword: Admin123!")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("color: #999; font-size: 11px;")
        layout.addWidget(info_label)

        self.setLayout(layout)

        # Set focus to username field
        self.username_input.setFocus()

    def _handle_login(self) -> None:
        """Handle login button click."""
        username = self.username_input.text().strip()
        password = self.password_input.text()

        # Validate inputs
        if not username:
            self._show_error("Please enter username or email")
            return

        if not password:
            self._show_error("Please enter password")
            return

        # Disable login button during authentication
        self.login_button.setEnabled(False)
        self.login_button.setText("Authenticating...")
        self.status_label.setText("")

        # Attempt authentication
        try:
            with get_db_context() as db:
                user = authenticate_user(
                    session=db,
                    username=username,
                    password=password,
                    ip_address="127.0.0.1",  # Desktop app
                    user_agent="Hassad Desktop Client",
                )

                # Store authenticated user
                self._authenticated_user = user

                # Set session
                session_manager.login(user)

            # Close dialog with success (after context manager completes)
            self.accept()

        except InvalidCredentialsError:
            self._show_error("Invalid username or password")
        except InactiveUserError:
            self._show_error("Your account is inactive. Please contact administrator.")
        except AuthenticationError as e:
            self._show_error(f"Authentication failed: {str(e)}")
        except Exception as e:
            self._show_error(f"An error occurred: {str(e)}")
        finally:
            # Re-enable login button
            self.login_button.setEnabled(True)
            self.login_button.setText("Login")

    def _show_error(self, message: str) -> None:
        """
        Display error message.

        Args:
            message: Error message to display
        """
        self.status_label.setText(message)
        self.password_input.clear()
        self.password_input.setFocus()

    def get_authenticated_user(self) -> Optional[User]:
        """
        Get authenticated user after successful login.

        Returns:
            User: Authenticated user or None
        """
        return self._authenticated_user


def main():
    """Test login window."""
    app = QApplication(sys.argv)
    login = LoginWindow()

    if login.exec() == QDialog.DialogCode.Accepted:
        user = login.get_authenticated_user()
        if user:
            QMessageBox.information(
                None,
                "Login Successful",
                f"Welcome, {user.full_name}!\nRole: {', '.join([r.name for r in user.roles])}",
            )
    else:
        print("Login cancelled")

    sys.exit(0)


if __name__ == "__main__":
    main()
