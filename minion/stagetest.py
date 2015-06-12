from ctypes import *

CDLL('libstdc++.so.6', mode=RTLD_GLOBAL)
# stagelib = CDLL('/usr/local/lib/libmadlib.so', 1)

stagelib = CDLL('/usr/lib/libmadlib.so', 1)
# define restypes that are not standard (INT)
stagelib.MCL_SingleReadN.restype = c_double
stagelib.MCL_MonitorN.restype = c_double


newposition = c_double(20)



stage = stagelib.MCL_InitHandle()
print(stage)
if stage == 0:
    print('cannot get a handle to the device')
else:
    stage.MCL_PrintDeviceInfo(stage)
    for axis in ['1', '2', '3']:
        position = stage.MCL_SingleReadN(axis, stage)
        print(axis, 'position in micron:', position)

# stage.MCL_ReleaseHandle(stage)





