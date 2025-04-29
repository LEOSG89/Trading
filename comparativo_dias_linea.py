import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import json


def comparativo_dias_linea(df: pd.DataFrame, chart_key: str = "dias_line_chart") -> None:
    if 'C&P' not in df.columns or 'Profit' not in df.columns or 'Día' not in df.columns:
        st.warning("Faltan columnas necesarias ('C&P', 'Profit' o 'Día') en el DataFrame.")
        return

    df = df.copy().reset_index(drop=True)
    df["Index"] = df.index
    df_idx = list(df.index)

    # Configuración inicial del archivo JSON
    json_file = f"{chart_key}_excl.json"
    dias_semana = ['Lu', 'Ma', 'Mi', 'Ju', 'Vi', 'Sa', 'Do']
    defaults = {
        "indices": [],
        "series": {dia: True for dia in dias_semana}
    }

    if os.path.exists(json_file):
        try:
            raw = json.load(open(json_file, 'r'))
            excl_data = {
                "indices": [i for i in raw.get("indices", []) if i in df_idx],
                "series": {dia: raw.get("series", {}).get(dia, True) for dia in dias_semana}
            }
        except Exception:
            excl_data = defaults
    else:
        excl_data = defaults

    # Estilo visual para los checkboxes
    st.markdown("""
    <style>
    [data-testid="column"] { padding: 0 !important; margin: 0 !important; }
    .stCheckbox>div { margin-bottom: 0.2rem; }
    .stCheckbox input[type="checkbox"] { margin: 0 4px 0 0; transform: scale(1.3); }
    </style>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Checkbox", "Exclusiones"])

    with tab1:
        cols = st.columns(7)
        for i, dia in enumerate(dias_semana):
            excl_data["series"][dia] = cols[i].checkbox(
                f"{dia}", value=excl_data["series"].get(dia, True), key=f"{chart_key}_{dia}_checkbox")

    with tab2:
        excl_indices = st.multiselect("Excluir índices:", options=df_idx, default=excl_data["indices"], key=f"{chart_key}_exclude_indices")
        excl_data["indices"] = excl_indices

    with open(json_file, "w") as f:
        json.dump(excl_data, f, indent=2)

    df = df.loc[~df.index.isin(excl_data["indices"])]
    df = df[df['C&P'].str.strip() != ""]  # Excluir vacíos en C&P
    df = df.reset_index(drop=True)
    df["Index"] = df.index

    fig = go.Figure()
    colores = ['blue', 'green', 'red', 'orange', 'purple', 'brown', 'gray']

    for i, dia in enumerate(dias_semana):
        if not excl_data["series"].get(dia, True):
            continue
        df_dia = df[df['Día'] == dia]
        if df_dia.empty:
            continue
        df_dia = df_dia.sort_values(by='Index')
        y = df_dia['Profit'].cumsum()
        fig.add_trace(go.Scatter(
            x=df_dia['Index'],
            y=y,
            mode='lines',
            name=f"{dia}",
            line=dict(color=colores[i % len(colores)]),
            hovertemplate=f"{dia}<br>Índice: %{{x}}<br>Acumulado: %{{y}}<extra></extra>"
        ))

    fig.update_layout(
        title="Suma Acumulativa de Profit por Día de la Semana",
        xaxis_title="Operaciones (índice)",
        yaxis_title="Profit Acumulado",
        height=400,
        width=900,
        showlegend=True
    )

    st.plotly_chart(fig, use_container_width=True, key=chart_key) 