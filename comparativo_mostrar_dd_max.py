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
                tramos.append((inicio, idx, duracion_str, valor_extremo))
                in_tramo = False

    if in_tramo:
        fecha_inicio = fechas[inicio]
        fecha_fin = fechas.iloc[-1]
        duracion = fecha_fin - fecha_inicio
        duracion_str = f"{duracion.days}d {duracion.seconds//3600}h {(duracion.seconds//60)%60}m"
        tramos.append((inicio, fechas.index[-1], duracion_str, valor_extremo))

    return tramos


def mostrar_dd_max(df: pd.DataFrame, chart_key: str) -> None:
    # Verificar columnas necesarias
    if 'DD/Max' not in df.columns or 'Fecha / Hora' not in df.columns:
        st.warning("Faltan las columnas necesarias en el DataFrame ('DD/Max' o 'Fecha / Hora').")
        return

    # Cargar o inicializar configuración
    chart_key_safe = chart_key.replace("/", "_").replace("\\", "_").replace(":", "_")
    json_file = f"{chart_key_safe}_settings.json"
    default_settings = {"mostrar_ddw": True, "mostrar_dup": True, "mostrar_grafico": True, "mostrar_tablas": True}
    if os.path.exists(json_file):
        try:
            with open(json_file, 'r') as f:
                settings = json.load(f)
            for k, v in default_settings.items():
                settings.setdefault(k, v)
        except:
            settings = default_settings.copy()
    else:
        settings = default_settings.copy()

    # Controles de usuario
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        mostrar_ddw = st.checkbox("🔴 D.Dw", value=settings["mostrar_ddw"], key=f"{chart_key_safe}_ddw")
    with col2:
        mostrar_dup = st.checkbox("🟢 D.Up", value=settings["mostrar_dup"], key=f"{chart_key_safe}_dup")
    with col3:
        mostrar_grafico = st.checkbox("📈 Mostrar gráfico", value=settings["mostrar_grafico"], key=f"{chart_key_safe}_grafico")
    with col4:
        mostrar_tablas = st.checkbox("📋 Mostrar tablas", value=settings["mostrar_tablas"], key=f"{chart_key_safe}_tablas")

    # Guardar configuración si cambió
    new_settings = {"mostrar_ddw": mostrar_ddw, "mostrar_dup": mostrar_dup,
                    "mostrar_grafico": mostrar_grafico, "mostrar_tablas": mostrar_tablas}
    if new_settings != settings:
        try:
            with open(json_file, 'w') as f:
                json.dump(new_settings, f)
        except:
            pass

    # Preparar datos
    dd_str_vals = df['DD/Max'].astype(str)
    dd_numeric = pd.to_numeric(dd_str_vals.str.rstrip('%'), errors='coerce').fillna(0.0)
    fechas = pd.to_datetime(df['Fecha / Hora'], errors='coerce')
    if dd_numeric.empty:
        st.info("No hay datos disponibles para mostrar.")
        return

    dd_negativos = dd_numeric.where(dd_numeric < 0, 0.0)
    dd_positivos = dd_numeric.where(dd_numeric > 0, 0.0)
    tramos_ddw = detectar_tramos(dd_numeric, fechas, modo='ddw')
    tramos_dup = detectar_tramos(dd_numeric, fechas, modo='dup')

    # Mostrar top 2 tramos
    col1, col2, col3, col4 = st.columns(4)
    if tramos_ddw:
        top_ddw = sorted(tramos_ddw, key=lambda x: x[3])[:2]
        with col1:
            if len(top_ddw) >= 1:
                _, _, dur0, val0 = top_ddw[0]
                st.markdown(f"<h6 style='text-align: center;'>{dur0}</h6>", unsafe_allow_html=True)
                st.markdown(f"<h6 style='text-align: center; color:red;'>{val0:.2f}%</h6>", unsafe_allow_html=True)
            else:
                st.markdown("<h6 style='text-align: center;'>N/A</h6>", unsafe_allow_html=True)
        with col2:
            if len(top_ddw) >= 2:
                _, _, dur1, val1 = top_ddw[1]
                st.markdown(f"<h6 style='text-align: center;'>{dur1}</h6>", unsafe_allow_html=True)
                st.markdown(f"<h6 style='text-align: center; color:red;'>{val1:.2f}%</h6>", unsafe_allow_html=True)
            else:
                st.markdown("<h6 style='text-align: center;'>N/A</h6>", unsafe_allow_html=True)

    if tramos_dup:
        top_dup = sorted(tramos_dup, key=lambda x: -x[3])[:2]
        with col3:
            if len(top_dup) >= 1:
                _, _, dur0, val0 = top_dup[0]
                st.markdown(f"<h6 style='text-align: center;'>{dur0}</h6>", unsafe_allow_html=True)
                st.markdown(f"<h6 style='text-align: center; color:green;'>{val0:.2f}%</h6>", unsafe_allow_html=True)
            else:
                st.markdown("<h6 style='text-align: center;'>N/A</h6>", unsafe_allow_html=True)
        with col4:
            if len(top_dup) >= 2:
                _, _, dur1, val1 = top_dup[1]
                st.markdown(f"<h6 style='text-align: center;'>{dur1}</h6>", unsafe_allow_html=True)
                st.markdown(f"<h6 style='text-align: center; color:green;'>{val1:.2f}%</h6>", unsafe_allow_html=True)
            else:
                st.markdown("<h6 style='text-align: center;'>N/A</h6>", unsafe_allow_html=True)

    # Gráfico de líneas
    if mostrar_grafico:
        fig = go.Figure()
        if mostrar_ddw and not dd_negativos.empty:
            fig.add_trace(go.Scatter(x=dd_negativos.index, y=dd_negativos.values,
                                     mode='lines', fill='tozeroy', line=dict(color='red'),
                                     text=dd_str_vals.loc[dd_negativos.index],
                                     hovertemplate='Índice: %{x}<br>DD/Max: %{text}', showlegend=False))
        if mostrar_dup and not dd_positivos.empty:
            fig.add_trace(go.Scatter(x=dd_positivos.index, y=dd_positivos.values,
                                     mode='lines', fill='tozeroy', line=dict(color='green'),
                                     text=dd_str_vals.loc[dd_positivos.index],
                                     hovertemplate='Índice: %{x}<br>DD/Max: %{text}', showlegend=False))
        if not fig.data:
            st.info("No hay gráficos seleccionados para mostrar.")
            return
        fig.update_layout(xaxis_title='Índice', yaxis_title='DD/Max (%)',
                          template='plotly_dark', showlegend=False)
        st.plotly_chart(fig, use_container_width=True, key=chart_key_safe)

    # Tablas de top 5 tramos
    if mostrar_tablas and (mostrar_ddw or mostrar_dup):
        tab1, tab2 = st.tabs(["🔴 Top 5 tramos de D.Dw", "🟢 Top 5 tramos de D.Up"])
        with tab1:
            if mostrar_ddw:
                top5_ddw = sorted(tramos_ddw, key=lambda x: x[3])[:5]
                df_ddw = pd.DataFrame(top5_ddw, columns=["Desde", "Hasta", "Duración", "Máxima Caída"]).set_index("Desde")
                df_ddw["Máxima Caída"] = df_ddw["Máxima Caída"].map(lambda x: f"{x:.2f}%")
                st.table(df_ddw)
            else:
                st.info("No hay datos disponibles para D.Dw.")
        with tab2:
            if mostrar_dup:
                top5_dup = sorted(tramos_dup, key=lambda x: -x[3])[:5]
                df_dup = pd.DataFrame(top5_dup, columns=["Desde", "Hasta", "Duración", "Máxima Subida"]).set_index("Desde")
                df_dup["Máxima Subida"] = df_dup["Máxima Subida"].map(lambda x: f"{x:.2f}%")
                st.table(df_dup)
            else:
                st.info("No hay datos disponibles para D.Up.")
