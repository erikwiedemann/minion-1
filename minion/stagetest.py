from ctypes import *

CDLL('libstdc++.so.6', mode=RTLD_GLOBAL)
# stagelib = CDLL('/usr/local/lib/libmadlib.so', 1)

stagelib = CDLL('/usr/lib/libmadlib.so', 1)
# define restypes that are not standard (INT)
stagelib.MCL_SingleReadN.restype = c_double
stagelib.MCL_MonitorN.restype = c_double
stagelib.MCL_GetCalibration.restype = c_double


xpos_new = c_double(20)
ypos_new = c_double(20)
zpos_new = c_double(20)

stage = stagelib.MCL_InitHandle()
print(stage)
if stage == 0:
    print('cannot print device info')
else:
    stage.MCL_PrintDeviceInfo(stage)

# get range
if stage == 0:
    print('cannot get a handle to the device')
else:
    for axis in ['1', '2', '3']:
        range = stage.MCL_GetCalibration(axis, stage)
        print(axis, 'range in micron:', range)


# get current position
if stage == 0:
    print('cannot get a handle to the device')
else:
    for axis in ['1', '2', '3']:
        position = stage.MCL_SingleReadN(axis, stage)
        print(axis, 'position in micron:', position)

# stage.MCL_ReleaseHandle(stage)





