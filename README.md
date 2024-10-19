# monitorgarage

Template Covere example

```
- platform: template
  covers:
    garage_door:
      friendly_name: Garage Door
      unique_id: itsagaragedoor1234
      device_class: garage
      value_template: >
        {{ states('input_select.garagedoorhelper') }}
      open_cover:
        service: switch.turn_on
        entity_id: switch.garage_door_implant_5
      close_cover:
        service: switch.turn_on
        entity_id: switch.garage_door_implant_5
      stop_cover:
        service: switch.turn_on
        entity_id: switch.garage_door_implant_5
```

Example apps.yaml usage

```
monitorgarage:
  module: monitorgarage
  class: GarageMonitor
  door: cover.garage_door
  lower_sensor: binary_sensor.garage_door_bottom_sensor_window_door_is_open
  top_sensor: binary_sensor.garage_door_sensor_window_door_is_open
  input_select: input_select.garagedoorhelper
  toggle_switch: switch.garage_door_implant_5
```
