import board
from adafruit_seesaw import digitalio, rotaryio, seesaw

class Knob:
    def __init__(self):
        # Most of the init code is taken from the example code
        # in the seesaw library
        i2c = board.I2C()  # uses board.SCL and board.SDA
        s = seesaw.Seesaw(i2c, addr=0x36)

        seesaw_product = (s.get_version() >> 16) & 0xFFFF
        print(f"Found product {seesaw_product}")
        if seesaw_product != 4991:
            print("Wrong firmware loaded?  Expected 4991")

        # Configure seesaw pin used to read knob button presses
        # The internal pull up is enabled to prevent floating input
        s.pin_mode(24, s.INPUT_PULLUP)
        self._button = digitalio.DigitalIO(s, 24)

        self._encoder = rotaryio.IncrementalEncoder(s)
        self._last_position = self._encoder.position


    def is_button_pressed(self) -> bool:
        return not self._button.value
    
    def get_changed(self) -> int:
        """ Returns the number of encoder ticks that have changed since init or reinit
        Positive numbers = clockwise, negative = counterclockwise, 0 = unchanged
        """
        # flip the direction so clockwise increments
        position = self._encoder.position * -1

        if position == self._last_position:
            return 0
        
        return self._last_position-position

    def reinit(self):
        """ Reset the counter so the current position is the starting one """
        # flip the direction so clockwise increments
        self._last_position = self._encoder.position * -1
    
