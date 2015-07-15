import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.pyplot import cm
from scipy import ndimage as nd
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.colors import ColorConverter


# data = np.random.randn(10, 10, 10)
x_ = np.linspace(0., 1., 10)
y_ = np.linspace(0., 1., 10)
z_ = np.linspace(0., 1., 10)
x, y, z = np.meshgrid(x_, y_, z_)

x = np.ravel(x)
y = np.ravel(y)
z = np.ravel(z)

data = np.zeros((10, 10, 10))
data[5, 5, 5] = 1.
data = nd.filters.gaussian_filter(data, sigma=3)

data = np.ravel(data)
if data.min() < 0:
    data -= data.min()
data /= data.max()
print(data.max())
print(data.min())

import time
start = time.time()
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
Blues = plt.get_cmap('jet')
# ax.plot([1],[1],[1])
for i in range(len(x)):
    if data[i] > 0.8*data.max():
        value = Blues(data[i])
        ax.plot([x[i]], [y[i]], [z[i]], linestyle='None', marker='o', color=value, alpha=0.4)
ax.set_xlim3d(0, 1)
ax.set_ylim3d(0, 1)
ax.set_zlim3d(0, 1)
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
print(time.time()-start)
plt.show()