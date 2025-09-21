import sys
import time
import math
import gevent
from colorsys import hsv_to_rgb

from PIL import Image, ImageDraw, ImageFont
from unicornhatmini import UnicornHATMini


class Unicorn:
    def __init__(self):
        # From unicorn hat sample code
        self._unicornhatmini = UnicornHATMini()
 
        rotation = 0
        if len(sys.argv) > 1:
            try:
                rotation = int(sys.argv[1])
            except ValueError:
                print("Usage: {} <rotation>".format(sys.argv[0]))
                sys.exit(1)
                
        self._unicornhatmini.set_rotation(rotation)
        self._display_width, self._display_height = self._unicornhatmini.get_shape()

        print("{}x{}".format(self._display_width, self._display_height))

        # Do not look at unicornhatmini with remaining eye
        self._unicornhatmini.set_brightness(.1)
        
        # Load a nice 5x7 pixel font
        # Granted it's actually 5x8 for some reason :| but that doesn't matter
        self._font = ImageFont.truetype("5x7.ttf", 8)

        hue = .330
        self._timer_r, self._timer_g, self._timer_b = [int(c * 255) for c in hsv_to_rgb(hue, 1.0, 1.0)]

        hue = .530
        self._active_r, self._active_g, self._active_b = [int(c * 255) for c in hsv_to_rgb(hue, 1.0, 1.0)]

        self._blink_on = True
        
    def write_four(self, text):
        """ Writes up to 4 digits. If there are a full 4, the leftmost must be a 1
        since 4 full digits don't fit

        Returns a list of values that were set
        """

        res = [False] * self._display_width * self._display_height
        
        if int(text) == text:
            text = str(text)

        self.clear_numbers(show=False)
        index_start = 4 - len(text)
        for i in range(len(text)):
            self.write_one(text[i], index_start + i, res)
            
        self._unicornhatmini.show()

        return res
    
    def write_one(self, text, index, res):
        """ Write one digit. Index is 0 for leftmost digit and 3 for rightmost.
        Index 0 can only be used to write a 1 because the screen isn't wide enough

        This function does not write the result to the screen. The caller should do it"""

        # We don't assert that index 0 is the digit 1 because we don't want the program
        # to quit so we just assume it doesn't happen
        
        # The font we're using leaves the bottom two rows open so we can use it for other
        # things like indicators
        text_width, text_height = self._font.getsize(text)
        image = Image.new('P', (text_width, text_height), 0)
        draw = ImageDraw.Draw(image)

        # Draw the text into the image
        draw.text((0,0), text, font=self._font, fill=255)

        image_x_offset = 0
        display_x_offset = 0

        # leftmost digit has space for 3 pixels (2 for the digit and 1 for the blank space)
        if index == 0 and text_width > 3:
            image_x_offset = text_width-3
            text_width = 3
            
        if index > 0:
            # index 0 is 2 pixels wide plus one blank space = 3
            # every index after that is 4 pixels wide with one blank space = 5
            # we also adjust the offset if the text is skinnier (the digit 1, for example)
            display_x_offset = 3+ ((index-1)*5) + (5-text_width)

        if index == 3:
            # Each digit has a trailing space after it. For the last one, truncate this
            text_width -= 1

        #print(f"{text_height}x{text_width} value {text} at index {index}. image_offset {image_x_offset} display offset {display_x_offset}")

        # The generated image has a row of blank pixels at the top. It looks nice but we remove
        # it so we have more screen space to work with
        display_y_offset = -1
        text_y_offset = 1
        for y in range(text_y_offset, text_height):
            for x in range(text_width):
                if image.getpixel((x+image_x_offset, y)) == 255:
                    #print("x",end="")
                    self._unicornhatmini.set_pixel(x+display_x_offset, y+display_y_offset, self._timer_r, self._timer_g, self._timer_b)
                    res[((y+display_y_offset) * self._display_width) + x+display_x_offset] = True
                #else:
                #    print(".",end="")

            #print()
        print()


    def clear_numbers(self, show = True):
        """ Clear the display. Pass show=False if the caller is going to do other display changes.
        The caller should call show() in that case"""


        # -1 on the vertical so we don't clear the active timer indicators
        for y in range(self._display_height-1):
            for x in range(self._display_width):
                self._unicornhatmini.set_pixel(x, y, 0, 0, 0)

        if show:
            self._unicornhatmini.show()

    def clear_active_timers(self):
        for i in range(self._display_width):
            self._unicornhatmini.set_pixel(i, 6, 0,0,0)
        self._unicornhatmini.show()

    def clear_display(self):
        self.clear_active_timers()
        self.clear_numbers()

    def set_active_timers(self, timers):
        # In the first version I hardcoded 3 timers max and I'm too lazy to generalize it
        for (i, t) in enumerate(timers):
            if t:
                self._unicornhatmini.set_pixel(0+i*7, 6, self._active_r, self._active_g, self._active_b)
                self._unicornhatmini.set_pixel(1+i*7, 6, self._active_r, self._active_g, self._active_b)
            else:
                self._unicornhatmini.set_pixel(0+i*7, 6, 0,0,0)
                self._unicornhatmini.set_pixel(1+i*7, 6, 0,0,0)
        self._unicornhatmini.show()

    def show_rainbow(self, duration_seconds):
        """We do this in a gevent thread so we can also play the buzzer sound"""
        
        # from the unicornhatmini examples
        step = 0
        
        for i in range(duration_seconds*60):
            step += 1

            for x in range(0, self._display_width):
                for y in range(0, self._display_height):
                    dx = (math.sin(step / self._display_width + 20) * self._display_width) + self._display_height
                    dy = (math.cos(step / self._display_height) * self._display_height) + self._display_height
                    sc = (math.cos(step / self._display_height) * self._display_height) + self._display_width

                    hue = math.sqrt(math.pow(x - dx, 2) + math.pow(y - dy, 2)) / sc
                    r, g, b = [int(c * 255) for c in hsv_to_rgb(hue, 1, 1)]

                    self._unicornhatmini.set_pixel(x, y, r, g, b)

            self._unicornhatmini.show()
            gevent.sleep(1.0 / 60)


        self.clear_numbers()
        self.clear_active_timers()

        
    def show_thermo(self, data_c, threshold_temp_c, target_temp_c):
        """ data from the thermal camera is 24 high x 32 wide so the input is a list of 768 values.
        Get the value with data[h*32 + w] with h 0-23 and w 0-32

        our display is 7 high by 17 wide"""

        print(f"threshold {threshold_temp_c}, target {target_temp_c}, ex {data_c[0]}")
        display_data = [0]*7*17

        stat_cold = 0
        stat_going = 0
        stat_done = 0
            
        for display_row, data_row in enumerate(range(2,24,3)):
            for display_column, data_column in enumerate(range(1, 32, 2)):
                d = data_c[data_row*32 + data_column]
                # faint blue if below threshold
                r = 0
                g = 0
                b = 10
                if d >= threshold_temp_c and d < target_temp_c - 30:
                    intensity_pct = (d - threshold_temp_c) / (target_temp_c - threshold_temp_c)
                    r = 0
                    g = round(intensity_pct * 100)
                    if intensity_pct > .5 and not self._blink_on:
                        g = 0
                    b = 25

                if d >= target_temp_c - 30 and d < target_temp_c:
                    if self._blink_on:
                        r = 100
                    else:
                        r = 30
                    g = 0
                    b = 0

                if d >= target_temp_c:
                    r = 200
                    g = 0
                    b = 0
                    
                if d <= threshold_temp_c:
                    stat_cold += 1
                elif d < target_temp_c:
                    stat_going += 1
                elif d >= target_temp_c:
                    stat_done += 1
                    
                self._unicornhatmini.set_pixel(display_column, display_row, r, g, b)
                print(f"{round(d,1)} ", end="")
                """
                if b > 0:
                    print(".",end="")
                elif g > 0:
                    print("o",end="")
                elif r > 0:
                    print("X",end="")
                """
            print()
        print()
        self._unicornhatmini.show()
        
        if self._blink_on:
            self._blink_on = False
        else:
            self._blink_on = True

        return [stat_cold, stat_going, stat_done]
            
        
