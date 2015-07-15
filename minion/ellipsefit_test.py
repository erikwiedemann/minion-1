import numpy as np
import scipy.optimize as opt
import matplotlib.pyplot as plt
import matplotlib.style as mplstyle
mplstyle.use('ggplot')
from matplotlib.patches import Ellipse
import scipy.ndimage as ndi
import scipy.signal as sig
import time

def creategaussian(x, y, height, x0, y0, sigmax, sigmay, rot, offset):
    phi = np.deg2rad(rot)
    a = np.cos(phi)**2/(2.*sigmax**2) + np.sin(phi)**2/(2.*sigmay**2)
    b = - np.sin(2.*phi)/(4.*sigmax**2) + np.sin(2.*phi)/(4.*sigmay**2)
    c = np.sin(phi)**2/(2.*sigmax**2) + np.cos(phi)**2/(2.*sigmay**2)

    fn = offset + height*np.exp(-(a*(x-x0)**2 + 2*b*(x-x0)*(y-y0) + c*(y-y0)**2))
    return fn

def fit_fun(data, height, x0, y0, sigmax, sigmay, rot, offset):
    guess = creategaussian(x, y, height, x0, y0, sigmax, sigmay, rot, offset)
    return np.ravel(guess)



# map_original = np.loadtxt('/home/michael/Dropbox/NFP/2015/MASTERARBEIT/minion/minion/data/nv_x33_37_y30_05_z26_33.txt')

map_original = np.loadtxt('/home/michael/Dropbox/NFP/2015/MASTERARBEIT/minion/minion/data/nv_x33_37_y30_05_z26_33_yz.txt')
map_original = map_original[190:230, 18:30]

# map_original = np.loadtxt('/home/michael/Dropbox/NFP/2015/MASTERARBEIT/minion/minion/data/nv_x33_37_y30_05_z26_33_xz.txt')
# map_original = map_original[180:270, 0:30]
data = map_original
data /= data.max()
m, n = np.shape(data)

# Create x and y indices
x = np.linspace(0, n-1, n)
y = np.linspace(0, m-1, m)
x, y = np.meshgrid(x, y)
# #create data
# data = creategaussian(x, y, 1, 10, 10, 2, 4, 45, 0.)
# data /= data.max()
# data += np.random.random((21, 21))*0.3
# data /= data.max()

plt.matshow(data, origin='lower')
p0 = [1., n/2., m/2., n/4., m/4., 45., 0.1]
t1 = time.time()
popt, pcov = opt.curve_fit(fit_fun, data, np.ravel(data), p0)
print(time.time()-t1)
print(popt)

ell = Ellipse([popt[1], popt[2]], width=2*popt[3], height=2*popt[4], angle=-popt[5], lw=3)
ax = plt.gca()
ax.add_artist(ell)
ell.set_facecolor('None')
ell.set_edgecolor('white')
plt.plot(popt[1], popt[2], 'w.', ms=10)

plt.matshow(creategaussian(x, y, *popt), origin='lower')

plt.figure()
plt.plot(np.ravel(data))
plt.plot(np.ravel(creategaussian(x, y, *popt)))
plt.show()