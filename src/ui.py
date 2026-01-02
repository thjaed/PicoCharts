from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2, PEN_P4 # type: ignore
import ujson
import utime
import os
import battery
from clock import Clock

display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2, pen_type=PEN_P4)
brightness = 0.8

calendar = Clock()

# Colours
WHITE = display.create_pen(255, 255, 255)
GREY = display.create_pen(80, 80, 80)
DARK_GREY = display.create_pen(60, 60, 60)
BLACK = display.create_pen(0, 0, 0)
GREEN = display.create_pen(0, 255, 0)

def update():
    display.update()
    
def set_brightness(level):
    global brightness
    display.set_backlight(level)
    brightness = level

def screen_off():
    display.set_backlight(0)

def screen_on():
    display.set_backlight(brightness)
    
def setup():
    global page
    display.clear()
    display.set_font("bitmap6")
    display.set_backlight(brightness)
    page = "home"

class MenuBar:
    def draw(self):
        time_secs = utime.time()

        clock = calendar.get_clock(time_secs)
        date = calendar.get_date(time_secs)
        battery_level = battery.percentage()

        clock_width = display.measure_text(clock, scale=2)
        date_width = display.measure_text(date, scale=2)

        display.set_pen(GREY)
        display.rectangle(0, 0, 320, 15) # Top bar
        display.set_pen(WHITE)
        display.line(0, 14, 320, 14) # Line

        display.set_pen(WHITE)
        display.set_font("bitmap6")
        display.text(clock, 0, 0, scale=2) # Clock
        display.text(date, int((clock_width + (290 - clock_width) / 2) - (date_width / 2)), 0, scale=2) # Date

        # Battery Icon
        display.set_pen(WHITE)
        display.rectangle(290, 2, 25, 10) # White border
        display.rectangle(315, 4, 2, 6) # Notch
        display.set_pen(GREY)
        display.rectangle(292, 4, 21, 6) # Grey background
        if battery.charging():
            display.set_pen(GREEN) # Battery icon green if charging
        else:
            display.set_pen(WHITE)
        display.rectangle(293, 5, (round((battery_level / 100) * 19)), 4) # Charge level

class Home:
    def __init__(self):
        self.box_heights = []
        self.scroll_distance = 0
        self.content_height = 0
        
    def go(self):
        global page
        page = "home"
        display.set_pen(GREY)
        display.clear()
        self.scroll_distance = 0
        self.draw()
        bar.draw()
    
    def draw(self):
        display.set_pen(GREY)
        display.clear()
        
        cal_today_exists = "cal_today.jsonl" in os.listdir()
        
        if cal_today_exists:
            with open("cal_today.jsonl", "r") as f:
                valid_events = []
                for line in f:
                    try:
                        event = ujson.loads(line)
                        valid_events.append(event)
                    except ValueError:
                        pass  # Skip malformed lines
        
            if valid_events:
                self.content_height = 0
                self.box_heights = []

                for event in valid_events:
                    title=event.get("title")
                    #pretty_time=f"{calendar.get_clock(event.get('start'))} - {calendar.get_clock(event.get('end'))}"
                    pretty_time = event.get("start")
                    location=event.get("location")
                    attendees=event.get("attendees")

                    start_y = 15 + self.scroll_distance + self.content_height # Box start
                    line_y = start_y # Text start

                    box_height = 0

                    # Increase box height for every line of text
                    if title: box_height += 20
                    if pretty_time: box_height += 14
                    if location: box_height += 14
                    if attendees: box_height += 14

                    box_height += 2 # Padding
                    self.box_heights.append(box_height)

                    display.set_pen(GREY)
                    display.rectangle(0, start_y, 320, box_height) # Event box
                    display.set_pen(WHITE)
                    display.line(0, box_height + line_y - 1, 320, box_height + line_y - 1) # Bottom bar

                    # Text
                    display.set_pen(WHITE)
                    if title:
                        display.text(title, 5, line_y, scale=3)
                        line_y += 20
                    if pretty_time:
                        display.text(pretty_time, 5, line_y, scale=2)
                        line_y += 14
                    if location:
                        display.text(location, 5, line_y, scale=2)
                        line_y += 14
                    if attendees:
                        display.text(attendees, 5, line_y, scale=2)
                        line_y += 14

                    self.content_height += box_height
                    
            elif not cal_today_exists:
                message.show("No Calendar File!", change_page=False)
            elif cal_today_exists and not valid_events:
                message.show("No Events Today", change_page=False)
            
        bar.draw()
    
    def scroll(self, direction):
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

class Menu:
    def __init__(self):
        self.entries = ["Generate Calendar Day", "Say Hello World"]
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
        name = self.entries[self.selected]
        if name == "Generate Calendar Day":
            message.show("Please Wait")
            time = utime.time()
            calendar.gen_cal_day(time)
            calendar.remove_past_events()
        elif name == "Say Hello World":
            print("Hello World!")
            message.show("Hello World!")
            utime.sleep_ms(1000)
        home.go()

class Message:
    def __init__(self):
        self.text = ""
    
    def show(self, text, change_page=True):
        global page
        if change_page: page = "message"
        display.set_pen(GREY)
        display.clear()
        display.set_font("bitmap6")
        display.set_pen(WHITE)
        text_width = display.measure_text(text, scale=2)
        display.text(text, int((320 / 2) - (text_width / 2)), 108, scale=2)
        display.update()

message = Message()
home = Home()
bar = MenuBar()
menu = Menu()
