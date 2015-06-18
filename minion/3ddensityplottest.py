import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.pyplot import cm
from scipy import ndimage as nd
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.colors import ColorConverter

def bin_ndarray(ndarray, new_shape, operation='mean'):
    """
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

data = np.zeros((100, 100, 100))
data[50, 50, 50] = 10.
data = nd.filters.gaussian_filter(data, sigma=7)
data = np.round(data * 100000., decimals=0)

newlen = 50
threshhold = 50

data = bin_ndarray(data, (newlen,newlen,newlen))
x, y, z = (data > threshhold).nonzero()

print(np.shape(x), np.shape(y), np.shape(z))


fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
color = data[(data > threshhold).nonzero()]
print(np.shape(color))
print(color.min(), color.max())
img = ax.scatter(x, y, z, zdir='z', c=color, cmap=cm.jet, linewidths=0, alpha=0.2, depthshade=False, marker='.', s=4*newlen)
cb = plt.colorbar(img)
ax.set_xlim([0, newlen])
ax.set_ylim([0, newlen])
ax.set_zlim([0, newlen])




plt.show()