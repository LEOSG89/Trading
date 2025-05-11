import os
import streamlit as st
import pandas as pd
import json
from config import COL_FILE


def subir_archivo(upload_key: str = 'uploader') -> pd.DataFrame:
    """
    Lee un archivo CSV/XLSX subido por el usuario y devuelve un DataFrame en bruto.
    - Evita recargar el mismo archivo si nombre, tamaño y marca de tiempo no cambian.
    - Asigna a st.session_state:
        - datos: DataFrame leído
        - loaded_file_id: tupla (nombre, size, last_modified)
    - Guarda lista de columnas en COL_FILE si hay datos.
    """
    uploaded = st.file_uploader(
        "Selecciona archivo CSV/XLSX", type=["csv", "xlsx"], key=upload_key
    )

    # Resetear estado si se quita el archivo
    if uploaded is None:
        st.session_state.pop('loaded_file_id', None)
        return pd.DataFrame()

    # Identificador de versión de archivo
    file_id = (
        uploaded.name,
        getattr(uploaded, 'size', None),
        getattr(uploaded, 'last_modified', None)
    )
    anterior_id = st.session_state.get('loaded_file_id')

    # Si no cambia el archivo, devolvemos el existente
    if anterior_id == file_id and 'datos' in st.session_state:
        return st.session_state.datos

    # Leer el archivo según extensión
    try:
        if uploaded.name.lower().endswith('.csv'):
            df = pd.read_csv(uploaded, dtype=str)
        else:
            df = pd.read_excel(uploaded, dtype=str)
    except Exception as e:
        st.error(f"Error al cargar el archivo: {e}")
        return pd.DataFrame()

    # Actualizar estado
    st.session_state.datos = df
    st.session_state.loaded_file_id = file_id

    # Persistir metadatos de columnas
    if not df.empty:
        try:
            os.makedirs(os.path.dirname(COL_FILE), exist_ok=True)
            with open(COL_FILE, 'w') as f:
                json.dump(list(df.columns), f)
        except Exception as e:
            st.warning(f"No se pudo guardar metadatos de columnas: {e}")

    # Siempre devolver el DataFrame en sesión
    return st.session_state.datos
