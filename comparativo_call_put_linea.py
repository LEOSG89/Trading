import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

def comparativo_call_put_linea(df: pd.DataFrame, chart_key: str = "call_put_area") -> None:
    """
    Gráfico de área acumulativa para CALL vs PUT vs TOTAL,
    con checkbox para mostrar/ocultar series y resumen,
    y dos tablas en pestañas: CALL/PUT y General.
    """
    # 1) Validar columnas
    if 'C&P' not in df.columns or 'Profit' not in df.columns:
        st.warning("Faltan columnas necesarias ('C&P' o 'Profit') en el DataFrame.")
        return

    # 2) Copiar y reiniciar índice
    df = df.copy().reset_index(drop=True)

    # 3) Inyectar CSS (solo una vez)
    if 'css_call_put' not in st.session_state:
        st.markdown("""
        <style>
          [data-testid="column"] { padding: 0 !important; margin: 0 !important; }
          .stCheckbox>div { margin-bottom: 0.2rem; }
          .stCheckbox input[type="checkbox"] { margin: 0 4px 0 0; transform: scale(1.3); }
        </style>""", unsafe_allow_html=True)
        st.session_state['css_call_put'] = True

    # 4) Checkbox de series y de resumen
    c1, c2, c3, c4 = st.columns([1,1,1,1])
    with c1:
        mostrar_call  = st.checkbox("🟢 CALL",   value=True, key=f"{chart_key}_call_chk")
    with c2:
        mostrar_put   = st.checkbox("🔴 PUT",    value=True, key=f"{chart_key}_put_chk")
    with c3:
        mostrar_total = st.checkbox("🔵 TOTAL",  value=True, key=f"{chart_key}_total_chk")
    with c4:
        mostrar_resumen = st.checkbox("Mostrar resumen", value=True, key=f"{chart_key}_resumen_chk")

    # 5) Sub-DFs y acumulados
    df_call = df[df['C&P'].str.upper() == 'CALL']
    df_put  = df[df['C&P'].str.upper() == 'PUT']

    call_cumsum = df_call['Profit'].cumsum()
    put_cumsum  = df_put['Profit'].cumsum()

    call_full = call_cumsum.reindex(df.index, method='ffill').fillna(0)
    put_full  = put_cumsum.reindex(df.index, method='ffill').fillna(0)
    total_cumsum = call_full + put_full

    # 6) Construcción del gráfico
    fig = go.Figure()
    if mostrar_call and not df_call.empty:
        neg = call_cumsum.where(call_cumsum < 0, 0)
        pos = call_cumsum.where(call_cumsum > 0, 0)
        fig.add_trace(go.Scatter(
            x=df_call.index, y=neg, mode='lines',
            line=dict(color='rgba(255,0,0,1)', width=1),
            fill='tozeroy', fillcolor='rgba(255,0,0,0.1)'))
        fig.add_trace(go.Scatter(
            x=df_call.index, y=pos, mode='lines',
            line=dict(color='rgba(0,255,0,1)', width=1),
            fill='tozeroy', fillcolor='rgba(0,255,0,0.2)'))
    if mostrar_put and not df_put.empty:
        neg = put_cumsum.where(put_cumsum < 0, 0)
        pos = put_cumsum.where(put_cumsum > 0, 0)
        fig.add_trace(go.Scatter(
            x=df_put.index, y=neg, mode='lines',
            line=dict(color='rgba(255,0,0,1)', width=1),
            fill='tozeroy', fillcolor='rgba(255,0,0,0.1)'))
        fig.add_trace(go.Scatter(
            x=df_put.index, y=pos, mode='lines',
            line=dict(color='rgba(255,0,0,1)', width=1),
            fill='tozeroy', fillcolor='rgba(255,0,0,0.1)'))
    if mostrar_total:
        fig.add_trace(go.Scatter(
            x=df.index, y=total_cumsum, mode='lines',
            line=dict(color='cyan'), fill='tozeroy',
            fillcolor='rgba(0,255,255,0.1)'))

    fig.update_layout(
        xaxis_title="Operación (índice)",
        yaxis_title="Profit Acumulado",
        template='plotly_dark',
        height=400,
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True, key=chart_key)

    # 7) Resumen en tablas, si corresponde
    if mostrar_resumen:
        # Cálculo de métricas
        total_call    = call_full.iloc[-1] if not call_full.empty else 0.0
        total_put     = put_full.iloc[-1]  if not put_full.empty  else 0.0
        total_cp      = total_cumsum.iloc[-1] if not total_cumsum.empty else 0.0
        mask_otros    = ~df['C&P'].str.upper().isin(['CALL','PUT'])
        otros         = df.loc[mask_otros, 'Profit']
        total_dep     = otros[otros>0].sum()
        total_ret     = -otros[otros<0].sum()
        pct_call      = (total_call/total_dep*100) if total_dep else np.nan
        pct_put       = (total_put/total_dep*100)  if total_dep else np.nan
        pct_subida    = (total_cp/total_dep*100)   if total_dep else np.nan

        # Tablas en pestañas
        tab1, tab2 = st.tabs(["CALL/PUT", "General"])
        with tab1:
            df_cp = pd.DataFrame({
                'Métrica': ['Total CALL','Total PUT','% Subida CALL','% Subida PUT'],
                'Valor': [
                    f"{total_call:.2f}",
                    f"{total_put:.2f}",
                    f"{pct_call:.2f}%" if not np.isnan(pct_call) else 'N/A',
                    f"{pct_put:.2f}%"  if not np.isnan(pct_put)  else 'N/A'
                ]
            })
            st.table(df_cp)
        with tab2:
            df_gen = pd.DataFrame({
                'Métrica': ['Total CALL+PUT','Total depósitos','Total retiros','% Subida vs depósitos'],
                'Valor': [
                    f"{total_cp:.2f}",
                    f"{total_dep:.2f}",
                    f"{total_ret:.2f}",
                    f"{pct_subida:.2f}%" if not np.isnan(pct_subida) else 'N/A'
                ]
            })
            st.table(df_gen)
