import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import json


def comparativo_call_put_linea(df: pd.DataFrame, chart_key: str = "call_put_trend") -> None:
    if 'C&P' not in df.columns or 'Profit' not in df.columns:
        st.warning("Faltan columnas necesarias ('C&P' o 'Profit') en el DataFrame.")
        return

    df = df.copy().reset_index(drop=True)
    df["Index"] = df.index
    df_idx = list(df.index)

    # Configuración de JSON para exclusión y checkboxes
    json_file = f"{chart_key}_excl.json"
    defaults = {
        "indices": [],
        "series": {"CALL": True, "PUT": True}
    }

    if os.path.exists(json_file):
        try:
            raw = json.load(open(json_file, 'r'))
            excl_data = {
                "indices": [i for i in raw.get("indices", []) if i in df_idx],
                "series": {
                    "CALL": raw.get("series", {}).get("CALL", True),
                    "PUT": raw.get("series", {}).get("PUT", True)
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
            excl_data["series"]["CALL"] = st.checkbox("🟢 CALL", value=excl_data["series"].get("CALL", True), key=f"{chart_key}_call_checkbox")
        with col2:
            excl_data["series"]["PUT"] = st.checkbox("🔴 PUT", value=excl_data["series"].get("PUT", True), key=f"{chart_key}_put_checkbox")

    with tab2:
        excl_indices = st.multiselect("Excluir índices:", options=df_idx, default=excl_data["indices"], key=f"{chart_key}_exclude_indices")
        excl_data["indices"] = excl_indices

    # Guardar JSON actualizado
    with open(json_file, "w") as f:
        json.dump(excl_data, f, indent=2)

    # Aplicar exclusiones
    df = df.loc[~df.index.isin(excl_data["indices"])]
    df = df.reset_index(drop=True)
    df["Index"] = df.index

    df_call = df[df['C&P'].str.upper() == 'CALL']
    df_put = df[df['C&P'].str.upper() == 'PUT']

    call_cumsum = df_call['Profit'].cumsum()
    put_cumsum = df_put['Profit'].cumsum()

    fig = go.Figure()

    # Preparar datos para customdata
    call_customdata = df_call[['Profit']].to_numpy()
    put_customdata = df_put[['Profit']].to_numpy()

    if excl_data["series"].get("CALL", True) and not df_call.empty:
        fig.add_trace(go.Scatter(
            x=df_call.index,
            customdata=call_customdata,
            y=call_cumsum,
            mode='lines',
            name='CALL',
            line=dict(color='green'),
            hovertemplate='CALL<br>Índice: %{x}<br>Profit: %{customdata[0]}<br>Acumulado: %{y}<extra></extra>'
        ))

    if excl_data["series"].get("PUT", True) and not df_put.empty:
        fig.add_trace(go.Scatter(
            x=df_put.index,
            customdata=put_customdata,
            y=put_cumsum,
            mode='lines',
            name='PUT',
            line=dict(color='red'),
            hovertemplate='PUT<br>Índice: %{x}<br>Profit: %{customdata[0]}<br>Acumulado: %{y}<extra></extra>'
        ))

    fig.update_layout(
        title="Tendencia Acumulativa CALL vs PUT",
        xaxis_title="Operaciones (índice)",
        yaxis_title="Profit Acumulado",
        height=400,
        width=900,
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True, key=chart_key)
