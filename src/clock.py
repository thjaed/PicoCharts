import utime # type: ignore
import machine # type: ignore
import usocket # type: ignore
import ustruct # type: ignore

import config


cal_generated_today = False
# Months and days as strings for displaying date
months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

def get_clock(secs=utime.time()): # Returns a clock string from timestamp
    time = utime.localtime(secs)

    # gets hour and minuite from time
    # Adds a 0 in front if less than 9
    hour = str(time[3]) if time[3] > 9 else f"0{time[3]}"
    minute = str(time[4]) if time[4] > 9 else f"0{time[4]}"

    return f"{hour}:{minute}"

def get_date(secs=utime.time()): # Returns a date string from timestamp
    time = utime.localtime(secs)

    day = days[time[6]]
    month = months[time[1] - 1]

    return f"{day} {time[2]} {month}"
    
def get_date_cc_api(secs=utime.time()):
    # Returns date as a string in YYYY-MM-DD as needed by the classchars API
    time = utime.localtime(secs)
        
    day = str(time[2]) if time[2] > 9 else f"0{time[2]}"
    month = str(time[1]) if time[1] > 9 else f"0{time[1]}"
    year = time[0]
        
    return f"{day}-{month}-{year}"
    
def clock_str_to_secs(clock_str):
    # Returns mins passed in a day from a time in HH:MM form
    hrs = int(clock_str[0:2])
    mins = int(clock_str[3:5])
    return (hrs * 60) + mins
    
def set_time_ntp():
    print("Setting time via NTP")
    global rtc
    rtc = machine.RTC()
    NTP_DELTA = 2208988800
    NTP_QUERY = bytearray(48)
    NTP_QUERY[0] = 0x1B
    addr = usocket.getaddrinfo(config.NTP_HOST, 123)[0][-1]
    s = usocket.socket(usocket.AF_INET, usocket.SOCK_DGRAM)
    try:
        s.settimeout(1)
        res = s.sendto(NTP_QUERY, addr)
        msg = s.recv(48)
    finally:
        s.close()
    ntp_time = ustruct.unpack("!I", msg[40:44])[0]
    t = utime.gmtime(ntp_time - NTP_DELTA + config.TZ_OFFSET_SEC)
    rtc.datetime((t[0], t[1], t[2], t[6] + 1, t[3], t[4], t[5], 0))