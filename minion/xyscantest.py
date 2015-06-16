import numpy as np
from ctypes import *
import time
import serial
import matplotlib.pylab as plt
counter = serial.Serial('/dev/ttyUSB1', baudrate=4000000, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1)
fpgaclock = 80*10**6
counttime = 0.005  # in s
counttime_bytes = (int(counttime*fpgaclock)).to_bytes(4, byteorder='little')
counter.write(b'T'+counttime_bytes)
counter.write(b't')
dt_bytes = counter.read(4)
dt = int.from_bytes(dt_bytes, byteorder='little')/fpgaclock
print(dt)


res = 21
zres = 5
xmin = 5.
xmax = 10.
ymin = 5.
ymax = 10.
zmin=1.
zmax=1.
dimension = 2
alignment = 'xy'


scanmat = np.zeros((res, res))

CDLL('libstdc++.so.6', mode=RTLD_GLOBAL)
# stagelib = CDLL('/usr/local/lib/libmadlib.so', 1)

stagelib = CDLL('libmadlib.so', 1)
# define restypes that are not standard (INT)
stagelib.MCL_SingleReadN.restype = c_double
stagelib.MCL_MonitorN.restype = c_double
stagelib.MCL_GetCalibration.restype = c_double


stage = stagelib.MCL_InitHandleOrGetExisting()
print(stage)





if stage==0:
    print('cannot get a handle to the device')
else:
    if dimension == 2:
        mat = np.zeros((res, res, 2))  # preallocate

        dim1 = np.linspace(xmin, xmax, res)  # 1-x
        dim2 = np.linspace(ymin, ymax, res)  # 2-y

        mat[:, :, 0] = dim1
        mat[1::2, :, 0] = np.fliplr(mat[1::2, :, 0])  # mirror the odd rows such that the scan goes like a snake
        mat[:, :, 1] = dim2
        mat[:, :, 1] = mat[:, :, 1].T

        list1 = np.reshape(mat[:, :, 0], (1, res**2))
        list2 = np.reshape(mat[:, :, 1], (1, res**2))

        indexmat = np.indices((res, res))  # 0-x, 1-y,
        indexmat = np.swapaxes(indexmat, 0, 2)

        indexmat[1::2, :, :] = np.fliplr(indexmat[1::2, :, :])
        indexlist = indexmat.reshape((1, res**2, 2))

        print('go to start position')
        status1 = stagelib.MCL_SingleWriteN(c_double(5.0), 1, stage)
        time.sleep(0.01)
        status2 = stagelib.MCL_SingleWriteN(c_double(5.0), 2, stage)
        time.sleep(0.01)
        pos1 = stagelib.MCL_SingleReadN(1, stage)
        pos2 = stagelib.MCL_SingleReadN(2, stage)
        print(pos1, pos2)
        time.sleep(1)

        for i in range(0, res**2):
            if i%res ==0:
                print(i/(res**2))
            # print('index : ', indexlist[0, i, 0], indexlist[0, i, 1])
            status0 = stagelib.MCL_SingleWriteN(c_double(list1[0, i]), 1, stage)
            status1 = stagelib.MCL_SingleWriteN(c_double(list2[0, i]), 2, stage)
            time.sleep(0.02)

            pos1 = stagelib.MCL_SingleReadN(1, stage)
            pos2 = stagelib.MCL_SingleReadN(2, stage)
            # print('pos error', pos1-list1[0, i], pos2-list2[0, i])

            counter.write(b'C')
            time.sleep(counttime*1.1)
            answer = counter.read(8)
            apd1 = answer[:4]
            apd2 = answer[4:]
            apd1_count = int.from_bytes(apd1, byteorder='little')
            apd2_count = int.from_bytes(apd2, byteorder='little')
            # print('counts:',apd1_count, apd2_count)

            scanmat[indexlist[0, i, 0], indexlist[0, i, 1]] = apd1_count + apd2_count

plt.matshow(scanmat)
plt.show()
counter.close()
print(counter)

stagelib.MCL_ReleaseHandle(stage)
