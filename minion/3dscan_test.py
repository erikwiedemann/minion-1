import numpy as np

xmin = 0.
xmax = 3.
ymin = 4.
ymax = 7.
zmin = 0.
zmax = 9.


axis1 = 2  # x
axis2 = 1  # y
axis3 = 3  # z

startpos1 = xmin
startpos2 = ymin
startpos3 = zmin

resolution1 = 4
resolution2 = 4
resolution3 = 4


dim1 = np.linspace(xmin, xmax, resolution1)  # 1-x
dim2 = np.linspace(ymin, ymax, resolution2)  # 2-y
dim3 = np.linspace(zmin, zmax, resolution3)  # 3-z

dim1 = np.tile(dim1, (1, resolution2*resolution3))
dim2 = np.tile(dim2, (resolution1, 1))
dim2 = dim2.T
dim2 = np.tile(dim2, (resolution3, 1))
dim3 = np.tile(dim3, (resolution1*resolution2, 1))
dim3 = dim3.T

print(np.shape(dim1))
print(np.shape(dim2))
print(np.shape(dim3))

list1 = np.reshape(dim1, (1, resolution1*resolution2*resolution3))
list2 = np.reshape(dim2, (1, resolution1*resolution2*resolution3))
list3 = np.reshape(dim3, (1, resolution1*resolution2*resolution3))

# print(dim1)
# print(dim2)
# print(dim3)
print('-----------------------------------------------')
print(list1[0,0:17])
print(list2[0,0:17])
print(list3[0,0:17])

# print(list1)
# print(list2)
# print(list3)

indexmat = np.indices((resolution1, resolution2, resolution3))


indexlist = indexmat.reshape((1, 3, resolution1*resolution2*resolution3))
#
print(indexlist[0,0]) # z
print(indexlist[0,1]) # y
print(indexlist[0,2]) # z