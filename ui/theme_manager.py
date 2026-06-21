"""
Theme Manager for Hassad ERP System
====================================

Manages application themes including Light, Dark, and RTL modes.
Provides runtime theme switching, locale detection, and theme persistence.

Features:
- Light and Dark theme support
- RTL (Right-to-Left) layout for Arabic
- Runtime theme switching without restart
- Automatic locale detection
- Theme preference persistence
- Signal emission for theme change events
- Comprehensive logging

Phase: F2.1 - Theme Engine Implementation
Version: 1.0.0
Author: Hassad ERP Development Team
"""

import os
import json
import locale
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from enum import Enum

from PyQt6.QtCore import QObject, pyqtSignal, Qt
from PyQt6.QtWidgets import QApplication

# ============================================================================
# LOGGING SETUP
# ============================================================================

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

# Configure theme engine logger
theme_logger = logging.getLogger('theme_engine')
theme_logger.setLevel(logging.INFO)

# File handler for theme engine
theme_handler = logging.FileHandler('logs/theme_engine.log', encoding='utf-8')
theme_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
theme_handler.setFormatter(theme_formatter)
theme_logger.addHandler(theme_handler)

# Console handler for important messages
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)
console_handler.setFormatter(theme_formatter)
theme_logger.addHandler(console_handler)

# ============================================================================
# THEME ENUMERATIONS
# ============================================================================

class ThemeMode(Enum):
    """Available theme modes."""
    LIGHT = "light"
    DARK = "dark"

class LayoutDirection(Enum):
    """Layout direction for text."""
    LTR = "ltr"  # Left-to-Right (English, etc.)
    RTL = "rtl"  # Right-to-Left (Arabic, Hebrew, etc.)

# ============================================================================
# THEME MANAGER CLASS
# ============================================================================

