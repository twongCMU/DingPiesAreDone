#!/usr/bin/python3

import time
#import rainbowhat as rh
from unicorn_mini import Unicorn
from buzzer import Buzzer
import gevent
import sys
import math
import RPi.GPIO as GPIO

TIMER_NUMBER = 3
TIMER_MAX_ID = 2
TIMER_BOGUS_ID = TIMER_MAX_ID + 1
class DingTimer:

    def __init__(self, display, buzzer):
        """this code was developed for 3 timers due to the hardware I was using
        """
        # each timer is a tuple of muted T/F, the end time, and the gevent handle
        self._timer_list = [(False, 0, None)] * TIMER_NUMBER

        # start with left timer
        self._current_timer = 0 

        self._unicorn = display
        self._buzzer = buzzer

    def start_timer(self, seconds: int):
        ret = self.get_free_timer()
        
        # if there are no timers available, make a noise
        if ret is None:
            self._buzzer.start(90)
            self._buzzer.ChangeFrequency(415.30)
            #rh.buzzer.midi_note(68, .5)
            time.sleep(.5)
            #rh.buzzer.midi_note(60, .5)
            self._buzzer.ChangeFrequency(261.63)
            time.sleep(.5)
            self._buzzer.stop()
            return

        print("Using timer " + str(ret))
        # make a noise just to have an auditory indication
        self._buzzer.play_start_timer()
        #rh.buzzer.midi_note(80, .2)

        mute_timer = False
        if seconds <= 60:
            mute_timer = True

        # partially update accounting so the gevent has it
        self._timer_list[self._current_timer] = (mute_timer, time.time() + seconds, None)
        
        # spawn a timer async so that we can spawn new timers while that is running
        event = gevent.spawn(self._one_timer,self._current_timer)

        # update accounting then display timer LED
        self._timer_list[self._current_timer] = (mute_timer, time.time() + seconds, event)
        self._set_active_timer_rainbow()

        # print the timer here and block-sleep so even if another timer is
        # active we see the time for a moment before the other timer continues to be shown
        self._print_timer(seconds)
        time.sleep(.5)

        # resume showing the timer that is closest to finishing
        # (which might not be this timer)
        self.show_closest_timer()

    def add_time(self, amount):
        # There might be a race here if a timer ends just as we add time to it
        (muted, end_time, event) = self._timer_list[self._current_timer]
        end_time += amount
        if end_time-time.time() > 60 and muted:
            muted = False
        self._timer_list[self._current_timer] = (muted, end_time, event)

        self._buzzer.play_add_timer()
        #rh.buzzer.midi_note(60, .2)
        #gevent.sleep(.2)
        #rh.buzzer.midi_note(100, .2)

        # This might make this timer longer than another one where we should call show_closest_timer
        # except then we can't continue to add time to this current timer so we don't do that.
        # It is rare that I use multiple timers and even more rare that I would add enough time
        # in this way to make them conflict so I'll just let this case occur rather than trying
        # to solve it
        
    def subtract_time(self, amount):
        # There might be a race here if a timer ends just as we subtract time from it
        (muted, end_time, event) = self._timer_list[self._current_timer]
        end_time -= amount
        if end_time-time.time() < 60 and not muted:
            muted = True
        self._timer_list[self._current_timer] = (muted, end_time, event)

        self._buzzer.play_subtract_timer()
        #rh.buzzer.midi_note(100, .2)
        #gevent.sleep(.2)
        #rh.buzzer.midi_note(60, .2)
        # see big comment in add_time

    def get_free_timer(self):
        """Find a free timer slot and set it as the current timer
        if there is one

        Returns:
          a free timer slot ID or None
        """
        cur_time = time.time()
        for i in range(TIMER_NUMBER):
            (m, t, e) = self._timer_list[i]
            print("checking timer " + str(i) + " with time " + str(t))
            if t < cur_time:
                print("looks good")
                self._current_timer = i
                return i
        return None
        
    def _set_active_timer_rainbow(self):
        """ Light the LEDs for active timer
        An active timer is one that is counting down and not done yet
        
        Having a function to set all at once is useful because the
        lights are used for other things so this can recreate the proper
        state
        
        Note that the rainbow LEDs are numbered right to left but our
        timers are labeled left to right so we have to be sure to set 
        the right pixel
        """
        t = time.time()
        active_list = []
        for i in range(3):
            (muted, end_time, event) = self._timer_list[i]        
            if end_time > t:
                active_list.append(True)
            else:
                active_list.append(False)
        self._unicorn.set_active_timers(active_list)
        
    def _clear_timer(self, id: int):
        self._timer_list[id] = (False, 0, None)

    def _get_timer_end_time(self, id:int):
        (ignore, endtime, event) = self._timer_list[id]
        return endtime

    def _is_timer_muted(self, id: int):
        (muted, ignore, event) = self._timer_list[id]
        return muted

    def _mute_timer(self, id: int):
        print("muting " + str(id))
        (ignore, end_time, event) = self._timer_list[id]
        self._timer_list[id] = (True, end_time, event)

    def mute_all(self):
        for i in range(3):
            self._mute_timer(i)

    def _unmute_timer(self, id: int):
        print("unmuting " + str(id))
        (ignore, end_time, event) = self._timer_list[id]
        self._timer_list[id] = (False, end_time, event)

    def active_timer_count(self):
        count = 0

        cur_time = time.time()
        for i in range(3):
            (muted, end_time, event) = self._timer_list[i]
            if end_time > cur_time:
                count += 1

        return count
                
    def show_closest_timer(self):
        closest_id = TIMER_BOGUS_ID
        closest_time = sys.maxsize
        cur_time = time.time()
        
        for i in range(3):
            (muted, end_time, event) = self._timer_list[i]
            if end_time > cur_time and end_time < closest_time:
                print("Timer " + str(i) + " looks good")
                closest_id = i
                closest_time = end_time

        if closest_id == TIMER_BOGUS_ID:
            print("No timer to show")
            self._unicorn.clear_numbers()
            return
        
        for i in range(3):
            if i == closest_id:
                self._current_timer = i

    def _print_timer(self, seconds: int):
        m = int(seconds/60.0)
        s = seconds % 60
        s_print = str(s)
        if s < 10:
            s_print = "0" + str(s)
        m_print = str(m)

        if m == 0:
            self._unicorn.write_four(s_print)
        else:
            self._unicorn.write_four(m_print + s_print)


    def _one_timer(self, timer_id: int):
        cur_time = time.time()

        #warning_sent = False
        #if self._get_timer_end_time(timer_id) - cur_time < 60:
        #    warning_sent = True
        #    print("setting warning set to true")
        while cur_time < self._get_timer_end_time(timer_id):
            print(f"cur timer is {self._current_timer}")
            if self._current_timer == timer_id:
                time_left = math.ceil(self._get_timer_end_time(timer_id) - cur_time)
                self._print_timer(time_left)
                #print(f"warning sent {warning_sent}")
                if not self._is_timer_muted(timer_id) and time_left <= 60:
                    self._buzzer.play_timer_oneminute_warning()
                    #rh.buzzer.midi_note(60, 1)
                    #gevent.sleep(.5)
                    #rh.buzzer.midi_note(60, 1)
                    #warning_sent = True

                    # Mute the timer
                    self._mute_timer(timer_id)
                    
            gevent.sleep(.5)
            cur_time = time.time()

        self._unicorn.write_four("00")
        
        # this timer is done. Show another timer if needed
        # while the alarm goes off
        self.show_closest_timer()
        
        # it's possible to light the rainbow here while another timer
        # is also doing so but I think we can blame the user it they set
        # multiple timers to end at the same time
        #rh.rainbow.set_all(255,255,255)
        #rh.rainbow.show()
        gevent.spawn(self._unicorn.show_rainbow, 5)
        gevent.spawn(self._buzzer.play_timer_done)
        #rh.buzzer.midi_note(60, 5)
        #rh.buzzer.midi_note(68, 5)
        rgb_r = 255
        rgb_g = 255
        rgb_b = 0
        """
        for _ in range(50):
            temp = rgb_r
            rgb_r = rgb_g
            rgb_g = rgb_b
            rgb_b = temp
            #rh.rainbow.set_all(rgb_r, rgb_g, rgb_b)
            #rh.rainbow.show()
            gevent.sleep(.1)
        """

        #rh.rainbow.clear()
        #rh.rainbow.show()
        self._unicorn.clear_numbers()

        # we just lit the rainbow for the timer finishing so
        # reset the rainbow to show active timers
        self._set_active_timer_rainbow()

    def cancel_timer(self):
        """Cancel the current timer
        """
        (m, t, event) = self._timer_list[self._current_timer]
        if event is not None:
            event.kill()
        self._timer_list[self._current_timer] = (True, 0, None)
        self._set_active_timer_rainbow()
        self.show_closest_timer()
        
        
