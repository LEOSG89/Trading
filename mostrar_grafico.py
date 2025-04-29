import plotly.graph_objects as go
import streamlit as st
import pandas as pd
import time

# Agregar contador global al inicio del archivo
_contador_graficos = 0

def mostrar_grafico_barras(df, columna, numero_grafico=1):
    """Muestra un gráfico de barras"""
    try:
        # Crear una copia del DataFrame excluyendo DEP y RET
        df_sin_dep_ret = df[~df['Activo'].str.contains('DEP|RET', na=False)].copy()
        
        # Convertir la columna a numérica
        df_sin_dep_ret[columna] = pd.to_numeric(df_sin_dep_ret[columna], errors='coerce')
        
        # Crear un selector múltiple para excluir operaciones adicionales
        operaciones_a_excluir = st.multiselect(
            'Selecciona operaciones adicionales a excluir:',
            options=df_sin_dep_ret.index.tolist(),
            key=f"excluir_barras_{numero_grafico}"
        )
        
        # Filtrar el DataFrame excluyendo las operaciones seleccionadas
        if operaciones_a_excluir:
            df_sin_dep_ret = df_sin_dep_ret[~df_sin_dep_ret.index.isin(operaciones_a_excluir)]
        
        # Crear el gráfico de barras
        fig = go.Figure()
        
        # Agregar barras para valores positivos (verdes)
        df_positivo = df_sin_dep_ret[df_sin_dep_ret[columna] > 0]
        if not df_positivo.empty:
            fig.add_trace(go.Bar(
                x=df_positivo.index,
                y=df_positivo[columna],
                name='Positivo',
                marker_color='green'
            ))
        
        # Agregar barras para valores negativos (rojos)
        df_negativo = df_sin_dep_ret[df_sin_dep_ret[columna] < 0]
        if not df_negativo.empty:
            fig.add_trace(go.Bar(
                x=df_negativo.index,
                y=df_negativo[columna],
                name='Negativo',
                marker_color='red'
            ))
        
        # Agregar barras para valores cero (grises)
        df_cero = df_sin_dep_ret[df_sin_dep_ret[columna] == 0]
        if not df_cero.empty:
            fig.add_trace(go.Bar(
                x=df_cero.index,
                y=df_cero[columna],
                name='Cero',
                marker_color='gray'
            ))
        
        # Configurar el layout del gráfico
        fig.update_layout(
            title=f'Gráfico de Barras - {columna}',
            xaxis_title='Número de Operación',
            yaxis_title=columna,
            showlegend=True,
            barmode='group'
        )
        
        # Mostrar el gráfico
        st.plotly_chart(fig, use_container_width=True, key=f"grafico_barras_{numero_grafico}")
        
    except Exception as e:
        st.error(f"Error al mostrar el gráfico de barras: {str(e)}")

def mostrar_grafico_area(df, columna):
    """
    Muestra un gráfico de área con los valores de Profit Tot.
    """
    try:
        # Convertir la columna Profit Tot. a numérico
        df['Profit Tot.'] = pd.to_numeric(df['Profit Tot.'], errors='coerce')
        
        # Crear el gráfico de área
        fig = go.Figure(data=[
            go.Scatter(
                x=df.index,
                y=df['Profit Tot.'],
                fill='tozeroy',
                mode='lines',
                line=dict(color='rgba(0, 255, 0, 0.7)'),
                fillcolor='rgba(0, 255, 0, 0.3)',
                name='Profit Tot.',
                hovertemplate='Profit Tot.: %{y:.2f}%<extra></extra>'
            )
        ])
        
        # Personalizar el layout
        fig.update_layout(
            title='Gráfico de Área - Profit Tot.',
            xaxis_title='Operación',
            yaxis_title='Profit Tot. (%)',
            showlegend=True,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(
                showgrid=True,
                gridcolor='rgba(0,0,0,0.1)',
                showticklabels=True
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='rgba(0,0,0,0.1)',
                tickformat='.2f'
            )
        )
        
        st.plotly_chart(fig, use_container_width=True, key=f"grafico_area_{columna}")
    except Exception as e:
        st.error(f"❌ Error al crear el gráfico de área: {str(e)}")
        # Mostrar algunos valores para debug
        st.error(f"Valores en Profit Tot.: {df['Profit Tot.'].head().tolist()}")

