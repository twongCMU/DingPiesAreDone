import sys
import time

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
        self._r, self._g, self._b = [int(c * 255) for c in hsv_to_rgb(hue, 1.0, 1.0)]
        
    def write_four(self, text):
        """ Writes up to 4 digits. If there are a full 4, the leftmost must be a 1
        since 4 full digits don't fit
        """
        
        if int(text) == text:
            text = str(text)

        self.clear_screen(show=False)
        index_start = 4 - len(text)
        for i in range(len(text)):
            self.write_one(text[i], index_start + i)
            
        self._unicornhatmini.show()
        
    def write_one(self, text, index):
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

        print(f"{text_height}x{text_width} value {text} at index {index}. image_offset {image_x_offset} display offset {display_x_offset}")

        # The generated image has a row of blank pixels at the top. It looks nice but we remove
        # it so we have more screen space to work with
        display_y_offset = -1
        text_y_offset = 1
        for y in range(text_y_offset, text_height):
            for x in range(text_width):
                if image.getpixel((x+image_x_offset, y)) == 255:
                    print("x",end="")
                    self._unicornhatmini.set_pixel(x+display_x_offset, y+display_y_offset, self._r, self._g, self._b)
                else:
                    print(".",end="")

            print()
        print()


    def clear_screen(self, show = True):
        """ Clear the display. Pass show=False if the caller is going to do other display changes.
        The caller should call show() in that case"""
        
        for y in range(self._display_height):
            for x in range(self._display_width):
                self._unicornhatmini.set_pixel(x, y, 0, 0, 0)

        if show:
            self._unicornhatmini.show()
