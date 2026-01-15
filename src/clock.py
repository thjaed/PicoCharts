import utime # type: ignore
import machine # type: ignore
import usocket # type: ignore
import ustruct # type: ignore

import config

cal_generated_today = False
# Months and days as strings for displaying date
months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
# Days in each month (non-leap year)
DAYS_IN_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

def get_clock(secs=None): # Returns a clock string from timestamp
    if secs is None:
        secs = utime.time()

    time = utime.localtime(secs)

    # gets hour and minuite from time
    # Adds a 0 in front if less than 9
    hour = str(time[3]) if time[3] > 9 else f"0{time[3]}"
    minute = str(time[4]) if time[4] > 9 else f"0{time[4]}"

    return f"{hour}:{minute}"

def get_date(secs=None): # Returns a date string from timestamp
    if secs is None:
        secs = utime.time()

    time = utime.localtime(secs)

    day = days[time[6]]
    month = months[time[1] - 1]

    return f"{day} {time[2]} {month}"
    
def clock_str_to_secs(clock_str=get_clock()):
    # Returns mins passed in a day from a time in HH:MM form
    hrs = int(clock_str[0:2])
    mins = int(clock_str[3:5])
    return (hrs * 60) + mins
    
def set_time_ntp():
    yield "Setting time"
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
    yield "Time set"

def date_to_secs(date):
    # Returns epoch secs from a string in YYYY-MM-DD
    year = int(date[0:4])
    month = int(date[5:7])
    day = int(date[8:10])

    secs = utime.mktime([year, month, day, 0, 0, 0, 0, 0])
    return secs

def today():
    # Returns date as a string in YYYY-MM-DD as needed by the classchars API
    time = utime.localtime()
        
    day = str(time[2]) if time[2] > 9 else f"0{time[2]}"
    month = str(time[1]) if time[1] > 9 else f"0{time[1]}"
    year = time[0]

    return f"{year}-{month}-{day}"

def august():
    lt = utime.localtime()
    c_yr = lt[0]
    c_mnth = lt[1]

    if c_mnth >= 8:
        r_yr = c_yr
    else:
        r_yr = c_yr - 1

    return f"{r_yr}-08-01"

def this_monday():
    # VIBECODED FUNCTION #
    lt = utime.localtime()
    c_yr = lt[0]
    c_mnth = lt[1]
    c_day = lt[2]

    # Get the day of week (0=Monday, 6=Sunday)
    day_of_week = lt[6]
    # Calculate days back to Monday
    days_back = day_of_week
    # Calculate Monday's date
    monday_day = c_day - days_back

    # Handle month wraparound
    if monday_day <= 0:
        c_mnth -= 1
        if c_mnth == 0:
            c_mnth = 12
            c_yr -= 1
        # Days in previous month
        days_in_prev_month = DAYS_IN_MONTH.copy()
        if c_mnth == 2 and (c_yr % 4 == 0 and (c_yr % 100 != 0 or c_yr % 400 == 0)):
            days_in_prev_month[1] = 29
        monday_day += days_in_prev_month[c_mnth - 1]

    return f"{c_yr}-{c_mnth:02d}-{monday_day:02d}"

def last_week():
    # VIBECODED FUNCTION #
    lt = utime.localtime()
    c_yr = lt[0]
    c_mnth = lt[1]
    c_day = lt[2]
    day_of_week = lt[6]

    # Calculate days back to Monday of this week, then back 7 more days
    days_back = day_of_week + 7
    monday_day = c_day - days_back

    # Handle month wraparound
    monday_mnth = c_mnth
    monday_yr = c_yr
    if monday_day <= 0:
        monday_mnth -= 1
        if monday_mnth == 0:
            monday_mnth = 12
            monday_yr -= 1
        days_in_prev_month = DAYS_IN_MONTH.copy()
        if monday_mnth == 2 and (monday_yr % 4 == 0 and (monday_yr % 100 != 0 or monday_yr % 400 == 0)):
            days_in_prev_month[1] = 29
        monday_day += days_in_prev_month[monday_mnth - 1]

    sunday_day = monday_day + 6
    sunday_mnth = monday_mnth
    sunday_yr = monday_yr

    # Handle month wraparound for Sunday
    days_in_current_month = DAYS_IN_MONTH.copy()
    if sunday_mnth == 2 and (sunday_yr % 4 == 0 and (sunday_yr % 100 != 0 or sunday_yr % 400 == 0)):
        days_in_current_month[1] = 29
    if sunday_day > days_in_current_month[sunday_mnth - 1]:
        sunday_day = sunday_day - days_in_current_month[sunday_mnth - 1]
        sunday_mnth += 1
        if sunday_mnth > 12:
            sunday_mnth = 1
            sunday_yr += 1

    return [f"{monday_yr}-{monday_mnth:02d}-{monday_day:02d}", f"{sunday_yr}-{sunday_mnth:02d}-{sunday_day:02d}"]


def seven_days_ago():
    # VIBECODED FUNCTION #
    lt = utime.localtime()
    c_yr = lt[0]
    c_mnth = lt[1]
    c_day = lt[2]
        
    past_day = c_day - 7
    past_mnth = c_mnth
    past_yr = c_yr
        
    if past_day <= 0:
        past_mnth -= 1
        if past_mnth == 0:
            past_mnth = 12
            past_yr -= 1
        days_in_prev_month = DAYS_IN_MONTH.copy()
        if past_mnth == 2 and (past_yr % 4 == 0 and (past_yr % 100 != 0 or past_yr % 400 == 0)):
            days_in_prev_month[1] = 29
        past_day += days_in_prev_month[past_mnth - 1]
        
    return f"{past_yr}-{past_mnth:02d}-{past_day:02d}"

def one_month_future():
    # VIBECODED FUNCTION #
    lt = utime.localtime()
    c_yr = lt[0]
    c_mnth = lt[1]
    c_day = lt[2]
        
    future_mnth = c_mnth + 1
    future_yr = c_yr
    future_day = c_day
        
    if future_mnth > 12:
        future_mnth = 1
        future_yr += 1
        
    # Adjust day if it exceeds days in future month
    days_in_future_month = DAYS_IN_MONTH.copy()
    if future_mnth == 2 and (future_yr % 4 == 0 and (future_yr % 100 != 0 or future_yr % 400 == 0)):
        days_in_future_month[1] = 29
    if future_day > days_in_future_month[future_mnth - 1]:
        future_day = days_in_future_month[future_mnth - 1]
        
    return f"{future_yr}-{future_mnth:02d}-{future_day:02d}"