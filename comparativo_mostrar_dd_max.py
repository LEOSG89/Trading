import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import os
import json


def detectar_tramos(dd_numeric: list, fechas: list, modo: str, df: pd.DataFrame) -> list:
    tramos = []
    in_tramo = False
    inicio = None
    valor_extremo = 0.0

    for idx, val in enumerate(dd_numeric):
        if val is None:
            # trata valores vacíos como cierre de tramo
            if in_tramo:
                fecha_inicio = fechas[inicio]
                fecha_fin = fechas[idx]
                duracion = fecha_fin - fecha_inicio
                duracion_str = f"{duracion.days}d {duracion.seconds // 3600}h {(duracion.seconds // 60) % 60}m"
                cantidad_ops = df.iloc[inicio:idx+1][
                    ~((df['Deposito'].notna() & df['Deposito'].ne(0)) |
                      (df['Retiro'].notna() & df['Retiro'].ne(0)))
                ].shape[0]
                tramos.append((inicio, idx, duracion_str, valor_extremo, duracion, cantidad_ops))
            in_tramo = False
            continue
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
                duracion_str = f"{duracion.days}d {duracion.seconds // 3600}h {(duracion.seconds // 60) % 60}m"
                cantidad_ops = df.iloc[inicio:idx+1][
                    ~((df['Deposito'].notna() & df['Deposito'].ne(0)) |
                      (df['Retiro'].notna() & df['Retiro'].ne(0)))
                ].shape[0]
                tramos.append((inicio, idx, duracion_str, valor_extremo, duracion, cantidad_ops))
                in_tramo = False

    if in_tramo and inicio is not None:
        fecha_inicio = fechas[inicio]
        fecha_fin = fechas[-1]
        duracion = fecha_fin - fecha_inicio
        duracion_str = f"{duracion.days}d {duracion.seconds // 3600}h {(duracion.seconds // 60) % 60}m"
        cantidad_ops = df.iloc[inicio:][
            ~((df['Deposito'].notna() & df['Deposito'].ne(0)) |
              (df['Retiro'].notna() & df['Retiro'].ne(0)))
        ].shape[0]
        tramos.append((inicio, len(fechas)-1, duracion_str, valor_extremo, duracion, cantidad_ops))

    return tramos


