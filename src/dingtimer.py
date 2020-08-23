#!/usr/bin/python3

import time
import rainbowhat as rh
import gevent
import sys
import math

TIMER_NUMBER = 3
TIMER_MAX_ID = 2
TIMER_BOGUS_ID = TIMER_MAX_ID + 1
class DingTimer:

    def __init__(self):
        """this code was developed for 3 timers due to the hardware I was using
        """
        # each timer is a tuple of muted T/F, the end time, and the gevent handle
        self._timer_list = [(False, 0, None)] * TIMER_NUMBER

        # start with left timer
        self._current_timer = 0 

    def start_timer(self, seconds: int):
        ret = self.get_free_timer()
        
        # if there are no timers available, make a noise
        if ret is None:
            rh.buzzer.midi_note(68, .5)
            gevent.sleep(.5)
            rh.buzzer.midi_note(60, .5)
            return

        print("Using timer " + str(ret))
        # make a noise just to have an auditory indication
        rh.buzzer.midi_note(80, .2)

        # spawn a timer async so that we can spawn new timers while that is running
        event = gevent.spawn(self._one_timer, seconds, self._current_timer)

        # update accounting then display timer LED
        self._timer_list[self._current_timer] = (False, time.time() + seconds, event)
        self._set_active_timer_rainbow()
        
        # print the timer here and block-sleep so even if another timer is
        # active we see the time for a moment before the other timer continues to be shown
        self._print_timer(seconds)
        time.sleep(.5)

        # resume showing the timer that is closest to finishing
        # (which might not be this timer)
        self.show_closest_timer()

    def timer_right(self):
        """Switch to the timer to the right of the current one, if possible
        """
        self.timer_select(self._current_timer + 1)
        self.illuminate_timer()
        
    def timer_left(self):
        """Switch to the timer to the left of the current one, if possible
        """
        self.timer_select(self._current_timer - 1)
        self.illuminate_timer()

    def timer_select(self, t: int):
        """Switch to a specific timer

        Parameters:
          t (int) the timer to use
        """
        if t < 0:
            self._current_timer = 0
        elif t > 2:
            self._current_timer = 2
        else:
            self._current_timer = t

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
        
    def illuminate_timer(self):
        if self._current_timer == 0:
            rh.lights.rgb(1, 0, 0)
        if self._current_timer == 1:
            rh.lights.rgb(0, 1, 0)
        if self._current_timer == 2:
            rh.lights.rgb(0, 0, 1)
      

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
        for i in range(3):
            (muted, end_time, event) = self._timer_list[i]
            if end_time > t:
                rh.rainbow.set_pixel(6-(i*3), 50, 50, 50)
            else:
                rh.rainbow.set_pixel(6-(i*3), 0, 0, 0)
        rh.rainbow.show()
        
    def _clear_timer(self, id: int):
        self._timer_list[id] = (False, 0, None)

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

        for i in range(3):
            (muted, end_time, event) = self._timer_list[i]
            if end_time > cur_time and end_time < closest_time:
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
            rh.display.clear()
            rh.display.show()
            return
        
        for i in range(3):
            if i == closest_id:
                self._unmute_timer(i)
                self._current_timer = i
            else:
                self._mute_timer(i)

    def _print_timer(self, seconds: int):
        m = int(seconds/60.0)
        s = seconds % 60
        s_print = str(s)
        if s < 10:
            s_print = "0" + str(s)
        m_print = str(m)
        if len(m_print) == 1:
            m_print = " " + m_print
        if m == 0:
            rh.display.print_str("  " + s_print)
        else:
            rh.display.print_str(m_print + s_print)
        rh.display.show()
            
    def _one_timer(self, seconds: int, timer_id: int):
        cur_time = time.time()
        end_time = cur_time + seconds
        warning_sent = False
        if seconds < 60:
            warning_sent = True
        while cur_time < end_time:
            if not self._is_timer_muted(timer_id):
                time_left = math.ceil(end_time - cur_time)
                self._print_timer(time_left)

                if time_left <= 60 and not warning_sent:
                    rh.buzzer.midi_note(60, 1)
                    gevent.sleep(.5)
                    rh.buzzer.midi_note(60, 1)
                    warning_sent = True
            gevent.sleep(.5)
            cur_time = time.time()

        rh.display.print_str("  00")
        rh.display.show()
        
        # this timer is done. Show another timer if needed
        # while the alarm goes off
        self.show_closest_timer()
        
        # it's possible to light the rainbow here while another timer
        # is also doing so but I think we can blame the user it they set
        # multiple timers to end at the same time
        rh.rainbow.set_all(255,255,255)
        rh.rainbow.show()
        rh.buzzer.midi_note(60, 5)
        rh.buzzer.midi_note(68, 5)
        rgb_r = 255
        rgb_g = 255
        rgb_b = 0
        for _ in range(50):
            temp = rgb_r
            rgb_r = rgb_g
            rgb_g = rgb_b
            rgb_b = temp
            rh.rainbow.set_all(rgb_r, rgb_g, rgb_b)
            rh.rainbow.show()
            gevent.sleep(.1)

        rh.rainbow.clear()
        rh.rainbow.show()
        rh.display.clear()
        rh.display.show()

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
        
        
