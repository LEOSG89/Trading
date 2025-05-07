import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import os
import json

def detectar_tramos(dd_numeric: pd.Series, fechas: pd.Series, modo: str) -> list:
    tramos = []
    in_tramo = False
    inicio = None
    valor_extremo = 0.0

    for idx, val in dd_numeric.items():
        if not in_tramo and ((modo == 'ddw' and val < 0) or (modo == 'dup' and val > 0)):
            in_tramo = True
            inicio = idx
            valor_extremo = val
        elif in_tramo:
            if (modo == 'ddw' and val < valor_extremo) or (modo == 'dup' and val > valor_extremo):
                valor_extremo = val
            if (modo == 'ddw' and val >= 0) or (modo == 'dup' and val <= 0):
                fecha_inicio = fechas[inicio]
                fecha_fin = fechas[idx]
                duracion = fecha_fin - fecha_inicio
                duracion_str = f"{duracion.days}d {duracion.seconds//3600}h {(duracion.seconds//60)%60}m"
                duracion_td = duracion
                cantidad_ops = idx - inicio + 1
                tramos.append((inicio, idx, duracion_str, valor_extremo, duracion_td, cantidad_ops))
                in_tramo = False

    if in_tramo:
        fecha_inicio = fechas[inicio]
        fecha_fin = fechas.iloc[-1]
        duracion = fecha_fin - fecha_inicio
        duracion_str = f"{duracion.days}d {duracion.seconds//3600}h {(duracion.seconds//60)%60}m"
        duracion_td = duracion
        cantidad_ops = fechas.index[-1] - inicio + 1
        tramos.append((inicio, fechas.index[-1], duracion_str, valor_extremo, duracion_td, cantidad_ops))

    return tramos

def mostrar_dd_max(df: pd.DataFrame, chart_key: str) -> None:
    if df.empty or 'DD/Max' not in df.columns or 'Fecha / Hora' not in df.columns:
        st.warning("Faltan datos o columnas necesarias para mostrar D.Dw/D.Up.")
        return

    dd_str_vals = df['DD/Max'].astype(str)
    dd_numeric = pd.to_numeric(dd_str_vals.str.rstrip('%'), errors='coerce').fillna(0.0)
    fechas = pd.to_datetime(df['Fecha / Hora'], errors='coerce')

    df = df.copy()
    df['dd_val'] = dd_numeric
    df['signo_dd'] = df['dd_val'].apply(lambda v: 1 if v > 0 else -1 if v < 0 else 0)
    df['run_id_dd'] = (df['signo_dd'] != df['signo_dd'].shift()).cumsum()

    mostrar_tablas = True
    mostrar_ddw = True
    mostrar_dup = True

    tramos_ddw = detectar_tramos(dd_numeric, fechas, modo='ddw')
    tramos_dup = detectar_tramos(dd_numeric, fechas, modo='dup')

    top5_ddw = sorted(tramos_ddw, key=lambda x: x[3])[:5] if mostrar_ddw else []
    top5_dup = sorted(tramos_dup, key=lambda x: -x[3])[:5] if mostrar_dup else []

    # Gráfico de líneas con área y sombreado usando anotaciones invisibles para tooltip
    if mostrar_ddw or mostrar_dup:
        shapes = []
        annotations = []
        for i, tramo in enumerate(top5_ddw):
            shapes.append(dict(
                type='rect', xref='x', yref='paper',
                x0=tramo[0], x1=tramo[1], y0=0, y1=1,
                fillcolor='red', opacity=0.15, layer='below', line_width=0
            ))
            annotations.append(dict(
                x=(tramo[0] + tramo[1]) / 2,
                y=1.01,
                xref='x', yref='paper',
                text=f"Máx: {tramo[3]:.2f}%<br>Ops: {tramo[5]}",
                showarrow=False,
                font=dict(color='red', size=12),
                hovertext=f"Máx: {tramo[3]:.2f}%<br>Ops: {tramo[5]}",
                opacity=0
            ))
        for i, tramo in enumerate(top5_dup):
            shapes.append(dict(
                type='rect', xref='x', yref='paper',
                x0=tramo[0], x1=tramo[1], y0=0, y1=1,
                fillcolor='green', opacity=0.15, layer='below', line_width=0
            ))
            annotations.append(dict(
                x=(tramo[0] + tramo[1]) / 2,
                y=1.01,
                xref='x', yref='paper',
                text=f"Máx: {tramo[3]:.2f}%<br>Ops: {tramo[5]}",
                showarrow=False,
                font=dict(color='green', size=12),
                hovertext=f"Máx: {tramo[3]:.2f}%<br>Ops: {tramo[5]}",
                opacity=0
            ))

        fig = go.Figure()
        if mostrar_ddw:
            ddw_vals = dd_numeric.where(dd_numeric < 0, 0)
            fig.add_trace(go.Scatter(
                x=df.index,
                y=ddw_vals,
                fill='tozeroy',
                mode='lines',
                line=dict(color='red'),
                name='D.Dw',
                hovertemplate='Índice: %{x}<br>DD/Max: %{y:.2f}%'
            ))
        if mostrar_dup:
            dup_vals = dd_numeric.where(dd_numeric > 0, 0)
            fig.add_trace(go.Scatter(
                x=df.index,
                y=dup_vals,
                fill='tozeroy',
                mode='lines',
                line=dict(color='green'),
                name='D.Up',
                hovertemplate='Índice: %{x}<br>DD/Max: %{y:.2f}%'
            ))

        fig.update_layout(
            title="Gráfico DD/Max",
            xaxis_title="Índice",
            yaxis_title="DD/Max (%)",
            template="plotly_dark",
            showlegend=True,
            shapes=shapes,
            annotations=annotations
        )
        st.plotly_chart(fig, use_container_width=True)

    if mostrar_tablas and (mostrar_ddw or mostrar_dup):
        tab1, tab2 = st.tabs(["🔴 Top 5 tramos de D.Dw", "🟢 Top 5 tramos de D.Up"])
        with tab1:
            if mostrar_ddw:
                df_ddw = pd.DataFrame(top5_ddw, columns=["Desde", "Hasta", "Duración", "Máxima Caída", "Duración TD", "Operaciones"]).set_index("Desde")
                df_ddw["Máxima Caída"] = df_ddw["Máxima Caída"].map(lambda x: f"{x:.2f}%")
                df_ddw["Racha D. dw"] = df_ddw["Duración TD"].map(lambda td: td.total_seconds() / 60 if pd.notna(td) else 0).map(lambda m: f"{int(m//60)}h {int(m%60)}m")
                df_ddw.drop(columns=["Duración TD"], inplace=True)
                st.table(df_ddw)
            else:
                st.info("No hay datos disponibles para D.Dw.")
        with tab2:
            if mostrar_dup:
                df_dup = pd.DataFrame(top5_dup, columns=["Desde", "Hasta", "Duración", "Máxima Subida", "Duración TD", "Operaciones"]).set_index("Desde")
                df_dup["Máxima Subida"] = df_dup["Máxima Subida"].map(lambda x: f"{x:.2f}%")
                df_dup["Racha D. up"] = df_dup["Duración TD"].map(lambda td: td.total_seconds() / 60 if pd.notna(td) else 0).map(lambda m: f"{int(m//60)}h {int(m%60)}m")
                df_dup.drop(columns=["Duración TD"], inplace=True)
                st.table(df_dup)
            else:
                st.info("No hay datos disponibles para D.Up.")
