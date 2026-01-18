from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2, PEN_P4 # type: ignore
from pimoroni import RGBLED # type: ignore
import ujson # type: ignore
import os
import utime # type: ignore

#import battery
import config
import clock
import state
from classcharts import ClassCharts

display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2, pen_type=PEN_P4)
brightness = config.BRIGHTNESS

classcharts = ClassCharts()

# Colours
WHITE = display.create_pen(255, 255, 255)
GREY = display.create_pen(80, 80, 80)
DARK_GREY = display.create_pen(60, 60, 60)
BLACK = display.create_pen(0, 0, 0)
GREEN = display.create_pen(0, 255, 0)
RED = display.create_pen(255, 0, 0)
YELLOW = display.create_pen(255, 255, 0)
BLUE = display.create_pen(0, 0, 255)

def setup():
    global page, display
    display.clear()
    led.off()
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
    led.off()

def measure_wrapped_text(text, wrap_px, char_width, line_height):
    # VIBECODED FUNCTION #
    chars_per_line = wrap_px // char_width
    lines = 0

    for paragraph in text.split("\n"):
        if not paragraph:
            lines += 1
            continue
        lines += (len(paragraph) + chars_per_line - 1) // chars_per_line

    return lines * line_height

class LED:
    def __init__(self):
        self.led = RGBLED(6, 7, 8)
        self.off()
    
    def off(self):
        self.led.set_rgb(0, 0, 0)
    
    def notify(self):
        self.led.set_rgb(0, 0, 10)

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
            time = clock.get_clock()
            date = clock.get_date()

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
        self.data = []
        self.box_heights = []
        self.scroll_distance = 0
        self.content_height = 0
        
    def go(self):
        global page
        page = "timetable"
        self.scroll_distance = 0

        # Load data from file into self.data
        self.data = []
        if "timetable.jsonl" in os.listdir():
            with open("timetable.jsonl", "r") as f:
                for l in f:
                    l = ujson.loads(l)
                    if (state.WiFi.connected and l.get("end_time_secs") > utime.time()) or (not state.WiFi.connected):
                        self.data.append({
                            "subject": l.get("subject"),
                            "time": l.get("time"),
                            "room": l.get("room"),
                            "teacher": l.get("teacher")
                        })
        else:
            message.show("No timetable file!", change_page=False)
            return False
                
        self.draw()
        bar.draw()
    
    def draw(self):
        display.set_pen(GREY)
        display.clear()
              
        if len(self.data) > 0:
            self.content_height = 0
            self.box_heights = []

            for l in self.data:
                subject = l["subject"]
                time = l["time"]
                room = l["room"]
                teacher = l["teacher"]

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
                        
        else:
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
        self.data = []
        self.time_ranges = ["august", "this_week", "last_week"]
        self.time_range = 0

    def go(self):
        global page
        page = "behaviour"

        # Load data from file into self.data
        self.data = []
        if "behaviour.jsonl" in os.listdir():
            with open("behaviour.jsonl", "r") as f:
                for l in f:
                    l = ujson.loads(l)
                    self.data.append({
                        "time": l.get("time"),
                        "positive": l.get("positive"),
                        "negative": l.get("negative")
                    })
        else:
            message.show("No behaviour file!", change_page=False)
            return False
        
        self.draw()
    
    def toggle_time_range(self):
        if self.time_range < len(self.time_ranges) - 1:
            self.time_range += 1
        else:
            self.time_range = 0
    
    def draw(self):
        display.set_pen(GREY)
        display.clear()
        
        positives = self.data[self.time_range]["positive"]
        negatives = self.data[self.time_range]["negative"]

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

