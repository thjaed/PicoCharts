import asyncio
import utime # type: ignore
import sys
import os
import ujson # type: ignore

from pybuttons import Button
from classcharts import ClassCharts
import ui
import clock
import wifi
import config
import state
import battery

classcharts = ClassCharts()
message = ui.message
bar = ui.bar
led = ui.led
hwviewer = ui.hwviewer
timetable = ui.timetable
menu = ui.Menu()
timetable_change_date = ui.timetable_chage_date
behaviour = ui.Behaviour()
attendance = ui.Attendence()
homework = ui.Homework()
bootscreen = ui.BootScreen()

fps = 30
display_update_time = int((1/fps) * 1000) # Calculates time to sleep in ms
ui.setup()

def press_handler(btn, pattern):
    state.UI.last_interaction_time = utime.time()
    if state.UI.sleeping:
        device_wake_up()
    else:
        if pattern == Button.SINGLE_PRESS:
            if btn.get_id() == BUTTON_A:
                if ui.page == "menu":
                    menu_exec() # Run the code associated with the button
                elif ui.page == "behaviour":
                    behaviour.toggle_time_range()
                    behaviour.draw()
                elif ui.page == "attendance":
                    attendance.toggle_time_range()
                    attendance.draw()
                elif ui.page == "homework":
                    homework.select()
                elif ui.page == "timetable":
                    timetable_change_date.go()
                elif ui.page == "timetable_change_date":
                    timetable_change_date.select()

            if btn.get_id() == BUTTON_B:
                if ui.page == "homework_viewer":
                    homework.go()
                elif ui.page == "menu": # Go to timetable page
                    timetable.go()
                elif ui.page == "timetable_change_date":
                    timetable.go()
                elif ui.page != "menu": # Go to menu page
                    menu.go()

            if btn.get_id() == BUTTON_X:
                if ui.page == "timetable": # Scroll events page up
                    timetable.scroll(direction="up")
                elif ui.page == "homework":
                    homework.scroll(direction="up")
                elif ui.page == "homework_viewer":
                    hwviewer.scroll(direction="up")
                elif ui.page == "menu": # Highlight the button above
                    menu.scroll(direction="up")
                elif ui.page == "timetable_change_date":
                    timetable_change_date.change_date(direction="forward")

            elif btn.get_id() == BUTTON_Y:
                if ui.page == "timetable":  # Scroll events page down
                    timetable.scroll(direction="down")
                elif ui.page == "homework":
                    homework.scroll(direction="down")
                elif ui.page == "homework_viewer":
                    hwviewer.scroll(direction="down")
                elif ui.page == "menu": # Highlight the button below
                    menu.scroll(direction="down")
                elif ui.page == "timetable_change_date":
                    timetable_change_date.change_date(direction="back")

def menu_exec():
        # Executes code for selected entry
        name = menu.entries[menu.selected]

        if name == "Timetable":
            timetable.go()
        
        elif name == "Behaviour":
            behaviour.go()
        
        elif name == "Attendance":
            attendance.go()
        
        elif name == "Homework":
            homework.go()        
        
        elif name == "Connect and Refresh Data":
            for text in wifi.wifi_connect():
                message.show(text)
    
            if state.WiFi.connected:
                for text in clock.set_time_ntp():
                    message.show(text)
                for text in classcharts.save_data():
                    message.show(text)
            else:
                message.show("OFFLINE")
                utime.sleep(1)

            timetable.go()

def device_to_sleep():
    # Turns off screen
    state.UI.sleeping = True
    ui.screen_off()

def device_wake_up():
    # Turns on screen
    state.UI.sleeping = False
    timetable.go()
    ui.screen_on()

async def monitor_buttons():
    # Watches for input on buttons
    while True:
        for btn in buttons:
            btn.read()
        await asyncio.sleep_ms(10) # 10ms poll time

async def update_menu_bar():
    while True:
        if (ui.page != "menu" and
            ui.page != "timetable_change_date" and
            not state.UI.sleeping
            ):
            bar.draw()
        await asyncio.sleep_ms(1000) # Refresh menu bar every sec

async def sleep_handler():
    # Puts screen to sleep after certain time has elapsed from last interaction
    while True:
        time = utime.time()
        if time - config.SLEEP_TIME_SEC > state.UI.last_interaction_time and state.UI.sleeping == False:
            device_to_sleep()
        await asyncio.sleep_ms(display_update_time)

async def update_data():
    await asyncio.sleep(1200)
    # Periodically updates data
    while True:
        if wifi.test_connection() and state.UI.sleeping:
            led.updating()
            for text in classcharts.save_data():
                print(text)
            led.off()

            # Turn LED on if there are unseen hw tasks
            if len(state.Homework.unseen_ids) > 0:
                led.notify()
            else:
                led.off()
        
        await asyncio.sleep(1200)

async def connection_tester():
    # Periodically check for wifi connectivity
    while True:
        wifi.test_connection()
        await asyncio.sleep(30)
    
def init():
    # Startup sequence
    bootscreen.draw()
    bootscreen.print("Initialising Battery")
    battery.init()
    for text in wifi.wifi_connect():
        bootscreen.print(text)
    if state.WiFi.connected:
        for text in clock.set_time_ntp():
            bootscreen.print(text)
        for text in classcharts.save_data():
            bootscreen.print(text)
    
    # Starts functions that need to be run asyncrously
    asyncio.create_task(monitor_buttons())
    asyncio.create_task(update_menu_bar())
    if not config.FORCE_OFFLINE:
        asyncio.create_task(connection_tester())
        asyncio.create_task(update_data())

    # Start monitoring time to sleep
    state.UI.last_interaction_time = utime.time()
    asyncio.create_task(sleep_handler())
    
    # Draw UI
    timetable.go()

    print("Finished startup")

async def main():
    init()
    while True:
        # Refresh screen if awake
        if not state.UI.sleeping:
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