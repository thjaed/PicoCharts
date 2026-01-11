import ujson # type: ignore

from uclasscharts_api import StudentClient
import clock
import secrets

class ClassCharts:
    def login(self):
        # Authenticate with ClassCharts API
        self.client = StudentClient(code=secrets.CC_CODE, dob=secrets.CC_DOB)

        return "Authenticated with CC"

    def save_data(self):
        yield self.login()
        yield "Getting Timetable"
        yield self.save_timetable(login=False)
        yield "Getting Behaviour"
        yield self.save_behaviour(login=False)

        return "All data saved"

        
    def save_timetable(self, date_str=clock.today(), login=True):
        if login: self.login()
        # Query API
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
        
        # Write data to file
        with open("timetable.jsonl", "w") as f:
            for event in timetable:
                ujson.dump(event, f)
                f.write("\n")
        
        return "Saved Timetable"
        
    def save_behaviour(self, from_date=clock.august(), to_date=clock.today(), login=True):
        if login: self.login()
        # Query API

        behaviour = []
        times = ["august", "this_week", "last_week"]

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
                "positive": total_positive,
                "negative": total_negative
            })

        # Save data to file
        with open("behaviour.jsonl", "w") as f:
            for line in behaviour:
                ujson.dump(line, f)
                f.write("\n")
        
        return "Saved Behaviour"