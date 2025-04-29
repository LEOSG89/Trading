"""
Módulo para cálculos de operaciones ganadoras y perdedoras en trading.
"""

import pandas as pd
import streamlit as st


def calcular_operaciones_ganadoras_perdedoras(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula el número de operaciones ganadoras y perdedoras:
      - Excluye filas con valores en 'Deposito' o 'Retiro'.
      - Omite operaciones con Profit == 0 o no numéricos.
    Retorna un DataFrame de una sola fila con columnas:
      'Op. Ganadoras' y 'Op. Perdedoras'.
    """
    # Validar existencia de Profit
    if 'Profit' not in df.columns:
        return pd.DataFrame({'Op. Ganadoras': [0], 'Op. Perdedoras': [0]})

    # Convertir Profit a numérico
    profits = pd.to_numeric(df['Profit'], errors='coerce')

    # Excluir depósitos y retiros
    if 'Deposito' in df.columns and 'Retiro' in df.columns:
        mask_dr = df['Deposito'].notna() | df['Retiro'].notna()
        profits = profits[~mask_dr]

    # Filtrar operaciones válidas (profit distinto de cero)
    valid = profits[profits != 0].dropna()

    # Contar ganadoras y perdedoras
    ganadoras = (valid > 0).sum()
    perdedoras = (valid < 0).sum()

    return pd.DataFrame({'Op. Ganadoras': [int(ganadoras)], 'Op. Perdedoras': [int(perdedoras)]})


def render_operaciones_ganadoras_perdedoras(df: pd.DataFrame) -> None:
    """
    Renderiza en la sidebar la tabla "Op. Ganadoras / Perdedoras" con color:
      - Verde para ganadoras
      - Rojo para perdedoras
    """
    st.sidebar.markdown("### Op. Ganadoras / Perdedoras")
    tabla = pd.DataFrame({'Op. Ganadoras': [0], 'Op. Perdedoras': [0]})
    if not df.empty:
        tabla = calcular_operaciones_ganadoras_perdedoras(df)

    # Función para aplicar color
    def color_ganadoras_perdedoras(val, col_name):
        if col_name == 'Op. Ganadoras':
            return 'color: green'
        elif col_name == 'Op. Perdedoras':
            return 'color: red'
        else:
            return ''

    # Aplicar el estilo de color
    styled_table = tabla.style.applymap(lambda v: color_ganadoras_perdedoras(v, 'Op. Ganadoras'), subset=['Op. Ganadoras']) \
                              .applymap(lambda v: color_ganadoras_perdedoras(v, 'Op. Perdedoras'), subset=['Op. Perdedoras'])

    st.sidebar.dataframe(styled_table, hide_index=True, use_container_width=True)
