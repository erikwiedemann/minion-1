import serial
import time
counter = serial.Serial('/dev/ttyUSB2', baudrate=4000000, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1)

countername = 'Profilic Technology Inc.  USB-Serial Controller D'

fpgaclock = 80*10**6
counttime = 0.005  # in s
counttime_bytes = (int(counttime*fpgaclock)).to_bytes(4, byteorder='little')
print(counttime_bytes)
counter.write(b'T'+counttime_bytes)
counter.write(b't')
dt_bytes = counter.read(4)
dt = int.from_bytes(dt_bytes, byteorder='little')/fpgaclock
print(dt)
for i in range(10):
    counter.write(b'C')
    time.sleep(counttime*1.1)
    answer = counter.read(8)
    apd1 = answer[:4]
    apd2 = answer[4:]
    apd1_count = int.from_bytes(apd1, byteorder='little')
    apd2_count = int.from_bytes(apd2, byteorder='little')
    print(apd1_count, apd2_count)

counter.close()
print(counter)
