import networkx as nx
import matplotlib.pyplot as plt

G = nx.Graph()
Etapa = 3
##Jugador = 3
Estrategias = 3





def generar_arbol(Etapa, Estrategias): 
    contador_nodos = [0]
 
    def agregar_nodos(padre, nivel): 
        if nivel > Etapa: 
            return 
        for _ in range(Estrategias): 
            contador_nodos[0] += 1 
            hijo = contador_nodos[0] 
            G.add_edge(padre, hijo) 
            agregar_nodos(hijo, nivel + 1) 
 
    G.add_node(0)  # Nodo raíz 
    agregar_nodos(0, 1) 
    return G 

generar_arbol(Etapa,Estrategias)

nx.draw_planar(G, with_labels=True)
plt.show()