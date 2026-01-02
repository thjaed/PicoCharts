# This code is mostly from pimoroni
# https://github.com/pimoroni/pimoroni-pico/blob/main/micropython/examples/pimoroni_pico_lipo/battery_pico_display.py

from machine import ADC, Pin

vsys = ADC(Pin(29))                 # reads the system input voltage
power_connected = Pin(24, Pin.IN)   # reading GP24 tells us whether or not USB power is connected
conversion_factor = 3 * 3.3 / 65535

full_battery = 4.2                  # reference voltages for a full/empty battery, in volts
empty_battery = 2.8                 # the values could vary by battery size/manufacturer so you might need to adjust them

def percentage():
    # convert the raw ADC read into a voltage, and then a percentage
    voltage = vsys.read_u16() * conversion_factor
    percentage = round(100 * ((voltage - empty_battery) / (full_battery - empty_battery)))
    if percentage > 100:
        percentage = 100

    return percentage

def charging():
    if power_connected.value() == 1:
        return True
    else:
        return False