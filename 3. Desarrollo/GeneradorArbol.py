
import networkx as nx
from networkx.drawing.nx_pydot import write_dot, graphviz_layout
import matplotlib.pyplot as plt

G = nx.DiGraph()
Rondas = 2
##Jugador = 3
Estrategias = 3
TotalEstrategias = 0



def generar_arbol(Rondas, Estrategias): 
    contador_nodos = [0]
 
    def agregar_nodos(padre, profundidad): 
        if profundidad > Rondas: 
            return 
        for _ in range(Estrategias): 
            contador_nodos[0] += 1 
            hijo = contador_nodos[0] 
            G.add_edge(padre, hijo, id=TotalEstrategias) 
            agregar_nodos(hijo, profundidad + 1) 
 
    G.add_node(0)
    agregar_nodos(0, 1) 
    return G 

generar_arbol(Rondas,Estrategias)

pos = graphviz_layout(G, prog='dot')
nx.draw(G, pos, with_labels=True, node_size=350, node_color='lightblue')
plt.title('draw_networkx')
###plt.savefig('nx_test1.png')
plt.show()
print(G.edges(data=True))
print(G)