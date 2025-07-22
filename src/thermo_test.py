from thermo import Thermo
import time

t = Thermo()

while(1):
    print("Starting")
    t.do_thermo()

    time.sleep(.1)
    
