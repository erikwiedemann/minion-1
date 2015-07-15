import numpy as np
import gpib
import time




res = 201
freqmin = 2.8*10**9
freqmax = 2.84*10**9
power = -10  # -144 to +16 - better btw. -100 and +10
dt = 0.005  # counttime
adt = 0.01  # microwave settling time


freqlist = np.array(np.linspace(freqmin, freqmax, res))
# freqlistreversed = freqlist[::-1]
freqliststring = ', '.join(np.char.mod('%d', freqlist))
# freqlistreversedstring = ', '.join(np.char.mod('%d', freqlistreversed))
powerlist = np.ones(res)*power
powerliststring = 'dBm, '.join(np.char.mod('%d', powerlist))
print(freqliststring)
print(powerliststring)
# print(freqlistreversedstring)
print(':FREQ '+str(np.mean(freqlist)))
print(':POW '+str(np.mean(powerlist))+'dBm')


smiq = gpib.find('smiq06b')

try:
    gpib.write(smiq, '*RST')
    time.sleep(0.1)
    gpib.write(smiq, ':FREQ '+str(np.mean(freqlist)))
    gpib.write(smiq, ':POW '+str(np.mean(powerlist))+'dBm')


    gpib.write(smiq, ':LIST:DELETE:ALL')
    gpib.write(smiq, ':LIST:SELECT \'CWODMR\'')
    gpib.write(smiq, ':TRIG1:LIST:SOURCE SINGLE')
    gpib.write(smiq, ':LIST:MODE AUTO')
    gpib.write(smiq, ':LIST:DWELL '+str(dt+adt))

    gpib.write(smiq, ':LIST:FREQ '+freqliststring)
    gpib.write(smiq, ':LIST:POW '+powerliststring)

    print('switching on microwave')
    gpib.write(smiq, ':OUTP:STATE 1')
    gpib.write(smiq, ':LIST:LEARN')
    gpib.write(smiq, ':FREQ:MODE LIST')
    gpib.write(smiq, '*WAI')


except:
    print('oops - something went wrong')
    gpib.write(smiq, '*RST')
    gpib.close(smiq)


