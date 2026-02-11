from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2, PEN_P4 # type: ignore
from pimoroni import RGBLED # type: ignore
import ujson # type: ignore
import os
import utime # type: ignore

import battery
import config
import clock
import state
from classcharts import ClassCharts
import wifi

display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2, pen_type=PEN_P4)

classcharts = ClassCharts()

WIDTH, HEIGHT = display.get_bounds()

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
    
def update():
    display.update()
    
def screen_off():
    display.set_backlight(0)

def screen_on():
    display.set_backlight(config.BRIGHTNESS)

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

def truncate_text(text, max_px, char_width):
    text_width = 0
    trunc_str = ""

    for c in text:
        if text_width + char_width > max_px:
            break
        else:
            text_width += char_width
            trunc_str += c

    trunc_str = trunc_str.strip()

    if len(trunc_str) < len(text):
        trunc_str += "..."

    return trunc_str

class LED:
    def __init__(self):
        self.led = RGBLED(6, 7, 8)
        self.status = {
            "updating_data": False,
            "wifi_connecting": False,
            "unseen_homework": False,
            "booting": False
        }
        self.off()
    
    def update(self, reason, b):
        self.status[reason] = b
        
        if (self.status["updating_data"] or
            self.status["wifi_connecting"] or
            self.status["booting"]):
            self.dim_red()
        elif self.status["unseen_homework"]:
            self.dim_blue()
        else:
            self.off()
    
    def off(self):
        self.led.set_rgb(0, 0, 0)
    
    def dim_blue(self):
        self.led.set_rgb(0, 0, 1)
    
    def dim_red(self):
        self.led.set_rgb(1, 0, 0)

led = LED()

