"""
UI Helper Utilities for Hassad ERP.

Provides helper functions for safely embedding module windows
into the main application layout.
"""

import logging
from typing import Any

from PyQt6.QtWidgets import QWidget, QMainWindow, QVBoxLayout

logger = logging.getLogger(__name__)


def wrap_window_for_embedding(window_instance: Any, parent: QWidget = None) -> QWidget:
    """
    Wrap a QMainWindow instance for embedding in a layout.
    
    QMainWindow cannot be directly embedded in layouts (it's a top-level window).
    This function wraps it in a QWidget container that can be embedded.
    
    Args:
        window_instance: Instance of QMainWindow or QWidget to embed
        parent: Parent widget for the wrapper
        
    Returns:
        QWidget: Embeddable widget (either the original QWidget or a wrapper)
    """
    # If already a QWidget (not QMainWindow), return as-is
    if isinstance(window_instance, QWidget) and not isinstance(window_instance, QMainWindow):
        logger.debug(f"{window_instance.__class__.__name__} is QWidget - no wrapping needed")
        return window_instance
    
    # If it's a QMainWindow, we need to wrap it
    if isinstance(window_instance, QMainWindow):
        logger.info(f"Wrapping QMainWindow {window_instance.__class__.__name__} for embedding")
        
        # Create wrapper widget
        wrapper = QWidget(parent)
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Get the central widget from QMainWindow
        central = window_instance.centralWidget()
        if central:
            # Reparent the central widget to our wrapper
            central.setParent(wrapper)
            layout.addWidget(central)
            logger.debug(f"Extracted and wrapped central widget from {window_instance.__class__.__name__}")
        else:
            logger.warning(f"{window_instance.__class__.__name__} has no central widget - wrapping entire window")
            # Fallback: wrap the entire QMainWindow (may cause display issues)
            layout.addWidget(window_instance)
        
        return wrapper
    
    # Fallback for unknown types
    logger.warning(f"Unknown widget type: {type(window_instance)} - returning as-is")
    return window_instance
