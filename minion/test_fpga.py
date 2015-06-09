import serial
import time
counter = serial.Serial('/dev/ttyUSB1', baudrate=4000000, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1)

for i in range(10):
    counter.write(b'C')
    time.sleep(0.01)
    answer = counter.read(8)
    apd1 = answer[:4]
    apd2 = answer[4:]
    print(str(apd1)+'\t'+str(apd2))
    apd1_count = int.from_bytes(apd1, byteorder='little')
    apd2_count = int.from_bytes(apd2, byteorder='little')
    print(apd1_count, apd2_count)

counter.close()
print(counter)