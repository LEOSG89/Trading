import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import os
import json
import re


def mostrar_tiempo_puntos(df: pd.DataFrame, chart_key: str) -> None:
    """
    Gráfico de puntos para la columna 'T. Op', con colores definidos por la columna 'Profit'.
    Permite excluir puntos por color mediante checkboxes, o excluir puntos individuales.
    Ambas exclusiones se pueden alternar mediante pestañas, con persistencia en JSON.
    """
    if 'T. Op' not in df.columns or 'Profit' not in df.columns:
        st.warning("Faltan columnas requeridas: 'T. Op' o 'Profit'.")
        return

    st.markdown("""
    <style>
    [data-testid="column"] { padding: 0 !important; margin: 0 !important; }
    .stCheckbox>div { margin-bottom: 0.2rem; }
    .stCheckbox input[type="checkbox"] { margin: 0 4px 0 0; transform: scale(1.3); }
    </style>
    """, unsafe_allow_html=True)

    df_idx = list(df.index)
    json_file = f"{chart_key}_excl.json"
    excl_file = f"{chart_key}_excl_puntos.json"

    excl_data = {'cero': False, 'positivo': False, 'negativo': False}
    excl_puntos = []

    if os.path.exists(json_file):
        try:
            with open(json_file, 'r') as f:
                loaded_data = json.load(f)
                if isinstance(loaded_data, dict):
                    excl_data.update(loaded_data)
        except Exception:
            pass

    if os.path.exists(excl_file):
        try:
            with open(excl_file, 'r') as f:
                excl_puntos = json.load(f)
        except Exception:
            excl_puntos = []

    excl_puntos = [i for i in excl_puntos if i in df_idx]

    tiempo_str_vals = df['T. Op'].astype(str)

    def convertir_a_minutos(t):
        minutos = 0
        if 'd' in t:
            dias = int(re.search(r'(\d+)d', t).group(1)) if re.search(r'(\d+)d', t) else 0
            minutos += dias * 24 * 60
        if 'h' in t:
            horas = int(re.search(r'(\d+)h', t).group(1)) if re.search(r'(\d+)h', t) else 0
            minutos += horas * 60
        if 'm' in t:
            mins = int(re.search(r'(\d+)m', t).group(1)) if re.search(r'(\d+)m', t) else 0
            minutos += mins
        return minutos

    tiempo_min = tiempo_str_vals.apply(convertir_a_minutos)
    tiempo_text = tiempo_str_vals

    profit_str_vals = df['Profit'].astype(str)
    profit_numeric = pd.to_numeric(profit_str_vals.str.replace(',', ''), errors='coerce').fillna(0.0)

    fig = go.Figure()

    tab1, tab2 = st.tabs(["Por Color", "Por Puntos"])

    with tab1:
        col1, col2, col3 = st.columns([1, 1, 1], gap="small")
        with col1:
            show_cero = not st.checkbox("🟡", value=excl_data['cero'], key=f"cb_{chart_key}_cero")
        with col2:
            show_positivo = not st.checkbox("🟢", value=excl_data['positivo'], key=f"cb_{chart_key}_positivo")
        with col3:
            show_negativo = not st.checkbox("🔴", value=excl_data['negativo'], key=f"cb_{chart_key}_negativo")

        conditions = [
            (profit_numeric == 0, 'yellow', show_cero),
            (profit_numeric > 0, 'green', show_positivo),
            (profit_numeric < 0, 'red', show_negativo)
        ]
    with tab2:
        excl_manual = st.multiselect(
            "Excluir puntos manualmente:",
            options=df_idx,
            default=excl_puntos,
            key=f"manual_{chart_key}_puntos"
        )
        excl_puntos = excl_manual

        conditions = [
            (profit_numeric == 0, 'yellow', not excl_data['cero']),
            (profit_numeric > 0, 'green', not excl_data['positivo']),
            (profit_numeric < 0, 'red', not excl_data['negativo'])
        ]

    for condition, color, show in conditions:
        if show:
            idx_valid = condition & ~condition.index.isin(excl_puntos)
            fig.add_trace(go.Scatter(
                x=tiempo_min[idx_valid].index,
                y=tiempo_min[idx_valid].values,
                mode='markers',
                marker=dict(color=color, size=15),
                text=tiempo_text.loc[idx_valid],
                hovertemplate='Índice: %{x}<br>Tiempo: %{text}',
                customdata=tiempo_min[idx_valid].index,
                showlegend=False
            ))

    try:
        with open(json_file, 'w') as f:
            json.dump({'cero': not show_cero, 'positivo': not show_positivo, 'negativo': not show_negativo}, f)
        with open(excl_file, 'w') as f:
            json.dump(excl_puntos, f)
    except Exception:
        st.warning("No se pudo guardar la configuración de exclusión.")

    fig.update_layout(
        xaxis_title='Índice',
        yaxis_title='Tiempo en minutos',
        template='plotly_dark',
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True, key=chart_key)
