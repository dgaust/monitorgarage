import queue
from typing import List
import appdaemon.plugins.hass.hassapi as hass
import time
import json
from enum import Enum

# Both bottom and top are closed = fully closeed.
# Bottom goes to open, top is still closed = opening.
# Both bottom and top sensor are open = fully open.
# Top goes to closed, bottom is open = closing.

# ToDo include tilt sensor measures
# If opening > 20s without fully open, then suspect button pressed to stop and next press will be to close. Query tilt sensors to estimate percentage open
# If closing > 20s without fully closed, then suspect button pressed to stop and next press will be to open.  Query tilt sensors to estimate percentage open

class CoverMode(Enum):
    Open = 1
    Closed = 2
    Opening = 3
    Closing = 4

class monitorgarage(hass.Hass): 
    currentpostion = 0
    current_door_state = "closed"
    top_sensor_state = "off"
    bottom_sensor_state = "off"
    input_select = ""
    next_direction = ""

    def initialize(self):
        self.queuedlogger("Started monitoring the garage door")
        try:
            # Get the garage door and the top and bottom sensors
            self.garagedoor = self.args.get('door')        
            self.top_sensor = self.args.get('top_sensor')
            self.bottom_sensor = self.args.get('lower_sensor')
            self.input_select = self.args.get('input_select')
            self.toggle_switch = self.args.get('toggle_switch')
        except:
            self.queuedlogger("Error getting sensor settings.")
        finally:
            # Get the current state so we can setup correctly
            #self.current_door_state = self.get_state(self.garagedoor)

            # Calculate State based on sensor status 
            self.top_sensor_state = self.get_state(self.top_sensor)
            self.bottom_sensor_state = self.get_state(self.bottom_sensor)
            self.queuedlogger("Top State: " + self.top_sensor_state + " Bottom State: " + self.bottom_sensor_state)
            if (self.top_sensor_state == "off" and self.bottom_sensor_state == "off"):
                self.setcoverinputselect("Closed")
            elif (self.top_sensor_state == "unavalable" or self.bottom_sensor_state == "unavailable"):
                self.setcoverinputselect == "Open"
            else:
                self.setcoverinputselect == "Open"               
            
            # Setup listeners for the various states of monitoring entity
            self.listen_state(self.top_sensor_state_change, self.top_sensor)
            self.listen_state(self.bottom_sensor_state_change, self.bottom_sensor)
            self.listen_state(self.toggle_switch_listener, self.toggle_switch)

    def toggle_switch_listener(self, entity, attribute, old, new, kwargs):
        self.queuedlogger("Control switch toggled")
        
        self.current_door_state = self.get_state(self.input_select)
        
        # checks state to make sure the door is moving, which means it will stop in a partial open position
        if (new == 'on' and (self.current_door_state == "Closing" or self.current_door_state == 'Opening')):
            self.setcoverinputselect("Open")
        elif (new == 'on' and self.current_door_state == 'Open'):
            if self.next_direction == "Close":
                self.setcoverinputselect("Closing")
            elif self.next_direction == "Open":
                self.setcoverinputselect("Opening")

        # then if the set the next direction state
        if (new == 'on' and self.current_door_state == 'Opening'):
            self.next_direction = "Close"
        elif (new == 'on' and self.current_door_state == 'Closing'):
            self.next_direction = 'Open' 
        
        # ToDo set the right option here
        # if (new == 'on' and (self.current_door_state == "Closing" or self.current_door_state == 'Opening')):
        #    self.setcoverinputselect("Open")   

    def top_sensor_state_change(self, entity, attribute, old, new, kwargs):
        self.queuedlogger(entity +" changed to " + new)
        if (new == 'on'):
            self.setcoverposition(100)
            self.setcoverinputselect("Open")
        elif (new == 'off'):
            self.setcoverposition(75)
            self.setcoverinputselect("Closing")

    def bottom_sensor_state_change(self, entity, attribute, old, new, kwargs):
        self.queuedlogger(entity +" changed to " + new)
        if (new == 'off'):
            self.setcoverposition(0)
            self.setcoverinputselect("Closed")
        elif (new == 'on'):
            self.setcoverposition(25)
            self.setcoverinputselect("Opening")

    def setcoverposition(self, position):
        self.queuedlogger("Cover position set to: " + str(position))

    def setcoverinputselect(self, option):
        self.queuedlogger("Setting input select to: " + option)
        self.select_option(self.input_select, option)
        if (option == "Closing"):
            self.next_direction = "Open"
        elif (option == "Opening"):
            self.next_direction = "Close"

    # set up a proper logging queue
    def queuedlogger(self, message):
        self.log(message)  
