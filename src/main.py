import asyncio
import utime # type: ignore
import ujson # type: ignore
import os
from pybuttons import Button
from pimoroni import RGBLED # type: ignore
from ui import Menu, MenuBar, Home
import ui
import network # type: ignore
from time import sleep
from classcharts import ClassCharts
import machine # type: ignore
from clock import Clock
import usocket as socket
import ustruct as struct

## SETTINGS ##
TZ_OFFSET_SEC = 0
UNIX_TIMESTAMP = 1743581357
#UNIX_TIMESTAMP = 0
sleep_time = 20
fps = 30
WIFI_SSID = "Mars Guest"
WIFI_PASS = "2299synwk6xk"
CC_CODE = "HAM5PJFGHV"
CC_DOB = "2010-05-05"

def set_time(timestamp=0):
    global rtc
    rtc = machine.RTC()
    if timestamp:
        t = utime.localtime(timestamp)
        rtc.datetime((t[0], t[1], t[2], t[6]+1, t[3], t[4], t[5], 0))
    else:
        NTP_HOST = "pool.ntp.org"
        NTP_DELTA = 2208988800
        NTP_QUERY = bytearray(48)
        NTP_QUERY[0] = 0x1B
        addr = socket.getaddrinfo(NTP_HOST, 123)[0][-1]
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.settimeout(1)
            res = s.sendto(NTP_QUERY, addr)
            msg = s.recv(48)
        finally:
            s.close()
        ntp_time = struct.unpack("!I", msg[40:44])[0]
        
        t = utime.gmtime(ntp_time - NTP_DELTA + TZ_OFFSET_SEC)
        rtc.datetime((t[0], t[1], t[2], t[6] + 1, t[3], t[4], t[5], 0))

menu = Menu()
bar = MenuBar()
home = Home()
clock = Clock()
classcharts = ClassCharts()

cal_generated_today = False
sleeping = False
last_interaction_time = utime.time()
wifi_connected = False
display_update_time = int((1/fps) * 1000) # Calculates time to sleep in ms
ui.setup()

def press_handler(btn, pattern):
    global last_interaction_time, sleeping
    last_interaction_time = utime.time()
    if sleeping:
        device_wake_up()
    else:
        if pattern == Button.SINGLE_PRESS:
            if btn.get_id() == BUTTON_A:
                if ui.page == "menu":
                    menu.exec() # Run the code associated with the button

            if btn.get_id() == BUTTON_B:
                if ui.page == "home": # Go to menu page
                    menu.go()
                elif ui.page == "menu": # Go to home page
                    home.go()

            if btn.get_id() == BUTTON_X:
                if ui.page == "home": # Scroll events page up
                    home.scroll(direction="up")
                elif ui.page == "menu": # Highlight the button above
                    menu.scroll(direction="up")

            elif btn.get_id() == BUTTON_Y:
                if ui.page == "home":  # Scroll events page down
                    home.scroll(direction="down")
                elif ui.page == "menu": # Highlight the button below
                    menu.scroll(direction="down")
                    
def wifi_connect():
    global wifi_connected
    # Init Wi-Fi Interface
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    # Connect to your network
    wlan.connect(WIFI_SSID, WIFI_PASS)

    # Wait for Wi-Fi connection
    connection_timeout = 10
    while connection_timeout > 0:
        if wlan.status() >= 3:
            break
        connection_timeout -= 1
        print('Waiting for Wi-Fi connection...')
        sleep(1)

    # Check if connection is successful
    if wlan.status() != 3:
        raise RuntimeError('Failed to establish a network connection')
    else:
        wifi_connected = True
        print('Connection successful!')
        network_info = wlan.ifconfig()
        print('IP address:', network_info[0])


def device_to_sleep():
    global sleeping
    sleeping = True
    ui.screen_off()

def device_wake_up():
    global sleeping
    sleeping = False
    ui.screen_on()

async def monitor_buttons():
    while True:
        for btn in buttons:
            btn.read()
        await asyncio.sleep_ms(10) # 10ms poll time

async def update_menu_bar():
    while True:
        if ui.page == "home" and not sleeping:
            bar.draw()
        await asyncio.sleep_ms(1000) # Refresh menu bar every sec

async def sleep_handler():
    global last_interaction_time, sleeping
    while True:
        time = utime.time()
        if time - sleep_time > last_interaction_time:
            device_to_sleep()
        await asyncio.sleep_ms(display_update_time)
    
def init():
    print("Starting...")
    print("Connecting to internet")
    wifi_connect()
    print("Setting Time")
    set_time(UNIX_TIMESTAMP)
    print("Connecting to classcharts")
    classcharts.login()
    print("Getting lessons")
    classcharts.save_timetable(clock.get_date_classcharts(utime.time()))
    print("Done!")
    home.go()
    
async def main():
    init()
    asyncio.create_task(update_menu_bar())
    asyncio.create_task(monitor_buttons())
    asyncio.create_task(sleep_handler())
    
    while True:
        if not sleeping:
            ui.update()
        await asyncio.sleep_ms(display_update_time)

# Button setup
PINS = [12, 13, 14, 15]
BUTTON_A = 12
BUTTON_B = 13
BUTTON_X = 14
BUTTON_Y = 15

buttons = []
for pin in PINS:
    btn = Button(Button.MODE_DIGITAL, pin)
    btn.on_press(press_handler) \
       .on_press_for(press_handler, 700)  # 700ms = long press
    buttons.append(btn)
    
led = RGBLED(6, 7, 8)
led.set_rgb(0, 0, 0)

asyncio.run(main())
