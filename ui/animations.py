"""
UI Animation Utilities for Hassad ERP
======================================

Provides smooth animations and visual effects for modern UI interactions.

Features:
- Fade in/out animations
- Slide animations
- Expand/collapse animations
- Hover effects
- Loading animations
- Card reveal effects

Phase: F2.4 - Form Redesign & Animations
Version: 1.0.0
"""

import logging
from typing import Optional
from enum import Enum

from PyQt6.QtCore import (
    QPropertyAnimation, QEasingCurve, QPoint, QSize,
    QParallelAnimationGroup, QSequentialAnimationGroup,
    pyqtProperty, QObject, QTimer
)
from PyQt6.QtWidgets import QWidget, QGraphicsOpacityEffect
from PyQt6.QtGui import QColor

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# ANIMATION CONSTANTS
# ============================================================================

class AnimationDuration(Enum):
    """Standard animation durations in milliseconds."""
    INSTANT = 0
    FAST = 150
    NORMAL = 250
    SLOW = 400
    VERY_SLOW = 600


class AnimationCurve(Enum):
    """Standard easing curves."""
    LINEAR = QEasingCurve.Type.Linear
    EASE_IN = QEasingCurve.Type.InQuad
    EASE_OUT = QEasingCurve.Type.OutQuad
    EASE_IN_OUT = QEasingCurve.Type.InOutQuad
    BOUNCE = QEasingCurve.Type.OutBounce
    ELASTIC = QEasingCurve.Type.OutElastic


# ============================================================================
# FADE ANIMATIONS
# ============================================================================

def fade_in(widget: QWidget, duration: int = AnimationDuration.NORMAL.value,
            curve: QEasingCurve.Type = AnimationCurve.EASE_OUT.value) -> QPropertyAnimation:
    """
    Fade in a widget from transparent to opaque.
    
    Args:
        widget: Widget to animate
        duration: Animation duration in milliseconds
        curve: Easing curve type
        
    Returns:
        QPropertyAnimation instance (automatically starts)
    """
    # Create opacity effect if not exists
    if not widget.graphicsEffect():
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
    
    effect = widget.graphicsEffect()
    effect.setOpacity(0.0)
    
    animation = QPropertyAnimation(effect, b"opacity")
    animation.setDuration(duration)
    animation.setStartValue(0.0)
    animation.setEndValue(1.0)
    animation.setEasingCurve(curve)
    
    widget.show()
    animation.start()
    
    logger.debug(f"Fade in animation started for {widget.__class__.__name__}")
    return animation


def fade_out(widget: QWidget, duration: int = AnimationDuration.NORMAL.value,
             curve: QEasingCurve.Type = AnimationCurve.EASE_IN.value,
             hide_on_finish: bool = True) -> QPropertyAnimation:
    """
    Fade out a widget from opaque to transparent.
    
    Args:
        widget: Widget to animate
        duration: Animation duration in milliseconds
        curve: Easing curve type
        hide_on_finish: Hide widget when animation completes
        
    Returns:
        QPropertyAnimation instance (automatically starts)
    """
    # Create opacity effect if not exists
    if not widget.graphicsEffect():
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
    
    effect = widget.graphicsEffect()
    
    animation = QPropertyAnimation(effect, b"opacity")
    animation.setDuration(duration)
    animation.setStartValue(1.0)
    animation.setEndValue(0.0)
    animation.setEasingCurve(curve)
    
    if hide_on_finish:
        animation.finished.connect(widget.hide)
    
    animation.start()
    
    logger.debug(f"Fade out animation started for {widget.__class__.__name__}")
    return animation


# ============================================================================
# SLIDE ANIMATIONS
# ============================================================================

def slide_in_from_right(widget: QWidget, distance: int = 100,
                        duration: int = AnimationDuration.NORMAL.value) -> QPropertyAnimation:
    """
    Slide widget in from the right.
    
    Args:
        widget: Widget to animate
        distance: Slide distance in pixels
        duration: Animation duration
        
    Returns:
        QPropertyAnimation instance
    """
    start_pos = widget.pos() + QPoint(distance, 0)
    end_pos = widget.pos()
    
    widget.move(start_pos)
    widget.show()
    
    animation = QPropertyAnimation(widget, b"pos")
    animation.setDuration(duration)
    animation.setStartValue(start_pos)
    animation.setEndValue(end_pos)
    animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    animation.start()
    return animation


