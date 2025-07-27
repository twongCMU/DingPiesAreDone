from buzzer import Buzzer
from knob import Knob
from unicorn_mini import Unicorn
import adafruit_mlx90640
import board
import busio
import gevent
import time

class Thermo:
    def __init__(self):
        self._knob = Knob()
        self._unicorn = Unicorn()
        
        # camera might pick up stuff outside of the heated surface; ignore
        # anything below this temp
        self._threshold_temp = 150
        
        self._start_temp = 350
        self._increment_temp = 25
        self._timeout_secs = 2 # how long to wait to lock in final value

        # From the adafruit sample code
        i2c = busio.I2C(board.SCL, board.SDA, frequency=400000)
        self._mlx = adafruit_mlx90640.MLX90640(i2c)
        print("MLX addr detected on I2C", [hex(i) for i in self._mlx.serial_number])
        # To reduce the load on the hardware we use a low sample rate. For
        # cooking purposes, 2 frames per second should be plenty
        self._mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ

        self._buzzer = Buzzer()
    def do_thermo(self):
        """If knob has changed, run full thermo sequence,
        otherwise nothing"""

        if self._knob.get_changed() == 0:
            return

        target_temp = self.get_target_temp()
        self.wait_for_target(target_temp)

    def wait_for_target(self, target_temp):
        frame = [0]*768
        while True:
            try:
                self._mlx.getFrame(frame)
            except ValueError:
                continue

            print(f"Target temp {target_temp}")
            ready = True
            threshold_met = False
            for h in range(24):
                for w in range(32):
                    t = (frame[h*32 + w]*9/5)+32
                    print("%0.1f, " % t, end="")
                    if t > self._threshold_temp and t < target_temp:
                        ready = False

                    # In case everything is below the threshold
                    if t > self._threshold_temp:
                        threshold_met = True
                        
                print()
            print()
            print(f"Threshold_met {threshold_met} ready {ready}")
            if threshold_met and ready:
                break

            break

        print("OOOOO")
        gevent.spawn(self._unicorn.show_rainbow, 5)
        gevent.spawn(self._buzzer.play_timer_done)
        print("DONEEEEE")

    def get_target_temp(self) -> int:
        """Poll the knob for the target temp, returns integer temperature"""
        
        time_lastchanged = time.time()
        last_change_val = 0
        temperature = 0
        while (time.time() - time_lastchanged < self._timeout_secs):
            current_change_val = self._knob.get_changed()
            if current_change_val != last_change_val:
                time_lastchanged = time.time()

                temperature = self._start_temp + self._increment_temp*last_change_val
                print(f"{time_lastchanged}: {temperature}")
                self._unicorn.write_four(temperature)
                last_change_val = current_change_val
            time.sleep(.1)
        print(f"Final: {temperature}")
        self._unicorn.write_four(temperature)
        self._knob.reinit()

        return temperature
