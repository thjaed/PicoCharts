# PicoCharts
 PicoCharts is a pocket-sized embedded device that lets students view their timetable, homework, behaviour, and attendance without needing a phone. I built this device using a Raspberry Pi Pico 2 W and I am using an online API for the data (ClassCharts). Hence the name "PicoCharts".

 <img src="/hardware/front.jpg" alt="Front" width="400">

## Backstory
 After my school banned the use of mobile phones, I had the idea of creating a device that could let me view my timetable at school. This was also a good opportunity to improve my hardware design & soldering skills, and to improve my programming.
 
 The project started by just reading an exported calendar file from Outlook (project [cal-pal](https://github.com/thjaed/cal-pal)), but quickly grew after I upgraded to the Pico 2 W with wireless connectivity. I found documentation for the API of the platform my school uses, thank you to the creators of https://classchartsapi.github.io/api-docs/, without this community resource my project would not have been possible. I developed a Python & MicroPython wrapper for the API (https://github.com/thjaed/classcharts-api-python) which is accessible for anyone else wanting to integrate with the ClassCharts API.

## Features
 Here are some features of PicoCharts:

 ### Timetable
  - Label next to lessons with homework due
  - Timetables for different days can be viewed
  - Custom breaks can be added, e.g. Lunch or Break
  - 'Next' label on lessons
  - Lessons in the past are automatically removed
  - Auto-updates after a new day
  - View timetables for different days and store them offline

 ### Homework
  - Front LED turns on if there is unseen homework
  - Description can be viewed by clicking on a homework task
  - Due-date colour coded to make it clear if a homework is late or not
  - Homework marked as seen on ClassCharts when it is clicked on

 ### Attendance
  - Colour-coded background based on percentage
  - Easily choose a time range (Since August, This Week or Last Week)

 ### Behaviour
  - Easily choose a time range (Since August, This Week or Last Week)

## Using PicoCharts yourself
 To use PicoCharts, all you need is a Raspberry Pi Pico 2 W and a Pimoroni Pico Display Pack 2.0" (No soldering required, just attach a headered Pico 2 W to the back of the Pico Display). The Pico LiPo SHIM is only required if you want to use PicoCharts with a battery and the Adafruit LC709203F is only required if you want the battery percentage in the corner of the screen. Note that you will need to solder these battery boards.

 In terms of software, you need to install [Pimoroni's MicroPython build](https://github.com/pimoroni/pimoroni-pico-rp2350/releases/latest) to your Pico. Then copy everything in the [src](/src/) folder to your Pico. You can do this in the IDE 'Thonny'.
 
 Make sure to modify [secrets.py](/src/secrets.py), this is where you put your ClassCharts login details and WiFi networks.
 
 In [config.py](/src/config.py), you can change settings such as timezone and brightness. This is also where you define what times your breaks are, so make sure to change the times to reflect your school day. Disable ENABLE_BATTERY_gauge (enabled by default) if you are not using the battery gauge.

 If you decide to replicate my hardware, there are [STL Files](/hardware/stl_files/) for my design.

## Hardware
 ### I used the following hardware:
  - Pimoroni Pico Display Pack 2.0" - this is the screen and has the built in buttons and RGB LED
  - Raspberry Pi Pico 2W
  - Adafruit LC709203F battery fuel gauge - measure the charge level of the battery
  - Pimoroni Pico LiPo SHIM
  - USB-C breakout board with 512K resistors (so it works with modern chargers)
  - 1200mAh LiPo battery

At the start, I was using the Pico Display with the Pico plugged in to the headers on the back. But this made the device too thick so I decided to remove the headers from the display and solder 30 AWG wire directly. In the process of removing the headers I accidentally ripped off some pads (I had bad equipment) including the 3V supply. But luckily I traced it back to a resistor and soldered on to it, which saved the screen.

I used a USB-C breakout board to add USB-C. I soldered to the touch pads underneath the Pi to get USB data signals working over it, so I can program the Pi through the USB-C port as well.

 ### Wiring diagram
  <img src="/hardware/wiring-diagram.jpg" alt="Wiring Diagram" width="400">

 ### Internals
  <img src="/hardware/internals.jpg" alt="Internals" width="400">
  
 ### Back
  <img src="/hardware/back.jpg" alt="Back" width="400">

## Software
 ### High-level overview
  PicoCharts gets and displays data by first requesting data from the ClassCharts API. This happens at bootup and at a set interval, when the device is sleeping. This data is then simplified and saved into a JSON file in the flash storage. When a page is opened on the device, the corresponding file is read and loaded into a list. This list is then read by a draw function, which then puts the data on the screen inside scrollable pages and organised boxes.

  If the user requests to view the timetable for a different day and the JSON file for that day is not saved, then the data is requested and saved into a new JSON file. If the file already exists, it is opened with little to no waiting.
 
 ### Use of AI generated code
  AI was used selectively for complex date arithmetic and initial scrolling logic. All AI-assisted code is clearly commented.

## Acknowledgements
 In this project I used:

 - pybuttons by @oscaracena - https://github.com/oscaracena/pybuttons
 - ClassCharts API Docs  by @veloii - https://github.com/classchartsapi/api-docs
 - PicoGraphics by @pimoroni - https://github.com/pimoroni/pimoroni-pico/tree/main/micropython/modules/picographics
 - MicroPython_LC709203F by @chris-reichl - https://github.com/chris-reichl/MicroPython_LC709203F
 - I based my 3D printed case on: Pimoroni Pico Display pack 2.0 Case by @PMcGregor_848641 - https://www.printables.com/model/473270-pimoroni-pico-display-pack-20-case