class BootScreen:
    def draw(self):
        display.set_pen(BLACK)
        display.clear()

        display.set_pen(WHITE)

        # Splash text
        text_width = display.measure_text("PICOCHARTS", scale=4)
        display.text("PICOCHARTS", 160 -  text_width // 2, 50, scale=4)

        text_width = display.measure_text("by @thjaed", scale=2)
        display.text("by @thjaed", 160 -  text_width // 2, 80, scale=2)

        display.update()
    
    def print(self, text):
        print(text)
        # Clear text area
        display.set_pen(BLACK)
        display.rectangle(0, 190, WIDTH, 50)

        # Write text
        display.set_pen(WHITE)
        text_width = display.measure_text(text, scale=2)
        display.text(text, 160 -  text_width // 2, 190, scale=2)

        display.update()

class MenuBar:
    def __init__(self):
        # Constants
        self.height = 15

    def draw(self):
        display.set_pen(GREY)
        display.rectangle(0, 0, WIDTH, self.height) # Top bar
        display.set_pen(WHITE)
        display.line(0, self.height - 1, WIDTH, self.height - 1) # Line

        if not state.Clock.rtc_set:
            # Draw offline indicator instead of date and time
            display.set_pen(RED)

            text_width = display.measure_text("OFFLINE", scale=2)
            display.text("OFFLINE", 160 - text_width // 2, 0, scale=2)
        else:
            time = clock.get_clock()
            date = clock.get_date()

            clock_width = display.measure_text(time, scale=2)
            date_width = display.measure_text(date, scale=2)

            display.set_pen(WHITE)
            display.text(time, 0, 0, scale=2) # Clock
            display.text(date, int((clock_width + (290 - clock_width) / 2) - (date_width / 2)), 0, scale=2) # Date

        if state.Battery.connected:
            #Battery Icon
            battery_level = battery.percentage()
            display.set_pen(WHITE)
            display.rectangle(290, 2, 25, 10) # White border
            display.rectangle(315, 4, 2, 6) # Notch
            display.set_pen(GREY)
            display.rectangle(292, 4, 21, 6) # Grey background
            display.set_pen(WHITE)
            display.rectangle(293, 5, (round((battery_level / 100) * 19)), 4) # Charge level

bar = MenuBar()

class Timetable:
    def __init__(self):
        # Constants
        self.menu_bar_height = bar.height
        self.date_indic_height = 15
        self.y_top_pad = 5         # space between top of text and top of box
        self.y_bot_pad = 5         # space between bottom of text and bottom of box
        self.x_pad = 5             # space between left side of screen and where text starts
        self.line_height = 14      # height of each line at scale=2 inc. padding
        self.title_height = 18     # height of title exc. padding
        self.title_pad = 5         # space after title to visually separate it
        self.period_number_box_width = 40
        self.period_number_box_pad = 10
        self.label_edge_pad = 4
        self.label_text_x_pad = 5
        self.label_box_height = 18
        self.label_y_text_pad = 2

        # Variables
        self.data = []
        self.box_heights = []
        self.scroll_distance = 0
        self.cumulative_box_height = 0
        self.content_start = self.menu_bar_height

    def go(self, date=None):
        global page
        page = "timetable"
        self.scroll_distance = 0

        if date is None and not state.Clock.rtc_set:
            # point to earliest file
            available_files = [f.split("timetable_")[1].split(".jsonl")[0] for f in os.listdir() if "timetable_" in f]
            if len(available_files) > 0:
                available_files = sorted(available_files, key=clock.date_to_secs)
                self.date = available_files[0]
            else:
                # last resort if offline and no files
                self.date = None

        elif date is None:
            # today
            self.date = clock.secs_to_date()

        else:
            # point to specified file
            self.date = date

        # show blue date banner
        self.show_date = (not state.Clock.rtc_set) or (self.date != clock.secs_to_date())

        file_name = f"timetable_{self.date}.jsonl"

        # Load data from file into self.data
        self.data = []
        if file_name in os.listdir():
            with open(file_name, "r") as f:
                for l in f:
                    l = ujson.loads(l)
                    if ((state.Clock.rtc_set and l.get("end") > utime.time()) or
                        (not state.Clock.rtc_set) or
                        (state.Clock.rtc_set and self.date != clock.secs_to_date())):
                        self.data.append(l)
        else:
            message.show("No timetable file!")
            return False

        if "homework.jsonl" in os.listdir() and len(self.data) > 0:
            # add homework tasks to lessons

            with open("homework.jsonl", "r") as f:
                hw = []
                for t in f:
                    hw.append(ujson.loads(t))

            for l in self.data:
                # loop through lessons
                if l["type"] == "lesson":
                    for t in hw:
                        # loop through homework tasks
                        if (t["due_date"] == l["date"]) and (t["subject"] == l["subject"]):
                            # add homework task to lesson if its subject and due date matches
                            l["hw_task"] = {
                                "title": t["title"],
                                "completed": t["completed"]
                            }
                            break

        self.draw()
        bar.draw()
    
    def draw(self):
        display.set_pen(GREY)
        display.clear()

        if self.show_date:
            self.content_start = self.menu_bar_height + self.date_indic_height
        else:
            self.content_start = self.menu_bar_height
        
        self.cumulative_box_height = 0
        self.box_heights = []
              
        if len(self.data) > 0:
            now = utime.time()
            future_times = [e["start"] for e in self.data if e["start"] > now]

            for e in self.data: # loops through each event
                y_box_start = self.content_start + self.scroll_distance + self.cumulative_box_height
                y_text_start = y_box_start + self.y_top_pad
                label_box_y = y_text_start
                next_event = False

                if ((len(future_times) > 0) and 
                (e["start"] == min(future_times)) and
                (not self.show_date) and
                (state.Clock.rtc_set)):
                    next_event = True

                if e["type"] == "lesson":
                    subject = e["subject"]
                    time = e["time"]
                    room = e["room"]
                    teacher = e["teacher"]
                    period_num = e["period_num"]
                    if e.get("hw_task"):
                        hw_task = e["hw_task"]
                        num_lines = 4
                    else:
                        hw_task = None
                        num_lines = 3
                    box_height = self.y_top_pad + (self.title_height + self.title_pad) + (self.line_height * num_lines) + self.y_bot_pad

                    # used for scrolling
                    self.box_heights.append(box_height)

                    # Box
                    display.set_pen(GREY)
                    display.rectangle(0, y_box_start, WIDTH, box_height)

                    # Period number box
                    if period_num != None:
                        # Increase X Padding for text
                        x_pad = self.x_pad + self.period_number_box_width

                        display.set_pen(WHITE)

                        # Number
                        text_width = display.measure_text(period_num, scale=4)
                        display.text(period_num, self.period_number_box_width // 2 - text_width // 2, y_box_start + box_height // 2 - 12, scale=4)

                        # Dividing line
                        display.line(self.period_number_box_width - 3, y_box_start, self.period_number_box_width - 3, y_box_start + box_height, 3)
                    else:
                        x_pad = self.x_pad

                    # Bottom bar
                    display.set_pen(WHITE)
                    display.line(0, y_box_start + box_height - 1, WIDTH, y_box_start + box_height - 1, 3)

                    # Text
                    display.set_pen(WHITE)

                    display.text(subject, x_pad, y_text_start, scale=3)
                    y_text_start += 20 # increment line start

                    display.text(time, x_pad, y_text_start, scale=2)
                    y_text_start += 14

                    display.text(room, x_pad, y_text_start, scale=2)
                    y_text_start += 14

                    display.text(teacher, x_pad, y_text_start, scale=2)
                    y_text_start += 14

                    if hw_task is not None:
                        hw_completed = hw_task["completed"]
                        hw_title = hw_task["title"]

                        if hw_completed: display.set_pen(GREEN)
                        else: display.set_pen(RED)

                        display.text(truncate_text(f"Homework: {hw_title}", max_px=WIDTH - self.period_number_box_width + 20, char_width=12), x_pad, y_text_start, scale=2)
                        y_text_start += 14

                elif e["type"] == "break":
                    time = e["time"]
                    name = e["name"]

                    box_height = self.y_top_pad + (self.line_height * 2) + self.y_bot_pad

                    # used for scrolling
                    self.box_heights.append(box_height)

                    # Box
                    display.set_pen(GREY)
                    display.rectangle(0, y_box_start, WIDTH, box_height)

                    # Text
                    display.set_pen(WHITE)

                    text_width = display.measure_text(name, scale=2)
                    display.text(name, WIDTH // 2 - text_width // 2, y_text_start, scale=2)
                    y_text_start += 14 # increment line start

                    text_width = display.measure_text(time, scale=2)
                    display.text(time, WIDTH // 2 - text_width // 2, y_text_start, scale=2)
                    y_text_start += 14

                # Bottom bar
                    display.set_pen(WHITE)
                    display.line(0, y_box_start + box_height - 1, WIDTH, y_box_start + box_height - 1, 3)

                if next_event:
                        # draw 'Next' label
                        text_width = display.measure_text("Next", scale=2)

                        label_y_text_start = label_box_y + self.label_y_text_pad

                        x_start = WIDTH - self.label_edge_pad - text_width - self.label_text_x_pad - self.label_text_x_pad
                        label_x_text_start = x_start + self.label_text_x_pad

                        display.set_pen(WHITE)
                        display.rectangle(
                          x_start,
                          label_box_y,
                          self.label_text_x_pad + text_width + self.label_text_x_pad,
                          self.label_box_height
                        )

                        display.set_pen(BLACK)
                        display.text("Next", label_x_text_start, label_y_text_start, scale=2)

                self.cumulative_box_height += box_height
                        
        else:
            message.show("No more lessons today!")
        
        if self.show_date:
            # draw date label if we are not looking at today
            display.set_pen(GREY)
            display.rectangle(0, 15, WIDTH, 15) # Top bar
            display.set_pen(WHITE)
            display.line(0, 29, WIDTH, 29) # Line

            text = f"Showing {clock.get_date(clock.date_to_secs(self.date))}"

            text_width = display.measure_text(text, scale=2)

            display.set_pen(BLUE)

            display.text(text, (WIDTH // 2 - text_width // 2), 15, scale=2) # Date

        bar.draw() # Draw menu bar on top
    
    def scroll(self, direction):
        # VIBECODED FUNCTION #
        visible_height = HEIGHT - self.content_start
        scroll_offset = -self.scroll_distance # Scroll distance
        curr_height = 0

        if self.cumulative_box_height > 0:
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

timetable = Timetable()

class TimetableChangeDate:
    def __init__(self):
        self.day_offset = 0 # number of days from the current day
        self.day_timestamp = 0
        self.available_days = []
        self.scrolled = 0
    
    def go(self):
        global page
        page = "timetable_change_date"
        self.offline = not wifi.test_connection() or not state.Clock.rtc_set
        # reset selected day
        self.day_offset = 0
        self.day_timestamp = utime.time()

        # get dates of timetables already stored
        self.available_days = [f.split("timetable_")[1].split(".jsonl")[0] for f in os.listdir() if "timetable_" in f]

        # convert the date in the file name to a timestamp and sort them
        self.available_days_timestamp = sorted(list(map(clock.date_to_secs, self.available_days)))

        # convert the sorted timestamps into date strings to be displayed
        self.available_days = list(map(clock.get_date, self.available_days_timestamp))

        if len(self.available_days) > 0 or not self.offline:
            self.draw()
        else:
            message.show("No files!")
    
    def scroll(self, direction):
        if self.offline and len(self.available_days) > 0:
            if direction == "back" and self.scrolled - 1 >= 0:
                self.scrolled -= 1
            elif direction == "back" and self.scrolled == 0:
                self.scrolled = len(self.available_days_timestamp) - 1
            elif direction == "forward" and self.scrolled + 1 < len(self.available_days_timestamp):
                self.scrolled += 1
            elif direction == "forward" and self.scrolled == len(self.available_days_timestamp) - 1:
                self.scrolled = 0
            
            self.day_timestamp = self.available_days_timestamp[self.scrolled]

            self.draw()

        elif not self.offline:
            if direction == "back":
                self.day_offset -= 1
            elif direction == "forward":
                self.day_offset += 1

            self.day_timestamp = utime.time() + self.day_offset * 86400

            self.draw()
    
    def draw(self):
        display.set_pen(GREY)
        display.clear()

        if self.offline:
            display.set_pen(RED)
            text_width = display.measure_text("Offline files", scale=2)
            display.text("Offline files", (WIDTH // 2 - text_width // 2), (HEIGHT // 2 - 12) - 100, scale=2)

            for index, day_timestamp in enumerate(self.available_days_timestamp):
                height_offset = 0
                if abs(index - self.scrolled) in [1, 0]:
                    # if text is selected or adjacent to selected
                    if index == self.scrolled:
                        # if selected
                        display.set_pen(WHITE)
                        self.day_timestamp = day_timestamp
                    elif abs(index - self.scrolled) == 1:
                        # if adjacant
                        display.set_pen(DARK_GREY)
                
                    height_offset = (index - self.scrolled) * 40 # should problably make 40 a constant

                    day = clock.get_date(day_timestamp) # pretty day sting
                    text_width = display.measure_text(day, scale=2)
                    display.text(day, (WIDTH // 2 - text_width // 2), (HEIGHT // 2 - 12) + height_offset, scale=2)
        else:
            for pos in [-1, 0, 1]:
                day = clock.get_date(self.day_timestamp + (pos * 86400))

                if pos == 0 and day in self.available_days:
                    # green if file saved already
                    display.set_pen(GREEN)
                elif pos == 0:
                    # white if not downloaded
                    display.set_pen(WHITE)
                else:
                    # not selected, adjacent
                    display.set_pen(DARK_GREY)

                text_width = display.measure_text(day, scale=2)
                display.text(day, (WIDTH // 2 - text_width // 2), (HEIGHT // 2 - 12) + (pos * 40), scale=2)
    
    def select(self):
        if not self.offline and self.day_offset == 0:
            # go to normal timetable page if going to todays date
            timetable.go()
        elif (not self.offline) or (self.offline and len(self.available_days) > 0):
            date = clock.secs_to_date(self.day_timestamp)
            
            # list files that are for the target date
            file_exists = f"timetable_{date}.jsonl" in os.listdir()

            if file_exists:
                # go to existing file
                timetable.go(date=date)

            elif wifi.test_connection():
                # if connected to internet and no file found
                message.show("Getting Timetable")

                # check if max file count has been reached
                files = [f for f in os.listdir() if "timetable_" in f]
                if len(files) >= config.MAX_TIMETABLES:
                    # sort in order of creation date
                    sorted_files = sorted(files, key=lambda x: int(clock.date_to_secs(x.split("timetable_")[1].split(".jsonl")[0])))
                    if not self.offline:
                        # don't remove today's timetable
                        sorted_files.remove(f"timetable_{clock.secs_to_date()}.jsonl")
                    # delete oldest one
                    os.remove(sorted_files[0])

                led.update("updating_data", True)
                classcharts.save_timetable(date=date)
                led.update("updating_data", False)

                timetable.go(date=date)
                
            else:
                # if no file and not online
                message.show("OFFLINE")
                utime.sleep(1)
                timetable.go()

timetable_chage_date = TimetableChangeDate()

class Behaviour:
    def __init__(self):
        # Variables
        self.data = []
        self.time_range = 0

        # Constants
        self.time_ranges = ["august", "this_week", "last_week"]
        self.time_box_pad = 5      # space between start and end of text and box start and end
        self.time_box_y = 200      # how high the time range box is
        self.time_box_height = 20  # height of time range box

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
            message.show("No behaviour file!")
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

        # Green box
        display.set_pen(GREEN)
        display.rectangle(0, 0, WIDTH // 2, HEIGHT)
        
        # Red box
        display.set_pen(RED)
        display.rectangle(WIDTH // 2, 0, WIDTH // 2, HEIGHT)

        display.set_pen(WHITE)

        # Positives label
        text_width = display.measure_text("Positives", scale=2)
        display.text("Positives", WIDTH // 4 - text_width // 2, WIDTH // 4, scale=2)

        # Positives big number
        text_width = display.measure_text(positives, scale=4)
        display.text(positives, WIDTH // 4 - text_width // 2, HEIGHT // 2, scale=4)

        # Negatives label
        text_width = display.measure_text("Negatives", scale=2)
        display.text("Negatives", WIDTH // 2 + WIDTH // 4 - text_width // 2, WIDTH // 4, scale=2)

        # Negatives big number
        text_width = display.measure_text(negatives, scale=4)
        display.text(negatives, WIDTH // 2 + WIDTH // 4 - text_width // 2, HEIGHT // 2, scale=4)

        if self.time_ranges[self.time_range] == "august":
            text = "Since August"
        elif self.time_ranges[self.time_range] == "this_week":
                text = "This Week"
        elif self.time_ranges[self.time_range] == "last_week":
                text = "Last Week"
        
        # Time range box
        text_width = display.measure_text(text, scale=2)
        display.set_pen(WHITE)
        display.rectangle(
                          (WIDTH // 2 - (text_width // 2)) - self.time_box_pad,
                          self.time_box_y - self.time_box_pad,
                          text_width + (self.time_box_pad * 2),
                          self.time_box_height
            )

        display.set_pen(BLACK)
        display.text(text, (WIDTH // 2 - (text_width // 2)), self.time_box_y - 2, scale=2) # Time range text

        bar.draw()

class Attendence:
    def __init__(self):
        # Variables
        self.data = []
        self.time_range = 0

        # Constants
        self.time_ranges = ["august", "this_week", "last_week"]
        self.time_box_pad = 5      # space between start and end of text and box start and end
        self.time_box_y = 200      # how high the time range box is
        self.time_box_height = 20  # height of time range box

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
            message.show("No attendance file!")
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
        
        for l in self.data:
            if l["time"] == self.time_ranges[self.time_range]:
                percentage = l["percentage"]
                break
        
        # Colour coded background based on percentage
        if percentage > 95:
            display.set_pen(GREEN)
        elif percentage > 85:
            display.set_pen(YELLOW)
        else:
            display.set_pen(RED)
        
        percentage = f"{percentage}%" # put % sign in front

        display.rectangle(0, 0, WIDTH, HEIGHT)
    
        display.set_pen(WHITE)
        text_width = display.measure_text(percentage, scale=5)
        display.text(percentage, 160 - text_width // 2, 100, scale=5) # percentage number

        if self.time_ranges[self.time_range] == "august":
            text = "Since August"
        elif self.time_ranges[self.time_range] == "this_week":
                text = "This Week"
        elif self.time_ranges[self.time_range] == "last_week":
                text = "Last Week"
        
        # Time range box
        text_width = display.measure_text(text, scale=2)
        display.set_pen(WHITE)
        display.rectangle(
                          (WIDTH // 2 - (text_width // 2)) - self.time_box_pad,
                          self.time_box_y - self.time_box_pad,
                          text_width + (self.time_box_pad * 2),
                          self.time_box_height
            )

        display.set_pen(BLACK)
        display.text(text, (WIDTH // 2 - (text_width // 2)), self.time_box_y - 2, scale=2) # Time range text

        bar.draw()

class Homework:
    def __init__(self):
        # Variables
        self.data = []
        self.box_heights = []
        self.scroll_distance = 0
        self.cumulative_box_height = 0
        self.selected = 0
        
        # Constants
        self.content_start = 15    # where menu bar ends
        self.y_top_pad = 5         # space between top of text and top of box
        self.y_bot_pad = 5         # space between bottom of text and bottom of box
        self.x_pad = 5             # space between left side of screen and where text starts
        self.line_height = 14      # height of each line at scale=2 inc. padding
        self.title_pad = 5         # space after title to visually separate it
        self.status_marker_width = 10
        
    def go(self):
        global page
        page = "homework"

        self.data = []
        if "homework.jsonl" in os.listdir(): # if file exists
            with open("homework.jsonl", "r") as f:
                for l in f:
                    # Load data from file into self.data
                    l = ujson.loads(l)
                    if not l["completed"]:
                        self.data.append(l)
        else:
            message.show("No homework file!")
            return False # dont continue to draw
        
        self.draw()
    
    def draw(self):
        display.set_pen(GREY)
        display.clear()
            
        if len(self.data) > 0:
            self.cumulative_box_height = 0
            self.box_heights = []

            for index, l in enumerate(self.data): # loops through each homework task
                selected = self.selected == index # True if this box is currently highlighted

                title = l["title"]
                teacher = l["teacher"]
                subject = l["subject"]
                due_date_str = l["due_date_str"]
                late = l["late"]
                task_id = l["task_id"]
                seen = task_id not in state.Homework.unseen_ids

                y_box_start = self.content_start + self.scroll_distance + self.cumulative_box_height
                y_text_start = y_box_start + self.y_top_pad
                
                title_height = measure_wrapped_text(title, WIDTH - 20, 12, self.line_height) + self.title_pad
                box_height = self.y_top_pad + title_height + (self.line_height * 2) + self.y_bot_pad

                # used for scrolling
                self.box_heights.append(box_height)

                # Box
                if selected:
                    # box white if highlighted
                    display.set_pen(WHITE)
                else:
                    display.set_pen(GREY)
                display.rectangle(0, y_box_start, WIDTH, box_height)

                x_pad = self.x_pad

                if not seen:
                    x_pad += self.status_marker_width
                    display.set_pen(BLUE)
                    display.rectangle(0, y_box_start, self.status_marker_width, box_height)
                
                #if completed:
                #    x_pad += self.status_marker_width
                #    display.set_pen(GREEN)
                #    display.rectangle(0, y_box_start, self.status_marker_width, box_height)

                # Bottom Bar
                if selected:
                    # text white if highlighted
                    display.set_pen(BLACK)
                else:
                    display.set_pen(WHITE)

                display.line(0, y_box_start + box_height - 1, WIDTH, y_box_start + box_height - 1)

                # Text
                display.text(title, x_pad, y_text_start, wordwrap=WIDTH - 20, scale=2)
                y_text_start += measure_wrapped_text(title, WIDTH - 20, 12, 14) + self.title_pad # increment line start

                display.text(f"{teacher} | {subject}", x_pad, y_text_start, scale=2)
                y_text_start += self.line_height

                if late:
                    # Set text to red if task is late
                    display.set_pen(RED)
                else:
                    display.set_pen(GREEN)
                display.text(f"Due on {due_date_str}", x_pad, y_text_start, scale=2)
                y_text_start += self.line_height

                self.cumulative_box_height += box_height
        else:
            message.show("All homework completed!")
        
        bar.draw() # Draw menu bar on top
    
    def select(self):
            task = self.data[self.selected]
            task_id = task["task_id"]

            if task_id in state.Homework.unseen_ids:
                if wifi.test_connection():
                    # mark task as seen on classcharts if it is unseen
                    led.update("updating_data", True)
                    message.show("Please Wait")
                    classcharts.mark_seen(task_id)
                    led.update("updating_data", False)
                else:
                    state.Homework.unseen_ids.remove(task_id)

                if len(state.Homework.unseen_ids) == 0:
                    # turn led off if there are no other unseen tasks
                    led.update("unseen_homework", False)

            hwviewer.go(task)
    
    def scroll(self, direction):
        # BASED ON VIBECODED FUNCTION #
        visible_height = 225
        scroll_offset = -self.scroll_distance # Scroll distance
        curr_height = 0

        if self.cumulative_box_height > 0:
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
        # Variables
        self.data = {}
        self.desc_start_offset = 0

        # Constants
        self.content_start = 15    # where menu bar ends
        self.y_top_pad = 5         # space between top of text and top of box
        self.y_bot_pad = 5         # space between bottom of text and bottom of box
        self.x_pad = 5             # space between left side of screen and where text starts
        self.line_height = 14      # height of each line at scale=2 inc. padding
        self.title_pad = 5         # space after title to visually separate it
        self.desc_top_pad = 5      # space between header and description

    def go(self, data):
        global page
        page = "homework_viewer"

        self.desc_start_offset = 0

        self.title = data["title"]
        self.teacher = data["teacher"]
        self.subject = data["subject"]
        self.due_date_str = data["due_date_str"]
        self.late = data["late"]
        self.description = data["description"]

        self.draw()
        bar.draw()
    
    def draw(self):
        display.set_pen(GREY)
        display.clear()

        self.header_end = (
            self.content_start + self.y_top_pad
            + measure_wrapped_text(self.title, WIDTH - 20, 12, self.line_height)
            + self.title_pad + (self.line_height * 2) + self.y_bot_pad
            )

        desc_start = self.desc_start_offset + self.header_end + self.desc_top_pad

        y_text_start = self.content_start + self.y_top_pad

        # Draw description text
        display.set_pen(WHITE)
        display.text(self.description, self.x_pad, desc_start, wordwrap=WIDTH - 20, scale=2)

        # Draw box over description
        display.set_pen(GREY)
        display.rectangle(0, 0, WIDTH, self.header_end)

        # Info text
        display.set_pen(WHITE)
        display.text(self.title, self.x_pad, y_text_start, wordwrap=WIDTH - 20, scale=2) # Title
        y_text_start += measure_wrapped_text(self.title, WIDTH - 20, 12, self.line_height) + self.title_pad # increment line start

        display.text(f"{self.teacher} | {self.subject}", self.x_pad, y_text_start, scale=2) # Teacher and subject
        y_text_start += 14

        if self.late:
            # Set due date to red if task is late
            display.set_pen(RED)
        else:
            display.set_pen(GREEN)

        display.text(f"Due on {self.due_date_str}", self.x_pad, y_text_start, scale=2) # Due date
        y_text_start += 14

        display.set_pen(WHITE)
        display.line(0, self.header_end, WIDTH, self.header_end) # Bottom bar

        bar.draw()

    def scroll(self, direction):
        visible_area = HEIGHT - self.header_end
        if direction == "down":
            if ((measure_wrapped_text(self.description, WIDTH - 20, 12, self.line_height)
                + self.desc_start_offset + 5) > visible_area):
                # If description has not scrolled up to far
                self.desc_start_offset -= 14

        elif direction == "up":
            if self.desc_start_offset < 0: # If the description has been scrolled down at all
                self.desc_start_offset += 14  

        self.draw()

hwviewer = HomeworkViewer()

class Menu:
    def __init__(self):
        # Variables
        self.selected = 0

        # Constants
        self.entries = [
                        "Timetable",
                        "Behaviour",
                        "Attendance",
                        "Homework",
                        "Connect and Refresh Data"
                    ]
        self.box_height = 32
        self.y_top_pad = 8

    def go(self):
        global page
        page = "menu"
        self.selected = 0
        self.draw()
        
    def draw(self):
        display.set_pen(GREY)
        display.clear()

        for index, name in enumerate(self.entries):
            cumulative_content_height = index * 30

            if index == self.selected:
                # White box to indicate selection
                display.set_pen(WHITE)
                display.rectangle(0, cumulative_content_height, WIDTH, self.box_height)
                display.set_pen(BLACK)
            else:
                display.set_pen(GREY)
                display.rectangle(0, cumulative_content_height, WIDTH, self.box_height)
                display.set_pen(WHITE)

            display.text(name, 5, cumulative_content_height + self.y_top_pad, scale=2)
    
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

    def show(self, text):
        global page
        
        display.set_pen(GREY)
        display.clear()
        
        # Measure width in order to put text in centre of screen
        text_width = display.measure_text(text, scale=2)
        
        print(text)
        display.set_pen(WHITE)
        display.text(text, (WIDTH // 2 - text_width // 2), (HEIGHT // 2 - 12), wordwrap=WIDTH - 20, scale=2)
        
        display.update()

message = Message()
