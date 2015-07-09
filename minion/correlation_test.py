import numpy as np
import scipy.optimize as opt
import matplotlib.pyplot as plt
import matplotlib.style as mplstyle
mplstyle.use('ggplot')
from matplotlib.patches import Ellipse
import scipy.ndimage as ndi
import scipy.signal as sig
import time


data = np.zeros((100, 100))
data[50, 50] = 1.
data[20, 30] = 1.
data[15, 90] = 1.
data[75, 10] = 1.
data[85, 65] = 1.

nvkernel = [[0., 1., 0.], [1., 1., 1.], [0., 1., 0.]]
data = ndi.convolve(data, nvkernel)
data = ndi.gaussian_filter(data, 1)
data += np.random.random((100, 100))*0.15

datamap = np.zeros((100, 100))
datamap[48:52, 48:52] = data[48:52, 48:52]
datamap[13:17, 88:92] = data[13:17, 88:92]
data = np.roll(data, -10, axis=0)
data = np.roll(data, 5, axis=1)

t1 = time.time()
corr1 = sig.correlate2d(data, datamap, 'same')
print(time.time()-t1)

t2 = time.time()
corr2 = sig.fftconvolve(data, datamap[::-1, ::-1], 'same')  # best solution!!! - 100 times faster
print(time.time()-t2)

plt.matshow(data, origin='lower')
plt.colorbar()
plt.matshow(datamap, origin='lower')
plt.colorbar()
plt.matshow(corr1, origin='lower')
plt.colorbar()
plt.matshow(corr2, origin='lower')
plt.colorbar()


plt.show()
