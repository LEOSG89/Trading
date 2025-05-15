import streamlit as st
import time
from s3_utils import maybe_autosave

st.set_page_config(page_title="Hoja de Trading", page_icon="📈", layout="wide")

# 1) Mostrar mensaje si el autosave anterior dejó algo
if st.session_state.get("auto_save_message"):
    st.success(st.session_state.pop("auto_save_message"))

# 2) Inicializar flags solo una vez
if "data_modified" not in st.session_state:
    st.session_state.data_modified = False
if "last_auto_save" not in st.session_state:
    st.session_state.last_auto_save = time.time()

# 3) Intentar el auto‐save (con el mismo código que el botón)


# — ahora siguen tus otros imports —
import pandas as pd
import os, json
import config
from io import BytesIO

from auto_save_s3 import schedule_auto_save

from gestor_archivos_s3 import (
    list_saved_files,
    save_uploaded_file,
    load_file_df,
    delete_saved_file,
    update_file
)

# Inicializa flags en sesión
if "data_modified" not in st.session_state:
    st.session_state.data_modified = False
if "last_auto_save" not in st.session_state:
    st.session_state.last_auto_save = time.time()
       
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
from comparativo_calendario import mostrar_calendario
from convertir_fechas import convertir_fechas
from calculos_tabla_principal import (
    calcular_profit_operacion, calcular_porcentaje_profit_op, calcular_profit_total,
    calcular_dd_max, calcular_dd_up, calcular_profit_t, calcular_profit_alcanzado_vectorizado,
    calcular_profit_media_vectorizado
)
from eliminar_columnas_duplicadas_contador import limpiar_columnas
from tabla_editable_eliminar_renombrar_limpiar_columnas import tabla_editable_eliminar_renombrar_limpiar_columnas

SELECT_FILE = 'selected_asset.json'

def init_session():
    if os.path.exists(config.COL_FILE):
        try:
            with open(config.COL_FILE, 'r') as f:
                cols = json.load(f)
        except:
            cols = config.FIXED_COLS
    else:
        cols = config.FIXED_COLS
    # Si no existe o llegó a ser None, lo (re)inicializamos como DataFrame vacío
    if 'datos' not in st.session_state or st.session_state.datos is None:
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
# Inicializar loaded_file para controlar la recarga desde AWS
if "loaded_file" not in st.session_state:
    st.session_state.loaded_file = None
    
if st.session_state.get("multi_uploader") is None and "ya_subido" in st.session_state:
    del st.session_state["ya_subido"]
if 'pintar_colores' not in st.session_state:
    st.session_state.pintar_colores = False

# ———————— Gestión de múltiples archivos ————————
with st.sidebar.expander("Archivos", expanded=True):
        # Switch para activar/desactivar autoguardado
    st.session_state.auto_save_enabled = st.checkbox(
        "Autoguardar en S3",
        value=st.session_state.get("auto_save_enabled", True),
        help="Habilita o deshabilita que las operaciones se guarden automáticamente en S3"
    )
    # 1) Selector de archivo
    saved  = list_saved_files()
    nombres = [f["name"] for f in saved]
    nombres.insert(0, "↑ Subir nuevo ↑")
    choice = st.selectbox("Archivo activo:", nombres, key="selector_archivo")

    # 2) Subir nuevo
    if choice == "↑ Subir nuevo ↑":
        up = st.file_uploader("Sube CSV/XLSX", type=["csv","xlsx"], key="multi_uploader")
        if up:
            save_uploaded_file(up)
            st.success(f"Guardado '{up.name}'. Ahora selecciónalo arriba.")
             # Si estamos en “Subir nuevo” limpiamos el flag
            st.session_state.loaded_file = None
    # 3) Archivo existente
    else:
        # 3a) Eliminar
        if st.button("🗑️ Eliminar archivo seleccionado"):
            delete_saved_file(choice)
            st.success(f"El archivo '{choice}' ha sido eliminado.")
            st.stop()

        # 3b) Cargar en memoria
        if st.session_state.loaded_file != choice:
           df = load_file_df(choice)
           if not df.empty:
               st.session_state.datos = df
           st.session_state.loaded_file = choice

        # 3c) Guardar cambios manual
        if st.button("💾 Guardar cambios en S3", key="save_sidebar"):
            buffer = BytesIO()
            st.session_state.datos.to_csv(buffer, index=False, encoding="utf-8")
            buffer.seek(0)
            update_file(choice, buffer.getvalue())
            st.success(f"Archivo '{choice}' actualizado correctamente en S3")

