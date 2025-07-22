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

    def write_number(self, text):
        # The font we're using leaves the bottom two rows open so we can use it for other
        # things like indicators
        text_width, text_height = self._font.getsize(str(text))
        image = Image.new('P', (text_width, text_height), 0)
        draw = ImageDraw.Draw(image)

        # Draw the text into the image
        draw.text((0,0), str(text), font=self._font, fill=255)

        print(f"{text_height}x{text_width} value {text}")
        for y in range(text_height):
            for x in range(text_width):
                hue = .330
                r, g, b = [int(c * 255) for c in hsv_to_rgb(hue, 1.0, 1.0)]
                if image.getpixel((x, y)) == 255:
                    print("x",end="")
                    self._unicornhatmini.set_pixel(x, y, r, g, b)
                else:
                    print(".",end="")
                    self._unicornhatmini.set_pixel(x, y, 0, 0, 0)

            print()
        print()
        self._unicornhatmini.show()

