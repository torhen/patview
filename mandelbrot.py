import numpy as np
from matplotlib import pyplot as plt
from numba import njit, prange


# def make_array(x0, x1, y0, y1):
#     width = 500
#     x = np.linspace(x0, x1, width)
#     y = np.linspace(y0, y1, width)
#     m = np.meshgrid(x, y)

#     C = m[0] + 1j * m[1]
#     X = np.zeros_like(C)
#     I = np.full_like(C, -1, dtype=int)

#     for i in range(100):
#         X = X**2 + C
#         I[(abs(X) > 2) & (I < 0)] = i

#     return I


@njit(parallel=True)
def make_array(x0, x1, y0, y1):
    width = 500
    x = np.linspace(x0, x1, width)
    y = np.linspace(y0, y1, width)

    I = np.full((width, width), -1, dtype=np.int32)

    for iy in prange(width):
        for ix in range(width):
            cx = x[ix]
            cy = y[iy]
            c = complex(cx, cy)
            z = 0j

            for i in range(100):
                z = z*z + c
                if abs(z) > 2:
                    I[iy, ix] = i
                    break

    return I

def on_button_press(event):
    if event.xdata is None or event.ydata is None:
        return

    global g_x0, g_x1, g_y0, g_y1

    xm, ym = event.xdata, event.ydata

    # current center
    cx = (g_x0 + g_x1) / 2
    cy = (g_y0 + g_y1) / 2

    # shift amount
    dx = xm - cx
    dy = ym - cy

    # move window so clicked point becomes center
    g_x0 += dx
    g_x1 += dx
    g_y0 += dy
    g_y1 += dy

    update()

        
def on_scroll(event):
    global g_x0, g_x1, g_y0, g_y1
    if event.xdata is None or event.ydata is None:
        return

    f = 0.9 if event.button == 'up' else 1.1
    xm, ym = event.xdata, event.ydata


    g_x0 = xm + (g_x0 - xm) * f
    g_x1 = xm + (g_x1 - xm) * f
    g_y0 = ym + (g_y0 - ym) * f
    g_y1 = ym + (g_y1 - ym) * f

    update()

def update():
    arr = make_array(g_x0, g_x1, g_y0, g_y1)
    im.set_data(arr)
    im.set_clim(arr.min(), arr.max())
    im.set_extent((g_x0, g_x1, g_y0, g_y1))
    fig.canvas.draw_idle()

g_x0 = -2.0
g_x1 = 2.0
g_y0 = -2.0
g_y1 = 2.0

fig = plt.figure()
fig.canvas.mpl_connect("button_press_event", on_button_press)
fig.canvas.mpl_connect("scroll_event", on_scroll)

ax = fig.add_subplot()
ax.grid()
arr = make_array(g_x0, g_x1, g_y0, g_y1)
im = ax.imshow(arr, extent=(g_x0, g_x1, g_y0, g_y1), cmap='gist_ncar', origin='lower')
# fig.colorbar()
plt.show()


        
