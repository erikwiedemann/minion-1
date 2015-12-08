import scipy.optimize as opt
import matplotlib.pyplot as plt
import matplotlib.style as mplstyle
mplstyle.use('ggplot')
from matplotlib.patches import Ellipse
import scipy.ndimage as ndi
import scipy.signal as sig
import time
import numpy as np
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



map_original = np.loadtxt('/home/michael/Dropbox/NFP/2015/MASTERARBEIT/minion/minion/data/nv_x33_37_y30_05_z26_33.txt')

# map_original = map_original[190:230, 18:30]

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

fig1 = plt.figure(figsize=(textwidth_inch/2, textwidth_inch/2))
ax1 = fig1.add_subplot(111)
ax1.matshow(data, origin='lower')
ax1.set_xlabel(r'x [pixel]')
ax1.set_ylabel(r'y [pixel]')
ax1.set_xlim([-0.5, 40.5])
ax1.set_ylim([-0.5, 40.5])


p0 = [1., n/2., m/2., n/4., m/4., 45., 0.1]
t1 = time.time()
popt, pcov = opt.curve_fit(fit_fun, data, np.ravel(data), p0)
print(time.time()-t1)
print(popt)

ell = Ellipse([popt[1], popt[2]], width=2*popt[3], height=2*popt[4], angle=-popt[5], lw=1)
ax1.add_artist(ell)
ell.set_facecolor('None')
ell.set_edgecolor('black')
ax1.plot(popt[1], popt[2], 'black', ms=50)

fig2 = plt.figure(figsize=(textwidth_inch/2, textwidth_inch/2))
ax2 = fig2.add_subplot(111)
ax2.matshow(creategaussian(x, y, *popt), origin='lower')
ax2.set_xlabel(r'x [pixel]')
ax2.set_ylabel(r'y [pixel]')
ax2.set_xlim([-0.5, 40.5])
ax2.set_ylim([-0.5, 40.5])


fig3 = plt.figure(figsize=(textwidth_inch/10*8, textwidth_inch/3))
ax3 = fig3.add_subplot(111)
ax3.plot(np.ravel(data))
ax3.plot(np.ravel(creategaussian(x, y, *popt)))
ax3.set_xlim([0, 1680])
ax3.set_ylim([0, 1.05])
ax3.set_xlabel(r'position [pixel]')
ax3.set_ylabel(r'intensity [norm.]')

ax1.tick_params(labelbottom='on', labeltop='off', labelleft='on')
ax2.tick_params(labelbottom='on', labeltop='off', labelleft='on')
ax3.tick_params(labelbottom='on', labeltop='off', labelleft='on')
ax3.locator_params(axis = 'x', nbins = 7)

mpl.rcParams.update({'font.size': 10, 'legend.fontsize': 10})

fig1.savefig('fit1.pdf', figsize=(textwidth_inch/2, textwidth_inch/2))
fig2.savefig('fit2.pdf', figsize=(textwidth_inch/2, textwidth_inch/2))
fig3.savefig('fit3.pdf', figsize=(textwidth_inch/10*8, textwidth_inch/3))

plt.show()