import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import json

def comparativo_call_barra(df: pd.DataFrame, chart_key: str = "call_bar_chart") -> None:
    if 'C&P' not in df.columns or 'Profit' not in df.columns:
        st.warning("Faltan columnas necesarias ('C&P' o 'Profit') en el DataFrame.")
        return

    df = df.copy().reset_index(drop=True)
    df["Index"] = df.index
    df_idx = list(df.index)

    json_file = f"{chart_key}_excl.json"
    defaults = {
        "indices": [],
        "series": {"Ganadoras": True, "Perdedoras": True}
    }

    if os.path.exists(json_file):
        try:
            raw = json.load(open(json_file, 'r'))
            excl_data = {
                "indices": [i for i in raw.get("indices", []) if i in df_idx],
                "series": {
                    "Ganadoras": raw.get("series", {}).get("Ganadoras", True),
                    "Perdedoras": raw.get("series", {}).get("Perdedoras", True)
                }
            }
        except Exception:
            excl_data = defaults
    else:
        excl_data = defaults

    st.markdown("""
    <style>
    [data-testid="column"] { padding: 0 !important; margin: 0 !important; }
    .stCheckbox>div { margin-bottom: 0.2rem; }
    .stCheckbox input[type="checkbox"] { margin: 0 4px 0 0; transform: scale(1.3); }
    </style>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Checkbox", "Exclusiones"])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            excl_data["series"]["Ganadoras"] = st.checkbox("🟢 Ganadoras", value=excl_data["series"].get("Ganadoras", True), key=f"{chart_key}_ganadoras")
        with col2:
            excl_data["series"]["Perdedoras"] = st.checkbox("🔴 Perdedoras", value=excl_data["series"].get("Perdedoras", True), key=f"{chart_key}_perdedoras")

    with tab2:
        excl_indices = st.multiselect("Excluir índices:", options=df_idx, default=excl_data["indices"], key=f"{chart_key}_exclude_indices")
        excl_data["indices"] = excl_indices

    with open(json_file, "w") as f:
        json.dump(excl_data, f, indent=2)

    df = df.loc[~df.index.isin(excl_data["indices"])]
    df = df.reset_index(drop=True)
    df["Index"] = df.index

    df_call = df[df['C&P'].str.upper() == 'CALL']
    df_call = df_call.copy()

    # Clasificación por ganadoras y perdedoras
    condiciones = []
    if excl_data['series'].get("Ganadoras", True):
        condiciones.append(df_call['Profit'] >= 0)
    if excl_data['series'].get("Perdedoras", True):
        condiciones.append(df_call['Profit'] < 0)

    if condiciones:
        filtro = condiciones[0]
        for cond in condiciones[1:]:
            filtro |= cond
        df_call = df_call[filtro]

    colores = ['green' if p >= 0 else 'red' for p in df_call['Profit']]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_call['Index'],
        y=df_call['Profit'],
        marker_color=colores,
        name='CALL',
        hovertemplate='CALL<br>Índice: %{x}<br>Profit: %{y}<extra></extra>'
    ))

    fig.update_layout(
        title="Profit Individual de CALL (Barras)",
        xaxis_title="Operaciones (índice)",
        yaxis_title="Profit",
        height=400,
        width=900,
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True, key=chart_key) 