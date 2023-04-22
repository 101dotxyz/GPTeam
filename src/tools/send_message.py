from pydantic import BaseModel, Field
from datetime import datetime
import pytz

from ..event.base import EventManager, Event, EventType
from ..utils.parameters import DEFAULT_LOCATION_ID

def send_message(agent_input, event_manager: EventManager):
    """Emits a message event to the Events table"""

    message = agent_input
    
    # TIMC - For testing purposes
    if input("Agent wants to send a message. Continue? (y/n) ") != "y":
        return

    # first, craft the event object
    event = Event(
        type=EventType.MESSAGE,
        description=message,
        location_id=DEFAULT_LOCATION_ID, #TODO: make this dynamic
        timestamp=datetime.now(pytz.utc)
    )

    # now add it to the events manager
    event_manager.add_event(event)

    print("Message added to event manager.")

    return "Message sent!"

