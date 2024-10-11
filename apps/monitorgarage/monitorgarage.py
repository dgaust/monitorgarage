import appdaemon.plugins.hass.hassapi as hass
from enum import Enum

class DoorState(Enum):
    Open = "Open"
    Closed = "Closed"
    Opening = "Opening"
    Closing = "Closing"
    Stopped = "Stopped"  # Represents a stopped state

class GarageMonitor(hass.Hass):
    def initialize(self):
        # Initialize states and parameters
        try:
            self.top_sensor = self.args.get('top_sensor')
            self.bottom_sensor = self.args.get('lower_sensor')
            self.toggle_button = self.args.get('toggle_switch')
            self.input_selector = self.args.get('input_select')
            self.current_state = DoorState.Closed
            self.next_state = DoorState.Open  # Initial next state when closed
            self.log(f"Bottom sensor is: {self.bottom_sensor} and Top sensor is: {self.top_sensor}")
            self.log(f"Garage monitor initialized. Current state: {self.current_state}")
            # Check the door state when loaded
            self.check_initial_state()
            # Listen for changes in sensors and button press
            self.listen_state(self.sensor_state_change, self.top_sensor)
            self.listen_state(self.sensor_state_change, self.bottom_sensor)
            self.listen_state(self.toggle_switch_listener, self.toggle_button)
            # Initial logging
            
        except Exception as e:
            # Log error if sensor settings retrieval fails
            self.queued_logger(f"Error getting sensor settings: {e}")

    def check_initial_state(self):
            # Check the sensor states at startup to determine the door's initial state
            top_state = self.get_state(self.top_sensor)
            bottom_state = self.get_state(self.bottom_sensor)
            # Door is CLOSED if Bottom State is OFF and Top State is OFF
            # Door is fully OPEN if Bottom state is ON and Top State is
            if top_state == "on" and bottom_state == "on":
                self.current_state = DoorState.Open
                self.next_state = DoorState.Closing
            elif top_state == "off" and bottom_state == "on":
                self.current_state = DoorState.Open
                self.next_state = DoorState.Closing
            elif top_state == "off" and bottom_state == "off":
                self.current_state = DoorState.Closed
                self.next_state = DoorState.Opening  # Default to opening if stopped
            self.set_cover_state(self.current_state)
            # Log the initial state detection
            self.log(f"Initial state check: Current state: {self.current_state}, Next state: {self.next_state}")

    def sensor_state_change(self, entity, attribute, old, new, cb_args):
        # Determine the current state based on sensors
        self.log(f"Sensor changed state: {entity}")
        self.top_state = self.get_state(self.top_sensor)
        self.bottom_state = self.get_state(self.bottom_sensor)
        self.log(f"Garage door sensor changed. Current state of lower: {self.bottom_state} and upper is: {self.top_state}")
        
        #Fully Closed
        if self.bottom_state == "off" and self.top_state == "off":
            self.current_state = DoorState.Closed
            self.next_state = DoorState.Opening 
            self.set_cover_state(self.current_state)          
        # Fully Open
        elif self.top_state == "on" and self.bottom_state == "on":
            self.current_state = DoorState.Open
            self.next_state = DoorState.Closing
            self.set_cover_state(self.current_state)
        # Fully Open and now closing
        elif self.top_state == "off" and self.lower_state == "on":
            self.current_state = DoorState.Closing
            self.next_state = DoorState.Closed
            self.set_cover_state(self.current_state)
        # Fully Closed and now opening
        elif self.top_state == "on" and self.lower_state == "off":
            self.current_state = DoorState.Opening
            self.next_state = DoorState.Open
            self.set_cover_state(self.current_state)

        
        
        # Log the state change

    def toggle_switch_listener(self, entity, attribute, old, new, kwargs):
        if new == "on":  # Button press detected
            if self.current_state in [DoorState.Open, DoorState.Closed]:
                # Fully open or closed, initiate opening or closing
                self.set_cover_state(self.next_state)
            elif self.current_state in [DoorState.Opening, DoorState.Closing]:
                # If opening or closing, stop the door
                self.current_state = DoorState.Open
                self.log("Stopping the door.")
                self.set_cover_state(self.current_state)
            elif self.current_state == DoorState.Open:
                # If stopped, reverse the direction
                self.set_cover_state(self.next_state)

    def set_cover_state(self, state):        
        self.log(f"Setting input select to: {state.value}")
        self.select_option(self.input_selector, state.value)
        if state == DoorState.Opening:
            self.current_state = DoorState.Opening
            self.next_state = DoorState.Closing
            self.log("Opening the garage door.")
        elif state == DoorState.Closing:
            self.current_state = DoorState.Closing
            self.next_state = DoorState.Opening
            self.log("Closing the garage door.")
