#!/usr/bin/python3

from adafruit_apds9960.apds9960 import APDS9960
import RPi.GPIO as GPIO

from rangefinder import RangeFinder

from dingtimer import DingTimer as dt
import gevent
import board

APDS9960_DIR_NONE = 0
APDS9960_DIR_UP = 1
APDS9960_DIR_DOWN = 2
APDS9960_DIR_LEFT = 3
APDS9960_DIR_RIGHT = 4
APDS9960_DIR_NEAR = 5
APDS9960_DIR_FAR = 6

port = 1

i2c = board.I2C()
apds = APDS9960(i2c)
apds.enable_gesture = True
apds.enable_proximity = True

mytimer = dt()

dirs = {
    APDS9960_DIR_NONE: "none",
    APDS9960_DIR_LEFT: "left",
    APDS9960_DIR_RIGHT: "right",
    APDS9960_DIR_UP: "up",
    APDS9960_DIR_DOWN: "down",
    APDS9960_DIR_NEAR: "near",
    APDS9960_DIR_FAR: "far",
}

try:

    while True:
        gevent.sleep(0.2)
        motion = apds.gesture()
        print(f"got {motion}")
        if motion != APDS9960_DIR_NONE:
            # Note: the sensor is mounted upside-down in my device so these are all reversed
            if motion == APDS9960_DIR_LEFT:
                # Add one minute if there is a timer, start a 1 minute timer if not
                if mytimer.active_timer_count() == 0:
                    mytimer.start_timer(60)
                else:
                    mytimer.add_time(60)
            elif motion == APDS9960_DIR_RIGHT:
                # Subtract one minute if there is an active timer
                if mytimer.active_timer_count() > 0:
                    mytimer.subtract_time(60)
                    
            elif motion == APDS9960_DIR_UP:
                mytimer.cancel_timer()
            elif motion == APDS9960_DIR_DOWN:
                mytimer.mute_all()
                rf = RangeFinder()
                minutes = rf.get_time()
                if minutes is not None:
                    mytimer.start_timer(minutes*60)
                else:
                    mytimer.show_closest_timer()
            print("Gesture={}".format(dirs.get(motion, "unknown")))


finally:
    GPIO.cleanup()
    print("Bye")
