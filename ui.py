import streamlit as st
import pandas as pd
import os, json
import config
from copia_tabla import copiar_datos_a_tabla
from botones import crear_botones_trading, crear_botones_iv_rank
from operations import agregar_operacion, procesar_deposito_retiro
from inversion import mostrar_sidebar_inversion
from riesgo_beneficio import render_riesgo_beneficio
from aciertos_beneficios import render_aciertos_beneficios
from capital import render_tabla_capital
from Op_ganadoras_perdedoras import render_operaciones_ganadoras_perdedoras
from esperanza_matematica import render_esperanza_matematica
from comparativos_graficos_barras import mostrar_profit_interactivo
from comparativos_graficos_linea import mostrar_profit_trend_interactivo
from comparativo_mostrar_dd_max import mostrar_dd_max
from comparativo_profit_area import mostrar_profit_area
from comparativo_profit_puntos import mostrar_profit_puntos
from comparativos_tiempo_puntos import mostrar_tiempo_puntos
from comparativo_call_put_linea import comparativo_call_put_linea
from Comparativo_call_barra import comparativo_call_barra
from comparativo_put_barra import comparativo_put_barra
from comparativo_dias_linea import comparativo_dias_linea
from comparativo_trade_diario_apilado import comparativo_trade_diario_apilado
from comparativo_profit_dia_semana import comparativo_profit_dia_semana
from comparativo_dona_call_put import comparativo_dona_call_put
from time_utils import calcular_tiempo_operacion_vectorizado, calcular_dia_live, calcular_tiempo_dr
from aplicar_color_general import aplicar_color_general
from tabla_ganancia_contratos_calculos import tabla_ganancia_contratos_calculos
from comparativo_histograma_profit_call_put import histograma_profit_call_put
from comparativo_racha_operaciones_dd_max import comparativo_racha_dd_max
from comparativo_mapa_calor_tiempo import mostrar_heatmaps_dia_hora
from calculos_tabla_principal import (
    calcular_profit_operacion, calcular_porcentaje_profit_op, calcular_profit_total,
    calcular_dd_max, calcular_dd_up, calcular_profit_t, calcular_profit_alcanzado_vectorizado,
    calcular_profit_media_vectorizado
)
from subir_archivo import subir_archivo
from eliminar_columnas_duplicadas_contador import limpiar_columnas
from tabla_editable_eliminar_renombrar_limpiar_columnas import tabla_editable_eliminar_renombrar_limpiar_columnas


SELECT_FILE = 'selected_asset.json'

st.set_page_config(page_title="Hoja de Trading", page_icon="📈", layout="wide")

def init_session():
    if os.path.exists(config.COL_FILE):
        try:
            with open(config.COL_FILE, 'r') as f:
                cols = json.load(f)
        except:
            cols = config.FIXED_COLS
    else:
        cols = config.FIXED_COLS
    if 'datos' not in st.session_state:
        st.session_state.datos = pd.DataFrame(columns=cols)
    if 'h' not in st.session_state or 'w' not in st.session_state:
        if os.path.exists(config.TABLE_FILE):
            try:
                with open(config.TABLE_FILE, 'r') as f:
                    cfg = json.load(f)
                st.session_state.h = cfg.get('height', 400)
                st.session_state.w = cfg.get('width', 800)
            except:
                st.session_state.h, st.session_state.w = 400, 800
        else:
            st.session_state.h, st.session_state.w = 400, 800
    if 'selected_asset' not in st.session_state:
        if os.path.exists(SELECT_FILE):
            try:
                with open(SELECT_FILE, 'r') as f:
                    sel = json.load(f)
                st.session_state.selected_asset = sel if sel in config.ASSETS else config.ASSETS[0]
            except:
                st.session_state.selected_asset = config.ASSETS[0]
        else:
            st.session_state.selected_asset = config.ASSETS[0]

init_session()
if 'pintar_colores' not in st.session_state:
    st.session_state.pintar_colores = False


