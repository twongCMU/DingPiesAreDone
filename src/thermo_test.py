from thermo import Thermo
import gevent

t = Thermo()

while(1):
    print("Starting")
    t.do_thermo()

    gevent.sleep(.1)
    
