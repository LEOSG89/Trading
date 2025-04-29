import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import json

def comparativo_trade_diario_apilado(df: pd.DataFrame, chart_key: str = "trade_diario_apilado") -> None:
    if 'C&P' not in df.columns or 'Fecha / Hora' not in df.columns:
        st.warning("Faltan columnas necesarias ('C&P' o 'Fecha / Hora') en el DataFrame.")
        return

    df = df.copy()
    df = df[df['C&P'].str.strip() != ""]  # excluir depósitos y retiros
    df = df.reset_index(drop=True)
    df['Fecha'] = pd.to_datetime(df['Fecha / Hora']).dt.date.astype(str)
    fechas_unicas = df['Fecha'].unique().tolist()

    # Configuración de exclusiones
    chart_key = chart_key.replace('/', '_').replace('\\', '_').replace(' ', '_')
    json_file = f"{chart_key}_excl.json"
    defaults = {
        "series": {"CALL": True, "PUT": True},
        "excl_fechas": []
    }

    if os.path.exists(json_file):
        try:
            raw = json.load(open(json_file, 'r'))
            excl_data = {
                "series": {
                    "CALL": raw.get("series", {}).get("CALL", True),
                    "PUT": raw.get("series", {}).get("PUT", True)
                },
                "excl_fechas": [f for f in raw.get("excl_fechas", []) if f in fechas_unicas]
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
            excl_data['series']['CALL'] = st.checkbox("🟢 CALL", value=excl_data['series'].get("CALL", True), key=f"{chart_key}_checkbox_call")
        with col2:
            excl_data['series']['PUT'] = st.checkbox("🔴 PUT", value=excl_data['series'].get("PUT", True), key=f"{chart_key}_checkbox_put")

    with tab2:
        excl_fechas = st.multiselect("Excluir fechas:", options=fechas_unicas, default=excl_data['excl_fechas'], key=f"{chart_key}_exclude_fechas")
        excl_data['excl_fechas'] = excl_fechas

    with open(json_file, 'w') as f:
        json.dump(excl_data, f, indent=2)

    # Aplicar exclusiones
    df = df[~df['Fecha'].isin(excl_data['excl_fechas'])]

    # Agrupar y contar operaciones por día
    conteo = df.groupby(['Fecha', 'C&P']).size().unstack(fill_value=0)

    fechas = conteo.index.tolist()
    call_vals = conteo['CALL'] if 'CALL' in conteo.columns and excl_data['series']['CALL'] else [0] * len(fechas)
    put_vals = conteo['PUT'] if 'PUT' in conteo.columns and excl_data['series']['PUT'] else [0] * len(fechas)

    fig = go.Figure()
    if excl_data['series']['CALL']:
        fig.add_trace(go.Bar(
            x=fechas,
            y=call_vals,
            customdata=[[c + p] for c, p in zip(call_vals, put_vals)],
            hovertemplate='Fecha: %{x}<br>CALL: %{y}<br>Total: %{customdata[0]}<extra></extra>',
            name='CALL',
            marker_color='green'
        ))
    if excl_data['series']['PUT']:
        fig.add_trace(go.Bar(
            x=fechas,
            y=put_vals,
            customdata=[[c + p] for c, p in zip(call_vals, put_vals)],
            hovertemplate='Fecha: %{x}<br>PUT: %{y}<br>Total: %{customdata[0]}<extra></extra>',
            name='PUT',
            marker_color='red'
        ))

    fig.update_layout(
        barmode='stack',
        title="Cantidad de Operaciones por Día (Apilado CALL / PUT)",
        xaxis_title="Fecha",
        yaxis_title="Cantidad de Operaciones",
        height=400,
        width=900,
        showlegend=True
    )

    st.plotly_chart(fig, use_container_width=True, key=chart_key)
