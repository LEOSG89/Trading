import streamlit as st
import pandas as pd


def tabla_editable_eliminar_renombrar_limpiar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Módulo para gestionar la edición de datos en pestañas:
    - Renombrar Cols
    - Eliminar Cols
    - Vaciar Cols
    - Vaciar Filas
    - Mover Filas
    - Agregar Cols
    """
    # Crear las pestañas con nombres ajustados
    tabs = st.tabs([
        "Renombrar Cols",
        "Eliminar Cols",
        "Vaciar Cols",
        "Vaciar Filas",
        "Mover Filas",
        "Agregar Cols"
    ])
    (
        tab_ren,
        tab_del,
        tab_clear_col,
        tab_clear_row,
        tab_move,
        tab_add
    ) = tabs

    # Pestaña: Renombrar Cols
    with tab_ren:
        st.divider()
        cols = df.columns.tolist()
        col_to_rename = st.selectbox(
            "Selecciona columna a renombrar", cols, key="tab_ren_col"
        )
        new_name = st.text_input(
            "Nuevo nombre de la columna", value=col_to_rename, key="tab_ren_name"
        )
        if st.button("Aplicar renombrado", key="tab_ren_btn"):
            if not new_name:
                st.warning("El nombre no puede estar vacío.")
            elif new_name in df.columns:
                st.error(f"'{new_name}' ya existe.")
            else:
                df.rename(columns={col_to_rename: new_name}, inplace=True)
                st.success(f"'{col_to_rename}' renombrada a '{new_name}'.")

    # Pestaña: Eliminar Cols
    with tab_del:
        st.divider()
        to_delete = st.multiselect(
            "Selecciona columnas a eliminar", df.columns.tolist(), key="tab_del_cols"
        )
        if st.button("Eliminar columnas", key="tab_del_btn"):
            if to_delete:
                df.drop(columns=to_delete, inplace=True)
                st.success(f"Eliminadas: {', '.join(to_delete)}")
            else:
                st.warning("Sin columnas seleccionadas.")

    # Pestaña: Vaciar Cols
    with tab_clear_col:
        st.divider()
        to_clear = st.multiselect(
            "Selecciona columnas a vaciar", df.columns.tolist(), key="tab_clear_cols"
        )
        if st.button("Vaciar columnas", key="tab_clear_btn"):
            if to_clear:
                for c in to_clear:
                    df[c] = ""
                st.success(f"Vaciadas: {', '.join(to_clear)}")
            else:
                st.warning("Sin columnas seleccionadas.")

    # Pestaña: Vaciar Filas
    with tab_clear_row:
        st.divider()
        row_opts = [str(i) for i in df.index]
        to_clear_rows = st.multiselect(
            "Selecciona filas a vaciar", row_opts, key="tab_clear_rows"
        )
        if st.button("Vaciar filas", key="tab_clear_rows_btn"):
            if to_clear_rows:
                for r in to_clear_rows:
                    df.loc[int(r), :] = ""
                st.success(f"Filas vaciadas: {', '.join(to_clear_rows)}")
            else:
                st.warning("Sin filas seleccionadas.")

    # Pestaña: Mover Filas
    with tab_move:
        st.divider()
        if df.shape[0] > 0:
            row_move = st.selectbox(
                "Selecciona fila a mover", [str(i) for i in df.index], key="tab_move_row"
            )
            dest = st.number_input(
                f"Mover antes de índice (0 a {len(df)}):", 0, len(df), int(row_move), key="tab_move_dest"
            )
            if st.button("Mover fila", key="tab_move_btn"):
                idx = int(row_move)
                if idx != dest:
                    row = df.loc[idx]
                    df.drop(index=idx, inplace=True)
                    df.reset_index(drop=True, inplace=True)
                    top = df.iloc[:dest]
                    bottom = df.iloc[dest:]
                    df = pd.concat([top, pd.DataFrame([row]), bottom], ignore_index=True)
                    st.success(f"Fila {idx} a posición {dest}.")

    # Pestaña: Agregar Cols
    with tab_add:
        st.divider()
        new_col = st.text_input("Nombre nueva columna", key="tab_add_name")
        if st.button("Agregar columna", key="tab_add_btn"):
            if not new_col:
                st.warning("Ingrese nombre.")
            elif new_col in df.columns:
                st.error(f"'{new_col}' existe.")
            else:
                df[new_col] = ["" for _ in range(len(df))]
                st.success(f"Columna '{new_col}' agregada.")

    return df
