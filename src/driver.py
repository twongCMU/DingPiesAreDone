#!/usr/bin/python3

#import gevent.monkey; gevent.monkey.patch_all()

from dingtimer import DingTimer as dt
import rainbowhat as rh
import time
import os
import gevent
from gevent.fileobject import FileObject

mytimer = dt()

pipein, pipeout = os.pipe()
pipein_fo = FileObject(pipein)

action = None

@rh.touch.A.press()
def touch_a(channel, b):
    global action
    a = "60\n".encode('utf-8')
    mytimer.timer_select(0)
    os.write(pipeout, a)

@rh.touch.B.press()
def touch_b(channel, b):
    global action
    a = "120\n".encode('utf-8')
    mytimer.timer_select(1)
    os.write(pipeout, a)

@rh.touch.C.press()
def touch_c(channel, c):
    global action
    #a = "4200\n".encode('utf-8')
    a = "600\n".encode('utf-8')
    mytimer.timer_select(2)
    os.write(pipeout, a)

while True:
    #if action:
    c = pipein_fo.readline()
    mytimer.start_timer(int(c))
