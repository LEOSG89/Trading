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

        # Solo procesar si es un archivo distinto al previamente cargado
        if nuevo_nombre != anterior_nombre:
            # Leemos y procesamos el archivo
            df = copiar_datos_a_tabla(archivo)

            # Si hubo un error y df es None, lo reportamos y salimos
            if df is None:
                st.error("No se pudo leer el archivo correctamente.")
                return None

            # Actualizamos estado
            st.session_state.datos = df
            st.session_state.loaded_filename = nuevo_nombre

            # Guardamos las columnas solo si hay datos
            if not df.empty:
                from config import COL_FILE
                with open(COL_FILE, 'w') as f:
                    json.dump(list(df.columns), f)

            return df

    return None
