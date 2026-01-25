# PicoCharts

 PicoCharts is a pocketable and versatile "school device". You can use it to view your timetable, behaviour, attendance and homework. I built this device using a Raspberry Pi Pico 2 W and I am using an online API for the data (ClassCharts). Hence the name "PicoCharts".

## Why?

 After my school banned the use of moblie phones, I had the idea of creating a device that could let me view my timetable at school. This was also a good oppourtunity to improve my hardware design & soldering skills, and to improve my programming.

## About

 The project started by just reading an exported calendar file from outlook, but quickly grew after I upgraded to the Pico 2 W with wireless connectivity. I found documentation for the API for the platform my school uses, thank you to the creators of https://classchartsapi.github.io/api-docs/, without this community resource my project would not have been possible. I developed a python & micropython wrapper for the API (https://github.com/thjaed/classcharts-api-python) which is accessible for anyone else wanting to intergrate with the ClassCharts API.

## Features
 Here are some features of PicoCharts:

### Timetable
 - Custom breaks can be added, e.g. Lunch or Break
 - Lessons in the past are automatically removed
 - Auto-updates after a new day
 - 'Current' and 'Next' labels on lessons (*Coming  very soon*)
 -  Label next to lessons that have homework due in on (*Coming  very soon*)
 - Timetables for different days can be viewed  (*Coming  very soon*)

### Behaviour
 - Easily  choose a time range (Since August, This Week or Last Week)
 - View reasons for behaviour points (*Coming  very soon*)

### Attendance
 - Colour-coded background based on percentage
 - Easily  choose a time range (Since August, This Week or Last Week)

### Homework
 - Front LED turns on if there is unseen homework
 - Description can be viewed by clicking on homework task
 - Due-date colour coded to make it clear if a homework is late or not
 - Homework marked as seen on ClassCharts when it is clicked on

## Use of AI generated code

 During this project, I kept the use of AI generated code to a minimum  as I wanted to learn things and be satisfied with what I had acomplished.

 With that being said, I did use some AI in my code, which I have labeled with comments to make it clear. I used AI in working out scrolling logic (although I have sinced replaced some of this with my own code) as well as some functions to do with working out dates, e.g. what was the date 1 month ago? 1 week ago? this monday? etc. I used AI for this because dates are incredibly boring and difficult to work with, and I didn't want this to be a burden.

## Acknowledgements

 In this project I used:

 - pybuttons by @oscaracena - https://github.com/oscaracena/pybuttons
 - ClassCharts API Docs  by @veloii - https://github.com/classchartsapi/api-docs
 - PicoGraphics by @pimoroni - https://github.com/pimoroni/pimoroni-pico/tree/main/micropython/modules/picographics
 - MicroPython_LC709203F by @chris-reichl - https://github.com/chris-reichl/MicroPython_LC709203F
 - I based my 3D printed case on: Pimoroni Pico Display pack 2.0 Case by @PMcGregor_848641 - https://www.printables.com/model/473270-pimoroni-pico-display-pack-20-case