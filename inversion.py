import streamlit as st
import pandas as pd
import os, json
from combinaciones import generar_combinaciones_contratos

# Stubs básicos para cálculos de inversión
# (los cálculos de depósitos y ganancias se mantienen en caso de futuras necesidades)
def calcular_total_depositos(df):
    try:
        return df['Deposito'].sum() if 'Deposito' in df.columns else 0.0
    except:
        return 0.0

def calcular_ganancias_totales(df):
    try:
        return df['Profit'].sum()
    except:
        return 0.0

# Nuevo cálculo de % Inversión: usa la suma directa de la columna 'Profit'
def calcular_porcentaje_inversion(monto: float, df: pd.DataFrame) -> float:
    """
    Devuelve el % de inversión sobre la suma total de la columna 'Profit'.
    Fórmula: (monto ÷ suma_profit) × 100
    """
    try:
        total_profit = df['Profit'].sum() if 'Profit' in df.columns else 0.0
        return (monto / total_profit * 100) if total_profit else 0.0
    except:
        return 0.0

# Archivo para persistir valores de inversión
INV_CONFIG = 'inversion_config.json'

def init_inversion_state():
    """
    Inicializa en session_state los valores de monto_invertir y valor_contrato desde disco.
    """
    if os.path.exists(INV_CONFIG):
        try:
            with open(INV_CONFIG, 'r') as f:
                cfg = json.load(f)
            st.session_state.monto_invertir = cfg.get('monto_invertir', 0.0)
            st.session_state.valor_contrato = cfg.get('valor_contrato', 0.0)
        except:
            st.session_state.monto_invertir = 0.0
            st.session_state.valor_contrato = 0.0
    else:
        st.session_state.monto_invertir = 0.0
        st.session_state.valor_contrato = 0.0

