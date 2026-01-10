import ujson # type: ignore

from uclasscharts_api import StudentClient
from config import VERBOSE_OUTPUT as v
import clock
import secrets

class ClassCharts:
    def login(self):
        # Authenticate with ClassCharts API
        if v: print("Authenticating with ClassCharts")
        self.client = StudentClient(code=secrets.CC_CODE, dob=secrets.CC_DOB)

    def save_data(self):
        print("saving all data from classcharts")
        self.login()
        self.save_timetable(login=False)
        self.save_behaviour(login=False)
        print("saved all data from classcharts")

        
    def save_timetable(self, date_str=clock.today(), login=True):
        print(f"Saving timetable to file for {clock.today()}...")
        if login: self.login()
        # Query API
        if v: print("Getting Timetable")
        response = self.client.get_lessons(date=date_str)
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
                "start_time": start_time,
                "end_time": end_time,
            }
            timetable.append(event)
            
            if v: print(f"{start_time}: {subject} with {teacher} in {room}")
        
        # Write data to file
        if v: print("Writing timetable to timetable.jsonl")
        with open("timetable.jsonl", "w") as f:
            for event in timetable:
                ujson.dump(event, f)
                f.write("\n")
        print("Done saving timetable to file")
        
    def save_behaviour(self, from_date=clock.august(), to_date=clock.today(), login=True):
        print("Saving behaviour to file...")
        if login: self.login()
        # Query API
        if v: print("Getting behaviour")
        response = self.client.get_behaviour(from_date=from_date, to_date=to_date)
        
        behaviour = response["data"]

        total_positive = 0
        total_negative = 0
        
        # Loop through points for each reason and sum them together to get total
        for i in behaviour["negative_reasons"]:
            total_negative += behaviour["negative_reasons"][i]
            
        for i in behaviour["positive_reasons"]:
            total_positive += behaviour["positive_reasons"][i]
        
        # Store in json format
        data_json = {
            "positive": total_positive,
            "negative": total_negative
        }

        print(f"Positives: {total_positive} Negatives: {total_negative}")

        if v: print("Writing behaviour to behaviour.jsonl")
        # Save data to file
        with open("behaviour.jsonl", "w") as f:
            ujson.dump(data_json, f)
        print("Done saving behaviour to file")