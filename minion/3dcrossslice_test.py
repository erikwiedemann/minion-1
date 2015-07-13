import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.pyplot import cm
from scipy import ndimage as nd
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.colors import ColorConverter

xx, yy = np.meshgrid(np.linspace(0,10,10), np.linspace(0,10,10))
data = np.zeros((10, 10, 10))
data[4,4,4] = 10.
data = nd.filters.gaussian_filter(data, sigma=1)
import time
start = time.time()
fig = plt.figure(1)
ax = fig.gca(projection='3d')

slicexy = data[:, :, 5]
slicexz = data[5, :, :]
sliceyz = data[:, 5, :]
ax.plot_surface(xx,yy,np.zeros((10,10))+5, rstride=1, cstride=1, facecolors=cm.jet(slicexy), shade=False, alpha=0.5)
ax.plot_surface(xx,np.zeros((10,10))+5, yy, rstride=1, cstride=1, facecolors=cm.jet(slicexz), shade=False, alpha=0.5)
ax.plot_surface(np.zeros((10,10))+5, xx, yy, rstride=1, cstride=1, facecolors=cm.jet(sliceyz), shade=False, alpha=0.5)

print(time.time()-start)
plt.show()

