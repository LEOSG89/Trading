import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import json

def comparativo_call_put_linea(df: pd.DataFrame, chart_key: str = "call_put_area") -> None:
    """
    Gráfico de área acumulativa para CALL vs PUT vs TOTAL,
    con:
      - CALL en verde (>0) o rojo (<0), sin pintar en 0, con 30% de opacidad y línea superior
      - PUT en rojo (<0) y rojo intenso (>0), sin pintar en 0, con 30% de opacidad y línea superior
      - TOTAL en cian
      - Exclusión persistente de índices y series CALL/PUT/TOTAL
    """
    # 1) Validar columnas
    if 'C&P' not in df.columns or 'Profit' not in df.columns:
        st.warning("Faltan columnas necesarias ('C&P' o 'Profit') en el DataFrame.")
        return

    # 2) Reset índice y lista de índices
    df = df.copy().reset_index(drop=True)
    df_idx = list(df.index)

    # 3) Carga del estado de exclusiones
    json_file = f"{chart_key}_excl.json"
    defaults = {"indices": [], "series": {"CALL": True, "PUT": True, "TOTAL": True}}
    if os.path.exists(json_file):
        try:
            raw = json.load(open(json_file, 'r'))
            excl_data = {
                "indices": [i for i in raw.get("indices", []) if i in df_idx],
                "series": {
                    "CALL":  raw.get("series", {}).get("CALL",  True),
                    "PUT":   raw.get("series", {}).get("PUT",   True),
                    "TOTAL": raw.get("series", {}).get("TOTAL", True)
                }
            }
        except json.JSONDecodeError:
            excl_data = defaults
    else:
        excl_data = defaults

    # 4) Inyección de CSS (solo una vez)
    if 'css_call_put' not in st.session_state:
        st.markdown("""
        <style>
          [data-testid="column"] { padding: 0 !important; margin: 0 !important; }
          .stCheckbox>div { margin-bottom: 0.2rem; }
          .stCheckbox input[type="checkbox"] { margin: 0 4px 0 0; transform: scale(1.3); }
        </style>""", unsafe_allow_html=True)
        st.session_state['css_call_put'] = True

    # 5) Controles de usuario
    tab1, tab2 = st.tabs(["Series", "Exclusiones"])
    with tab1:
        c1, c2, c3 = st.columns(3)
        with c1:
            excl_data["series"]["CALL"] = st.checkbox(
                "🟢 CALL", value=excl_data["series"]["CALL"],
                key=f"{chart_key}_call_chk"
            )
        with c2:
            excl_data["series"]["PUT"] = st.checkbox(
                "🔴 PUT", value=excl_data["series"]["PUT"],
                key=f"{chart_key}_put_chk"
            )
        with c3:
            excl_data["series"]["TOTAL"] = st.checkbox(
                "🔵 TOTAL", value=excl_data["series"]["TOTAL"],
                key=f"{chart_key}_total_chk"
            )
    with tab2:
        excl_data["indices"] = st.multiselect(
            "Excluir índices:", options=df_idx,
            default=excl_data["indices"],
            key=f"{chart_key}_idxs"
        )

    # 6) Guardar estado
    with open(json_file, "w") as f:
        json.dump(excl_data, f, indent=2)

    # 7) Filtrar DataFrame
    df = df.loc[~df.index.isin(excl_data["indices"])].reset_index(drop=True)

    # 8) Sub-DFs y acumulados
    df_call = df[df['C&P'].str.upper() == 'CALL']
    df_put  = df[df['C&P'].str.upper() == 'PUT']
    call_cumsum  = df_call['Profit'].cumsum()
    put_cumsum   = df_put['Profit'].cumsum()
    total_cumsum = df['Profit'].cumsum()

    # 9) Construcción de la figura
    fig = go.Figure()

    # --- CALL: línea + área rojo (<0) y verde (>0), opacidad 30% ---
    if excl_data["series"]["CALL"] and not df_call.empty:
        profits_call = df_call['Profit'].to_numpy()
        neg_call = call_cumsum.where(call_cumsum < 0, 0)
        pos_call = call_cumsum.where(call_cumsum > 0, 0)

        # CALL < 0
        fig.add_trace(go.Scatter(
            x=df_call.index,
            y=neg_call,
            mode='lines',
            line=dict(color='rgba(255,0,0,1)', width=1),
            fill='tozeroy',
            fillcolor='rgba(255,0,0,0.3)',
            name='CALL < 0',
            customdata=profits_call,
            hovertemplate=(
                'CALL<br>Índice: %{x}<br>'
                'Profit: %{customdata[0]}<br>'
                'Acumulado: %{y}<extra></extra>'
            )
        ))
        # CALL > 0
        fig.add_trace(go.Scatter(
            x=df_call.index,
            y=pos_call,
            mode='lines',
            line=dict(color='rgba(0,255,0,1)', width=1),
            fill='tozeroy',
            fillcolor='rgba(0,255,0,0.2)',
            name='CALL > 0',
            customdata=profits_call,
            hovertemplate=(
                'CALL<br>Índice: %{x}<br>'
                'Profit: %{customdata[0]}<br>'
                'Acumulado: %{y}<extra></extra>'
            )
        ))

    # --- PUT: línea + área rojo semitransparente (<0) y rojo intenso (>0), opacidad 30% ---
    if excl_data["series"]["PUT"] and not df_put.empty:
        profits_put = df_put['Profit'].to_numpy()
        neg_put = put_cumsum.where(put_cumsum < 0, 0)
        pos_put = put_cumsum.where(put_cumsum > 0, 0)

        # PUT < 0
        fig.add_trace(go.Scatter(
            x=df_put.index,
            y=neg_put,
            mode='lines',
            line=dict(color='rgba(255,0,0,1)', width=1),
            fill='tozeroy',
            fillcolor='rgba(255,0,0,0.3)',
            name='PUT < 0',
            customdata=profits_put,
            hovertemplate=(
                'PUT<br>Índice: %{x}<br>'
                'Profit: %{customdata[0]}<br>'
                'Acumulado: %{y}<extra></extra>'
            )
        ))
        # PUT > 0
        fig.add_trace(go.Scatter(
            x=df_put.index,
            y=pos_put,
            mode='lines',
            line=dict(color='rgba(255,0,0,1)', width=1),
            fill='tozeroy',
            fillcolor='rgba(255,0,0,0.3)',
            name='PUT > 0',
            customdata=profits_put,
            hovertemplate=(
                'PUT<br>Índice: %{x}<br>'
                'Profit: %{customdata[0]}<br>'
                'Acumulado: %{y}<extra></extra>'
            )
        ))

    # --- TOTAL ---
    if excl_data["series"]["TOTAL"]:
        fig.add_trace(go.Scatter(
            x=df.index,
            y=total_cumsum,
            mode='lines',
            fill='tozeroy',
            name='TOTAL',
            line=dict(color='cyan'),
            customdata=df[['Profit']].to_numpy(),
            hovertemplate=(
                'TOTAL<br>Índice: %{x}<br>'
                'Profit: %{customdata[0]}<br>'
                'Acumulado: %{y}<extra></extra>'
            )
        ))

    # 10) Layout y renderizado
    fig.update_layout(
        title="Tendencia Acumulativa Area CALL vs PUT vs TOTAL",
        xaxis_title="Operaciones (índice)",
        yaxis_title="Profit Acumulado",
        template='plotly_dark',
        height=400,
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True, key=chart_key)
