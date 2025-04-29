import pandas as pd
import streamlit as st

def copiar_datos_a_tabla(archivo_cargado):
    """
    Copia todos los datos del archivo cargado a la tabla principal,
    evitando duplicación de operaciones.
    
    Args:
        archivo_cargado: El archivo cargado por el usuario (CSV o Excel)
        
    Returns:
        DataFrame con todos los datos del archivo
    """
    try:
        # Leer el archivo según su extensión
        if archivo_cargado.name.endswith('.csv'):
            df_nuevo = pd.read_csv(archivo_cargado)
        else:
            df_nuevo = pd.read_excel(archivo_cargado)
            
        # Asegurarse de que el DataFrame tenga las columnas necesarias
        columnas_requeridas = [
            'Activo', 'C&P', 'D', 'Día', 'Fecha / Hora',
            'Fecha / Hora de Cierre', '#Cont', 'STRK Buy', 'STRK Sell'
        ]
        
        # Si el DataFrame no tiene las columnas requeridas, inicializarlas
        for columna in columnas_requeridas:
            if columna not in df_nuevo.columns:
                df_nuevo[columna] = None
                
        # Si ya existen datos en la sesión, verificar duplicados
        if 'datos' in st.session_state and not st.session_state.datos.empty:
            # Obtener las filas que no están en el DataFrame actual
            df_existente = st.session_state.datos
            df_final = pd.concat([df_existente, df_nuevo], ignore_index=True)
            df_final = df_final.drop_duplicates(subset=['Activo', 'C&P', 'Fecha / Hora'], keep='first')
        else:
            df_final = df_nuevo
            
        # Actualizar el estado de la sesión con los datos sin duplicados
        st.session_state.datos = df_final
        
        return df_final
        
    except Exception as e:
        st.error(f"Error al copiar los datos del archivo: {str(e)}")
        return None 