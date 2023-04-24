from pydantic import BaseModel, Field
from datetime import datetime
import pytz

from ..event.base import EventsManager, Event, EventType
from ..utils.parameters import DEFAULT_LOCATION_ID

def send_message(agent_input, events_manager: EventsManager):
    """Emits a message event to the Events table"""

    message = agent_input
    
    # TIMC - For testing purposes
    if input("Agent wants to send a message. Continue? (y/n) ") != "y":
        return

    # first, craft the event object
    event = Event(
        step=events_manager.current_step,
        timestamp=datetime.now(pytz.utc),
        type=EventType.MESSAGE,
        description=message,
        location_id=DEFAULT_LOCATION_ID, #TODO: make this dynamic
    )

    # now add it to the events manager
    events_manager.add_event(event)

    print("Message added to event manager at step " + str(events_manager.current_step) + ".")

    return "Message sent!"

