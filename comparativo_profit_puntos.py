import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import os
import json

def cargar_configuracion_exclusiones(chart_key, df_idx):
    json_file = f"{chart_key}_excl.json"
    excl_data = {
        "indices": [],
        "series": {"cero": True, "positivo": True, "negativo": True},
        "dr": {"deposito": False, "retiro": False}
    }
    if os.path.exists(json_file):
        try:
            with open(json_file, 'r') as f:
                raw = json.load(f)
            if isinstance(raw, dict):
                excl_data["indices"] = [i for i in raw.get("indices", []) if i in df_idx]
                s = raw.get("series", {})
                excl_data["series"] = {
                    "cero":     s.get("cero", True),
                    "positivo": s.get("positivo", True),
                    "negativo": s.get("negativo", True)
                }
                dr = raw.get("dr", {})
                excl_data["dr"] = {
                    "deposito": dr.get("deposito", False),
                    "retiro":   dr.get("retiro", False)
                }
        except Exception:
            pass
    return excl_data

def guardar_configuracion_exclusiones(chart_key, excl_data):
    json_file = f"{chart_key}_excl.json"
    try:
        with open(json_file, 'w') as f:
            json.dump(excl_data, f, indent=2)
    except Exception:
        st.warning("No se pudo guardar la configuración de exclusión.")

def mostrar_profit_puntos(df: pd.DataFrame, chart_key: str) -> None:
    if 'Profit' not in df.columns:
        st.warning("Falta la columna 'Profit' en el DataFrame.")
        return

    st.markdown("""
    <style>
    [data-testid="column"] { padding: 0 !important; margin: 0 !important; }
    .stCheckbox>div { margin-bottom: 0.2rem; }
    .stCheckbox input[type="checkbox"] { margin: 0 4px 0 0; transform: scale(1.3); }
    </style>
    """, unsafe_allow_html=True)

    df_idx    = list(df.index)
    excl_data = cargar_configuracion_exclusiones(chart_key, df_idx)

    profit_str = df['Profit'].astype(str)
    profit_num = pd.to_numeric(profit_str.str.replace(',', ''), errors='coerce').fillna(0.0)

    # Detectar depósitos/retiros en distintas estructuras posibles
    if 'Deposito' in df.columns and 'Retiro' in df.columns:
        is_deposito = df['Deposito'].notna() & (df['Deposito'] != 0)
        is_retiro   = df['Retiro'].notna()   & (df['Retiro']   != 0)
    elif 'Deposito o Retiro' in df.columns:
        col_dr      = df['Deposito o Retiro'].astype(str).str.strip().str.lower()
        is_deposito = col_dr == 'deposito'
        is_retiro   = col_dr == 'retiro'
    else:
        is_deposito = pd.Series(False, index=df.index)
        is_retiro   = pd.Series(False, index=df.index)

    # Tres pestañas de control
    tab_color, tab_puntos, tab_dr = st.tabs([
        "Por Color", "Por Puntos", "Depósitos/Retiros"
    ])

    # 1) Por Color
    with tab_color:
        c0, c1, c2 = st.columns(3)
        show_cero     = c0.checkbox("🟡 Ceros",    value=excl_data['series']['cero'],     key=f"{chart_key}_cero")
        show_positivo = c1.checkbox("🟢 Positivos", value=excl_data['series']['positivo'], key=f"{chart_key}_positivo")
        show_negativo = c2.checkbox("🔴 Negativos", value=excl_data['series']['negativo'], key=f"{chart_key}_negativo")

    # 2) Por Puntos (exclusión manual)
    with tab_puntos:
        excl_indices = st.multiselect(
            "Excluir puntos manualmente:",
            options=df_idx,
            default=excl_data["indices"],
            key=f"ms_{chart_key}"
        )

    # 3) Depósitos / Retiros
    with tab_dr:
        d0, d1 = st.columns(2)
        excl_depositos = d0.checkbox("⚪ Excluir Depósitos",
                                      value=excl_data['dr']['deposito'],
                                      key=f"{chart_key}_exc_dep")
        excl_retiros   = d1.checkbox("💗 Excluir Retiros",
                                      value=excl_data['dr']['retiro'],
                                      key=f"{chart_key}_exc_ret")

    # Guardar configuración completa
    excl_data = {
        "indices": excl_indices,
        "series": {
            "cero":     show_cero,
            "positivo": show_positivo,
            "negativo": show_negativo
        },
        "dr": {
            "deposito": excl_depositos,
            "retiro":   excl_retiros
        }
    }
    guardar_configuracion_exclusiones(chart_key, excl_data)

    # Máscara base: excluye manual y según DR
    mask_base = pd.Series(True, index=df.index)
    mask_base &= ~pd.Series(df.index.isin(excl_indices), index=df.index)
    if excl_depositos:
        mask_base &= ~is_deposito
    if excl_retiros:
        mask_base &= ~is_retiro

    # Dibujar trazas por color sobre mask_base
    fig = go.Figure()
    condiciones = [
        (profit_num == 0, 'yellow', show_cero),
        (profit_num >  0, 'green',  show_positivo),
        (profit_num <  0, 'red',    show_negativo)
    ]
    for cond, color, visible in condiciones:
        if not visible:
            continue
        m = mask_base & cond
        if m.any():
            fig.add_trace(go.Scatter(
                x=profit_num[m].index,
                y=profit_num[m].values,
                mode='markers',
                marker=dict(color=color, size=15),
                text=profit_str.loc[m],
                hovertemplate='Índice: %{x}<br>Profit: %{text}',
                showlegend=False
            ))

    fig.update_layout(
        xaxis_title='Índice',
        yaxis_title='Profit',
        template='plotly_dark',
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True, key=chart_key)
