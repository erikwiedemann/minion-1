import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button, RadioButtons
import scipy.ndimage as ndi

# data = np.zeros((10, 10, 10))
# data[5, 5, 5] = 10.
# data = ndi.filters.gaussian_filter(data, sigma=1)
# print(data.max())
data = np.load('/home/michael/Dropbox/NFP/2015/MASTERARBEIT/minion/minion/data/x34_60-35_60-y26_60-27_60-z20-40-tset5ms-tcou5ms.npy')


def cube_show_slider(cube, axis=2, **kwargs):
    """
    Display a 3d ndarray with a slider to move along the third dimension.

    Extra keyword arguments are passed to imshow
    """
    

    # check dim
    if not cube.ndim == 3:
        raise ValueError("cube should be an ndarray with ndim == 3")

    # generate figure
    fig = plt.figure()
    ax = plt.subplot(111)
    fig.subplots_adjust(left=0.25, bottom=0.25)

    # select first image
    s = [slice(0, 1) if i == axis else slice(None) for i in range(3)]
    im = cube[s].squeeze()

    # display image
    l = ax.matshow(im, **kwargs)
    cb = plt.colorbar(l)
    cb.set_clim(vmin=data.min(), vmax=data.max())
    cb.draw_all()
    # define slider
    axcolor = 'lightgoldenrodyellow'
    ax = fig.add_axes([0.25, 0.1, 0.65, 0.03], axisbg=axcolor)

    slider = Slider(ax, 'Axis %i index' % axis, 0, cube.shape[axis] - 1, valinit=0, valfmt='%i')

    def update(val):
        ind = int(slider.val)
        s = [slice(ind, ind + 1) if i == axis else slice(None) for i in range(3)]
        im = cube[s].squeeze()
        l.set_data(im, **kwargs)
        cb.set_clim(vmin=data.min(), vmax=data.max())
        cb.draw_all()
        fig.canvas.draw()

    slider.on_changed(update)

    plt.show()

cube_show_slider(data)
