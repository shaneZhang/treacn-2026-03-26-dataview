"""
Observer pattern implementation for data change notifications.

This module provides the observer pattern implementation to allow
components to be notified when data changes occur in the system.

Components:
- Subject: The object that maintains a list of observers and notifies them
- Observer: The interface for objects that want to be notified of changes
- Event: Represents a change event with type, data, and metadata
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
from datetime import datetime
import threading
from functools import wraps

from app.utils.logger import get_logger
from app.utils.exceptions import ObserverError

logger = get_logger(__name__)


class EventType(Enum):
    """Types of events that can be observed."""

    # Student events
    STUDENT_CREATED = "student_created"
    STUDENT_UPDATED = "student_updated"
    STUDENT_DELETED = "student_deleted"
    STUDENT_BULK_IMPORTED = "student_bulk_imported"

    # Class events
    CLASS_CREATED = "class_created"
    CLASS_UPDATED = "class_updated"
    CLASS_DELETED = "class_deleted"

    # Statistics events
    STATISTICS_GENERATED = "statistics_generated"
    STATISTICS_UPDATED = "statistics_updated"

    # Data events
    DATA_IMPORTED = "data_imported"
    DATA_EXPORTED = "data_exported"

    # Analysis events
    ANALYSIS_COMPLETED = "analysis_completed"
    VISUALIZATION_GENERATED = "visualization_generated"

    # System events
    SYSTEM_ERROR = "system_error"
    DATABASE_CONNECTED = "database_connected"
    DATABASE_DISCONNECTED = "database_disconnected"


class Event:
    """Represents an event that occurred in the system."""

    def __init__(
        self,
        event_type: EventType,
        data: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ):
        """
        Initialize an event.

        Args:
            event_type: Type of the event.
            data: Optional data associated with the event.
            source: Optional source of the event (e.g., component name).
            timestamp: Optional timestamp (defaults to now).
        """
        self.event_type = event_type
        self.data = data or {}
        self.source = source
        self.timestamp = timestamp or datetime.utcnow()
        self.event_id = f"{event_type.value}_{int(self.timestamp.timestamp() * 1000)}"

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the event to a dictionary.

        Returns:
            Dictionary representation of the event.
        """
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "data": self.data,
            "source": self.source,
            "timestamp": self.timestamp.isoformat()
        }

    def __repr__(self) -> str:
        """
        Return a string representation of the event.

        Returns:
            String representation.
        """
        return (
            f"Event(event_id='{self.event_id}', event_type='{self.event_type.value}', "
            f"source='{self.source}', timestamp='{self.timestamp}')"
        )


class Observer(ABC):
    """
    Abstract base class for observers.

    Observers implement this interface to receive notifications
    when events occur in the subject.
    """

    @abstractmethod
    def on_event(self, event: Event) -> None:
        """
        Handle an event.

        Args:
            event: The event that occurred.
        """
        pass

    def supports_event(self, event_type: EventType) -> bool:
        """
        Check if this observer supports a specific event type.

        Can be overridden by subclasses to filter events.

        Args:
            event_type: The event type to check.

        Returns:
            bool: True if the observer supports the event type, False otherwise.
        """
        return True