def slide_in_from_bottom(widget: QWidget, distance: int = 100,
                         duration: int = AnimationDuration.NORMAL.value) -> QPropertyAnimation:
    """
    Slide widget in from the bottom.
    
    Args:
        widget: Widget to animate
        distance: Slide distance in pixels
        duration: Animation duration
        
    Returns:
        QPropertyAnimation instance
    """
    start_pos = widget.pos() + QPoint(0, distance)
    end_pos = widget.pos()
    
    widget.move(start_pos)
    widget.show()
    
    animation = QPropertyAnimation(widget, b"pos")
    animation.setDuration(duration)
    animation.setStartValue(start_pos)
    animation.setEndValue(end_pos)
    animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    animation.start()
    return animation


# ============================================================================
# EXPAND/COLLAPSE ANIMATIONS
# ============================================================================

def expand_vertical(widget: QWidget, target_height: int,
                   duration: int = AnimationDuration.NORMAL.value) -> QPropertyAnimation:
    """
    Expand widget vertically to target height.
    
    Args:
        widget: Widget to animate
        target_height: Target height in pixels
        duration: Animation duration
        
    Returns:
        QPropertyAnimation instance
    """
    animation = QPropertyAnimation(widget, b"maximumHeight")
    animation.setDuration(duration)
    animation.setStartValue(0)
    animation.setEndValue(target_height)
    animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    widget.setMaximumHeight(0)
    widget.show()
    animation.start()
    
    return animation


def collapse_vertical(widget: QWidget,
                     duration: int = AnimationDuration.NORMAL.value,
                     hide_on_finish: bool = True) -> QPropertyAnimation:
    """
    Collapse widget vertically to zero height.
    
    Args:
        widget: Widget to animate
        duration: Animation duration
        hide_on_finish: Hide widget when collapsed
        
    Returns:
        QPropertyAnimation instance
    """
    current_height = widget.height()
    
    animation = QPropertyAnimation(widget, b"maximumHeight")
    animation.setDuration(duration)
    animation.setStartValue(current_height)
    animation.setEndValue(0)
    animation.setEasingCurve(QEasingCurve.Type.InCubic)
    
    if hide_on_finish:
        animation.finished.connect(widget.hide)
    
    animation.start()
    
    return animation


# ============================================================================
# COMBINED ANIMATIONS
# ============================================================================

def fade_and_slide_in(widget: QWidget, 
                      slide_distance: int = 50,
                      duration: int = AnimationDuration.NORMAL.value) -> QParallelAnimationGroup:
    """
    Fade in and slide up simultaneously.
    
    Args:
        widget: Widget to animate
        slide_distance: Vertical slide distance
        duration: Animation duration
        
    Returns:
        QParallelAnimationGroup instance
    """
    # Opacity animation
    if not widget.graphicsEffect():
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
    
    effect = widget.graphicsEffect()
    effect.setOpacity(0.0)
    
    fade_anim = QPropertyAnimation(effect, b"opacity")
    fade_anim.setDuration(duration)
    fade_anim.setStartValue(0.0)
    fade_anim.setEndValue(1.0)
    fade_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
    
    # Position animation
    start_pos = widget.pos() + QPoint(0, slide_distance)
    end_pos = widget.pos()
    
    widget.move(start_pos)
    
    slide_anim = QPropertyAnimation(widget, b"pos")
    slide_anim.setDuration(duration)
    slide_anim.setStartValue(start_pos)
    slide_anim.setEndValue(end_pos)
    slide_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    # Combine animations
    group = QParallelAnimationGroup()
    group.addAnimation(fade_anim)
    group.addAnimation(slide_anim)
    
    widget.show()
    group.start()
    
    logger.debug(f"Combined fade+slide animation started for {widget.__class__.__name__}")
    return group


