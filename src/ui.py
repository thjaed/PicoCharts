from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2, PEN_P4 # type: ignore
from pimoroni import RGBLED # type: ignore
import ujson # type: ignore
import utime # type: ignore
import os

#import battery
import config
import clock
from classcharts import ClassCharts
import wifi
import state

display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2, pen_type=PEN_P4)
led = RGBLED(6, 7, 8)
brightness = config.BRIGHTNESS

classcharts = ClassCharts()

# Colours
WHITE = display.create_pen(255, 255, 255)
GREY = display.create_pen(80, 80, 80)
DARK_GREY = display.create_pen(60, 60, 60)
BLACK = display.create_pen(0, 0, 0)
GREEN = display.create_pen(0, 255, 0)
RED = display.create_pen(255, 0, 0)

def setup():
    global page, display
    display.clear()
    led.set_rgb(0, 0, 0)
    display.set_font("bitmap6")
    display.set_backlight(config.BRIGHTNESS)
    page = "timetable"
    
def update():
    display.update()
    
def set_brightness(level):
    global brightness
    display.set_backlight(level)
    brightness = level
    print(f"Set brightness to {brightness}")

def screen_off():
    display.set_backlight(0)

def screen_on():
    display.set_backlight(brightness)

def cleanup():
    display.clear()
    display.set_backlight(0)
    led.set_rgb(0, 0, 0)

