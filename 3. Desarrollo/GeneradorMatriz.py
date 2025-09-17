'''
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def forma_probabilistico(rondas:int, estrategias:int) -> tuple[int,int]:
    if estrategias == 1:
        filas = 1
        columnas = 1
    else:
        filas = ((estrategias**rondas - estrategias**2) // (estrategias - 1)) + 2*estrategias
        columnas = (estrategias**rondas - 1) // (estrategias - 1)
    return filas, columnas

def crear_dataframe_matriz(rondas:int, estrategias:int, fill=0.0) -> pd.DataFrame:
    filas, columnas = forma_probabilistico(rondas, estrategias)
    index = [f"a{i}" for i in range(1, filas+1)]
    cols  = [f"X{j}" for j in range(columnas)]
    data = np.full((filas, columnas), fill, dtype=float)
    return pd.DataFrame(data, index=index, columns=cols)

def visualizar_matriz(df:pd.DataFrame):
    filas, columnas = df.shape
    if filas <25 and columnas < 25:
        print(df)
    elif filas>24 and columnas>24:
        print(df.iloc[:20, :20])
        print("...")

    print(f"Matriz de {filas} filas y {columnas} columnas:")



# Ejemplo (tus valores):
Rondas = 3
Estrategias = 5
df = crear_dataframe_matriz(Rondas, Estrategias, fill=0.0)
visualizar_matriz(df)



print(df.shape)     # (filas, columnas)
print(df.index[:5]) # primeras filas (a1, a2, ...)
print(df.columns[:5])  # primeras columnas (X0, X1, ...)
print(df) 
'''

import math
import numpy as np
import pandas as pd
import os

# ----- Utilidades de paginación -----
def page_counts(n_rows: int, n_cols: int, page_size: int = 20):
    """Devuelve (#páginas_filas, #páginas_columnas). Páginas 1-based."""
    return math.ceil(n_rows / page_size), math.ceil(n_cols / page_size)

def window_indices(row_page: int, col_page: int, n_rows: int, n_cols: int, page_size: int = 20):
    """Índices [r0:r1, c0:c1] para la ventana actual (maneja límites)."""
    r0 = (row_page - 1) * page_size
    c0 = (col_page - 1) * page_size
    r1 = min(r0 + page_size, n_rows)
    c1 = min(c0 + page_size, n_cols)
    return r0, r1, c0, c1

def show_window(data, row_page: int, col_page: int, page_size: int = 20):
    """Muestra el bloque 20x20 (o menos en bordes). Soporta NumPy o DataFrame."""
    # Tomar shape
    if isinstance(data, pd.DataFrame):
        n_rows, n_cols = data.shape
    else:  # asumimos NumPy
        n_rows, n_cols = data.shape

    # Páginas totales
    rp_total, cp_total = page_counts(n_rows, n_cols, page_size)
    # Índices de la ventana
    r0, r1, c0, c1 = window_indices(row_page, col_page, n_rows, n_cols, page_size)

    print(f"\nVentana filas {r0+1}-{r1} / {n_rows} | columnas {c0+1}-{c1} / {n_cols} "
          f"(pág filas {row_page}/{rp_total}, pág cols {col_page}/{cp_total})")

    # Slice y print
    if isinstance(data, pd.DataFrame):
        bloque = data.iloc[r0:r1, c0:c1]
        # Mostrar completo (sin truncar)
        with pd.option_context("display.max_rows", None, "display.max_columns", None, "display.width", 200):
            print(bloque)
    else:
        bloque = data[r0:r1, c0:c1]
        # Imprimir como DataFrame para que se vea bonito
        print(pd.DataFrame(bloque))

# ----- Demo con DataFrame con encabezados a1..aN y X0..X(M-1) -----
def crear_df(n_rows: int, n_cols: int):
    idx = [f"a{i}" for i in range(1, n_rows+1)]
    cols = [f"X{j}" for j in range(n_cols)]
    arr = np.arange(n_rows*n_cols, dtype=float).reshape(n_rows, n_cols)
    return pd.DataFrame(arr, index=idx, columns=cols)

# Ejemplo: 150x150
df = crear_df(81, 137)

# Navegación simple por consola
row_page, col_page = 1, 1
page_size = 10
show_window(df, row_page, col_page, page_size)

while True:
    cmd = input("\nComandos: [Enter]=siguiente, 'prev', 'r+'/'r-' (pág filas), 'c+'/'c-' (pág cols), 'goto r c', 'q': ").strip().lower()
    os.system('cls')
    if cmd == "q":
        break
    elif cmd == "":  # siguiente: avanza columnas y salta a filas cuando termine columnas
        rp_total, cp_total = page_counts(*df.shape, page_size)
        if col_page < cp_total:
            col_page += 1
        else:
            col_page = 1
            if row_page < rp_total:
                row_page += 1
            else:
                row_page, col_page = 1, 1  # vuelve al inicio
    elif cmd == "prev":
        if col_page > 1:
            col_page -= 1
        else:
            rp_total, cp_total = page_counts(*df.shape, page_size)
            col_page = cp_total
            row_page = rp_total if row_page == 1 else row_page - 1
    elif cmd == "r+":
        rp_total, _ = page_counts(*df.shape, page_size)
        row_page = min(row_page + 1, rp_total)
    elif cmd == "r-":
        row_page = max(row_page - 1, 1)
    elif cmd == "c+":
        _, cp_total = page_counts(*df.shape, page_size)
        col_page = min(col_page + 1, cp_total)
    elif cmd == "c-":
        col_page = max(col_page - 1, 1)
    elif cmd.startswith("goto"):
        try:
            _, r_str, c_str = cmd.split()
            r, c = int(r_str), int(c_str)
            rp_total, cp_total = page_counts(*df.shape, page_size)
            row_page = max(1, min(r, rp_total))
            col_page = max(1, min(c, cp_total))
        except Exception:
            print("Uso: goto <pág_filas> <pág_cols> (enteros 1-based)")
    else:
        print("Comando no reconocido.")
        continue

    show_window(df, row_page, col_page, page_size)




'''
# Si quieres visualizar heatmap:
plt.imshow(df.values, cmap='viridis', interpolation='nearest')
plt.colorbar()
plt.title("Heatmap de la matriz")
plt.show()
'''