def mostrar_dd_max(df: pd.DataFrame, chart_key: str) -> None:
    safe_key = chart_key.replace('/', '_')
    config_path = f"{safe_key}_config.json"

    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                cfg = json.load(f)
        except (json.JSONDecodeError, IOError):
            cfg = {'sombras': True, 'ddw': True, 'dup': True}
    else:
        cfg = {'sombras': True, 'ddw': True, 'dup': True}

    col1, col2, col3 = st.columns(3)
    with col1:
        mostrar_sombras = st.checkbox("Sombras de racha", value=cfg['sombras'], key=f"{safe_key}_shapes")
    with col2:
        mostrar_ddw = st.checkbox("🔴Mostrar D.Dw", value=cfg['ddw'], key=f"{safe_key}_ddw")
    with col3:
        mostrar_dup = st.checkbox("🟢Mostrar D.Up", value=cfg['dup'], key=f"{safe_key}_dup")

    cfg.update({'sombras': mostrar_sombras, 'ddw': mostrar_ddw, 'dup': mostrar_dup})
    try:
        with open(config_path, 'w') as f:
            json.dump(cfg, f)
    except IOError:
        st.error(f"No se pudo guardar la configuración en {config_path}")

    if df.empty or 'DD/Max' not in df.columns or 'Fecha / Hora' not in df.columns:
        st.warning("Faltan datos o columnas necesarias.")
        return

    dd_raw = df['DD/Max']
    dd_series = pd.to_numeric(dd_raw.astype(str).str.rstrip('%'), errors='coerce')
    dd_list = [v if not pd.isna(v) else None for v in dd_series.tolist()]
    dd_clean = [v if v is not None else 0.0 for v in dd_list]

    fechas = pd.to_datetime(df['Fecha / Hora'], errors='coerce').tolist()

    tramos_ddw = detectar_tramos(dd_clean, fechas, 'ddw', df) if mostrar_ddw else []
    tramos_dup = detectar_tramos(dd_clean, fechas, 'dup', df) if mostrar_dup else []
    top5_ddw = sorted(tramos_ddw, key=lambda x: x[3])[:5]
    top5_dup = sorted(tramos_dup, key=lambda x: -x[3])[:5]

    numeric_vals = [v for v in dd_list if v is not None]
    y_max = max(numeric_vals) if numeric_vals else 0.0
    y_min = min(numeric_vals) if numeric_vals else 0.0
    pad = (y_max - y_min) * 0.1 if y_max != y_min else 1
    yt, yb = y_max + pad, y_min - pad

    fig = go.Figure()
    if mostrar_ddw:
        # Graficar DDw, excepto el último None (no mostrar punto en None)
        y_ddw = []
        total = len(dd_list)
        for i, v in enumerate(dd_list):
            if i == total - 1 and v is None:
                y_ddw.append(None)
            elif v is not None and v < 0:
                y_ddw.append(v)
            else:
                y_ddw.append(0)
        fig.add_trace(go.Scatter(
            x=list(range(total)),
            y=y_ddw,
            fill='tozeroy', mode='lines', line=dict(color='red'), showlegend=False,
            hovertemplate="Índice: %{x}<br>DD/Max: %{y:.2f}%<extra></extra>"
        ))
    if mostrar_dup:
        # Graficar DUp, excepto el último None
        y_dup = []
        total = len(dd_list)
        for i, v in enumerate(dd_list):
            if i == total - 1 and v is None:
                y_dup.append(None)
            elif v is not None and v > 0:
                y_dup.append(v)
            else:
                y_dup.append(0)
        fig.add_trace(go.Scatter(
            x=list(range(total)),
            y=y_dup,
            fill='tozeroy', mode='lines', line=dict(color='green'), showlegend=False,
            hovertemplate="Índice: %{x}<br>DD/Max: %{y:.2f}%<extra></extra>"
        ))

    if mostrar_sombras:
        for start, end, dur_str, val, _, ops in top5_ddw:
            fig.add_shape(
                type='rect', x0=start, x1=end, y0=yb, y1=yt,
                fillcolor='red', opacity=0.09, line_width=0, layer='below'
            )
            mid_x, mid_y = (start + end) / 2, (yb + yt) / 2
            info = f"Duración: {dur_str}<br>Máx Caída: {val:.2f}%<br>Ops: {ops}<extra></extra>"
            fig.add_trace(go.Scatter(
                x=[mid_x], y=[mid_y], mode='markers', marker=dict(size=20, color='rgba(0,0,0,0)'),
                hovertemplate=info, showlegend=False
            ))
        for start, end, dur_str, val, _, ops in top5_dup:
            fig.add_shape(
                type='rect', x0=start, x1=end, y0=yb, y1=yt,
                fillcolor='green', opacity=0.09, line_width=0, layer='below'
            )
            mid_x, mid_y = (start + end) / 2, (yb + yt) / 2
            info = f"Duración: {dur_str}<br>Máx Subida: {val:.2f}%<br>Ops: {ops}<extra></extra>"
            fig.add_trace(go.Scatter(
                x=[mid_x], y=[mid_y], mode='markers', marker=dict(size=20, color='rgba(0,0,0,0)'),
                hovertemplate=info, showlegend=False
            ))

    fig.update_layout(
        xaxis_title='Índice', yaxis_title='DD/Max (%)', template='plotly_dark', showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

    tab1, tab2 = st.tabs(['🔴 Top D.Dw', '🟢 Top D.Up'])
    with tab1:
        if top5_ddw:
            df_ddw = pd.DataFrame(top5_ddw, columns=['Desde','Hasta','Duración','Máx Caída','Duración TD','Ops'])
            df_ddw.set_index('Desde', inplace=True)
            df_ddw['Máx Caída'] = df_ddw['Máx Caída'].map(lambda x: f"{x:.2f}%")
            st.dataframe(df_ddw.drop(columns=['Duración TD']))
        else:
            st.info('No hay D.Dw')
    with tab2:
        if top5_dup:
            df_dup = pd.DataFrame(top5_dup, columns=['Desde','Hasta','Duración','Máx Subida','Duración TD','Ops'])
            df_dup.set_index('Desde', inplace=True)
            df_dup['Máx Subida'] = df_dup['Máx Subida'].map(lambda x: f"{x:.2f}%")
            st.dataframe(df_dup.drop(columns=['Duración TD']))
        else:
            st.info('No hay D.Up')
