import os
import json
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

def mostrar_profit_interactivo(df: pd.DataFrame, chart_key: str) -> None:
    """Gráfico de barras interactivo con pestañas para excluir índices y depósitos/retiros,
    persistencia en JSON y exclusión por defecto de índice 0 que puedes ajustar."""
    json_file = f"{chart_key}_excl.json"

    # — cargar JSON si existe, o preparar raw "vacío" —
    if os.path.exists(json_file):
        try:
            raw = json.load(open(json_file, 'r'))
        except Exception:
            raw = {}
    else:
        raw = None  # señal de "primera vez"

    # determinar exclusiones iniciales
    if isinstance(raw, dict):
        excl_indices = raw.get("indices", [])
        excl_dep     = raw.get("deposito", False)
        excl_ret     = raw.get("retiro", False)
    else:
        # primera vez: excluimos por defecto 0
        excl_indices = [0] if 0 in df.index else []
        excl_dep = False
        excl_ret = False

    # no avanzar si falta Profit
    if 'Profit' not in df.columns or df.empty:
        st.warning("No hay datos")
        return

    # convertir Profit a numérico
    profit = pd.to_numeric(df['Profit'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)

    # detectar depósitos/retiros
    if 'Deposito o Retiro' in df.columns:
        dr = df['Deposito o Retiro'].astype(str).str.strip().str.lower()
        is_deposito = dr == 'deposito'
        is_retiro   = dr == 'retiro'
    else:
        is_deposito = df.get('Deposito', pd.Series(False, index=df.index)).notna() & (df.get('Deposito') != 0)
        is_retiro   = df.get('Retiro',   pd.Series(False, index=df.index)).notna()   & (df.get('Retiro')   != 0)

    # — UI en pestañas —
    tab_idxs, tab_dr = st.tabs(["Excluir Índices", "Filtros Depósitos/Retiros"])

    with tab_idxs:
        valid_indices = list(df.index)
        excl_indices = [i for i in excl_indices if i in valid_indices]

        excl_indices = st.multiselect(
        "Selecciona índices a excluir:",
        options=valid_indices,
        default=excl_indices,
        key=f"{chart_key}_ms"
    )


    with tab_dr:
        col_dep, col_ret = st.columns(2)
        excl_dep = col_dep.checkbox(
            "⚪ Excluir Depósitos",
            value=excl_dep,
            key=f"{chart_key}_dep"
        )
        excl_ret = col_ret.checkbox(
            "🩷 Excluir Retiros",
            value=excl_ret,
            key=f"{chart_key}_ret"
        )

    # — guardar configuración actualizada —
    cfg = {
        "indices": excl_indices,
        "deposito": excl_dep,
        "retiro": excl_ret
    }
    try:
        with open(json_file, 'w') as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        st.error(f"Error al guardar configuración: {e}")

    # — aplicar exclusiones al serie de profit —
    mask = ~profit.index.isin(excl_indices)
    profit = profit[mask]
    if excl_dep:
        profit = profit[~is_deposito.loc[profit.index]]
    if excl_ret:
        profit = profit[~is_retiro.loc[profit.index]]

    # — separar positivos/negativos y trazar —
    pos = profit[profit > 0]
    neg = profit[profit < 0]

    fig = go.Figure()
    if not pos.empty:
        fig.add_trace(go.Bar(x=pos.index, y=pos.values, name='Positivo', marker_color='green'))
    if not neg.empty:
        fig.add_trace(go.Bar(x=neg.index, y=neg.values, name='Negativo', marker_color='red'))

    fig.update_layout(
        barmode='group',
        xaxis_title='Índice',
        yaxis_title='Profit',
        template='plotly_dark',
        legend={'itemclick': 'toggle', 'itemdoubleclick': 'toggleothers'},
        showlegend=True
    )

    st.plotly_chart(fig, use_container_width=True, key=chart_key)
