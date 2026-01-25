from machine import I2C, Pin # type: ignore
from LC709203F_CR import LC709203F

i2c = I2C(1,scl=Pin(27), sda=Pin(26)) # GP0=SDA GP1=SCL
sensor = LC709203F(i2c)

def percentage():
    return round(sensor.cell_percent)