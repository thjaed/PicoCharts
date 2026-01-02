import utime

class Clock:
    def __init__(self):
        self.cal_generated_today = False
        # Months and days as strings for displaying date
        self.months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        self.days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    def get_clock(self, secs): # Returns a clock string from timestamp
            time = utime.localtime(secs)

            # gets hour and minuite from time
            # Adds a 0 in front if less than 9
            hour = str(time[3]) if time[3] > 9 else f"0{time[3]}"
            minute = str(time[4]) if time[4] > 9 else f"0{time[4]}"

            return f"{hour}:{minute}"

    def get_date(self, secs): # Returns a date string from timestamp
        time = utime.localtime(secs)

        day = self.days[time[6]]
        month = self.months[time[1] - 1]

        return f"{day} {time[2]} {month}"
    
    def get_date_classcharts(self, secs):
        time = utime.localtime(secs)
        
        day = str(time[2]) if time[2] > 9 else f"0{time[2]}"
        month = str(time[1]) if time[1] > 9 else f"0{time[1]}"
        year = time[0]
        
        return f"{day}-{month}-{year}"
        