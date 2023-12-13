import appdaemon.plugins.hass.hassapi as hass
from enum import Enum

class CoverMode(Enum):
    Open = 1
    Closed = 2
    Opening = 3
    Closing = 4

class MonitorGarage(hass.Hass):
    current_position = 0
    current_door_state = CoverMode.Closed
    top_sensor_state = "off"
    bottom_sensor_state = "off"
    input_select = ""
    next_direction = ""

    def initialize(self):
        # Log initialization
        self.queued_logger("Started monitoring the garage door")
        
        try:
            # Get the garage door and the top and bottom sensors
            self.garage_door = self.args.get('door')
            self.top_sensor = self.args.get('top_sensor')
            self.bottom_sensor = self.args.get('lower_sensor')
            self.input_select = self.args.get('input_select')
            self.toggle_switch = self.args.get('toggle_switch')
        except Exception as e:
            # Log error if sensor settings retrieval fails
            self.queued_logger(f"Error getting sensor settings: {e}")
        finally:
            # Get the current state so we can set up correctly
            self.top_sensor_state = self.get_state(self.top_sensor)
            self.bottom_sensor_state = self.get_state(self.bottom_sensor)
            self.queued_logger(f"Top State: {self.top_sensor_state} Bottom State: {self.bottom_sensor_state}")

            # Set initial state based on sensor status
            if self.top_sensor_state == "off" and self.bottom_sensor_state == "off":
                self.set_cover_input_select(CoverMode.Closed)
            elif self.top_sensor_state == "unavailable" or self.bottom_sensor_state == "unavailable":
                self.set_cover_input_select(CoverMode.Open)
            else:
                self.set_cover_input_select(CoverMode.Open)

            # Setup listeners for the various states of monitoring entity
            self.listen_state(self.top_sensor_state_change, self.top_sensor)
            self.listen_state(self.bottom_sensor_state_change, self.bottom_sensor)
            self.listen_state(self.toggle_switch_listener, self.toggle_switch)

    def toggle_switch_listener(self, entity, attribute, old, new, kwargs):
        # Log when the control switch is toggled
        self.queued_logger("Control switch toggled")
        self.current_door_state = self.get_state(self.input_select)

        # Check state to determine if the door is moving and stop in a partial open position
        if new == 'on' and (self.current_door_state == CoverMode.Closing or self.current_door_state == CoverMode.Opening):
            self.set_cover_input_select(CoverMode.Open)
        elif new == 'on' and self.current_door_state == CoverMode.Open:
            # Set the next direction based on the previous state
            if self.next_direction == "Close":
                self.set_cover_input_select(CoverMode.Closing)
            elif self.next_direction == "Open":
                self.set_cover_input_select(CoverMode.Opening)

        # Set the next direction state
        if new == 'on' and self.current_door_state == CoverMode.Opening:
            self.next_direction = "Close"
        elif new == 'on' and self.current_door_state == CoverMode.Closing:
            self.next_direction = 'Open'

    def top_sensor_state_change(self, entity, attribute, old, new, kwargs):
        # Log when the top sensor state changes
        self.queued_logger(f"{entity} changed to {new}")
        if new == 'on':
            self.set_cover_position(100)
            self.set_cover_input_select(CoverMode.Open)
        elif new == 'off':
            self.set_cover_position(75)
            self.set_cover_input_select(CoverMode.Closing)

    def bottom_sensor_state_change(self, entity, attribute, old, new, kwargs):
        # Log when the bottom sensor state changes
        self.queued_logger(f"{entity} changed to {new}")
        if new == 'off':
            self.set_cover_position(0)
            self.set_cover_input_select(CoverMode.Closed)
        elif new == 'on':
            self.set_cover_position(25)
            self.set_cover_input_select(CoverMode.Opening)

    def set_cover_position(self, position):
        # Log when the cover position is set
        self.queued_logger(f"Cover position set to: {position}")

    def set_cover_input_select(self, option):
        # Log when the input select is set
        self.queued_logger(f"Setting input select to: {option.name}")
        self.select_option(self.input_select, option.name)
        
        # Set the next direction based on the chosen option
        if option == CoverMode.Closing:
            self.next_direction = "Open"
        elif option == CoverMode.Opening:
            self.next_direction = "Close"

    def queued_logger(self, message):
        # Log messages with proper queue handling
        self.log(message)
