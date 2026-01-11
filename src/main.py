import asyncio
import utime # type: ignore
import sys

from pybuttons import Button
from ui import Menu, MenuBar, Timetable, Behaviour
import ui
from classcharts import ClassCharts
import clock
import wifi
import config
from config import VERBOSE_OUTPUT as v
from bootscreen import BootScreen

menu = Menu()
bar = MenuBar()
timetable = Timetable()
behaviour = Behaviour()
classcharts = ClassCharts()
bs = BootScreen()

cal_generated_today = False
sleeping = False
wifi_connected = False
fps = 30
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
                if v: print("Button A")
                if ui.page == "menu":
                    menu.exec() # Run the code associated with the button
                elif ui.page == "behaviour":
                    behaviour.toggle_time_range()
                    behaviour.draw()

            if btn.get_id() == BUTTON_B:
                if v: print("Button B")
                if ui.page != "menu": # Go to menu page
                    menu.go()
                elif ui.page == "menu": # Go to timetable page
                    timetable.go()

            if btn.get_id() == BUTTON_X:
                if v: print("Button X")
                if ui.page == "timetable": # Scroll events page up
                    timetable.scroll(direction="up")
                elif ui.page == "menu": # Highlight the button above
                    menu.scroll(direction="up")

            elif btn.get_id() == BUTTON_Y:
                if v: print("Button Y")
                if ui.page == "timetable":  # Scroll events page down
                    timetable.scroll(direction="down")
                elif ui.page == "menu": # Highlight the button below
                    menu.scroll(direction="down")

def device_to_sleep():
    # Turns off screen
    global sleeping
    sleeping = True
    ui.screen_off()

def device_wake_up():
    # Turns on screen
    global sleeping
    sleeping = False
    ui.screen_on()

async def monitor_buttons():
    # Watches for input on buttons
    while True:
        for btn in buttons:
            btn.read()
        await asyncio.sleep_ms(10) # 10ms poll time

async def update_menu_bar():
    while True:
        if ui.page != "menu" and not sleeping:
            bar.draw()
        await asyncio.sleep_ms(1000) # Refresh menu bar every sec

async def sleep_handler():
    # Puts screen to sleep after certain time has elapsed from last interaction
    global last_interaction_time, sleeping
    while True:
        time = utime.time()
        if time - config.SLEEP_TIME_SEC > last_interaction_time and sleeping == False:
            device_to_sleep()
        await asyncio.sleep_ms(display_update_time)
    
def init():
    global last_interaction_time
    # Startup sequence
    print("Starting...")
    bs.draw()
    wifi.wifi_connect()
    clock.set_time_ntp()
    classcharts.save_data()
    
    # Starts functions that need to be run asyncrously
    asyncio.create_task(update_menu_bar())
    asyncio.create_task(monitor_buttons())
    
    # Draw UI
    timetable.go()

    # Start monitoring time to sleep
    last_interaction_time = utime.time()
    asyncio.create_task(sleep_handler())

    print("Finished startup")

async def main():
    init()
    while True:
        # Refresh screen if awake
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

# Start main loop
try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Goodbye!")
    ui.cleanup()
    sys.exit()