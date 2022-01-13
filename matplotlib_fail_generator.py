import matplotlib.pyplot as plt
import numpy as np
image = np.random.randn(256, 256, 3)
image= np.array(image/image.max()*255, dtype= np.uint8)
fig, axes = plt.subplots() #эта строка не должна быть внутри цикла
for i in range(500):
    print(i)
    axes.cla()
    axes.imshow(image)