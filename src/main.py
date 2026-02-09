import asyncio
import utime # type: ignore
import sys

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
timetable_change_date = ui.timetable_chage_date
menu = ui.Menu()
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
            led.update("updating_data", True)
            for text in wifi.wifi_connect():
                message.show(text)
    
            if state.WiFi.connected:
                for text in clock.set_time_ntp():
                    message.show(text)
                get_data(print_type="message", background=False)
            else:
                message.show("OFFLINE")
                utime.sleep(1)

            led.update("updating_data", False)
            timetable.go()
        
def device_to_sleep():
    # Turns off screen
    state.UI.sleeping = True
    ui.screen_off()

def device_wake_up():
    # Turns on screen
    if state.UI.reset_page_after_sleep:
        timetable.go()
    state.UI.reset_page_after_sleep = False
    state.UI.sleeping = False
    ui.screen_on()

def get_data(print_type, background):
    if wifi.test_connection() and ((state.UI.sleeping and background) or (not background)):
        led.update("updating_data", True)

        for text in classcharts.save_data():
            if print_type == "console": print(text)
            elif print_type == "message": message.show(text)
            elif print_type == "boot": bootscreen.print(text)

        led.update("updating_data", False)

        # Turn LED on if there are unseen hw tasks
        led.update("unseen_homework", len(state.Homework.unseen_ids) > 0)

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
        if state.UI.sleeping and time - config.SLEEP_TIME_SEC - 600 > state.UI.last_interaction_time:
            state.UI.reset_page_after_sleep = True
        if not state.UI.sleeping and time - config.SLEEP_TIME_SEC > state.UI.last_interaction_time:
            device_to_sleep()
        await asyncio.sleep(1)

async def update_data():
    await asyncio.sleep(1200)
    # Periodically updates data
    while True:
        get_data(print_type="console", background=True)
        await asyncio.sleep(1200)

async def connection_tester():
    # Periodically check for wifi connectivity
    while True:
        if not wifi.test_connection() and state.UI.sleeping:
            # attempt to connect if there is no connection
            led.update("wifi_connecting", True)
            wifi.wifi_connect()
            led.update("wifi_connecting", False)

        await asyncio.sleep(30)
    
def init():
    # Startup sequence
    led.update("booting", True)
    bootscreen.draw()
    bootscreen.print("Initialising Battery")
    battery.init()
    for text in wifi.wifi_connect():
        bootscreen.print(text)
    if state.WiFi.connected:
        for text in clock.set_time_ntp():
            bootscreen.print(text)
        get_data(print_type="boot", background=False)
    
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
    led.update("booting", False)

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