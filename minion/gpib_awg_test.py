import gpib
import time

def query(handle, command, numbytes=100):
    gpib.write(handle,command)
    time.sleep(0.1)
    response = gpib.read(handle,numbytes)
    return response

awg = gpib.find('awg520')
try:
    identity = query(awg, '*IDN?')
    print(identity.decode('utf-8'))

    answer = query(awg, "SOURce:VOLTage:AMPLitude?")
    print(float(answer))

    gpib.close(awg)
except:
    print('oops')
    gpib.close(awg)
