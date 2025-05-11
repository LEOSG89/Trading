import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import os
import json
import re


def mostrar_tiempo_puntos(df: pd.DataFrame, chart_key: str) -> None:
    """
    Gráfico de puntos para la columna 'T. Op', con colores definidos por la columna 'Profit',
    puntos especiales para depósitos (azul claro) y retiros (rosado).
    Permite excluir puntos por tipo (depósito/retiro), por resultados (positivo, cero, negativo),
    y puntos individuales. Todas las opciones persisten en JSON.
    """
    # Validar columnas necesarias
    for col in ['T. Op', 'Profit', 'Deposito', 'Retiro']:
        if col not in df.columns:
            st.warning(f"Falta la columna requerida: '{col}'.")
            return

    # Estilos personalizados
    st.markdown("""
    <style>
    [data-testid=\"column\"] { padding: 0 !important; margin: 0 !important; }
    .stCheckbox>div { margin-bottom: 0.2rem; }
    .stCheckbox input[type=\"checkbox\"] { margin: 0 4px 0 0; transform: scale(1.3); }
    </style>
    """, unsafe_allow_html=True)

    # Preparar índices y archivos JSON
    df_idx = list(df.index)
    settings_file = f"{chart_key}_excl.json"
    points_file   = f"{chart_key}_excl_puntos.json"

    # Cargar configuración previa
    excl_data = {'cero': False, 'positivo': False, 'negativo': False, 'deposito': False, 'retiro': False}
    excl_points = []
    if os.path.exists(settings_file):
        try:
            with open(settings_file, 'r') as f:
                data = json.load(f)
                if isinstance(data, dict): excl_data.update(data)
        except:
            pass
    if os.path.exists(points_file):
        try:
            with open(points_file, 'r') as f:
                excl_points = json.load(f)
        except:
            excl_points = []
    excl_points = [i for i in excl_points if i in df_idx]

    # Convertir 'T. Op' a minutos y crear formatos
    tiempo_str = df['T. Op'].astype(str)
    def to_min(t):
        d = int(re.search(r"(\d+)d", t).group(1)) if re.search(r"(\d+)d", t) else 0
        h = int(re.search(r"(\d+)h", t).group(1)) if re.search(r"(\d+)h", t) else 0
        m = int(re.search(r"(\d+)m", t).group(1)) if re.search(r"(\d+)m", t) else 0
        return d*1440 + h*60 + m
    tiempo_min = tiempo_str.apply(to_min)
    tiempo_fmt = {i: f"{tiempo_min[i]//1440}d {((tiempo_min[i]%1440)//60):02d}h {(tiempo_min[i]%60):02d}m" for i in df_idx}

    # Valores numéricos
    profit_num   = pd.to_numeric(df['Profit'].astype(str).str.replace(',',''), errors='coerce')
    deposito_num = pd.to_numeric(df['Deposito'].astype(str), errors='coerce').fillna(0)
    retiro_num   = pd.to_numeric(df['Retiro'].astype(str), errors='coerce').fillna(0)

    # Pestañas de exclusión
    tab_dep, tab_color, tab_points = st.tabs(["Depósitos/Retiro", "Por Color", "Por Puntos"])

    # Depósitos / Retiros (checkboxes lado a lado)
    with tab_dep:
        col1, col2 = st.columns(2, gap="small")
        with col1:
            ex_dep = st.checkbox("Excluir Depósitos", value=excl_data['deposito'], key=f"cb_{chart_key}_deposito")
        with col2:
            ex_ret = st.checkbox("Excluir Retiros",   value=excl_data['retiro'],   key=f"cb_{chart_key}_retiro")
        show_depositos = not ex_dep
        show_retiros   = not ex_ret

    # Por Color
    with tab_color:
        c1, c2, c3 = st.columns(3, gap="small")
        ex_cero = c1.checkbox("🟡", value=excl_data['cero'],     key=f"cb_{chart_key}_cero")
        ex_pos  = c2.checkbox("🟢", value=excl_data['positivo'], key=f"cb_{chart_key}_positivo")
        ex_neg  = c3.checkbox("🔴", value=excl_data['negativo'], key=f"cb_{chart_key}_negativo")
    show_cero = not ex_cero
    show_pos  = not ex_pos
    show_neg  = not ex_neg

    # Por Puntos
    with tab_points:
        excl_points = st.multiselect(
            "Excluir puntos manualmente:", df_idx,
            default=excl_points, key=f"manual_{chart_key}_puntos"
        )

    # Crear figura
    fig = go.Figure()

    # Depósitos
    if show_depositos:
        idx = (deposito_num > 0) & ~pd.Series(df_idx).isin(excl_points)
        xs = [i for i in df_idx if idx.loc[i]]
        ys = [tiempo_min[i] for i in xs]
        texts = [tiempo_fmt[i] for i in xs]
        fig.add_trace(go.Scatter(x=xs, y=ys, mode='markers', marker=dict(color='lightblue', size=20),
                                 customdata=[deposito_num.loc[i] for i in xs], text=texts,
                                 hovertemplate="Depósito: %{customdata}<br>Tiempo: %{text}<br>Índice: %{x}",
                                 showlegend=False))

    # Retiros
    if show_retiros:
        idx = (retiro_num > 0) & ~pd.Series(df_idx).isin(excl_points)
        xs = [i for i in df_idx if idx.loc[i]]
        ys = [tiempo_min[i] for i in xs]
        texts = [tiempo_fmt[i] for i in xs]
        fig.add_trace(go.Scatter(x=xs, y=ys, mode='markers', marker=dict(color='pink', size=20),
                                 customdata=[retiro_num.loc[i] for i in xs], text=texts,
                                 hovertemplate="Retiro: %{customdata}<br>Tiempo: %{text}<br>Índice: %{x}",
                                 showlegend=False))

    # Profit según color
    for cond, show, color_map in [
        (profit_num==0, show_cero,  lambda _: 'yellow'),
        (profit_num>0, show_pos,   lambda _: 'green'),
        (profit_num<0, show_neg,   lambda _: 'red')
    ]:
        if show:
            idx = cond & ~pd.Series(df_idx).isin(excl_points) & (deposito_num==0) & (retiro_num==0)
            xs = [i for i in df_idx if idx.loc[i]]
            ys = [tiempo_min[i] for i in xs]
            texts = [tiempo_fmt[i] for i in xs]
            colors = [color_map(profit_num.loc[i]) for i in xs]
            fig.add_trace(go.Scatter(x=xs, y=ys, mode='markers', marker=dict(color=colors, size=25),
                                     customdata=[profit_num.loc[i] for i in xs], text=texts,
                                     hovertemplate="Profit: %{customdata}<br>Tiempo: %{text}<br>Índice: %{x}",
                                     showlegend=False))

    # Guardar configuración
    try:
        with open(settings_file, 'w') as f:
            json.dump({'deposito': ex_dep, 'retiro': ex_ret,
                       'cero': ex_cero, 'positivo': ex_pos, 'negativo': ex_neg}, f)
        with open(points_file, 'w') as f:
            json.dump(excl_points, f)
    except:
        st.warning("No se pudo guardar la configuración de exclusión.")

    # Mostrar
    fig.update_layout(xaxis_title='Índice', yaxis_title='Tiempo (min)', template='plotly_dark', showlegend=False)
    st.plotly_chart(fig, use_container_width=True, key=f"{chart_key}_tiempo")

