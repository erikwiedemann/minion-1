import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.pyplot import cm
from scipy import ndimage as nd
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.colors import ColorConverter

def bin_ndarray(ndarray, new_shape, operation='mean'):
    """
    http://stackoverflow.com/questions/8090229/resize-with-averaging-or-rebin-a-numpy-2d-array
    Bins an ndarray in all axes based on the target shape, by summing or
        averaging.

    Number of output dimensions must match number of input dimensions.

    """
    if not operation.lower() in ['sum', 'mean', 'average', 'avg']:
        raise ValueError("Operation not supported.")
    if ndarray.ndim != len(new_shape):
        raise ValueError("Shape mismatch: {} -> {}".format(ndarray.shape,
                                                           new_shape))
    compression_pairs = [(d, c//d) for d,c in zip(new_shape,
                                                  ndarray.shape)]
    flattened = [l for p in compression_pairs for l in p]
    ndarray = ndarray.reshape(flattened)
    for i in range(len(new_shape)):
        if operation.lower() == "sum":
            ndarray = ndarray.sum(-1*(i+1))
        elif operation.lower() in ["mean", "average", "avg"]:
            ndarray = ndarray.mean(-1*(i+1))
    return ndarray

# change to plot on 3d ax to increase speed further

data = np.load('/home/michael/Dropbox/NFP/2015/MASTERARBEIT/minion/minion/data/x34_60-35_60-y26_60-27_60-z20-40-tset5ms-tcou5ms.npy')
print(np.shape(data))
data[:100, :, :] = 0
data[155:, :, :] = 0
# data = nd.filters.gaussian_filter(data, sigma=7)
# data = np.round(data * 100000., decimals=0)

# newlen = 50
threshlow = 18000
threshhigh = 20000

x, y, z = (threshlow < data).nonzero()




fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
color = data[(threshlow < data).nonzero()]
print(np.shape(color))
print(color.min(), color.max())
img = ax.scatter(x, y, z, zdir='z', c=color, cmap=cm.jet, linewidths=0, alpha=0.3, depthshade=False, marker='.', s=300)
cb = plt.colorbar(img)
ax.set_xlim([120, 155])
ax.set_ylim([0, 21])
ax.set_zlim([0, 21])




plt.show()