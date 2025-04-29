import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os
import json

def histograma_profit_call_put(df: pd.DataFrame, chart_key: str = "histograma_call_put") -> None:
    if 'C&P' not in df.columns or 'Profit' not in df.columns:
        st.warning("Faltan columnas necesarias ('C&P' o 'Profit') en el DataFrame.")
        return

    df = df.copy().reset_index(drop=True)

    cols_to_check = ["Deposito", "Retiro"]
    cols_existentes = [col for col in cols_to_check if col in df.columns]
    if cols_existentes:
        df = df[df[cols_existentes].isnull().all(axis=1)]

    safe_chart_key = chart_key.replace("/", "_").replace("\\", "_").replace(":", "_")
    json_file = f"{safe_chart_key}_excl.json"
    defaults = {"series": {"CALL": True, "PUT": True, "JUNTOS": True}}

    if os.path.exists(json_file):
        try:
            with open(json_file, 'r') as f:
                raw = json.load(f)
            excl_data = {"series": {key: raw.get("series", {}).get(key, True) for key in defaults["series"]}}
        except Exception:
            excl_data = defaults
    else:
        excl_data = defaults

    st.markdown(
        """
        <style>
        [data-testid="column"] { padding: 0 !important; margin: 0 !important; }
        .stCheckbox>div { margin-bottom: 0.2rem; }
        .stCheckbox input[type="checkbox"] { margin: 0 4px 0 0; transform: scale(1.3); }
        </style>
        """, unsafe_allow_html=True
    )

    st.subheader("Opciones de visualización")
    col1, col2, col3 = st.columns(3)
    with col1:
        excl_data["series"]["CALL"] = st.checkbox("🟢 Ver CALL", value=excl_data["series"]["CALL"], key=f"{chart_key}_call")
    with col2:
        excl_data["series"]["PUT"] = st.checkbox("🔴 Ver PUT", value=excl_data["series"]["PUT"], key=f"{chart_key}_put")
    with col3:
        excl_data["series"]["JUNTOS"] = st.checkbox("🟣 Ver juntos", value=excl_data["series"]["JUNTOS"], key=f"{chart_key}_juntos")

    with open(json_file, "w") as f:
        json.dump(excl_data, f, indent=2)

    df_call = df[df['C&P'].str.upper() == 'CALL']
    df_put = df[df['C&P'].str.upper() == 'PUT']

    fig = go.Figure()
    # Número de series activas para calcular ancho
    n_series = sum(excl_data["series"].values()) or 1
    width_factor = 1.0

    def generar_histograma(df_subset, name, color_base):
        hist, bin_edges = np.histogram(df_subset['Profit'], bins=20)
        bin_centers = 0.5 * (bin_edges[1:] + bin_edges[:-1])

        if color_base == 'green':
            color = 'rgba(0, 200, 0, 0.7)'
        elif color_base == 'red':
            color = 'rgba(200, 0, 0, 0.7)'
        else:
            color = 'rgba(128, 0, 128, 0.7)'

        fig.add_trace(go.Bar(
            x=bin_centers,
            y=hist,
            name=name,
            marker_color=color,
            opacity=0.8,
            width=(bin_edges[1] - bin_edges[0]) * width_factor,
            customdata=np.stack((bin_edges[:-1], bin_edges[1:]), axis=-1),
            hovertemplate="Rango: %{customdata[0]:.2f} - %{customdata[1]:.2f}<br>Cant: %{y}<extra></extra>"
        ))

    if excl_data["series"]["CALL"] and not df_call.empty:
        generar_histograma(df_call, 'CALL', 'green')
    if excl_data["series"]["PUT"] and not df_put.empty:
        generar_histograma(df_put, 'PUT', 'red')
    if excl_data["series"]["JUNTOS"] and not df.empty:
        generar_histograma(df, 'CALL+PUT', 'purple')

    fig.update_layout(
        title="Histograma de Profit (CALL vs PUT)",
        xaxis_title="Profit",
        yaxis_title="Cantidad de operaciones",
        barmode='overlay',
        height=400,
        width=900
    )

    st.plotly_chart(fig, use_container_width=True, key=chart_key)
