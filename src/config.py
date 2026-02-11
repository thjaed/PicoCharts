###########################
#### PICOCHARTS CONFIG ####
###########################


# Offset in seconds from UTC
TZ_OFFSET_SEC = 0
# Time screen takes to sleep in seconds
SLEEP_TIME_SEC = 20
# Brightness of screen from 0 to 1
BRIGHTNESS = 0.8
# NTP server used for setting time
NTP_HOST = "pool.ntp.org"
# Seconds until wifi connection script gives up
WIFI_TIMEOUT = 20
# Force offline mode
FORCE_OFFLINE = False
# Maximum number of timetable files
MAX_TIMETABLES = 10
# Break times:
# "name" is the displayed name of the break e.g. "Break" or "Lunch"
# "start" and "end" are the times in "HH:MM" form when the break starts and ends
BREAKS = [
    {
        "name": "Break",
        "start": "10:45",
        "end": "11:00"
    },

    {
        "name": "Lunch",
        "start": "12:25",
        "end": "13:10"
    }
]