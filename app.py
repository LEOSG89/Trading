import streamlit as st
import pandas as pd
from funciones.cargar_archivo import cargar_archivo
from funciones.mostrar_grafico import mostrar_grafico_barras
from funciones.agregar_fila import agregar_fila
from funciones.modulo_fechas_new import agregar_tiempo_operacion
from funciones.colores import mostrar_tabla_con_colores

# Configuración de la página
st.set_page_config(
    page_title="Hoja de Trading",
    page_icon="📊",
    layout="wide"
)

# Título de la aplicación
st.title("📊 Hoja de Trading")

# Cargar archivo
archivo = st.file_uploader("Carga tu archivo de operaciones", type=['csv', 'xlsx', 'xls'])

if archivo is not None:
    # Cargar datos
    df = cargar_archivo(archivo)
    
    # Procesar datos
    df = agregar_tiempo_operacion(df)
    
    # Botones de acción
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("➕ Agregar Nueva Operación"):
            df = agregar_fila(df)
    
    with col2:
        if st.button("📊 Mostrar Gráficos"):
            st.subheader("Gráficos de Operaciones")
            col1, col2 = st.columns(2)
            
            with col1:
                mostrar_grafico_barras(df, "Profit", 1)
            
            with col2:
                mostrar_grafico_barras(df, "% Profit. Op", 2)
    
    with col3:
        if st.button("📈 Estadísticas"):
            st.subheader("Estadísticas")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total de Operaciones", len(df))
            
            with col2:
                st.metric("Operaciones Ganadoras", len(df[df['Profit'] > 0]))
            
            with col3:
                st.metric("Operaciones Perdedoras", len(df[df['Profit'] < 0]))
    
    with col4:
        if st.button("💾 Guardar Cambios"):
            st.download_button(
                label="Descargar archivo actualizado",
                data=df.to_csv(index=False).encode('utf-8'),
                file_name='operaciones_actualizadas.csv',
                mime='text/csv'
            )
    
    # Mostrar tabla con colores
    mostrar_tabla_con_colores(df)
else:
    st.info("👆 Por favor, carga un archivo para comenzar") 