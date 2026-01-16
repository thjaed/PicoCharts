# PicoCharts

PicoCharts is a pocketable and versatile "school device". You can use it to view your timetable, behaviour, attendance and homework. I built this device using a Raspberry Pi Pico 2 W and I am using an online API for the data (ClassCharts). Hence the name "PicoCharts".

# Why?

After my school banned the use of moblie phones, I had the idea of creating a device that could let me view my timetable at school. This was also a good oppourtunity to improve my hardware design & soldering skills, and to improve my programming.

# About

The project started by just reading an exported calendar file from outlook, but quickly grew after I upgraded to the Pico 2 W with wireless connectivity. I found documentation for the API for the platform my school uses, thank you to the creators of https://classchartsapi.github.io/api-docs/, without this community resource my project would not have been possible. I developed a python & micropython wrapper for the API (https://github.com/thjaed/classcharts-api-python) which is accessible for anyone else wanting to intergrate with the ClassCharts API.