class Attendence:
    def __init__(self):
        self.data = []
        self.time_ranges = ["august", "this_week", "last_week"]
        self.time_range = 0

    def go(self):
        global page
        page = "attendance"

        # Load data from file into self.data
        self.data = []
        if "attendance.jsonl" in os.listdir():
            with open("attendance.jsonl", "r") as f:
                for l in f:
                    l = ujson.loads(l)
                    self.data.append({
                        "time": l.get("time"),
                        "percentage": l.get("percentage")
                    })
        else:
            message.show("No attendance file!", change_page=False)
            return False
        
        self.draw()
    
    def toggle_time_range(self):
        if self.time_range < len(self.time_ranges) - 1:
            self.time_range += 1
        else:
            self.time_range = 0
    
    def draw(self):
        display.set_pen(GREY)
        display.clear()
        
        percentage = self.data[self.time_range]["percentage"]
        
        if percentage > 95:
            display.set_pen(GREEN)
        elif percentage > 85:
            display.set_pen(YELLOW)
        else:
            display.set_pen(RED)
        
        percentage = f"{percentage}%"

        display.rectangle(0, 0, 320, 240)
    
        display.set_pen(WHITE)

        text_width = display.measure_text(percentage, scale=5)
        display.text(percentage, 160 - text_width // 2, 100, scale=5)

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

class Homework:
    def __init__(self):
        self.data = []
        self.box_heights = []
        self.scroll_distance = 0
        self.content_height = 0
        self.selected = 0
        
    def go(self):
        global page
        page = "homework"

        # Load data from file into self.data
        self.data = []
        if "homework.jsonl" in os.listdir():
            with open("homework.jsonl", "r") as f:
                for l in f:
                    l = ujson.loads(l)
                    self.data.append({
                        "title": l.get("title"),
                        "teacher": l.get("teacher"),
                        "subject": l.get("subject"),
                        "due_date_str": l.get("due_date_str"),
                        "issue_date_str": l.get("issue_date_str"),
                        "seen": l.get("seen"),
                        "completed": l.get("completed"),
                        "late": l.get("late"),
                        "description": l.get("description")
                    })
        else:
            message.show("No homework file!", change_page=False)
            return False
        
        self.draw()
        bar.draw()
    
    def draw(self):
        display.set_pen(GREY)
        display.clear()
        
        self.content_height = 0
        self.box_heights = []
        unseen_hw = False
            
        if len(self.data) > 0:
            for index, l in enumerate(self.data):
                selected = self.selected == index
    
                title = l["title"]
                teacher = l["teacher"]
                subject = l["subject"]
                due_date_str = l["due_date_str"]
                late = l["late"]
                completed = l["completed"]

                if l["seen"] == False:
                    unseen_hw = True

                start_y = 15 + self.scroll_distance + self.content_height # Box start
                line_y = start_y + 5 # Text start

                box_height = 0
                # Increase box height for every line of text
                if title: box_height += measure_wrapped_text(title, 300, 12, 14) + 5
                if subject: box_height += 14
                if due_date_str: box_height += 14
                box_height += 5 # Padding

                if selected:
                    display.set_pen(WHITE)
                    display.rectangle(0, line_y - 5, 320, box_height + 5)
                else:
                    display.set_pen(GREY)
                    display.rectangle(0, line_y - 5, 320, box_height + 5)

                # Text
                if selected:
                    display.set_pen(BLACK)
                else:
                    display.set_pen(WHITE)

                display.line(0, box_height + line_y - 1, 320, box_height + line_y - 1) # Bottom bar

                if title:
                    display.text(title, 5, line_y, wordwrap=300, scale=2)
                    line_y += measure_wrapped_text(title, 300, 12, 14) + 5

                if subject:
                    display.text(f"{teacher} | {subject}", 5, line_y, scale=2)
                    line_y += 14

                if due_date_str:
                    if late:
                        # Set text to red if task is late
                        display.set_pen(RED)
                    else:
                        display.set_pen(GREEN)

                    display.text(f"Due on {due_date_str}", 5, line_y, scale=2)
                    line_y += 14

                box_height += 5
                self.box_heights.append(box_height)

                self.content_height += box_height

            if unseen_hw:
                led.off()
        else:
            message.show("All homework completed!", change_page=False)
        
        bar.draw() # Draw menu bar on top
    
    def select(self):
            hwviewer.go(self.data[self.selected])
    
    def scroll(self, direction):
        # BASED ON VIBECODED FUNCTION #
        visible_height = 225
        scroll_offset = -self.scroll_distance # Scroll distance
        curr_height = 0

        if self.content_height > 0:
            if direction == "up":
                if self.selected > 0:
                    self.selected -= 1

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

            elif direction == "down":
                if self.selected < len(self.data) - 1:
                    self.selected += 1

                for index, box_height in enumerate(self.box_heights):
                    # Set the top and bottom of the box
                    box_top = curr_height
                    box_bottom = curr_height + box_height

                    if (box_bottom > scroll_offset + visible_height) and (self.selected == index): # if selected box is off page
                        self.scroll_distance = -(box_bottom - visible_height) # scroll to the bottom of this box
                        self.draw()
                        return

                    curr_height += box_height # Move on to next box coords (y value)
                
            self.draw()

class HomeworkViewer:
    def __init__(self):
        self.desc_start_offset = 0
        self.data = {}

    def go(self, data):
        global page
        page = "homework_viewer"
        self.desc_start_offset = 0
        self.data = data
        self.draw()
        bar.draw()
    
    def draw(self):
        global header_end, description
        display.set_pen(GREY)
        display.clear()

        title = self.data["title"]
        teacher = self.data["teacher"]
        subject = self.data["subject"]
        due_date_str = self.data["due_date_str"]
        late = self.data["late"]
        description = self.data["description"]
        
        line_y = 20 # Text start
        header_end = 10 + 33 + measure_wrapped_text(title, 300, 12, 14) + 15

        desc_start = self.desc_start_offset + header_end + 5

        display.set_pen(WHITE)
        display.text(description, 5, desc_start, wordwrap=300, scale=2)

        # Draw header over description
        display.set_pen(GREY)
        display.rectangle(0, 0, 320, header_end)

        # Text
        display.set_pen(WHITE)
        display.text(title, 5, line_y, wordwrap=300, scale=2)
        line_y += measure_wrapped_text(title, 300, 12, 14) + 5

        display.text(f"{teacher} | {subject}", 5, line_y, scale=2)
        line_y += 14

        if late:
            # Set text to red if task is late
            display.set_pen(RED)
        else:
            display.set_pen(GREEN)

        display.text(f"Due on {due_date_str}", 5, line_y, scale=2)
        line_y += 14

        display.set_pen(WHITE)
        
        line_y += 5
        display.line(0, header_end, 320, header_end) # Bottom bar
        line_y += 10

        bar.draw()

    def scroll(self, direction):
        visible_area = 240 - header_end
        if direction == "down":
            if (measure_wrapped_text(description, 300, 12, 14) + self.desc_start_offset + 5) > visible_area:
                self.desc_start_offset -= 14

        elif direction == "up":
            if self.desc_start_offset < 0:
                self.desc_start_offset += 14  

        self.draw()

class Menu:
    def __init__(self):
        self.entries = ["Timetable", "Behaviour", "Attendance", "Homework", "Connect and Refresh Data"]
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
        display.set_pen(WHITE)
        display.text(text, int((320 / 2) - (text_width / 2)), 108, scale=2)
        
        display.update()

led = LED()
message = Message()
hwviewer = HomeworkViewer()
bar = MenuBar()