def mostrar_sidebar_inversion(df: pd.DataFrame):
    """
    Despliega en la sidebar la sección de Inversión y Combinaciones de Contratos.
    """
    st.sidebar.markdown("### Inversión")
    init_inversion_state()

    # Añadimos una nueva pestaña "Niveles"
    tab1, tab2, tab3, tab4 = st.sidebar.tabs(["Tabla", "Editar Monto", "Editar Contrato", "Niveles"])

    # 1) Tabla de Resumen inicial
    # Ajustamos 'Monto a Invertir' según el nivel actual
    # Calculamos nivel de inversión según la suma total de Profit
    total_profit = df['Profit'].sum() if 'Profit' in df.columns else 0.0
    nivel_actual = None
    if total_profit >= 1000:
        for n in range(1, 11):
            lower = (2*n - 1) * 1000
            upper = lower + 1999
            if lower <= total_profit <= upper:
                nivel_actual = n
                break
    nivel_label = ">10" if (nivel_actual is None and total_profit >= (2*10 - 1)*1000) else str(nivel_actual or 0)
    # Valor de inversión base por nivel: nivel * 30
    try:
        inv_level = float(nivel_label) * 30
    except:
        inv_level = 0.0
    # Actualizamos estado y tabla
    st.session_state.monto_invertir = inv_level
    n_inicial = (inv_level / st.session_state.valor_contrato) if st.session_state.valor_contrato else 0.0
    tabla = pd.DataFrame({
        '% Inversión':      ['0%'],
        'Monto a Invertir': [f"{inv_level:.2f}"],
        '$ Contrato':       [f"{st.session_state.valor_contrato:.2f}"],
        'N. Contrato':      [f"{n_inicial:.2f}"],
        'Nivel':            [nivel_label]
    })

        # Calcular nivel de inversión según la suma total de Profit
    total_profit = df['Profit'].sum() if 'Profit' in df.columns else 0.0
    nivel_actual = None
    if total_profit >= 1000:
        for n in range(1, 11):
            lower = (2*n - 1) * 1000
            upper = lower + 1999
            if lower <= total_profit <= upper:
                nivel_actual = n
                break
    # Si supera el rango del nivel 10
    nivel_label = ">10" if (nivel_actual is None and total_profit >= (2*10 - 1)*1000) else str(nivel_actual or 0)
    tabla.loc[0, 'Nivel'] = nivel_label

    # 2) Editar Monto
    with tab2:
        monto = st.number_input(
            "Monto a invertir:",
            value=st.session_state.monto_invertir,
            step=0.01,
            format="%.2f",
            key='monto_input'
        )
        st.session_state.monto_invertir = monto
        with open(INV_CONFIG, 'w') as f:
            json.dump({
                'monto_invertir': monto,
                'valor_contrato': st.session_state.valor_contrato
            }, f)
        pct = calcular_porcentaje_inversion(monto, df)
        tabla.loc[0, '% Inversión']      = f"{pct:.2f}%"
        tabla.loc[0, 'Monto a Invertir'] = f"{monto:.2f}"
        n_contr = monto / st.session_state.valor_contrato if st.session_state.valor_contrato else 0.0
        tabla.loc[0, 'N. Contrato']      = f"{n_contr:.2f}"

    # 3) Editar Contrato
    with tab3:
        val_con = st.number_input(
            "Valor del contrato:",
            value=st.session_state.valor_contrato,
            step=0.01,
            format="%.2f",
            key='contrato_input'
        )
        st.session_state.valor_contrato = val_con
        with open(INV_CONFIG, 'w') as f:
            json.dump({
                'monto_invertir': st.session_state.monto_invertir,
                'valor_contrato': val_con
            }, f)
        tabla.loc[0, '$ Contrato'] = f"{val_con:.2f}"
        n_contr = st.session_state.monto_invertir / val_con if val_con else 0.0
        tabla.loc[0, 'N. Contrato'] = f"{n_contr:.2f}"

    # 4) Mostrar Tabla de Resumen
    # 4) Mostrar Tabla de Resumen
    with tab1:
        # Función para aplicar color amarillo a todos los valores
        def aplicar_color_amarillo(val):
            return 'color: goldenrod; text-align: center;'

        styled_tabla = tabla.style \
            .applymap(aplicar_color_amarillo) \
            .set_properties(**{'text-align': 'center'})  # Asegura centrado

        st.dataframe(styled_tabla, hide_index=True, use_container_width=True)


    # 5) Mostrar Tabla de Niveles (solo algunas filas visibles, resto con scroll)
    with tab4:
        niveles = []
        inversion = []
        capital = []
        porcentaje = []
        for n in range(1, 11):
            inv = n * 30
            cap1 = (2*n - 1) * 1000
            cap2 = 2 * n * 1000
            pct1 = round(inv/cap1*100, 1) if cap1 else 0.0
            pct2 = round(inv/cap2*100, 1) if cap2 else 0.0
            niveles.extend([n, n])
            inversion.extend([inv, inv])
            capital.extend([cap1, cap2])
            porcentaje.extend([f"{pct1}%", f"{pct2}%"])
        tabla_niveles = pd.DataFrame({
            'Niveles # C': niveles,
            'Inversión C.': inversion,
            'Capital T.': capital,
            '% I': porcentaje
        })
        st.dataframe(
            tabla_niveles,
            hide_index=True,
            use_container_width=True,
            height=150  # ALTURA DEL COMPONENTE (ajusta para filas visibles)
        )
    
    # 6) Combinaciones de Contratos
    st.sidebar.markdown("### Combinaciones de Contratos")
    try:
        num_ct = int(float(tabla.loc[0, 'N. Contrato']))
    except:
        num_ct = 0
    cols = [f'Contrato {i+1}' for i in range(4)]
    if num_ct >= 2:
        comps = generar_combinaciones_contratos(num_ct, k=4)
        if 'comps' not in st.session_state or st.sidebar.button("🟢 Generar Nuevas Combinaciones"):
            st.session_state.comps = comps
        tabla_combinaciones = pd.DataFrame(st.session_state.comps, columns=cols)
    else:
        tabla_combinaciones = pd.DataFrame([[0]*4], columns=cols)
    tabla_combinaciones = tabla_combinaciones.replace(0, '')
    st.sidebar.dataframe(tabla_combinaciones, hide_index=True, height=135)

    return tabla