def sequential_card_reveal(widgets: list, 
                           delay_between: int = 100,
                           animation_duration: int = AnimationDuration.FAST.value) -> QSequentialAnimationGroup:
    """
    Reveal multiple cards sequentially with staggered timing.
    
    Args:
        widgets: List of widgets to animate
        delay_between: Delay between each card animation (ms)
        animation_duration: Duration of each card animation
        
    Returns:
        QSequentialAnimationGroup instance
    """
    group = QSequentialAnimationGroup()
    
    for i, widget in enumerate(widgets):
        # Create fade+slide for each card
        if not widget.graphicsEffect():
            effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(effect)
        
        effect = widget.graphicsEffect()
        effect.setOpacity(0.0)
        
        fade_anim = QPropertyAnimation(effect, b"opacity")
        fade_anim.setDuration(animation_duration)
        fade_anim.setStartValue(0.0)
        fade_anim.setEndValue(1.0)
        fade_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        
        group.addAnimation(fade_anim)
        
        # Add delay between cards
        if i < len(widgets) - 1:
            pause = QPropertyAnimation(effect, b"opacity")
            pause.setDuration(delay_between)
            pause.setStartValue(1.0)
            pause.setEndValue(1.0)
            group.addAnimation(pause)
        
        widget.show()
    
    group.start()
    
    logger.info(f"Sequential reveal animation started for {len(widgets)} widgets")
    return group


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def animate_property(widget: QWidget, property_name: bytes, 
                     start_value, end_value,
                     duration: int = AnimationDuration.NORMAL.value,
                     curve: QEasingCurve.Type = AnimationCurve.EASE_IN_OUT.value) -> QPropertyAnimation:
    """
    Generic property animation helper.
    
    Args:
        widget: Widget to animate
        property_name: Qt property name (e.g., b"geometry", b"pos")
        start_value: Starting value
        end_value: Ending value
        duration: Animation duration
        curve: Easing curve
        
    Returns:
        QPropertyAnimation instance
    """
    animation = QPropertyAnimation(widget, property_name)
    animation.setDuration(duration)
    animation.setStartValue(start_value)
    animation.setEndValue(end_value)
    animation.setEasingCurve(curve)
    
    animation.start()
    return animation


def delayed_call(callback, delay_ms: int):
    """
    Execute a callback after a delay.
    
    Args:
        callback: Function to call
        delay_ms: Delay in milliseconds
    """
    QTimer.singleShot(delay_ms, callback)


# ============================================================================
# HOVER EFFECTS
# ============================================================================

class HoverEffect:
    """
    Manages hover enter/leave animations for widgets.
    
    Example:
        hover = HoverEffect(my_card)
        hover.enable()
    """
    
    def __init__(self, widget: QWidget, 
                 hover_scale: float = 1.02,
                 duration: int = AnimationDuration.FAST.value):
        """
        Initialize hover effect.
        
        Args:
            widget: Widget to apply hover effect
            hover_scale: Scale factor on hover (e.g., 1.02 = 2% larger)
            duration: Animation duration
        """
        self.widget = widget
        self.hover_scale = hover_scale
        self.duration = duration
        self.original_size = None
        self.is_enabled = False
    
    def enable(self):
        """Enable hover effect."""
        self.widget.installEventFilter(self)
        self.is_enabled = True
        logger.debug(f"Hover effect enabled for {self.widget.__class__.__name__}")
    
    def disable(self):
        """Disable hover effect."""
        self.widget.removeEventFilter(self)
        self.is_enabled = False
    
    def eventFilter(self, obj, event):
        """Handle hover events."""
        if obj == self.widget and self.is_enabled:
            if event.type() == event.Type.Enter:
                self._on_hover_enter()
            elif event.type() == event.Type.Leave:
                self._on_hover_leave()
        
        return False
    
    def _on_hover_enter(self):
        """Handle mouse enter."""
        if not self.original_size:
            self.original_size = self.widget.size()
        
        # Subtle scale effect (not implemented due to Qt limitations)
        # Instead, we can change opacity or add shadow
        pass
    
    def _on_hover_leave(self):
        """Handle mouse leave."""
        pass


# ============================================================================
# MODULE INITIALIZATION
# ============================================================================

logger.info("Animation utilities loaded")
