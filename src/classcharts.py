import ujson # type: ignore
import utime # type: ignore

from uclasscharts_api import StudentClient
import clock
import secrets

def strip_tags(text):
    # removes HTML tags from a string
    out = ""
    in_tag = False
    for c in text:
        if c == "<":
            # start of tag
            in_tag = True
        elif c == ">":
            # end of tag
            in_tag = False
        elif not in_tag:
            # add character to output if not inside tag
            out += c
    return out

def convert_text(text):
    # replace chars
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("</p>", "§§")
    text = text.replace("<br>", " ")
    text = text.replace("\n", " ")
    text = text.replace("§§", "\n\n")
    text = text.replace("&nbsp;", " ")
    text = text.replace("\"", "'")

    # remove useless spaces
    while "  " in text:
        text = text.replace("  ", " ")

    # remove spaces after newlines
    text = text.replace("\n ", "\n")

    # remove useless blank lines
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")
    
    # remove any leftover HTML tags
    text = strip_tags(text)

    # remove spaces at start and end
    text = text.strip()

    return text

class ClassCharts:
    def login(self):
        # Authenticate with ClassCharts API
        self.client = StudentClient(code=secrets.CC_CODE, dob=secrets.CC_DOB)

        return "Authenticated with CC"

    def save_data(self):
        yield self.login()
        yield "Getting Timetable"
        self.save_timetable(login=False)
        yield "Getting Behaviour"
        self.save_behaviour(login=False)
        yield "Getting Attendance"
        self.save_attendance(login=False)
        yield "Getting Homework"
        self.save_homework(login=False)

        yield "All data saved"

    def save_timetable(self, login=True):
        if login: self.login()
        # Query API
        response = self.client.get_lessons(date=clock.today())
        lessons = response["data"]
        meta = response["meta"]
        
        timetable = []
        
        for lesson in lessons:
            period_code = lesson["period_number"] # Period code is either REG, 1, 2, RB2, 3, 4, 5
            # Uses metadata response to match period code to start and end times
            for period in meta["periods"]:
                if period["number"] == period_code: 
                    start_time = period["start_time"][:5] # Gets start time in HH:MM format
                    end_time = period["end_time"][:5] # Gets end time in HH:MM format
                    
            subject = lesson["subject_name"]
            teacher = lesson["teacher_name"]
            room = lesson["room_name"]
            
            # Word Replacements
            if subject == "Art & Design - Photography":
                subject = "Photography"
                
            # Put data in json format so it can be saved to a file
            event = {
                "subject": subject,
                "teacher": teacher,
                "room": room,
                "time": f"{start_time} to {end_time}",
                "end_time_secs": clock.clock_str_to_secs(end_time)
            }
            timetable.append(event)
        
        # Write data to file
        with open("timetable.jsonl", "w") as f:
            for event in timetable:
                ujson.dump(event, f)
                f.write("\n")
        
        
    def save_behaviour(self, login=True):
        if login: self.login()

        behaviour = []
        times = ["august", "this_week", "last_week"]

        # Query API
        for time in times:
            if time == "august":
                response = self.client.get_behaviour(from_date=clock.august(), to_date=clock.today())
            elif time == "this_week":
                response = self.client.get_behaviour(from_date=clock.this_monday(), to_date=clock.today())
            elif time == "last_week":
                last_week = clock.last_week()
                response = self.client.get_behaviour(from_date=last_week[0], to_date=last_week[1])

            data = response["data"]

            total_positive = 0
            total_negative = 0

            # Loop through points for each reason and sum them together to get total
            for i in data["negative_reasons"]:
                total_negative += data["negative_reasons"][i]

            for i in data["positive_reasons"]:
                total_positive += data["positive_reasons"][i]

            # Store in json format
            behaviour.append({
                "time": time,
                "positive": str(total_positive),
                "negative": f"-{total_negative}" if total_negative > 0 else str(total_negative)
            })

        # Save data to file
        with open("behaviour.jsonl", "w") as f:
            for line in behaviour:
                ujson.dump(line, f)
                f.write("\n")


    def save_attendance(self, login=True):
        if login: self.login()

        attendance = []
        times = ["this_week", "last_week"]

        # Query API
        for time in times:
            if time == "this_week":
                response = self.client.get_attendance(from_date=clock.this_monday(), to_date=clock.today())
                since_august = response["meta"]["percentage_singe_august"]
            elif time == "last_week":
                last_week = clock.last_week()
                response = self.client.get_attendance(from_date=last_week[0], to_date=last_week[1])

            meta = response["meta"]

            # Store in json format
            attendance.append({
                "time": time,
                "percentage": int(meta["percentage"])
            })
        
        attendance.append({
            "time": "august",
            "percentage": int(since_august)
        })

        # Save data to file
        with open("attendance.jsonl", "w") as f:
            for line in attendance:
                ujson.dump(line, f)
                f.write("\n")
        

    def save_homework(self, login=True):
        if login: self.login()

        response = self.client.get_homework_tasks(from_date=clock.seven_days_ago(), to_date=clock.one_month_future(), display_date="due_date")
        data = response["data"]

        homeworks = []

        unseen_tasks = False

        for task in data:
            title = task["title"]
            teacher = task["teacher"]
            subject = task["subject"]
            due_date = task["due_date"]
            issue_date = task["issue_date"]
            description = convert_text(task["description"])
        
            if task["status"]["first_seen_date"] != None:
                seen = True
            else:
                seen = False
                unseen_tasks = True

            if task["status"]["ticked"] == "yes":
                completed = True
            else:
                completed = False
            
            due_date_secs = clock.date_to_secs(due_date)

            if due_date_secs < utime.time():
                late = True
            else:
                late = False

            due_date_str = clock.get_date(due_date_secs)
            issue_date_str = clock.get_date(clock.date_to_secs(issue_date))
            
            homeworks.append({
                "title": title,
                "teacher": teacher,
                "subject": subject,
                "due_date_str": due_date_str,
                "issue_date_str": issue_date_str,
                "seen": seen,
                "completed": completed,
                "late": late,
                "description": description
            })

        with open("homework.jsonl", "w") as f:
            for line in homeworks:
                ujson.dump(line, f)
                f.write("\n")
        
        return unseen_tasks