import numpy as np
from numpy import meshgrid, sin, cos, pi, linspace
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.pyplot import cm
from scipy import ndimage as nd
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.colors import ColorConverter
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


def calc_iso_surface(my_array, my_value, zs, interp_order=6, power_parameter=0.5):
    if interp_order < 1: interp_order = 1
    from numpy import argsort, take, clip, zeros
    dist = (my_array - my_value)**2
    arg = argsort(dist, axis=2)
    dist.sort(axis=2)
    w_total = 0.
    z = zeros(my_array.shape[:2], dtype=float)
    for i in range(int(interp_order)):
        zi = take(zs, arg[:,:,i])
        valuei = dist[:,:,i]
        wi = 1/valuei
        clip(wi, 0, 1.e6, out=wi) # avoiding overflows
        w_total += wi**power_parameter
        z += zi*wi**power_parameter
    z /= w_total
    return z

data = np.load('/home/michael/Dropbox/NFP/2015/MASTERARBEIT/minion/minion/data/x34_60-35_60-y26_60-27_60-z20-40-tset5ms-tcou5ms.npy')

dx = 1; dy = 1; dz = 20
nx = 21; ny = 21; nz = 201
xs = linspace(0,dx,nx)
ys = linspace(0,dy,ny)
zs = linspace(0,dz,nz)
X,Y,Z = meshgrid( xs, ys, zs)
my_array = data

fig = plt.figure()
ax = fig.gca(projection='3d')

z = calc_iso_surface( my_array, my_value=100, zs=zs, interp_order=6 )
ax.plot_surface(X[:,:,0], Y[:,:,0], z, cstride=4, rstride=4, color='g')

z = calc_iso_surface( my_array, my_value=1000, zs=zs, interp_order=6 )
ax.plot_surface(X[:,:,0], Y[:,:,0], z, cstride=4, rstride=4, color='y')

z = calc_iso_surface( my_array, my_value=10000, zs=zs, interp_order=6 )
ax.plot_surface(X[:,:,0], Y[:,:,0], z, cstride=4, rstride=4, color='b')

plt.show()







#
# data = np.load('/home/michael/Dropbox/NFP/2015/MASTERARBEIT/minion/minion/data/x34_60-35_60-y26_60-27_60-z20-40-tset5ms-tcou5ms.npy')
#
# xyproj = np.sum(data, axis=0)
# xzproj = np.sum(data, axis=1)
# yzproj = np.sum(data, axis=2)
#
# plt.matshow(xzproj, origin='lower', extent=[34.60, 35.60, 20., 40.])
# plt.matshow(yzproj, origin='lower', extent=[26.6, 27.6, 20., 40.])
# plt.figure()
# plt.plot(np.linspace(20., 40., 201), yzproj.sum(axis=1))
#
#
# # plt.show()
#