with st.sidebar.expander("Cargar y Ajustes", expanded=True):
    subir_archivo()
    st.slider("Alto Vista", 200, 1200, st.session_state.h, key='h')
    st.slider("Ancho Vista", 200, 2000, st.session_state.w, key='w')
    st.markdown("### Ajustar Rangos de Gráficos")
    total_filas = len(st.session_state.datos) - 1
    tab1, tab2, tab3, tab4 = st.tabs(["Columna 1", "Columna 2", "Columna 3", "Columna 4"])

    for i, tab in enumerate([tab1, tab2, tab3, tab4], start=1):
        with tab:
            # Número real de filas y último índice
            rows = len(st.session_state.datos)
            max_idx = rows - 1

            if max_idx > 0:
                # Preset y cálculo de filas por defecto
                preset = st.radio(
                    "Preset", [50, 100, 150, 'ALL'],
                    index=1, horizontal=True,
                    key=f"preset_col{i}"
                )
                filas_default = max_idx if preset == 'ALL' else min(int(preset), max_idx)
                start = max(0, max_idx - filas_default)
                end   = max_idx

                # Slider sólo si max_idx > 0
                rango_slider = st.slider(
                    f"Rango de filas Gráfico Columna {i}",
                    min_value=0,
                    max_value=max_idx,
                    value=(start, end),
                    key=f"filas_col{i}"
                )
            else:
                st.info("No hay suficientes filas para seleccionar un rango.")
                # Forzamos un rango válido (0,0) cuando no hay suficientes filas
                rango_slider = (0, max_idx if max_idx >= 0 else 0)

            # Guardar y mostrar leyenda
            st.session_state[f"rango_col{i}"] = rango_slider
            st.caption(
                f"Mostrando filas desde **{rango_slider[0]}** "
                f"hasta **{rango_slider[1]}** de **{max_idx if max_idx>=0 else 0}** filas."
            )


    sel = st.selectbox(
        "Selecciona Activo",
        config.ASSETS,
        index=config.ASSETS.index(st.session_state.selected_asset),
        key='selected_asset'
    )
    st.number_input("Valor (solo DEP/RET)", value=0.0, key='input_valor')

    # Llamada al módulo de edición en pestañas
    st.session_state.datos = tabla_editable_eliminar_renombrar_limpiar_columnas(
        st.session_state.datos
    )

    with open(config.TABLE_FILE, 'w') as f:
        json.dump({'height': st.session_state.h, 'width': st.session_state.w}, f)
    with open(SELECT_FILE, 'w') as f:
     json.dump(sel, f)

df = st.session_state.datos.copy()
df = limpiar_columnas(df)

for col in ['Fecha / Hora', 'Fecha / Hora de Cierre']:
    if col in df:
        df[col] = pd.to_datetime(df[col], errors='coerce')

df = calcular_tiempo_operacion_vectorizado(df)
if '% Profit. Op' in df.columns and not pd.api.types.is_string_dtype(df['% Profit. Op']):
    df['% Profit. Op'] = df['% Profit. Op'].astype(str)

df = calcular_dia_live(df)
df = calcular_tiempo_dr(df)
df = calcular_profit_operacion(df)
df = calcular_porcentaje_profit_op(df)
df = procesar_deposito_retiro(df)
df = calcular_profit_total(df)
df = calcular_dd_max(df)
df = calcular_dd_up(df)
df = calcular_profit_alcanzado_vectorizado(df)
df = calcular_profit_media_vectorizado(df)
df = calcular_profit_t(df)

st.session_state.datos = df

render_riesgo_beneficio(df)
render_aciertos_beneficios(df)
render_operaciones_ganadoras_perdedoras(df)
render_tabla_capital(df)
mostrar_sidebar_inversion(df)
render_esperanza_matematica(df)

# ► Aquí inserto el expander en la barra lateral
with st.sidebar.expander("Ganancia por Contratos", expanded=True):
    tabla_ganancia_contratos_calculos()

# Expander: Modo de entrenamiento
with st.expander("Modo de entrenamiento", expanded=False):
    if 'pintar_colores' not in st.session_state:
        st.session_state.pintar_colores = True

    # Ahora sí: Actualiza el valor de pintar_colores
    st.session_state.pintar_colores = st.checkbox(
        "Aplicar colores en la tabla", 
        value=st.session_state.pintar_colores
    )

    crear_botones_trading()
    crear_botones_iv_rank()


# ➡️ Revisar si hay que desactivar colores
if st.session_state.get('pintar_colores_disable_pending', False):
    st.session_state.pintar_colores = False
    st.session_state.pintar_colores_disable_pending = False

# Tabs principales: Vista y Edición
tab_vista, tab_edicion = st.tabs(["Vista", "Edición"])

