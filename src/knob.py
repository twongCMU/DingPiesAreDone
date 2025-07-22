from adafruit_seesaw import digitalio, rotaryio, seesaw

class Knob:
    def __init__(self):
        # Most of the init code is taken from the example code
        # in the seesaw library
        i2c = board.I2C()  # uses board.SCL and board.SDA
        seesaw = seesaw.Seesaw(i2c, addr=0x36)

        seesaw_product = (seesaw.get_version() >> 16) & 0xFFFF
        print(f"Found product {seesaw_product}")
        if seesaw_product != 4991:
            print("Wrong firmware loaded?  Expected 4991")

        # Configure seesaw pin used to read knob button presses
        # The internal pull up is enabled to prevent floating input
        seesaw.pin_mode(24, seesaw.INPUT_PULLUP)
        self._button = digitalio.DigitalIO(seesaw, 24)

        self._encoder = rotaryio.IncrementalEncoder(seesaw)
        self._last_position = None


    def has_changed(self) -> bool:
        position = encoder.position

        if position != last_position:
            self._last_position = position
            return True

        return False

    
