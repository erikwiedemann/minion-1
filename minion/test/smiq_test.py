import numpy as np
import gpib
import time
import serial



res = 201   # max 4000
freqmin = 2.86*10**9
freqmax = 2.88*10**9
power = -10  # -144 to +16 - better btw. -100 and +10
dt = 0.10  # counttime
adt = 0.001  # microwave settling time


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

#connect fpga and smiq
counter = serial.Serial('/dev/ttyUSB3', baudrate=4000000, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1)
fpgaclock = 80*10**6  # in Hz
counttime_bytes = (int(0.005*fpgaclock)).to_bytes(4, byteorder='little')
counter.write(b'T'+counttime_bytes)  # set counttime at fpga
counter.write(b't')  # check counttime
check_counttime = int.from_bytes(counter.read(4), byteorder='little')/fpgaclock
print('\t fpga counttime:', check_counttime)
print('\t counter connected')

smiq = gpib.find('smiq06b')

# enable triggered counting
counterbins = res.to_bytes(2, byteorder='little')
counter.write(b'B'+counterbins)  #SetNumberOfTriggeredCountingBins

triggermask = 8
triggerinvertmask = 8
counter.write(b'M'+(8).to_bytes(1, byteorder='little'))  #SetTriggerMask
counter.write(b'Q'+(8).to_bytes(1, byteorder='little'))  #SetTriggerinvertedMask

counter.write(b'K'+(1).to_bytes(4, byteorder='little'))  #SetTriggeredCountingBinRepetitions

counter.write(b'0')  #ResetTriggeredCountingData
counter.write(b'R')  #EnableTriggeredCounting


try:
    gpib.write(smiq, '*RST') # nicht jedes mal machen - nur bei programmstart
    time.sleep(0.1)
    gpib.write(smiq, ':FREQ '+str(np.mean(freqlist)))
    gpib.write(smiq, ':POW '+str(np.mean(powerlist))+'dBm')


    gpib.write(smiq, ':LIST:DELETE:ALL')
    gpib.write(smiq, ':LIST:SELECT \'CWODMR\'')
    gpib.write(smiq, ':TRIG1:LIST:SOURCE SINGLE')  # single trigger an liste
    gpib.write(smiq, ':LIST:MODE AUTO')  # liste einmal durchfahren
    gpib.write(smiq, ':LIST:DWELL '+str(dt+adt))

    gpib.write(smiq, ':LIST:FREQ '+freqliststring)
    gpib.write(smiq, ':LIST:POW '+powerliststring)


    print('switching on microwave')
    gpib.write(smiq, ':OUTP:STATE 1')
    gpib.write(smiq, ':LIST:LEARN')
    gpib.write(smiq, ':FREQ:MODE LIST')
    gpib.write(smiq, '*WAI')
    time.sleep(1)
    # hier ab und zu fragen ob er die liste gelernt hat - erst wenn fertig und auf FREQ?

    gpib.write(smiq, ':TRIG:LIST')  # startet


except:
    print('oops - something went wrong')
    gpib.write(smiq, '*RST')
    gpib.close(smiq)

counter.write(b'd')  #ReadTriggeredCountingData
time.sleep(0.1)
data = counter.read(res*3*2)  #2=two apds, res=numbins, 3=? - why not 4?
print(data)
# disable triggered counting
counter.write(b'r')  #DisableTriggeredCounting
counter.close()