with tab_vista:
    df_vista = df.copy()
    if 'Contador' in df_vista.columns:
        df_vista = df_vista.drop(columns=['Contador'])
    styled_df_vista = aplicar_color_general(df_vista)



    opciones_graficos = {
           "Barras": mostrar_profit_interactivo,
           "Líneas": mostrar_profit_trend_interactivo,
           "DD/Max": mostrar_dd_max,
           "Área": mostrar_profit_area,
           "Puntos": mostrar_profit_puntos,
           "Tiempo": mostrar_tiempo_puntos,
           "CALL vs PUT Línea": comparativo_call_put_linea,
           "CALL Barras": comparativo_call_barra,
           "PUT Barras": comparativo_put_barra,
           "Días Línea": comparativo_dias_linea,
           "CALL/PUT por Día (Apilado)": comparativo_trade_diario_apilado,
           "Profit por Día de Semana": comparativo_profit_dia_semana,
           "Porcentaje Aciertos CALL PUT (Dona)": comparativo_dona_call_put,
            "Histograma Profit CALL/PUT": histograma_profit_call_put,
            "Racha Operaciones DD/Max": comparativo_racha_dd_max,
            "Mapa de calor Tiempo": mostrar_heatmaps_dia_hora,
    }

    if styled_df_vista is not None:
        st.dataframe(styled_df_vista, width=st.session_state.w, height=st.session_state.h)
    else:
        st.dataframe(df_vista, width=st.session_state.w, height=st.session_state.h)

    secciones = [("", "rango_col1", "rango_col2"), (" Secundarios", "rango_col3", "rango_col4")]
    for seccion, rango1, rango2 in secciones:
        expanded = True if seccion == "" else False
        with st.expander(f"Gráficos Comparativos{seccion}", expanded=expanded):
            select_col1, select_col2 = st.columns(2, gap="medium")
            with select_col1:
                grafico_col1 = st.selectbox(f"Gráfico Columna 1{seccion}", list(opciones_graficos.keys()), key=f"grafico_1{seccion}")
            with select_col2:
                grafico_col2 = st.selectbox(f"Gráfico Columna 2{seccion}", list(opciones_graficos.keys()), index=1, key=f"grafico_2{seccion}")
            col1, col2 = st.columns(2, gap="small")
            with col1:
                opciones_graficos[grafico_col1](df.iloc[st.session_state[rango1][0]:st.session_state[rango1][1]+1], chart_key=f"chart_1_{grafico_col1}{seccion}")
            with col2:
                opciones_graficos[grafico_col2](df.iloc[st.session_state[rango2][0]:st.session_state[rango2][1]+1], chart_key=f"chart_2_{grafico_col2}{seccion}")

with tab_edicion:
    df_ed = df.reset_index(drop=True).copy()
    df_ed.insert(0, 'Contador', df_ed.index)
    df_ed['Eliminar'] = False
    df_ed.drop(columns=['D'], inplace=True, errors='ignore')

    numeric_cols = ['#Cont', 'STRK Buy', 'STRK Sell', 'Deposito', 'Retiro', 'Profit']
    for col in numeric_cols:
        if col in df_ed.columns:
            df_ed[col] = pd.to_numeric(df_ed[col], errors='coerce')

    for txt in ['T. Op', 'Tiempo D/R', '% Profit. Op', 'Profit Tot.', 'Profit Alcanzado', 'Profit Media']:
        if txt in df_ed.columns:
            df_ed[txt] = df_ed[txt].fillna('').astype(str)

    col_config = {'Contador': st.column_config.NumberColumn("Contador", disabled=True)}
    for col in df_ed.columns[2:]:
        if pd.api.types.is_bool_dtype(df_ed[col]):
            continue
        elif pd.api.types.is_numeric_dtype(df_ed[col]):
            col_config[col] = st.column_config.NumberColumn(col)
        elif pd.api.types.is_datetime64_any_dtype(df_ed[col]):
            col_config[col] = st.column_config.DatetimeColumn(col)
        else:
            col_config[col] = st.column_config.TextColumn(col)

    edited = st.data_editor(df_ed, column_config=col_config, hide_index=True, width=st.session_state.w, height=st.session_state.h, num_rows="dynamic")
    filtered = edited[edited['Eliminar'] == False]
    filtered = filtered.drop(columns=['Contador', 'Eliminar']).reset_index(drop=True)
    st.session_state.datos = filtered 
