import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import os
import time

os.chdir('/home/michael/Dropbox/NFP/2015/MASTERARBEIT/minion/minion/data')

data = np.loadtxt('kandidat_für_odmr_nahaufname.txt')

stepsize_corse = 5 # um - change to 0.05
stepsize_fine = 1  # um
stepsize_restart = 3  # um
restart_max = 2
counttime = 0.01  # s
settletime = 0.005  # s

# backup values
init_coord = [10, 40, 25]  # current stage pos
init_node = data[init_coord[0], init_coord[1]]  # for reference

def measure(x,y):
    return data[int(x), int(y)]  # add 3d - remove int


fig = plt.figure()
ax = fig.gca()
ax.matshow(data, origin = 'lower')

kernel = np.zeros((3, 3))  # preallocate - add 3d
# measure adjacent coords
current_node = init_node
current_coord = init_coord
new_node = current_node
new_coord = [0, 0, 0]
success = False
number_restarts = 0
run_number = 0
while success is not True:
    run_number += 1
    for (i, j), value in np.ndenumerate(kernel):
        new_coord = [current_coord[0]+(i-1)*stepsize_corse, current_coord[1]+(j-1)*stepsize_corse]
        kernel[i, j] = measure(*new_coord)  # add 3d
    maxpos = np.asarray(np.unravel_index(kernel.argmax(), kernel.shape))
    new_coord = [current_coord[0]+(maxpos[0]-1)*stepsize_corse, current_coord[1]+(maxpos[1]-1)*stepsize_corse]
    new_node = kernel[maxpos[0], maxpos[1]]
    print('____________')
    print('stepsize:',stepsize_corse)
    print(new_coord)
    print(new_node)
    print(current_node)
    print('restarts:',number_restarts)
    plt.scatter(new_coord[1], new_coord[0])

    if new_node > current_node:
        current_node = new_node
        current_coord = new_coord
    else:
        stepsize_corse -= 1
        if stepsize_corse < stepsize_fine:
            stepsize_corse = stepsize_restart
            if number_restarts >= restart_max:
                success = True
            number_restarts += 1

    time.sleep(0.01*8)


print('max_pos=',np.unravel_index(data.argmax(), data.shape))
print('run number:',run_number)
plt.axvline(current_coord[1])
plt.axhline(current_coord[0])
plt.show()

