import os
import json
import pandas as pd
import streamlit as st
from copia_tabla import copiar_datos_a_tabla

def subir_archivo(upload_key: str = 'uploader') -> pd.DataFrame | None:
    """
    Sube un archivo (CSV/XLSX), limpia el estado anterior y retorna un nuevo DataFrame.
    - Evita duplicación de archivos.
    - Reemplaza el DataFrame actual si el archivo es nuevo.
    """
    archivo = st.file_uploader("Carga CSV/XLSX", type=['csv', 'xlsx'], key=upload_key)

    if archivo is not None:
        nuevo_nombre = archivo.name
        anterior_nombre = st.session_state.get('loaded_filename', None)

        # Si es nuevo archivo
        if nuevo_nombre != anterior_nombre:
            df = copiar_datos_a_tabla(archivo)
            st.session_state.datos = df
            st.session_state.loaded_filename = nuevo_nombre

            # Guardar columnas en archivo de configuración
            if hasattr(st.session_state, 'datos') and not st.session_state.datos.empty:
                from config import COL_FILE
                with open(COL_FILE, 'w') as f:
                    json.dump(list(st.session_state.datos.columns), f)

            return df

    return None
