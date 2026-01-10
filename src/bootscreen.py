from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2, PEN_P4 # type: ignore

display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2, pen_type=PEN_P4)

WHITE = display.create_pen(255, 255, 255)
BLACK = display.create_pen(0, 0, 0)

class BootScreen:
    def draw(self):
        print("Drawing Bootscreen")
        display.set_pen(BLACK)
        display.clear()

        text_width = display.measure_text("PICOCHARTS", scale=4)

        display.set_pen(WHITE)
        display.text("PICOCHARTS", 160 -  text_width // 2, 50, scale=4)
        text_width = display.measure_text("by @thjaed", scale=2)
        display.text("by @thjaed", 160 -  text_width // 2, 80, scale=2)

        display.update()
    
    def print(self, text):
        # Clear text area
        display.set_pen(BLACK)
        display.rectangle(0, 190, 320, 50)

        # Write text
        display.set_pen(WHITE)
        text_width = display.measure_text(text, scale=2)
        display.text(text, 160 -  text_width // 2, 190, scale=2)

        display.update()