with st.expander("Modo de entrenamiento", expanded=True):
    if 'pintar_colores' not in st.session_state:
        st.session_state.pintar_colores = True
    st.session_state.pintar_colores = st.checkbox(
        "Aplicar colores en la tabla",
        value=st.session_state.pintar_colores
    )
    crear_botones_trading()
    crear_botones_iv_rank()

 # ———————— Ajustes y resto del sidebar ————————           
with st.sidebar.expander("Cargar y Ajustes", expanded=True):
    st.slider("Alto Vista", 200, 1200, st.session_state.h, key='h')
    st.slider("Ancho Vista", 200, 2000, st.session_state.w, key='w')
    st.markdown("### Ajustar Rangos de Gráficos")
    total_filas = len(st.session_state.datos) - 1
    tab1, tab2, tab3, tab4 = st.tabs(["Columna 1", "Columna 2", "Columna 3", "Columna 4"])

    for i, tab in enumerate([tab1, tab2, tab3, tab4], start=1):
        with tab:
            rows = len(st.session_state.datos)
            max_idx = rows - 1
            if max_idx > 0:
                preset = st.radio(
                    "Preset", [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 150, 200, 250, 'ALL'],
                    index=1, horizontal=True,
                    key=f"preset_col{i}"
                )
                filas_default = max_idx if preset == 'ALL' else min(int(preset), max_idx)
                start = max(0, max_idx - filas_default)
                end   = max_idx
                rango_slider = st.slider(
                    f"Rango de filas Gráfico Columna {i}",
                    min_value=0,
                    max_value=max_idx,
                    value=(start, end),
                    key=f"filas_col{i}"
                )
            else:
                st.info("No hay suficientes filas para seleccionar un rango.")
                rango_slider = (0, max_idx if max_idx >= 0 else 0)

            st.session_state[f"rango_col{i}"] = rango_slider
            st.caption(
                f"Mostrando filas desde **{rango_slider[0]}** hasta **{rango_slider[1]}** de **{max_idx if max_idx>=0 else 0}** filas."
            )

    sel = st.selectbox(
        "Selecciona Activo",
        config.ASSETS,
        index=config.ASSETS.index(st.session_state.selected_asset),
        key='selected_asset'
    )
    st.number_input("Valor (solo DEP/RET)", value=0.0, key='input_valor')

    st.session_state.datos = tabla_editable_eliminar_renombrar_limpiar_columnas(
        st.session_state.datos
    )
current_layout = {'height': st.session_state.h, 'width': st.session_state.w}
if st.session_state.get("prev_layout") != current_layout:
    with open(config.TABLE_FILE, 'w') as f:
        json.dump(current_layout, f)
    st.session_state.prev_layout = current_layout

if sel != st.session_state.get("prev_selected_asset"):
    with open(SELECT_FILE, 'w') as f:
        json.dump(sel, f)
    st.session_state.prev_selected_asset = sel

df = st.session_state.datos.copy()
df = limpiar_columnas(df)

df = convertir_fechas(
    df,
    cols=['Fecha / Hora', 'Fecha / Hora de Cierre'],
    dayfirst=True,      # ajusta según tu convención
    yearfirst=False
)
# Añadir columna Día (Lu, Ma, Mi, etc.)
df['Día'] = df['Fecha / Hora'].dt.weekday.map({0:'Lu', 1:'Ma', 2:'Mi', 3:'Ju', 4:'Vi', 5:'Sa', 6:'Do'})

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