def mostrar_grafico_area_dd_max_negativo(df, columna):
    """
    Muestra un gráfico de área con los valores de DD/Max.
    """
    try:
        # Convertir la columna DD/Max a numérico, eliminando el símbolo %
        df['DD/Max'] = df['DD/Max'].str.rstrip('%').astype('float')
        
        # Crear una serie con solo valores negativos
        dd_negativo = df['DD/Max'].copy()
        dd_negativo[dd_negativo > 0] = 0
        
        # Crear el gráfico de área
        fig = go.Figure(data=[
            go.Scatter(
                x=df.index,
                y=dd_negativo,
                fill='tozeroy',
                mode='lines',
                line=dict(color='red', width=1),
                fillcolor='rgba(255, 0, 0, 0.3)',
                name='DD/Max Negativo',
                hovertemplate='DD/Max: %{y:.2f}%<extra></extra>'
            )
        ])
        
        # Personalizar el layout
        fig.update_layout(
            title='Gráfico DD/Max Negativo',
            xaxis_title='Operación',
            yaxis_title='DD/Max (%)',
            showlegend=True,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(
                showgrid=True,
                gridcolor='rgba(0,0,0,0.1)',
                showticklabels=True
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='rgba(0,0,0,0.1)',
                tickformat='.2f'
            )
        )
        
        st.plotly_chart(fig, use_container_width=True, key=f"grafico_dd_max_{columna}")
    except Exception as e:
        st.error(f"❌ Error al crear el gráfico DD/Max negativo: {str(e)}")
        # Mostrar algunos valores para debug
        st.error(f"Valores en DD/Max: {df['DD/Max'].head().tolist()}")

def mostrar_grafico_tendencia_profit(df, columna):
    """
    Muestra un gráfico de tendencia comparando Profit Tot., Profit Alcanzado y Profit Media.
    """
    try:
        # Convertir las columnas a numérico
        df['Profit Tot.'] = pd.to_numeric(df['Profit Tot.'], errors='coerce')
        df['Profit Alcanzado'] = pd.to_numeric(df['Profit Alcanzado'], errors='coerce')
        df['Profit Media'] = pd.to_numeric(df['Profit Media'], errors='coerce')
        
        # Crear el gráfico de tendencia
        fig = go.Figure()
        
        # Agregar cada línea con su color correspondiente
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['Profit Tot.'],
            mode='lines',
            name='Profit Tot.',
            line=dict(color='green'),
            hoverinfo='text+y'
        ))
        
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['Profit Alcanzado'],
            mode='lines',
            name='Profit Alcanzado',
            line=dict(color='violet'),
            hoverinfo='text+y'
        ))
        
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['Profit Media'],
            mode='lines',
            name='Profit Media',
            line=dict(color='lightblue'),
            hoverinfo='text+y'
        ))
        
        # Personalizar el layout
        fig.update_layout(
            title='Gráfico de Tendencia Profit',
            xaxis_title='Operación',
            yaxis_title='Valor',
            showlegend=True,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(
                showgrid=True,
                gridcolor='rgba(0,0,0,0.1)',
                showticklabels=True
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='rgba(0,0,0,0.1)'
            )
        )
        
        st.plotly_chart(fig, use_container_width=True, key=f"grafico_tendencia_{columna}")
    except Exception as e:
        st.error(f"❌ Error al crear el gráfico de tendencia: {str(e)}")

def mostrar_grafico_tiempo_operacion(df, numero_grafico=1):
    """
    Muestra un gráfico de dispersión con el tiempo en el eje X y el número de operación en el eje Y.
    Excluye automáticamente las operaciones con Deposito o Retiro.
    Args:
        df: DataFrame con los datos
        numero_grafico: Número que identifica si es el primer o segundo gráfico (1 o 2)
    """
    try:
        # Convertir los tiempos a minutos
        df['T. Op Minutos'] = df['T. Op'].apply(convertir_tiempo_a_minutos)
        
        # Convertir Profit a numérico
        df['Profit'] = pd.to_numeric(df['Profit'], errors='coerce')
        
        # Filtrar el DataFrame para excluir filas con Deposito o Retiro
        df_sin_dep_ret = df[
            (df['Deposito'].isna() | df['Deposito'].eq('')) & 
            (df['Retiro'].isna() | df['Retiro'].eq(''))
        ].copy()
        
        # Crear un selector múltiple para excluir operaciones adicionales
        operaciones_a_excluir = st.multiselect(
            'Selecciona operaciones adicionales a excluir:',
            options=df_sin_dep_ret.index.tolist(),
            key=f"excluir_tiempo_{numero_grafico}"
        )
        
        # Filtrar el DataFrame excluyendo las operaciones seleccionadas
        if operaciones_a_excluir:
            df_sin_dep_ret = df_sin_dep_ret[~df_sin_dep_ret.index.isin(operaciones_a_excluir)]
        
        # Separar los valores según el Profit
        df_positivo = df_sin_dep_ret[df_sin_dep_ret['Profit'] > 0]
        df_negativo = df_sin_dep_ret[df_sin_dep_ret['Profit'] < 0]
        df_cero = df_sin_dep_ret[df_sin_dep_ret['Profit'] == 0]
        
        # Crear el gráfico de dispersión
    fig = go.Figure()
        
        # Agregar puntos para valores con Profit positivo (verdes)
        if not df_positivo.empty:
            fig.add_trace(go.Scatter(
                x=df_positivo['T. Op Minutos'],
                y=df_positivo.index,
                mode='markers',
                name='Profit Positivo',
                marker=dict(
                    color='green',
                    size=15,
                )
            ))
        
        # Agregar puntos para valores con Profit negativo (rojos)
        if not df_negativo.empty:
            fig.add_trace(go.Scatter(
                x=-df_negativo['T. Op Minutos'],  # Invertir el tiempo para mostrar a la izquierda
                y=df_negativo.index,
                mode='markers',
                name='Profit Negativo',
                marker=dict(
                    color='red',
                    size=15,
                )
            ))
        
        # Agregar puntos para valores con Profit cero (amarillos)
        if not df_cero.empty:
            fig.add_trace(go.Scatter(
                x=df_cero['T. Op Minutos'],
                y=df_cero.index,
                mode='markers',
                name='Profit Cero',
                marker=dict(
                    color='yellow',
                    size=15,
                )
            ))
        
        # Configurar el layout del gráfico
        fig.update_layout(
            title=f'Tiempo de Operación vs Número de Operación - Gráfico {numero_grafico}',
            xaxis_title='Tiempo (minutos)',
            yaxis_title='Número de Operación',
            showlegend=True,
            plot_bgcolor='rgba(0,0,0,0)',  # Fondo transparente
            paper_bgcolor='rgba(0,0,0,0)',  # Fondo del papel transparente
            xaxis=dict(
                range=[-max(df_sin_dep_ret['T. Op Minutos'].max(), abs(df_sin_dep_ret['T. Op Minutos'].min())),
                       max(df_sin_dep_ret['T. Op Minutos'].max(), abs(df_sin_dep_ret['T. Op Minutos'].min()))]
            )
        )
        
        # Mostrar el gráfico
    st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error al crear el gráfico de tiempo de operación: {str(e)}")
        st.error(f"Valores en T. Op: {df['T. Op'].head().tolist()}")

