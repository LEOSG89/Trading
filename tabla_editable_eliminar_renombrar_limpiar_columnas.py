import streamlit as st
import pandas as pd
import os
import time

# Archivo para persistencia de la tabla editada
STORAGE_FILE = "tabla_edicion.json"


def tabla_editable_eliminar_renombrar_limpiar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Módulo para gestionar la edición de datos en pestañas, con persistencia:
    - Renombrar Cols
    - Eliminar Cols
    - Vaciar Cols
    - Vaciar Filas
    - Mover Filas
    - Agregar Cols
    - Columnas personalizadas: Notas, Fotos
    - Carga/Guarda automática en JSON
    """
    # 1) Cargar datos persistidos si df está vacío
    if df.empty and os.path.exists(STORAGE_FILE):
        try:
            stored = pd.read_json(STORAGE_FILE, orient="table")
            df = stored.copy()
        except Exception:
            st.warning("No se pudo cargar datos previos, usando el DataFrame actual.")

    # 2) Asegurar columnas personalizadas
    for col in ['Notas', 'Fotos']:
        if col not in df.columns:
            df[col] = ""

    # 3) Crear pestañas
    tabs = st.tabs([
        "Renombrar Cols",
        "Eliminar Cols",
        "Vaciar Cols",
        "Vaciar Filas",
        "Mover Filas",
        "Agregar Cols"
    ])
    tab_ren, tab_del, tab_clear_col, tab_clear_row, tab_move, tab_add = tabs

    # 4) Renombrar Cols
    with tab_ren:
        st.divider()
        cols = df.columns.tolist()
        col_to_rename = st.selectbox("Selecciona columna a renombrar", cols, key="tab_ren_col")
        new_name = st.text_input("Nuevo nombre de la columna", value=col_to_rename, key="tab_ren_name")
        if st.button("Aplicar renombrado", key="tab_ren_btn"):
            if not new_name:
                st.warning("El nombre no puede estar vacío.")
            elif new_name in df.columns:
                st.error(f"'{new_name}' ya existe.")
            else:
                df.rename(columns={col_to_rename: new_name}, inplace=True)
                st.success(f"'{col_to_rename}' renombrada a '{new_name}'.")

    # 5) Eliminar Cols
    with tab_del:
        st.divider()
        to_delete = st.multiselect("Selecciona columnas a eliminar", df.columns.tolist(), key="tab_del_cols")
        if st.button("Eliminar columnas", key="tab_del_btn"):
            if to_delete:
                df.drop(columns=to_delete, inplace=True)
                st.success(f"Eliminadas: {', '.join(to_delete)}")
            else:
                st.warning("Sin columnas seleccionadas.")

    # 6) Vaciar Cols
    with tab_clear_col:
        st.divider()
        to_clear = st.multiselect("Selecciona columnas a vaciar", df.columns.tolist(), key="tab_clear_cols")
        if st.button("Vaciar columnas", key="tab_clear_btn"):
            if to_clear:
                for c in to_clear:
                    df[c] = ""
                st.success(f"Vaciadas: {', '.join(to_clear)}")
            else:
                st.warning("Sin columnas seleccionadas.")

    # 7) Vaciar Filas
    with tab_clear_row:
        st.divider()
        row_opts = [str(i) for i in df.index]
        to_clear_rows = st.multiselect("Selecciona filas a vaciar", row_opts, key="tab_clear_rows")
        if st.button("Vaciar filas", key="tab_clear_rows_btn"):
            if to_clear_rows:
                for r in to_clear_rows:
                    df.loc[int(r), :] = ""
                st.success(f"Filas vaciadas: {', '.join(to_clear_rows)}")
            else:
                st.warning("Sin filas seleccionadas.")

    # 8) Mover Filas
    with tab_move:
        st.divider()
        if df.shape[0] > 0:
            row_move = st.selectbox("Selecciona fila a mover", [str(i) for i in df.index], key="tab_move_row")
            dest = st.number_input(f"Mover antes de índice (0 a {len(df)}):", 0, len(df), int(row_move), key="tab_move_dest")
            if st.button("Mover fila", key="tab_move_btn"):
                idx = int(row_move)
                if idx != dest:
                    row = df.loc[idx].copy()
                    df.drop(index=idx, inplace=True)
                    df.reset_index(drop=True, inplace=True)
                    top = df.iloc[:dest]
                    bottom = df.iloc[dest:]
                    df = pd.concat([top, pd.DataFrame([row]), bottom], ignore_index=True)
                    st.success(f"Fila {idx} movida a posición {dest}.")

    # 9) Agregar Cols
    with tab_add:
        st.divider()
        new_col = st.text_input("Nombre nueva columna (vacío=ignorar)", key="tab_add_name")
        if st.button("Agregar columna", key="tab_add_btn"):
            if not new_col:
                st.warning("Ingrese nombre.")
            elif new_col in df.columns:
                st.error(f"'{new_col}' ya existe.")
            else:
                df[new_col] = ["" for _ in range(len(df))]
                st.success(f"Columna '{new_col}' agregada.")

    # 10) Guardar o limpiar persistencia manual
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Guardar tabla", key="save_tabla"):
            try:
                df.to_json(STORAGE_FILE, orient="table", force_ascii=False)
                st.session_state['tabla_last_save'] = time.time()
                st.success("Datos guardados correctamente.")
            except Exception as e:
                st.error(f"Error guardando: {e}")
    with col2:
        if st.button("Limpiar tabla", key="clear_tabla"):
            if os.path.exists(STORAGE_FILE):
                os.remove(STORAGE_FILE)
            df = df.iloc[0:0]
            st.success("Tabla limpiada. Refresca la página para reiniciar completamente.")

    # Auto-guardado cada 60s
    now = time.time()
    last = st.session_state.get('tabla_last_save', None)
    if last is None:
        st.session_state['tabla_last_save'] = now
    elif now - last > 60:
        try:
            df.to_json(STORAGE_FILE, orient="table", force_ascii=False)
            st.session_state['tabla_last_save'] = now
            st.info("Auto-guardado de la tabla.")
        except Exception:
            pass

    return df
