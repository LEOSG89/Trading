import pandas as pd
import streamlit as st
from typing import Tuple

# Reusar función de riesgo/beneficio para medias
from riesgo_beneficio import calcular_medias_operaciones


def calcular_porcentajes_acierto_error(df: pd.DataFrame) -> Tuple[float, float]:
    if 'Profit' not in df.columns:
        return 0.0, 0.0

    profit = pd.to_numeric(df['Profit'], errors='coerce')
    mask = profit.notna() & (profit != 0)
    if 'Deposito' in df.columns and 'Retiro' in df.columns:
        mask &= df['Deposito'].isna() & df['Retiro'].isna()

    total = mask.sum()
    if total == 0:
        return 0.0, 0.0

    aciertos = (profit[mask] > 0).sum()
    errores = (profit[mask] < 0).sum()

    pct_acierto = round(aciertos / total * 100, 2)
    pct_error = round(errores / total * 100, 2)
    return pct_acierto, pct_error


def render_aciertos_beneficios(df: pd.DataFrame) -> None:
    st.sidebar.markdown("### % de Aciertos / Beneficios M.")
    tabla = pd.DataFrame({
        '% Acierto':    ['0.00%'],
        '% Error':      ['0.00%'],
        'Beneficio M.': ['0.00'],
        'Riesgo M.':    ['0.00']
    })

    if not df.empty and 'Profit' in df.columns:
        pct_acierto, pct_error = calcular_porcentajes_acierto_error(df)
        media_pos, media_neg = calcular_medias_operaciones(df)

        tabla.loc[0, '% Acierto']    = f"{pct_acierto:.2f}%"
        tabla.loc[0, '% Error']      = f"{pct_error:.2f}%"
        tabla.loc[0, 'Beneficio M.'] = f"{media_pos:.2f}"
        tabla.loc[0, 'Riesgo M.']    = f"{media_neg:.2f}"

    # Función para aplicar colores
    def estilo_columna(val, col):
        try:
            if col == '% Acierto':
                return 'color: green; text-align: center;'
            elif col == '% Error':
                return 'color: red; text-align: center;'
            elif col == 'Beneficio M.':
                return 'color: green; text-align: center;'
            elif col == 'Riesgo M.':
                return 'color: red; text-align: center;'
        except:
            return 'text-align: center;'

    styled_table = tabla.style \
        .applymap(lambda v: estilo_columna(v, '% Acierto'), subset=['% Acierto']) \
        .applymap(lambda v: estilo_columna(v, '% Error'), subset=['% Error']) \
        .applymap(lambda v: estilo_columna(v, 'Beneficio M.'), subset=['Beneficio M.']) \
        .applymap(lambda v: estilo_columna(v, 'Riesgo M.'), subset=['Riesgo M.']) \
        .set_properties(**{'text-align': 'center'})

    st.sidebar.dataframe(styled_table, hide_index=True, use_container_width=True)
