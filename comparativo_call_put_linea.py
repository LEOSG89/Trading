import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
import json

def comparativo_call_put_linea(df: pd.DataFrame, chart_key: str = "call_put_area") -> None:
    """
    Gráfico de área acumulativa para CALL vs PUT vs TOTAL,
    con checkbox para mostrar/ocultar series y resumen,
    y persistencia de estados mediante JSON.
    """
    # Validar columnas
    if 'C&P' not in df.columns or 'Profit' not in df.columns:
        st.warning("Faltan columnas necesarias ('C&P' o 'Profit') en el DataFrame.")
        return

    # Copiar DataFrame
    df = df.copy().reset_index(drop=True)

    # Inyectar CSS para checkboxes
    if 'css_call_put' not in st.session_state:
        st.markdown(
            """
            <style>
              [data-testid=\"column\"] { padding: 0 !important; margin: 0 !important; }
              .stCheckbox>div { margin-bottom: 0.2rem; }
              .stCheckbox input[type=\"checkbox\"] { margin: 0 4px 0 0; transform: scale(1.3); }
            </style>
            """, unsafe_allow_html=True)
        st.session_state['css_call_put'] = True

    # Ruta de estado
    state_file = f"{chart_key}_state.json"
    if os.path.exists(state_file):
        try:
            saved = json.load(open(state_file))
        except Exception:
            saved = {}
    else:
        saved = {}

    # Checkboxes
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        mostrar_call = st.checkbox("🟢CALL", value=saved.get('call', True), key=f"{chart_key}_call")
    with c2:
        mostrar_put = st.checkbox("🔴PUT", value=saved.get('put', True), key=f"{chart_key}_put")
    with c3:
        mostrar_total = st.checkbox("🔵TOTAL", value=saved.get('total', True), key=f"{chart_key}_total")
    with c4:
        mostrar_resumen = st.checkbox("RESUMEN", value=saved.get('resumen', True), key=f"{chart_key}_resumen")

    # Guardar estados
    new_state = {'call': mostrar_call, 'put': mostrar_put,
                 'total': mostrar_total, 'resumen': mostrar_resumen}
    with open(state_file, 'w') as f:
        json.dump(new_state, f)

    # Calcular acumulados
    profits = df['Profit']
    mask_call = df['C&P'].str.upper() == 'CALL'
    mask_put = df['C&P'].str.upper() == 'PUT'

    call_cumsum = profits.where(mask_call).cumsum()
    put_cumsum = profits.where(mask_put).cumsum()

    call_full = call_cumsum.reindex(df.index).ffill().fillna(0)
    put_full = put_cumsum.reindex(df.index).ffill().fillna(0)
    total_cumsum = call_full + put_full

    # Construir gráfico
    fig = go.Figure()
    if mostrar_call:
        pos = call_full.where(call_full > 0, 0)
        neg = call_full.where(call_full < 0, 0)
        fig.add_trace(go.Scatter(x=df.index, y=pos, mode='lines',
                                 name='CALL +', line=dict(color='green'),
                                 fill='tozeroy'))
        fig.add_trace(go.Scatter(x=df.index, y=neg, mode='lines',
                                 name='CALL -', line=dict(color='red'),
                                 fill='tozeroy'))
    if mostrar_put:
        pos = put_full.where(put_full > 0, 0)
        neg = put_full.where(put_full < 0, 0)
        fig.add_trace(go.Scatter(x=df.index, y=pos, mode='lines',
                                 name='PUT +', line=dict(color='red'),
                                 fill='tozeroy'))
        fig.add_trace(go.Scatter(x=df.index, y=neg, mode='lines',
                                 name='PUT -', showlegend=False,
                                 line=dict(color='red'), fill='tozeroy'))
    if mostrar_total:
        fig.add_trace(go.Scatter(x=df.index, y=total_cumsum, mode='lines',
                                 name='TOTAL', line=dict(color='cyan'),
                                 fill='tozeroy'))

    # Layout sin leyenda
    fig.update_layout(xaxis_title="Operación (índice)",
                      yaxis_title="Profit Acumulado",
                      template='plotly_dark', height=400,
                      showlegend=False)

    st.plotly_chart(fig, use_container_width=True, key=chart_key)

        # Tablas resumen
    if mostrar_resumen:
        total_call = call_full.iloc[-1]
        total_put = put_full.iloc[-1]
        total_all = total_cumsum.iloc[-1]
        otros = df.loc[~mask_call & ~mask_put, 'Profit'].fillna(0)
        deps = otros[otros > 0].sum()
        rets = -otros[otros < 0].sum()

        pct_call = total_call / deps * 100 if deps else np.nan
        pct_put = total_put / deps * 100 if deps else np.nan
        pct_all = total_all / deps * 100 if deps else np.nan

        tab1, tab2 = st.tabs(["CALL/PUT", "GENERAL"])
        with tab1:
            df_cp = pd.DataFrame({
                'Métrica': ['CALL', 'PUT'],
                'Valor': [
                    f"{total_call:.2f}",
                    f"{total_put:.2f}"
                ]
            })
            st.table(df_cp)
        with tab2:
            df_gen = pd.DataFrame({
                'Métrica': ['TOTAL', 'Depósitos', 'Retiros', '% vs dep'],
                'Valor': [
                    f"{total_all:.2f}",
                    f"{deps:.2f}",
                    f"{rets:.2f}",
                    f"{pct_all:.2f}%"
                ]
            })
            st.table(df_gen)