with st.sidebar.expander("Ganancia por Contratos", expanded=False):
    tabla_ganancia_contratos_calculos()

if st.session_state.get('pintar_colores_disable_pending', False):
    st.session_state.pintar_colores = False
    st.session_state.pintar_colores_disable_pending = False

tab_vista, tab_edicion = st.tabs(["Vista", "Edición"])

with tab_vista:
    df_vista = df.copy()
    if 'Contador' in df_vista.columns:
        df_vista = df_vista.drop(columns=['Contador'])
        
    styled_df_vista = aplicar_color_general(df_vista)

    if styled_df_vista is not None:
        st.dataframe(styled_df_vista, width=st.session_state.w, height=st.session_state.h)
    else:
        st.dataframe(df_vista, width=st.session_state.w, height=st.session_state.h)

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
        "Calendario": mostrar_calendario,
    }
    secciones = [
        ("", "rango_col1", "rango_col2"),
        (" Secundarios", "rango_col3", "rango_col4")
    ]
    for seccion, rango1, rango2 in secciones:
        expanded = True if seccion == "" else False
        with st.expander(f"Gráficos Comparativos{seccion}", expanded=expanded):
            select_col1, select_col2 = st.columns(2, gap="medium")

            with select_col1:
                grafico_col1 = st.selectbox(
                    f"Gráfico Columna 1{seccion}",
                    list(opciones_graficos.keys()),
                    index=list(opciones_graficos.keys()).index(
                        "Racha Operaciones DD/Max" if seccion == "" else "Porcentaje Aciertos CALL PUT (Dona)"
                    ),
                    key=f"grafico_1{seccion}"
                )

            with select_col2:
                grafico_col2 = st.selectbox(
                    f"Gráfico Columna 2{seccion}",
                    list(opciones_graficos.keys()),
                    index=list(opciones_graficos.keys()).index(
                        "CALL vs PUT Línea" if seccion == "" else "DD/Max"
                    ),
                    key=f"grafico_2{seccion}"
                )

            # COLUMNAS DE GRÁFICOS CORREGIDAS
            col1, col2 = st.columns(2, gap="small")

            with col1:
                if grafico_col1 == "Calendario":
                    mostrar_calendario(
                        df,
                        chart_key=f"chart_1_{grafico_col1}{seccion}"
                    )
                else:
                    opciones_graficos[grafico_col1](
                        df.iloc[
                            st.session_state[rango1][0]
                            :st.session_state[rango1][1] + 1
                        ],
                        chart_key=f"chart_1_{grafico_col1}{seccion}"
                    )

            with col2:
                if grafico_col2 == "Calendario":
                    mostrar_calendario(
                        df,
                        chart_key=f"chart_2_{grafico_col2}{seccion}"
                    )
                else:
                    opciones_graficos[grafico_col2](
                        df.iloc[
                            st.session_state[rango2][0]
                            :st.session_state[rango2][1] + 1
                        ],
                        chart_key=f"chart_2_{grafico_col2}{seccion}"
                    )

with tab_edicion:
    df_ed = df.reset_index(drop=True).copy()
    df_ed.insert(0, 'Contador', df_ed.index)
    df_ed['Eliminar'] = False
    df_ed.drop(columns=[''], inplace=True, errors='ignore')
    
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

    edited = st.data_editor(
        df_ed,
        column_config=col_config,
        hide_index=True,
        width=st.session_state.w,
        height=st.session_state.h,
        num_rows="dynamic"
    )
    filtered = edited[edited['Eliminar'] == False]
    filtered = filtered.drop(columns=['Contador', 'Eliminar']).reset_index(drop=True)
    st.session_state.datos = filtered
    # ← Marcamos que la data ha cambiado para el auto‐save
    st.session_state.data_modified = True