class BootScreen:
    def draw(self):
        display.set_pen(BLACK)
        display.clear()

        text_width = display.measure_text("PICOCHARTS", scale=4)

        display.set_pen(WHITE)
        display.text("PICOCHARTS", 160 -  text_width // 2, 50, scale=4)
        text_width = display.measure_text("by @thjaed", scale=2)
        display.text("by @thjaed", 160 -  text_width // 2, 80, scale=2)

        display.update()
    
    def print(self, text):
        print(text)
        # Clear text area
        display.set_pen(BLACK)
        display.rectangle(0, 190, 320, 50)

        # Write text
        display.set_pen(WHITE)
        text_width = display.measure_text(text, scale=2)
        display.text(text, 160 -  text_width // 2, 190, scale=2)

        display.update()

class MenuBar:
    def draw(self):
        display.set_font("bitmap6")
        display.set_pen(GREY)
        display.rectangle(0, 0, 320, 15) # Top bar
        display.set_pen(WHITE)
        display.line(0, 14, 320, 14) # Line

        if not state.WiFi.connected:
            # Draw offline indicator instead of date and time
            display.set_pen(RED)
            text_width = display.measure_text("OFFLINE: DATA OUT OF DATE", scale=2)
            display.text("OFFLINE: DATA OUT OF DATE", 160 - text_width // 2, 0, scale=2)
        else:
            time_secs = utime.time()

            time = clock.get_clock(time_secs)
            date = clock.get_date(time_secs)

            clock_width = display.measure_text(time, scale=2)
            date_width = display.measure_text(date, scale=2)

            display.set_pen(WHITE)
            display.text(time, 0, 0, scale=2) # Clock
            display.text(date, int((clock_width + (290 - clock_width) / 2) - (date_width / 2)), 0, scale=2) # Date

        # Battery Icon
        #battery_level = battery.percentage()
        #display.set_pen(WHITE)
        #display.rectangle(290, 2, 25, 10) # White border
        #display.rectangle(315, 4, 2, 6) # Notch
        #display.set_pen(GREY)
        #display.rectangle(292, 4, 21, 6) # Grey background
        #if battery.charging():
        #    display.set_pen(GREEN) # Battery icon green if charging
        #else:
        #    display.set_pen(WHITE)
        #display.rectangle(293, 5, (round((battery_level / 100) * 19)), 4) # Charge level

class Timetable:
    def __init__(self):
        self.box_heights = []
        self.scroll_distance = 0
        self.content_height = 0
        
    def go(self):
        global page
        page = "timetable"
        self.scroll_distance = 0
        self.draw()
        bar.draw()
    
    def draw(self):
        display.set_pen(GREY)
        display.clear()
        
        if "timetable.jsonl" not in os.listdir() and state.WiFi.connected:
            message.show("No timetable file, generating one", change_page=False)
            classcharts.save_timetable()
        elif "timetable.jsonl" not in os.listdir() and not state.WiFi.connected:
            message.show("Offline: No Timetable")
            return False
        
        with open("timetable.jsonl", "r") as f:
            self.content_height = 0
            self.box_heights = []
            
            lessons_to_display = False
            
            for l in f:
                l = ujson.loads(l) # load into json format

                if state.WiFi.connected:
                    lesson_in_future = clock.clock_str_to_secs(l.get("end_time")) > clock.clock_str_to_secs()
                else:
                    # Load all lessons if not connected to wifi (can't tell time)
                    lesson_in_future = True

                if lesson_in_future:
                    lessons_to_display = True
                    
                    subject = l.get("subject")
                    time = f"{l.get("start_time")} to {l.get("end_time")}"
                    room = l.get("room")
                    teacher = l.get("teacher")
                    
                    start_y = 15 + self.scroll_distance + self.content_height # Box start
                    line_y = start_y # Text start
                    
                    box_height = 0
                    # Increase box height for every line of text
                    if subject: box_height += 20
                    if time: box_height += 14
                    if room: box_height += 14
                    if teacher: box_height += 14
                    box_height += 2 # Padding
                    self.box_heights.append(box_height)
                    
                    display.set_pen(GREY)
                    display.rectangle(0, start_y, 320, box_height) # Event box
                    display.set_pen(WHITE)
                    display.line(0, box_height + line_y - 1, 320, box_height + line_y - 1) # Bottom bar
                    
                    # Text
                    display.set_pen(WHITE)
                    if subject:
                        display.text(subject, 5, line_y, scale=3)
                        line_y += 20
                    if time:
                        display.text(time, 5, line_y, scale=2)
                        line_y += 14
                    if room:
                        display.text(room, 5, line_y, scale=2)
                        line_y += 14
                    if teacher:
                        display.text(teacher, 5, line_y, scale=2)
                        line_y += 14
                        
                    self.content_height += box_height
                        
            if not lessons_to_display:
                message.show("No more lessons today!", change_page=False)
            
        bar.draw() # Draw menu bar on top
    
    def scroll(self, direction):
        # VIBECODED FUNCTION #
        visible_height = 225
        scroll_offset = -self.scroll_distance # Scroll distance
        curr_height = 0

        if self.content_height > 0:
            if direction == "down":
                for box_height in self.box_heights:
                    # Set the top and bottom of the box
                    box_top = curr_height
                    box_bottom = curr_height + box_height

                    if box_bottom > scroll_offset + visible_height: # If the bottom of the box is off screen
                        self.scroll_distance = -(box_bottom - visible_height) # Set the scroll distance to the difference between the bottom of the box and the bottom of the screen
                        self.draw()
                        return


                    curr_height += box_height # Move on to next box coords (y value)

            elif direction == "up":
                for index, box_height in enumerate(self.box_heights):
                    # Set top of box
                    box_top = curr_height

                    if box_top >= scroll_offset: # If the top of the box is off screen
                        if index > 0: # If this is not the first box
                            self.scroll_distance = -sum(self.box_heights[:index - 1]) # Scroll the distance of all the boxes after it
                        else:
                            # This is the first box so we scroll all the way to the top
                            self.scroll_distance = 0
                        self.draw()
                        return

                    curr_height += box_height # Move on to next box coords (y value)

class Behaviour:
    def __init__(self):
        self.time_ranges = ["august", "this_week", "last_week"]
        self.time_range = 0

    def go(self):
        global page
        page = "behaviour"
        self.draw()
    
    def toggle_time_range(self):
        if self.time_range < len(self.time_ranges) - 1:
            self.time_range += 1
        else:
            self.time_range = 0
    
    def draw(self):
        display.set_pen(GREY)
        display.clear()

        if "behaviour.jsonl" not in os.listdir() and state.WiFi.connected:
            message.show("No behaviour file, generating one", change_page=False)
            classcharts.save_behaviour()
        elif "behaviour.jsonl" not in os.listdir() and not state.WiFi.connected:
            message.show("Offline: No Behaviour")
            return False
        
        with open("behaviour.jsonl", "r") as f:
            for l in f:
                l = ujson.loads(l)
                if l.get("time") == self.time_ranges[self.time_range]:
                    positives = str(l.get("positive"))
                    negatives = f"-{str(l.get("negative"))}" if l.get("negative") > 0 else str(l.get("negative")) # add - sign in front of negative points
        
        
        display.set_pen(GREEN)
        display.rectangle(0, 0, 160, 240)
        
        display.set_pen(RED)
        display.rectangle(160, 0, 160, 240)

        display.set_pen(WHITE)

        text_width = display.measure_text("Positives", scale=2)
        display.text("Positives", (80 - int(text_width / 2)), 80, scale=2)
        text_width = display.measure_text(positives, scale=4)
        display.text(positives, (80 - int(text_width / 2)), 120, scale=4)

        text_width = display.measure_text("Negatives", scale=2)
        display.text("Negatives", 160 + (80 - int(text_width / 2)), 80, scale=2)
        text_width = display.measure_text(negatives, scale=4)
        display.text(negatives, 160 + (80 - int(text_width / 2)), 120, scale=4)

        if self.time_ranges[self.time_range] == "august":
            text = "Since August"
        elif self.time_ranges[self.time_range] == "this_week":
                text = "This Week"
        elif self.time_ranges[self.time_range] == "last_week":
                text = "Last Week"
        
        text_width = display.measure_text(text, scale=2)
        display.set_pen(WHITE)
        display.rectangle((160 - (text_width // 2)) - 5, 200 - 5, text_width + 10, 20)

        display.set_pen(BLACK)
        display.text(text, (160 - (text_width // 2)), 200 - 2, scale=2)

        bar.draw()
    
class Menu:
    def __init__(self):
        self.entries = ["Timetable", "Behaviour", "Refresh Data", "Connect to WiFi and Get Data"]
        self.selected = 0
        
    def go(self):
        global page
        page = "menu"
        display.set_pen(GREY)
        display.clear()
        self.draw()
        
    def draw(self):
        for index, name in enumerate(self.entries):
            menu_content_height = index * 30

            if index == self.selected:
                # White box to indicate selection
                display.set_pen(WHITE)
                display.rectangle(0, menu_content_height, 320, 32)
                display.set_pen(BLACK)
            else:
                display.set_pen(GREY)
                display.rectangle(0, menu_content_height, 320, 32)
                display.set_pen(WHITE)

            display.text(name, 5, menu_content_height + 8, scale=2)
    
    def scroll(self, direction):
        if direction == "up":
            if self.selected > 0:
                self.selected += -1
                self.draw()
        
        elif direction == "down":
            if self.selected < len(self.entries) - 1:
                self.selected += 1
                self.draw()
    
    def exec(self):
        # Executes code for selected entry
        name = self.entries[self.selected]

        if name == self.entries[0]:
            timetable.go()
        
        elif name == self.entries[1]:
            behaviour.go()
            
        elif name == self.entries[2]:
            if state.WiFi.connected:
                message.show("Getting data from ClassCharts")
                for text in classcharts.save_data():
                    message.show(text)
            else:
                message.show("OFFLINE")
                utime.sleep_ms(3000)

            timetable.go()
        
        elif name == self.entries[3]:
            for text in wifi.wifi_connect():
                message.show(text)
    
            if state.WiFi.connected:
                for text in clock.set_time_ntp():
                    message.show(text)
                for text in classcharts.save_data():
                    message.show(text)
            else:
                message.show("OFFLINE")
                utime.sleep_ms(3000)

            timetable.go()

class Message:
    def __init__(self):
        self.text = ""

    def show(self, text, change_page=True):
        global page
        if change_page: page = "message"
        
        display.set_pen(GREY)
        display.clear()
        
        # Measure width in order to put text in centre of screen
        text_width = display.measure_text(text, scale=2)
        
        print(text)
        display.set_font("bitmap6")
        display.set_pen(WHITE)
        display.text(text, int((320 / 2) - (text_width / 2)), 108, scale=2)
        
        display.update()

message = Message()
timetable = Timetable()
behaviour = Behaviour()
bar = MenuBar()
menu = Menu()
