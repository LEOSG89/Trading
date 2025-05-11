import pandas as pd
import streamlit as st
from convertir_fechas import convertir_fechas

# Módulo "copia_tabla.py" actualizado para parsear fechas inmediatamente al leer

def copiar_datos_a_tabla(archivo_cargado):
    """
    Copia todos los datos del archivo cargado a la tabla principal,
    evitando duplicación de operaciones y parseando fechas desde el origen.
    """
    try:
        # 1) Leer archivo con fechas como texto
        if archivo_cargado.name.endswith('.csv'):
            df_nuevo = pd.read_csv(
                archivo_cargado,
                dtype={
                    'Fecha / Hora': str,
                    'Fecha / Hora de Cierre': str
                }
            )
        else:
            df_nuevo = pd.read_excel(
                archivo_cargado,
                converters={
                    'Fecha / Hora': str,
                    'Fecha / Hora de Cierre': str
                }
            )

        # 2) Asegurar columnas requeridas existan
        columnas_requeridas = [
            'Activo', 'C&P', 'D', 'Día',
            'Fecha / Hora', 'Fecha / Hora de Cierre',
            '#Cont', 'STRK Buy', 'STRK Sell'
        ]
        for col in columnas_requeridas:
            if col not in df_nuevo.columns:
                df_nuevo[col] = None

        # 3) Parsear fechas inmediatamente (día/mes/año)
        df_nuevo = convertir_fechas(
            df_nuevo,
            cols=['Fecha / Hora', 'Fecha / Hora de Cierre'],
            dayfirst=True,
            yearfirst=False
        )

        # 4) Evitar duplicados si ya hay datos previos
        if 'datos' in st.session_state and isinstance(st.session_state.datos, pd.DataFrame) and not st.session_state.datos.empty:
            df_existente = st.session_state.datos
            df_final = pd.concat([df_existente, df_nuevo], ignore_index=True)
            df_final = df_final.drop_duplicates(
                subset=['Activo', 'C&P', 'Fecha / Hora'], keep='first'
            )
        else:
            df_final = df_nuevo

        # 5) Actualizar estado y retornar
        st.session_state.datos = df_final
        return df_final

    except Exception as e:
        st.error(f"Error al copiar los datos del archivo: {e}")
        return None