class Subject:
    """
    Subject class that maintains a list of observers and notifies them of events.

    This is the core of the observer pattern implementation.
    Components can subscribe to events and be notified when they occur.
    """

    def __init__(self):
        """Initialize the subject."""
        self._observers: List[Observer] = []
        self._event_history: List[Event] = []
        self._lock = threading.RLock()
        self._max_history = 1000  # Maximum number of events to keep in history

    def add_observer(self, observer: Observer) -> None:
        """
        Add an observer to be notified of events.

        Args:
            observer: The observer to add.
        """
        with self._lock:
            if observer not in self._observers:
                self._observers.append(observer)
                logger.debug(f"Added observer: {observer.__class__.__name__}")

    def remove_observer(self, observer: Observer) -> None:
        """
        Remove an observer from the notification list.

        Args:
            observer: The observer to remove.
        """
        with self._lock:
            if observer in self._observers:
                self._observers.remove(observer)
                logger.debug(f"Removed observer: {observer.__class__.__name__}")

    def notify_observers(self, event: Event) -> None:
        """
        Notify all observers of an event.

        Args:
            event: The event to notify observers about.

        Raises:
            ObserverError: If there's an error notifying observers.
        """
        with self._lock:
            # Add event to history
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history.pop(0)

            # Notify observers
            observers = self._observers.copy()

        for observer in observers:
            try:
                if observer.supports_event(event.event_type):
                    observer.on_event(event)
            except Exception as e:
                logger.error(
                    f"Error notifying observer {observer.__class__.__name__} "
                    f"of event {event.event_type}: {e}"
                )
                raise ObserverError(
                    message=f"Error notifying observer of event {event.event_type}",
                    details={
                        "observer": observer.__class__.__name__,
                        "event": event.to_dict(),
                        "error": str(e)
                    }
                ) from e

    def notify_event(
        self,
        event_type: EventType,
        data: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None
    ) -> Event:
        """
        Create and notify an event.

        This is a convenience method that creates the Event object
        and notifies observers in one call.

        Args:
            event_type: Type of the event.
            data: Optional data associated with the event.
            source: Optional source of the event.

        Returns:
            Event: The event that was created and notified.
        """
        event = Event(event_type, data, source)
        self.notify_observers(event)
        logger.debug(f"Notified event: {event_type.value}")
        return event

    def get_event_history(
        self,
        event_type: Optional[EventType] = None,
        limit: Optional[int] = None
    ) -> List[Event]:
        """
        Get the event history, optionally filtered by event type.

        Args:
            event_type: Optional event type to filter by.
            limit: Optional maximum number of events to return.

        Returns:
            List[Event]: List of events from the history.
        """
        with self._lock:
            events = self._event_history.copy()

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if limit:
            events = events[-limit:]

        return events

    def clear_event_history(self) -> None:
        """Clear the event history."""
        with self._lock:
            self._event_history.clear()
        logger.debug("Cleared event history")


class LoggingObserver(Observer):
    """
    Observer that logs all events.

    This observer logs all events to the application logger.
    """

    def on_event(self, event: Event) -> None:
        """
        Log an event.

        Args:
            event: The event to log.
        """
        log_message = (
            f"Event: {event.event_type.value} | "
            f"Source: {event.source or 'unknown'} | "
            f"Data: {event.data}"
        )

        # Log at appropriate level based on event type
        if event.event_type == EventType.SYSTEM_ERROR:
            logger.error(log_message)
        else:
            logger.info(log_message)


class StatisticsUpdateObserver(Observer):
    """
    Observer that triggers statistics updates when student data changes.

    This observer listens for student-related events and triggers
    the recalculation of statistics.
    """

    def __init__(self, statistics_service):
        """
        Initialize the statistics update observer.

        Args:
            statistics_service: The statistics service to use for updates.
        """
        self._statistics_service = statistics_service

    def supports_event(self, event_type: EventType) -> bool:
        """
        Only support student-related events.

        Args:
            event_type: The event type to check.

        Returns:
            bool: True if the event is student-related, False otherwise.
        """
        return event_type in [
            EventType.STUDENT_CREATED,
            EventType.STUDENT_UPDATED,
            EventType.STUDENT_DELETED,
            EventType.STUDENT_BULK_IMPORTED
        ]

    def on_event(self, event: Event) -> None:
        """
        Trigger statistics update on student events.

        Args:
            event: The student-related event.
        """
        logger.info(
            f"Triggering statistics update due to event: {event.event_type.value}"
        )
        try:
            # In a real implementation, this would call the statistics service
            # to recalculate statistics for the affected grade/gender
            self._statistics_service.schedule_update(event)
        except Exception as e:
            logger.error(f"Error scheduling statistics update: {e}")


# Global event manager instance
_event_manager = Subject()


def get_event_manager() -> Subject:
    """
    Get the global event manager instance.

    Returns:
        Subject: The global event manager.
    """
    return _event_manager


# Convenience decorator for emitting events
def emit_event(
    event_type: EventType,
    source: Optional[str] = None,
    data_extractor: Optional[Callable[..., Dict[str, Any]]] = None
):
    """
    Decorator to emit an event after a function call.

    Args:
        event_type: Type of event to emit.
        source: Source of the event.
        data_extractor: Optional function to extract event data from the result.

    Returns:
        Decorator function.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            event_data = {}
            if data_extractor:
                event_data = data_extractor(result, *args, **kwargs)

            get_event_manager().notify_event(
                event_type=event_type,
                data=event_data,
                source=source or func.__name__
            )

            return result
        return wrapper
    return decorator


# Initialize the logging observer by default
get_event_manager().add_observer(LoggingObserver())