def mostrar_grafico_puntos(df, columna, numero_grafico=1):
    """Muestra un gráfico de dispersión de puntos"""
    try:
        # Crear una copia del DataFrame excluyendo DEP y RET
        df_sin_dep_ret = df[~df['Activo'].str.contains('DEP|RET', na=False)].copy()
        
        # Convertir la columna Profit a numérico
        df_sin_dep_ret['Profit'] = pd.to_numeric(df_sin_dep_ret['Profit'], errors='coerce')
        
        # Crear un selector múltiple para excluir operaciones adicionales
        operaciones_a_excluir = st.multiselect(
            'Selecciona operaciones adicionales a excluir:',
            options=df_sin_dep_ret.index.tolist(),
            key=f"excluir_puntos_{numero_grafico}"
        )
        
        # Filtrar el DataFrame excluyendo las operaciones seleccionadas
        if operaciones_a_excluir:
            df_sin_dep_ret = df_sin_dep_ret[~df_sin_dep_ret.index.isin(operaciones_a_excluir)]
        
        # Separar los valores según el Profit
        df_positivo = df_sin_dep_ret[df_sin_dep_ret['Profit'] > 0]
        df_negativo = df_sin_dep_ret[df_sin_dep_ret['Profit'] < 0]
        df_cero = df_sin_dep_ret[df_sin_dep_ret['Profit'] == 0]
        
        # Crear el gráfico de dispersión
    fig = go.Figure()
        
        # Agregar puntos para valores con Profit positivo (verdes)
        if not df_positivo.empty:
            fig.add_trace(go.Scatter(
                x=df_positivo.index,
                y=df_positivo['Profit'],
                mode='markers',
                marker=dict(color='green', size=12),
                name='Profit Positivo'
            ))
        
        # Agregar puntos para valores con Profit negativo (rojos)
        if not df_negativo.empty:
            fig.add_trace(go.Scatter(
                x=df_negativo.index,
                y=df_negativo['Profit'],
                mode='markers',
                marker=dict(color='red', size=12),
                name='Profit Negativo'
            ))
        
        # Agregar puntos para valores con Profit cero (amarillos)
        if not df_cero.empty:
            fig.add_trace(go.Scatter(
                x=df_cero.index,
                y=df_cero['Profit'],
                mode='markers',
                marker=dict(color='yellow', size=12),
                name='Profit Cero'
            ))
        
        # Configurar el layout del gráfico
        fig.update_layout(
            title='Distribución de Profit por Operación',
            xaxis_title='Número de Operación',
            yaxis_title='Profit',
            showlegend=True
        )
        
        # Mostrar el gráfico
        st.plotly_chart(fig, use_container_width=True, key=f"grafico_puntos_{numero_grafico}")
        
    except Exception as e:
        st.error(f"Error al mostrar el gráfico de puntos: {str(e)}")

def convertir_tiempo_a_minutos(tiempo_str):
    """
    Convierte un string de tiempo en formato 'd h m' a minutos.
    Args:
        tiempo_str: String con el tiempo en formato 'd h m'
    Returns:
        int: Tiempo en minutos
    """
    try:
        if pd.isna(tiempo_str) or tiempo_str == '':
            return 0
            
        # Dividir el string en sus componentes
        partes = tiempo_str.split()
        minutos = 0
        
        # Procesar cada parte
        for i in range(0, len(partes), 2):
            valor = int(partes[i])
            unidad = partes[i+1]
            
            if unidad == 'd':
                minutos += valor * 24 * 60
            elif unidad == 'h':
                minutos += valor * 60
            elif unidad == 'm':
                minutos += valor
        
        return minutos
    except:
        return 0