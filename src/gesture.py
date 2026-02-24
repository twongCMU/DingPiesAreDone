#!/usr/bin/python3

#from adafruit_apds9960.apds9960 import APDS9960
from apds9960.const import *
from apds9960 import APDS9960
import RPi.GPIO as GPIO
import smbus

from buzzer import Buzzer
from dingtimer import DingTimer as dt
from knob import Knob
from thermo import Thermo
from unicorn_mini import Unicorn

import RPi.GPIO as GPIO

import board
import eventlet
import gevent
import socketio
import threading
import time

"""
APDS9960_DIR_NONE = 0
APDS9960_DIR_UP = 1
APDS9960_DIR_DOWN = 2
APDS9960_DIR_LEFT = 3
APDS9960_DIR_RIGHT = 4
APDS9960_DIR_NEAR = 5
APDS9960_DIR_FAR = 6

port = 1
i2c = board.I2C()
apds = APDS9960(i2c, rotation=270)

apds.enable_gesture = True
apds.enable_proximity = True
#apds.gesture_gain = 3 # from the docs: 0=1x, 1=2x, 2=4x, 3=8x
"""

port = 1
bus = smbus.SMBus(port)
apds = APDS9960(bus)

unicorn = Unicorn()
buzzer = Buzzer()
mytimer = dt(unicorn, buzzer)

global pending_timer
pending_timer = -1
global silence_alarm
silence_alarm = False

# A dang server to hecking allow for remote thingies to start timers or silence them
sio = socketio.Server()
app = socketio.WSGIApp(sio, static_files={
        '/': {'content_type': 'text/html', 'filename': 'index.html'}
    })

@sio.event
def connect(sid, environ):
    print(f"Got remote io connection from {sid}")

@sio.event
def add_new_timer(sid, time_seconds):
    print(f"Got request to add new timer")
    global pending_timer
    pending_timer = time_seconds
        
@sio.event
def silence_alarm(sid):
    print(f"Got request to silence alarm")
    global silence_alarm
    silence_alarm = True


def serve_app(sio, app):
    app = socketio.Middleware(sio, app)
    eventlet.wsgi.server(eventlet.listen(('192.168.1.213', 5000)), app)
    
wst = threading.Thread(target=serve_app, args=(sio,app))
wst.daemon = True
wst.start()
print("Daemon started")
    
# for my hardware this is the black knob
# Used to set timer input. This is separate from the knob for thermo input
k = Knob(0x37)

t = Thermo(unicorn, buzzer)

dirs = {
    APDS9960_DIR_NONE: "none",
    APDS9960_DIR_LEFT: "left",
    APDS9960_DIR_RIGHT: "right",
    APDS9960_DIR_UP: "up",
    APDS9960_DIR_DOWN: "down",
    APDS9960_DIR_NEAR: "near",
    APDS9960_DIR_FAR: "far",
}

def get_target_time_minutes(knob) -> int:
    """Poll the knob for the number of minutes

    I don't need this yet but we can use the knob pushbutton for something like
    adding 30 seconds or instantly locking in the selection """

    timeout_secs = 2 # how long to wait before locking in selection
    start_minutes = 1 # initial number of minutes when starting a timer via knob input
    
    time_lastchanged = time.time()
    last_change_val = 0
    target_minutes = 0
    while (time.time() - time_lastchanged < timeout_secs):
        current_change_val = knob.get_changed()
        if current_change_val != last_change_val:
            time_lastchanged = time.time()

            target_minutes = start_minutes + current_change_val
            print(f"{time_lastchanged}: {target_minutes}")
            unicorn.write_four(str(target_minutes)+"00")
            last_change_val = current_change_val
        time.sleep(.1)
    print(f"Timer knob Final: {target_minutes}")
    unicorn.write_four(str(target_minutes)+"00")
    knob.reinit()

    return target_minutes

try:
    apds.enableGestureSensor(interrupts=False)
 
    while True:
        #print("Looping")
        # don't poll too often so we don't waste power
        gevent.sleep(0.2)

        # check if there is a request for the temperature alarm
        t.do_thermo()

        # If the knob is pressed, silence the alarm for timer-end
        if k.is_button_pressed() or silence_alarm:
            unicorn.exit_rainbow()
            buzzer.exit_play_timer_done()
            silence_alarm = False
            
        # check if there is a request for the long timer via knob
        if k.get_changed() != 0:
            print(f"knob changed")
            mytimer.mute_all()
            target_time_minutes = get_target_time_minutes(k)
            mytimer.start_timer(target_time_minutes*60)

        if pending_timer > 0:
            mytimer.start_timer(pending_timer)
            pending_timer = -1
               
        # check if there is a request for timer via gesture
        # Warning: for some reason this hangs if there is something in close proximity
        # so when testing make sure there is nothing in front of it
        motion = APDS9960_DIR_NONE
        if apds.isGestureAvailable():
            motion = apds.readGesture()

        if motion != APDS9960_DIR_NONE:
            if motion == APDS9960_DIR_RIGHT:
                # Add one minute if there is a timer, start a 1 minute timer if not
                if mytimer.active_timer_count() == 0:
                    mytimer.start_timer(60)
                else:
                    mytimer.add_time(60)
            elif motion == APDS9960_DIR_LEFT:
                # Subtract one minute if there is an active timer
                if mytimer.active_timer_count() > 0:
                    mytimer.subtract_time(60)
            elif motion == APDS9960_DIR_UP:
                t.end_thermo()
            elif motion == APDS9960_DIR_DOWN:
                mytimer.cancel_timer()

            print("Gesture={}".format(dirs.get(motion, "unknown")))

finally:
    GPIO.cleanup()
    print("Bye")
