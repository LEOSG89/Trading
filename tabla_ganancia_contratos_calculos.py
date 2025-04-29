import streamlit as st
import pandas as pd
import os, json

# Módulo: tabla_ganancia_contratos_calculos.py
# Función con pestañas para editar y mostrar tabla de ganancia por niveles
# Persistencia de parámetros en JSON y uso de st.form

CONFIG_FILE = 'ganancia_config.json'

@st.cache_data(show_spinner=False)
def load_parameters():
    """Carga parámetros desde JSON o devuelve valores por defecto (cacheado)."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
            return (
                data.get('cantidad_contratos', 1),
                data.get('costo_por_contrato', 0.0),
                data.get('precio_venta', 0.0)
            )
        except:
            pass
    return 1, 0.0, 0.0


def save_parameters(cantidad, costo, precio):
    """Guarda los parámetros en el JSON de configuración y limpia cache si es necesario."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump({
                'cantidad_contratos': cantidad,
                'costo_por_contrato': costo,
                'precio_venta': precio
            }, f)
        load_parameters.clear()  # invalidar caché para recargar
    except:
        st.warning("No se pudo guardar la configuración.")


def tabla_ganancia_contratos_calculos(
    niveles: list = [50, 100, 150, 200, 250, 300, 350, 400, 450, 500]
):
    """
    - Usa st.form para edición sin recarga en cada cambio
    - Parámetros cacheados y guardados al enviar el formulario
    """
    # Inicializar session state solo una vez
    if 'initialized' not in st.session_state:
        c, cost, price = load_parameters()
        st.session_state.update({
            'cantidad_contratos': c,
            'costo_por_contrato': cost,
            'precio_venta': price,
            'initialized': True
        })

    # Pestañas
    tab_table, tab_edit = st.tabs(["Tabla", "Editar"])

    # Pestaña de edición con st.form
    with tab_edit:
        with st.form("config_form"):
            cantidad = st.number_input(
                "Cant Contratos", min_value=0,
                value=st.session_state.cantidad_contratos,
                step=1, key='form_cantidad'
            )
            costo = st.number_input(
                "Costo", min_value=0.0,
                value=st.session_state.costo_por_contrato,
                step=0.01, format="%.2f", key='form_costo'
            )
            precio = st.number_input(
                "Precio Vta", min_value=0.0,
                value=st.session_state.precio_venta,
                step=0.01, format="%.2f", key='form_precio'
            )
            submitted = st.form_submit_button("Guardar cambios")
            if submitted:
                save_parameters(cantidad, costo, precio)
                # Actualizar session state para reflejar en la siguiente ejecución
                st.session_state['cantidad_contratos'] = cantidad
                st.session_state['costo_por_contrato'] = costo
                st.session_state['precio_venta'] = precio
                st.success("Configuración actualizada.")

    # Cálculos y presentación con session_state actual
    cantidad_contratos = st.session_state.cantidad_contratos
    costo_por_contrato = st.session_state.costo_por_contrato
    precio_venta = st.session_state.precio_venta
    gan_pct = (precio_venta / costo_por_contrato - 1) * 100 if costo_por_contrato else 0.0

    def style_gan_pct(val):
        try:
            num = float(str(val).strip('%'))
        except:
            return ''
        if num > 0:
            return 'color: green'
        elif num < 0:
            return 'color: red'
        return 'color: goldenrod'

    def fmt(val, dec=2):
        try:
            v = float(val)
            return str(int(v)) if v == int(v) else str(round(v, dec)).rstrip('0').rstrip('.')
        except:
            return ''

    with tab_table:
        # Resumen
        resumen = pd.DataFrame({
            'Cant': [cantidad_contratos],
            'Costo': [f"${fmt(costo_por_contrato,2)}"],
            'Precio Vta': [f"${fmt(precio_venta,2)}"],
            'Gan %': [f"{round(gan_pct)}%"]
        })
        st.dataframe(resumen.style.applymap(style_gan_pct, subset=['Gan %']), hide_index=True, use_container_width=True)

        # Tabla real
        be_real = (cantidad_contratos * costo_por_contrato) / precio_venta if precio_venta else 0.0
        vender_real = (cantidad_contratos - be_real) if be_real else 0.0
        actual = pd.DataFrame({
            'Gan %': [f"{round(gan_pct)}%"],
            'Precio Vta': [f"${fmt(precio_venta,2)}"],
            'B. Even': [fmt(be_real,2)],
            'C. Vender': [fmt(vender_real,1)]
        })
        st.dataframe(actual.style.applymap(style_gan_pct, subset=['Gan %']), hide_index=True, use_container_width=True)

        # Tabla niveles
        filas = []
        for n in niveles:
            precio_n = costo_por_contrato * (1 + n/100)
            be_n = (cantidad_contratos * costo_por_contrato) / precio_n if precio_n else 0.0
            vender_n = (cantidad_contratos - be_n) if be_n else 0.0
            filas.append({
                'Gan %': f"{n}%",
                'Precio Vta': f"${fmt(precio_n,0)}",
                'B. Even': fmt(be_n,2),
                'C. Vender': fmt(vender_n,1)
            })
        df_niv = pd.DataFrame(filas)
        st.dataframe(df_niv.style.applymap(style_gan_pct, subset=['Gan %']), hide_index=True, use_container_width=True)
