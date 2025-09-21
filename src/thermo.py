from knob import Knob
import adafruit_mlx90640
import board
import busio
import gevent
import time

class Thermo:
    def __init__(self, display, buzzer):
        # Knob 0x36 is the blue one in my configuration
        self._knob = Knob(0x36)
        self._unicorn = display
        
        # camera might pick up stuff outside of the heated surface; ignore
        # anything below this temp
        self._threshold_temp_c = self.f_to_c(100)

        # Thermo is enabled by a knob turn so the first temp displayed is
        # start_temp +- increment_temp not start_temp alone
        self._start_temp_f = 375
        self._increment_temp_f = 25
        self._timeout_secs = 2 # how long to wait to lock in final value

        # From the adafruit sample code
        i2c = busio.I2C(board.SCL, board.SDA, frequency=400000)
        self._mlx = adafruit_mlx90640.MLX90640(i2c)
        print("MLX addr detected on I2C", [hex(i) for i in self._mlx.serial_number])
        # To reduce the load on the hardware we use a low sample rate. For
        # cooking purposes, 2 frames per second should be plenty
        self._mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ

        self._buzzer = buzzer

        self._continue_thermo = None

    def f_to_c(self, f):
        return (f-32) * 5 / 9
        
    def do_thermo(self):
        """If knob has changed, run full thermo sequence,
        otherwise nothing"""

        if self._knob.get_changed() == 0:
            return

        target_temp_c = self.get_target_temp_c()
        #self.wait_for_target(target_temp_c)
        # Spawn a thread so that we can still create timers or cancel thermo from the caller
        gevent.spawn(self.wait_for_target, target_temp_c)

    def wait_for_target(self, target_temp_c):        
        frame_c = [0]*768
        threshold_met = False

        self._continue_thermo = True
        while self._continue_thermo:
            # Yield thread in case we want to start a timer too
            # This delay has a large effect on the CPU usage. On a pi zero w, 0.1 results
            # in CPU usage of 70-80%. 0.2 is 60-70%
            gevent.sleep(0.2) 
            try:
                self._mlx.getFrame(frame_c)
            except ValueError:
                continue

            print(f"Target temp {target_temp_c} C")

                       
            ### can trigger alarm if stat_done > stat_going I guess but might need to
            # trigger the alarm much earlier so I have time to get over to the stove
                        
            [stat_cold, stat_going, stat_done] = self._unicorn.show_thermo(frame_c, self._threshold_temp_c, target_temp_c)
            print(f"Stats: cold {stat_cold}, going {stat_going}, done {stat_done}, treshold {threshold_met}")
            
            if self._knob.is_button_pressed():
                print("Button is pressed")
                threshold_met = False
                break

        if threshold_met:
            done_r = gevent.spawn(self._unicorn.show_rainbow, 5)
            done_b = gevent.spawn(self._buzzer.play_timer_done)
            
            # Wait for alarm to be done before we clear the display state
            gevent.wait([done_r, done_b])
            
        self._unicorn.clear_display()

    def end_thermo(self):
        # This assumes the caller will yield the gevent thread so we don't do it here
        self._continue_thermo = False
        
    def get_target_temp_c(self) -> int:
        """Poll the knob for the target temp, returns integer temperature"""
        
        time_lastchanged = time.time()
        last_change_val = 0
        temperature = 0
        while (time.time() - time_lastchanged < self._timeout_secs):
            current_change_val = self._knob.get_changed()
            if current_change_val != last_change_val:
                time_lastchanged = time.time()

                temperature = self._start_temp_f + self._increment_temp_f*current_change_val
                print(f"{time_lastchanged}: {temperature}")
                self._unicorn.write_four(temperature)
                last_change_val = current_change_val
            time.sleep(.1)
        print(f"Final: {temperature}")
        self._unicorn.write_four(temperature)
        self._knob.reinit()

        return self.f_to_c(temperature)