class ThemeManager(QObject):
    """
    Manages application themes and layout direction.
    
    Provides centralized theme management with support for:
    - Light and Dark themes
    - RTL (Right-to-Left) layout
    - Runtime theme switching
    - Theme persistence
    - Locale detection
    
    Signals:
        theme_changed: Emitted when theme changes (theme_name: str, is_rtl: bool)
    """
    
    # Signal emitted when theme changes
    theme_changed = pyqtSignal(str, bool)  # (theme_name, is_rtl)
    
    # Theme file paths
    THEMES_DIR = Path("ui/themes")
    THEME_FILES = {
        ThemeMode.LIGHT: THEMES_DIR / "light.qss",
        ThemeMode.DARK: THEMES_DIR / "dark.qss",
    }
    RTL_THEME_FILE = THEMES_DIR / "rtl.qss"
    
    # Settings file
    SETTINGS_FILE = Path("ui/.theme_settings.json")
    
    # Default theme
    DEFAULT_THEME = ThemeMode.LIGHT
    DEFAULT_DIRECTION = LayoutDirection.LTR
    
    # RTL language codes
    RTL_LANGUAGES = ['ar', 'he', 'fa', 'ur']  # Arabic, Hebrew, Persian, Urdu
    
    def __init__(self, parent: Optional[QObject] = None):
        """
        Initialize Theme Manager.
        
        Args:
            parent: Parent QObject (optional)
        """
        super().__init__(parent)
        
        self._current_theme: ThemeMode = self.DEFAULT_THEME
        self._current_direction: LayoutDirection = self.DEFAULT_DIRECTION
        self._app: Optional[QApplication] = None
        
        # Theme cache
        self._theme_cache: Dict[str, str] = {}
        
        theme_logger.info("ThemeManager initialized")
        
        # Load persisted settings
        self._load_settings()
        
        # Detect system locale
        self._detect_locale()
    
    def _detect_locale(self) -> None:
        """
        Detect system locale and set RTL if Arabic or other RTL language.
        """
        try:
            # Get system locale
            system_locale = locale.getdefaultlocale()[0]
            
            if system_locale:
                language_code = system_locale.split('_')[0].lower()
                theme_logger.info(f"Detected system locale: {system_locale} (language: {language_code})")
                
                # Check if RTL language
                if language_code in self.RTL_LANGUAGES:
                    theme_logger.info(f"RTL language detected: {language_code}")
                    self._current_direction = LayoutDirection.RTL
                else:
                    theme_logger.info(f"LTR language detected: {language_code}")
                    self._current_direction = LayoutDirection.LTR
            else:
                theme_logger.warning("Could not detect system locale, defaulting to LTR")
                
        except Exception as e:
            theme_logger.error(f"Error detecting locale: {e}", exc_info=True)
            self._current_direction = LayoutDirection.LTR
    
    def _load_settings(self) -> None:
        """Load theme settings from file."""
        try:
            if self.SETTINGS_FILE.exists():
                with open(self.SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    
                # Load theme
                theme_name = settings.get('theme', self.DEFAULT_THEME.value)
                self._current_theme = ThemeMode(theme_name)
                
                # Load direction
                direction_name = settings.get('direction', self.DEFAULT_DIRECTION.value)
                self._current_direction = LayoutDirection(direction_name)
                
                theme_logger.info(f"Loaded settings: theme={self._current_theme.value}, direction={self._current_direction.value}")
            else:
                theme_logger.info("No existing theme settings found, using defaults")
                
        except Exception as e:
            theme_logger.error(f"Error loading theme settings: {e}", exc_info=True)
            # Use defaults on error
            self._current_theme = self.DEFAULT_THEME
            self._current_direction = self.DEFAULT_DIRECTION
    
    def _save_settings(self) -> None:
        """Save theme settings to file."""
        try:
            # Ensure directory exists
            self.SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            settings = {
                'theme': self._current_theme.value,
                'direction': self._current_direction.value
            }
            
            with open(self.SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)
            
            theme_logger.info(f"Saved theme settings: {settings}")
            
        except Exception as e:
            theme_logger.error(f"Error saving theme settings: {e}", exc_info=True)
    
    def _load_stylesheet(self, theme_file: Path) -> str:
        """
        Load stylesheet from file.
        
        Args:
            theme_file: Path to QSS file
            
        Returns:
            Stylesheet content as string
            
        Raises:
            FileNotFoundError: If theme file doesn't exist
        """
        if not theme_file.exists():
            error_msg = f"Theme file not found: {theme_file}"
            theme_logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        # Check cache
        cache_key = str(theme_file)
        if cache_key in self._theme_cache:
            theme_logger.debug(f"Using cached stylesheet: {theme_file.name}")
            return self._theme_cache[cache_key]
        
        # Load from file
        try:
            with open(theme_file, 'r', encoding='utf-8') as f:
                stylesheet = f.read()
            
            # Cache it
            self._theme_cache[cache_key] = stylesheet
            
            theme_logger.info(f"Loaded stylesheet: {theme_file.name} ({len(stylesheet)} characters)")
            return stylesheet
            
        except Exception as e:
            theme_logger.error(f"Error reading theme file {theme_file}: {e}", exc_info=True)
            raise
    
    def apply_theme(self, app: QApplication, theme_mode: Optional[ThemeMode] = None, 
                    direction: Optional[LayoutDirection] = None) -> bool:
        """
        Apply theme to application.
        
        Args:
            app: QApplication instance
            theme_mode: Theme to apply (Light/Dark). If None, uses current theme.
            direction: Layout direction (LTR/RTL). If None, uses current direction.
            
        Returns:
            True if theme applied successfully, False otherwise
        """
        try:
            self._app = app
            
            # Use provided values or current values
            if theme_mode is not None:
                self._current_theme = theme_mode
            if direction is not None:
                self._current_direction = direction
            
            theme_logger.info(f"Applying theme: {self._current_theme.value}, direction: {self._current_direction.value}")
            
            # Load base theme
            theme_file = self.THEME_FILES[self._current_theme]
            base_stylesheet = self._load_stylesheet(theme_file)
            
            # Load RTL stylesheet if needed
            if self._current_direction == LayoutDirection.RTL:
                rtl_stylesheet = self._load_stylesheet(self.RTL_THEME_FILE)
                # Combine stylesheets
                combined_stylesheet = base_stylesheet + "\n\n" + rtl_stylesheet
                theme_logger.info("Applied RTL stylesheet overlay")
            else:
                combined_stylesheet = base_stylesheet
            
            # Apply to application
            app.setStyleSheet(combined_stylesheet)
            
            # Set layout direction
            if self._current_direction == LayoutDirection.RTL:
                app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
                theme_logger.info("Set layout direction to RTL")
            else:
                app.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
                theme_logger.info("Set layout direction to LTR")
            
            # Save settings
            self._save_settings()
            
            # Emit signal
            is_rtl = (self._current_direction == LayoutDirection.RTL)
            self.theme_changed.emit(self._current_theme.value, is_rtl)
            
            theme_logger.info(f"✓ Theme applied successfully: {self._current_theme.value} ({self._current_direction.value})")
            return True
            
        except Exception as e:
            theme_logger.error(f"✗ Failed to apply theme: {e}", exc_info=True)
            return False
    
    def toggle_theme(self) -> bool:
        """
        Toggle between Light and Dark themes.
        
        Returns:
            True if toggle successful, False otherwise
        """
        if self._app is None:
            theme_logger.error("Cannot toggle theme: No application instance set")
            return False
        
        # Toggle theme
        new_theme = ThemeMode.DARK if self._current_theme == ThemeMode.LIGHT else ThemeMode.LIGHT
        
        theme_logger.info(f"Toggling theme: {self._current_theme.value} → {new_theme.value}")
        
        return self.apply_theme(self._app, theme_mode=new_theme)
    
    def set_light_theme(self) -> bool:
        """
        Set Light theme.
        
        Returns:
            True if successful, False otherwise
        """
        if self._app is None:
            theme_logger.error("Cannot set theme: No application instance set")
            return False
        
        return self.apply_theme(self._app, theme_mode=ThemeMode.LIGHT)
    
    def set_dark_theme(self) -> bool:
        """
        Set Dark theme.
        
        Returns:
            True if successful, False otherwise
        """
        if self._app is None:
            theme_logger.error("Cannot set theme: No application instance set")
            return False
        
        return self.apply_theme(self._app, theme_mode=ThemeMode.DARK)
    
    def toggle_direction(self) -> bool:
        """
        Toggle between LTR and RTL layout directions.
        
        Returns:
            True if toggle successful, False otherwise
        """
        if self._app is None:
            theme_logger.error("Cannot toggle direction: No application instance set")
            return False
        
        # Toggle direction
        new_direction = LayoutDirection.RTL if self._current_direction == LayoutDirection.LTR else LayoutDirection.LTR
        
        theme_logger.info(f"Toggling direction: {self._current_direction.value} → {new_direction.value}")
        
        return self.apply_theme(self._app, direction=new_direction)
    
    def set_rtl_mode(self, enable: bool) -> bool:
        """
        Enable or disable RTL mode.
        
        Args:
            enable: True to enable RTL, False for LTR
            
        Returns:
            True if successful, False otherwise
        """
        if self._app is None:
            theme_logger.error("Cannot set RTL mode: No application instance set")
            return False
        
        new_direction = LayoutDirection.RTL if enable else LayoutDirection.LTR
        return self.apply_theme(self._app, direction=new_direction)
    
    @property
    def current_theme(self) -> ThemeMode:
        """Get current theme mode."""
        return self._current_theme
    
    @property
    def current_direction(self) -> LayoutDirection:
        """Get current layout direction."""
        return self._current_direction
    
    @property
    def is_dark_theme(self) -> bool:
        """Check if current theme is dark."""
        return self._current_theme == ThemeMode.DARK
    
    @property
    def is_rtl(self) -> bool:
        """Check if current layout is RTL."""
        return self._current_direction == LayoutDirection.RTL
    
    def get_theme_name(self, bilingual: bool = False) -> str:
        """
        Get human-readable theme name.
        
        Args:
            bilingual: If True, return bilingual name (English + Arabic)
            
        Returns:
            Theme name string
        """
        if self._current_theme == ThemeMode.LIGHT:
            return "Light Theme | الوضع الفاتح" if bilingual else "Light Theme"
        else:
            return "Dark Theme | الوضع الداكن" if bilingual else "Dark Theme"
    
    def get_available_themes(self) -> Dict[str, str]:
        """
        Get list of available themes.
        
        Returns:
            Dictionary mapping theme values to display names
        """
        return {
            ThemeMode.LIGHT.value: "Light Theme | الوضع الفاتح",
            ThemeMode.DARK.value: "Dark Theme | الوضع الداكن"
        }
    
    def clear_cache(self) -> None:
        """Clear stylesheet cache (useful for development)."""
        self._theme_cache.clear()
        theme_logger.info("Theme cache cleared")
    
    def reload_theme(self) -> bool:
        """
        Reload current theme (useful for development/debugging).
        
        Returns:
            True if reload successful, False otherwise
        """
        if self._app is None:
            theme_logger.error("Cannot reload theme: No application instance set")
            return False
        
        theme_logger.info("Reloading theme...")
        self.clear_cache()
        return self.apply_theme(self._app)
    
    def get_theme_info(self) -> Dict[str, Any]:
        """
        Get comprehensive theme information.
        
        Returns:
            Dictionary with theme details
        """
        return {
            'theme': self._current_theme.value,
            'theme_display_name': self.get_theme_name(bilingual=True),
            'direction': self._current_direction.value,
            'is_dark': self.is_dark_theme,
            'is_rtl': self.is_rtl,
            'theme_file': str(self.THEME_FILES[self._current_theme]),
            'rtl_enabled': self.is_rtl,
        }


# ============================================================================
# GLOBAL THEME MANAGER INSTANCE
# ============================================================================

# Singleton instance
_theme_manager_instance: Optional[ThemeManager] = None

def get_theme_manager() -> ThemeManager:
    """
    Get global ThemeManager instance (singleton pattern).
    
    Returns:
        ThemeManager instance
    """
    global _theme_manager_instance
    
    if _theme_manager_instance is None:
        _theme_manager_instance = ThemeManager()
        theme_logger.info("Created global ThemeManager instance")
    
    return _theme_manager_instance


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def apply_theme(app: QApplication, theme_name: str = "light", enable_rtl: bool = False) -> bool:
    """
    Convenience function to apply theme.
    
    Args:
        app: QApplication instance
        theme_name: Theme name ("light" or "dark")
        enable_rtl: Enable RTL layout
        
    Returns:
        True if successful, False otherwise
    """
    manager = get_theme_manager()
    
    try:
        theme_mode = ThemeMode(theme_name.lower())
        direction = LayoutDirection.RTL if enable_rtl else LayoutDirection.LTR
        return manager.apply_theme(app, theme_mode=theme_mode, direction=direction)
    except ValueError:
        theme_logger.error(f"Invalid theme name: {theme_name}")
        return False


def toggle_theme() -> bool:
    """
    Convenience function to toggle theme.
    
    Returns:
        True if successful, False otherwise
    """
    manager = get_theme_manager()
    return manager.toggle_theme()


# ============================================================================
# MODULE INITIALIZATION
# ============================================================================

theme_logger.info("=" * 70)
theme_logger.info("Theme Engine Module Loaded")
theme_logger.info(f"Themes Directory: {ThemeManager.THEMES_DIR}")
theme_logger.info(f"Available Themes: {list(ThemeManager.THEME_FILES.keys())}")
theme_logger.info("=" * 70)
