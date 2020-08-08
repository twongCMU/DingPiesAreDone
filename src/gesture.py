#!/usr/bin/python3

from apds9960.const import *
from apds9960 import APDS9960
import RPi.GPIO as GPIO
import smbus

from rangefinder import RangeFinder

from dingtimer import DingTimer as dt
import gevent

port = 1
bus = smbus.SMBus(port)

apds = APDS9960(bus)
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
    apds.enableGestureSensor(interrupts=False)
    while True:
        gevent.sleep(0.5)
        if apds.isGestureAvailable():
            motion = apds.readGesture()
            if motion == APDS9960_DIR_LEFT:
                mytimer.start_timer(60)
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
