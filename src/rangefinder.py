import time
import gevent
import rainbowhat as rh
import qwiic

class RangeFinder:
    def __init__(self):
        self._tof = qwiic.QwiicVL53L1X()
        if self._tof.sensor_init() is None:
            print("Sensor online!\n")

    def get_time(self) -> int:

        rh.display.print_str("  GO")
        rh.display.show()
        gevent.sleep(.20)
        ret_minutes = 0
        ret_consecutive = 0
        start_time = time.time()
        while True:
            try:
                self._tof.start_ranging()
                time.sleep(.005)
                distance = self._tof.get_distance()
                time.sleep(.005)
                self._tof.stop_ranging()

                # input is in mm
                distance_inches = distance / 25.4
                distance_feet = distance_inches / 12.0

                # if we do nothing, time-out and return
                if time.time() - start_time > 10.0:
                    return None
                if distance_feet > 5.58 or distance_feet < .5:
                    rh.display.print_str("----")
                    rh.display.show()
                    continue

                minutes = int(round((distance_feet - .5) * 4))
                if minutes < 10:
                    rh.display.print_str("000" + str(minutes))
                else:
                    rh.display.print_str("00" + str(minutes))
                rh.display.show()
                if ret_minutes == minutes:
                    ret_consecutive += 1
                    if ret_consecutive > 15:
                        break
                else:
                    ret_minutes = minutes
                    ret_consecutive = 0

                #print("minutes: " + str(minutes))
                #print("Distance(mm): %s Distnance(ft): %s" % (distance, distance_feet))
                gevent.sleep(.05)
            except Exception as e:
                print(e)

        return minutes
