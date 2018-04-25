import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0,15, 15)
y = 1 * (1+1)**(x/12)

for i in range(len(x)):
    print('at timestep %i, demand is %f' %(x[i],y[i]))