import pandas as pd
import re

def limpiar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    """
    - Elimina columnas tipo 'Unnamed: 0', 'Unnamed: 0.1', etc.
    - Elimina columnas duplicadas por nombre.
    - Asegura que la columna '#' exista como contador correcto (0,1,2,...), y esté al final.
    - Reubica la columna 'D' justo al lado de 'Activo' si ambas existen.
    """

    # 1. Eliminar columnas tipo 'Unnamed: 0', 'Unnamed: 0.1', etc.
    df = df.loc[:, ~df.columns.str.match(r'^Unnamed: \d+(\.\d+)?$')]

    # 2. Eliminar columnas duplicadas (por nombre)
    df = df.loc[:, ~df.columns.duplicated(keep='first')]

    # 3. Asegurar columna '#' como contador válido y al final
    if '#' in df.columns:
        col_hash = pd.to_numeric(df['#'], errors='coerce')
        if not col_hash.equals(pd.Series(range(len(df)))):
            col_hash = pd.Series(range(len(df)), name='#')  # reemplaza si no es secuencial
    else:
        col_hash = pd.Series(range(len(df)), name='#')

    df = df.drop(columns=['#'], errors='ignore')  # eliminar si ya estaba
    df['#'] = col_hash  # agregar al final

    # 4. Mover columna 'D' al lado derecho de 'Activo', si existen
    if 'Activo' in df.columns and 'D' in df.columns:
        cols = list(df.columns)
        cols.remove('D')
        activo_idx = cols.index('Activo')
        cols.insert(activo_idx + 1, 'D')
        df = df[cols]

    return df
