import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import os
import json

def mostrar_profit_trend_interactivo(df: pd.DataFrame, chart_key: str) -> None:
    cols_req = ['Profit Tot.', 'Profit Alcanzado', 'Profit Media']
    if df.empty or not all(col in df.columns for col in cols_req):
        st.warning("No hay datos")
        return

    json_file = f"{chart_key}_excl.json"
    defaults = {
        "indices": [],
        "series": {"Profit Tot.": True, "Profit Alcanzado": True, "Profit Media": True}
    }

    if os.path.exists(json_file):
        try:
            raw = json.load(open(json_file, 'r'))
            if isinstance(raw, list):
                excl_data = {"indices": raw, "series": defaults["series"]}
            elif isinstance(raw, dict):
                excl_data = {
                    "indices": raw.get("indices", []),
                    "series": {
                        "Profit Tot.": raw.get("series", {}).get("Profit Tot.", True),
                        "Profit Alcanzado": raw.get("series", {}).get("Profit Alcanzado", True),
                        "Profit Media": raw.get("series", {}).get("Profit Media", True),
                    }
                }
            else:
                excl_data = defaults.copy()
        except Exception:
            excl_data = defaults.copy()
    else:
        excl_data = defaults.copy()

    # Pestañas de controles
    tab_lineas, tab_ops = st.tabs(["Excluir Líneas", "Excluir Operaciones"])

    with tab_lineas:
        cols = st.columns(3)
        with cols[0]:
            show_tot = st.checkbox("🟢 Profit", value=excl_data["series"]["Profit Tot."], key=f"tot_{chart_key}")
        with cols[1]:
            show_alc = st.checkbox("🟣 Profit Alcanzado", value=excl_data["series"]["Profit Alcanzado"], key=f"alc_{chart_key}")
        with cols[2]:
            show_med = st.checkbox("🔵 Profit Media", value=excl_data["series"]["Profit Media"], key=f"med_{chart_key}")

    with tab_ops:
        excl_idx = st.multiselect(
            label="",
            options=list(df.index),
            default=excl_data["indices"],
            key=f"ms_{chart_key}"
        )

    # Guardar estado
    excl_data = {
        "indices": excl_idx,
        "series": {
            "Profit Tot.": show_tot,
            "Profit Alcanzado": show_alc,
            "Profit Media": show_med
        }
    }
    try:
        with open(json_file, 'w') as f:
            json.dump(excl_data, f)
    except Exception:
        pass

    # Preparar datos filtrados
    sub_df = df.loc[~df.index.isin(excl_data["indices"]), cols_req].copy()
    sub_df = sub_df.apply(lambda s: pd.to_numeric(
        s.astype(str).str.replace('[,%]', '', regex=True),
        errors='coerce'
    ).fillna(0.0))

    # Construir el gráfico
    fig = go.Figure()
    if show_tot:
        fig.add_trace(go.Scatter(
            x=sub_df.index,
            y=sub_df['Profit Tot.'],
            mode='lines',
            line=dict(color='green', width=2)
        ))
    if show_alc:
        fig.add_trace(go.Scatter(
            x=sub_df.index,
            y=sub_df['Profit Alcanzado'],
            mode='lines',
            line=dict(color='violet', width=2)
        ))
    if show_med:
        fig.add_trace(go.Scatter(
            x=sub_df.index,
            y=sub_df['Profit Media'],
            mode='lines',
            line=dict(color='blue', width=2)
        ))

    fig.update_layout(
        xaxis_title='Índice',
        yaxis_title='Valor',
        template='plotly_dark',
        showlegend=False  # oculta la leyenda pero mantiene los colores
    )

    st.plotly_chart(fig, use_container_width=True, key=chart_key)


