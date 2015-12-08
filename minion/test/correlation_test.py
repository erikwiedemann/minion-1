import numpy as np
import scipy.optimize as opt
import matplotlib.pyplot as plt
import matplotlib.style as mplstyle
from matplotlib.patches import Ellipse
import scipy.ndimage as ndi
import scipy.signal as sig
import time
import os
import matplotlib as mpl
from matplotlib.pyplot import cm
from matplotlib import rc
from matplotlib import ticker


mplstyle.use('ggplot')  # 'ggplot', 'dark_background', 'bmh', 'fivethirtyeight'
rc('font', **{'family': 'serif', 'serif': ['Computer Modern']})
rc('text', usetex=True)
mpl.rcParams.update({'figure.autolayout' : True, 'font.size': 10, 'legend.fontsize': 10})
textwidth_inch = 6.299






data = np.zeros((100, 100))
data[50, 50] = 1.
data[20, 30] = 1.
data[45, 75] = 1.
data[75, 10] = 1.
data[85, 65] = 1.

nvkernel = [[0., 1., 0.], [1., 1., 1.], [0., 1., 0.]]
data = ndi.convolve(data, nvkernel)
data = ndi.gaussian_filter(data, 1)
data += np.random.random((100, 100))*0.15
# np.savetxt(time.strftime('scanhistory/'+'%Y-%m-%d_%H-%M-%S')+'_scan.txt', data)


fig1 = plt.figure(figsize=(textwidth_inch/2, textwidth_inch/2))
ax1 = fig1.add_subplot(111)
img1 = ax1.matshow(data, origin='lower')
cbar1 = plt.colorbar(img1, fraction=0.046, pad=0.04)

datamap = np.zeros((100, 100))
datamap[48:52, 48:52] = data[48:52, 48:52]
datamap[42:48, 72:78] = data[42:48, 72:78]
data = np.roll(data, -10, axis=0)
data = np.roll(data, 5, axis=1)


t1 = time.time()
corr1 = sig.correlate2d(data, datamap, 'same')
print(time.time()-t1)

t2 = time.time()
corr2 = sig.fftconvolve(data, datamap[::-1, ::-1], 'same')  # best solution!!! - 100 times faster
print(time.time()-t2)




fig2 = plt.figure(figsize=(textwidth_inch/2, textwidth_inch/2))
ax2 = fig2.add_subplot(111)
img2 = ax2.matshow(datamap, origin='lower')
cbar2 = plt.colorbar(img2, fraction=0.046, pad=0.04)

fig3 = plt.figure(figsize=(textwidth_inch/2, textwidth_inch/2))
ax3 = fig3.add_subplot(111)
img3 = ax3.matshow(corr2, origin='lower')
cbar3 = plt.colorbar(img3, fraction=0.046, pad=0.04)







ax1.tick_params(labelbottom='on', labeltop='off', labelleft='on')
ax2.tick_params(labelbottom='on', labeltop='off', labelleft='on')
ax3.tick_params(labelbottom='on', labeltop='off', labelleft='on')

ax1.set_xlabel(r'x [pixel]')
ax1.set_ylabel(r'y [pixel]')
ax2.set_xlabel(r'x [pixel]')
ax2.set_ylabel(r'y [pixel]')
ax3.set_xlabel(r'x [pixel]')
ax3.set_ylabel(r'y [pixel]')


mpl.rcParams.update({'font.size': 10, 'legend.fontsize': 10})

fig1.savefig('auto1.pdf', figsize=(textwidth_inch/2, textwidth_inch/2))
fig2.savefig('auto2.pdf', figsize=(textwidth_inch/2, textwidth_inch/2))
fig3.savefig('auto3.pdf', figsize=(textwidth_inch/2, textwidth_inch/2))


plt.show()
