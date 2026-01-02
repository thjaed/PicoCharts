from uclasscharts_api import StudentClient
import ujson
import utime

class ClassCharts:
    def login(self):
        self.client = StudentClient(code="HAM5PJFGHV", dob="2010-05-05")
    
    def save_timetable(self, date_str):
        response = self.client.get_lessons(date=date_str)
        lessons = response["data"]
        meta = response["meta"]
        
        timetable = []
        
        for lesson in lessons:
            period_num = lesson["period_number"]
            for period in meta["periods"]:
                if period["number"] == period_num:
                    start_time = period['start_time'][:5]
            subject = lesson["subject_name"]
            teacher = lesson["teacher_name"]
            room = lesson["room_name"]
            event = {"title": subject, "start": start_time, "location": room}
            timetable.append(event)
        
            print(f"{start_time}: {subject} with {teacher} in {room}")
        
        with open("cal_today.jsonl", "w") as f:
            for event in timetable:
                ujson.dump(event, f)
                f.write("\n")
