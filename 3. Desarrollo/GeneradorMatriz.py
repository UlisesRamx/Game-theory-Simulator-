import numpy as np
import matplotlib.pyplot as plt

n = 15  # Estrategias
m = 13  # Escenarios
matriz = np.zeros((n, m))
data = np.random.rand(n, m)
plt.imshow(data, cmap='viridis', interpolation='nearest')
plt.colorbar()  # Add a color scale
plt.title("Heatmap of a Large Array")
plt.show()
print(matriz)

