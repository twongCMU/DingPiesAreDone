import time
import RPi.GPIO as GPIO
import gevent

class Buzzer:
    # There's nothing special about the tones in this file; I just carried them over
    # from the previous version of this code I hacked together
    
    def __init__(self):
        triggerPin = 21 # this is how I soldered my buzzer to the raspberry pi
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(triggerPin, GPIO.OUT)
        
        self._buzzer = GPIO.PWM(triggerPin, 440)

        # To prematurely exit play_timer_done() if a button is pressed
        self._do_buzzer = True
        
    def play(self, freq, duration_sec):
        self._buzzer.start(90)
        self._buzzer.ChangeFrequency(freq)
        time.sleep(duration_sec)
        self._buzzer.stop()

    def play_start_timer(self):
        self.play(830.61, .2)

    def play_add_timer(self):
        self.play(261.63, .2)
        self.play(2637.02, .2)

    def play_subtract_timer(self):
        self.play(2637.02, .2)
        self.play(261.63, .2)

    def play_timer_oneminute_warning(self):
        self.play(261.63, 1)
        time.sleep(.5)
        self.play(261.63, 1)

    def play_timer_done(self):
        """We do this in a gevent thread so we can also draw on the screen"""

        # In case we pressed the button without a timer being done, reset this value before we start
        self._do_buzzer = True
        
        for i in range(40):
            if not self._do_buzzer:
                break
            self.play(261.63, .1)
            gevent.sleep(.001)
        for i in range(40):
            if not self._do_buzzer:
                break
            self.play(415.30, .1)
            gevent.sleep(.001)

        # Reset value for next time we call play_timer_done()
        self._do_buzzer = True

    def exit_play_timer_done(self):
        self._do_buzzer = False
            
