import numpy as np
from ctypes import *
import time

CDLL('libstdc++.so.6', mode=RTLD_GLOBAL)
# stagelib = CDLL('/usr/local/lib/libmadlib.so', 1)

stagelib = CDLL('libmadlib.so', 1)
# define restypes that are not standard (INT)
stagelib.MCL_SingleReadN.restype = c_double
stagelib.MCL_MonitorN.restype = c_double
stagelib.MCL_GetCalibration.restype = c_double

xpos_new = c_double(20)
ypos_new = c_double(20)
zpos_new = c_double(20)
stage = stagelib.MCL_InitHandleOrGetExisting()
print(stage)



res = 5
zres = 5
xmin = 5.
xmax = 7.
ymin = 5.
ymax = 7.
zmin=1.
zmax=1.
dimension = 2
alignment = 'xy'

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
        for axis in [1, 2, 3]:
            position = stagelib.MCL_SingleWriteN(5.0, axis, stage)
            time.sleep(0.1)
        time.sleep(1)
        for axis in [1, 2, 3]:
            position = stagelib.MCL_SingleReadN(axis, stage)
            print(axis, 'position in micron:', position)
        time.sleep(1)

        for i in range(0, res**2):
            print(list1[0, i], list2[0, i], indexlist[0, i, 0], indexlist[0, i, 1])
            stagelib.MCL_SingleWriteN(list1[0, i], 0, stage)


stagelib.MCL_ReleaseHandle(stage)
