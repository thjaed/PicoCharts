from machine import I2C, Pin # type: ignore
from LC709203F_CR import LC709203F

import state

def init():
    global sensor
    i2c = I2C(1,scl=Pin(27), sda=Pin(26))
    i2c.scan()
    sensor = LC709203F(i2c)
    state.Battery.connected = isinstance(sensor.cell_percent, float)
    return state.Battery.connected

def percentage():
    if isinstance(sensor.cell_percent, float):
        return round(sensor.cell_percent)
    else:
        state.Battery.connected = False
        return 0