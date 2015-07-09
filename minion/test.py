from matplotlib.widgets import  RectangleSelector
import matplotlib.pyplot as plt
import numpy as np

def onselect(eclick, erelease):
    'eclick and erelease are matplotlib events at press and release'
    print (' startposition : (%f, %f)' % (eclick.xdata, eclick.ydata))
    print (' endposition   : (%f, %f)' % (erelease.xdata, erelease.ydata))
    print (' used button   : ', eclick.button)
    ax.set_ylim(np.min([eclick.ydata, erelease.ydata]), np.max([eclick.ydata, erelease.ydata]))
    ax.set_xlim(np.min([eclick.xdata, erelease.xdata]), np.max([eclick.xdata, erelease.xdata]))
    plt.draw()

def toggle_selector(event):
    print (' Key pressed.')
    if event.key in ['Q', 'q'] and toggle_selector.RS.active:
        print( ' RectangleSelector deactivated.')
        toggle_selector.RS.set_active(False)
    if event.key in ['A', 'a'] and not toggle_selector.RS.active:
        print (' RectangleSelector activated.')
        toggle_selector.RS.set_active(True)
    if event.key in [' ']:
        print('reset')
        ax.set_ylim(0., 1.)
        ax.set_xlim(0., 1.)
        plt.draw()

x = np.arange(100)/(99.0)
y = np.sin(x)
fig = plt.figure()
ax = plt.subplot(111)
ax.plot(x,y)

toggle_selector.RS = RectangleSelector(ax, onselect, drawtype='box')
plt.connect('key_press_event', toggle_selector)
plt.show()