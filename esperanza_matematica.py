"""
Módulo para cálculos de esperanza matemática en operaciones de trading.
"""

import pandas as pd
import streamlit as st

from aciertos_beneficios import calcular_porcentajes_acierto_error
from riesgo_beneficio    import calcular_medias_operaciones


def calcular_esperanza_matematica(df: pd.DataFrame) -> float:
    """
    Calcula la esperanza matemática en porcentaje:
      EM = (% Acierto/100 * Beneficio M.) - (% Error/100 * Riesgo M.)

    Retorna:
      Un float representando la esperanza matemática en proporción.
    """
    pct_acierto, pct_error = calcular_porcentajes_acierto_error(df)
    media_pos, media_neg = calcular_medias_operaciones(df)
    em = (pct_acierto / 100 * media_pos) - (pct_error / 100 * media_neg)
    return em


def calcular_ganancia_esperada(df: pd.DataFrame) -> float:
    """
    Calcula la ganancia esperada en dinero:
      GE = % Acierto/100 * Beneficio M.

    Retorna:
      Un float con la ganancia esperada.
    """
    pct_acierto, _ = calcular_porcentajes_acierto_error(df)
    media_pos, _ = calcular_medias_operaciones(df)
    return pct_acierto / 100 * media_pos


def render_esperanza_matematica(df: pd.DataFrame) -> None:
    """
    Renderiza en la barra lateral la sección 'Esperanza Matemática' con dos métricas:
      - EM (%)           : Esperanza matemática en %
      - Ganancia Esperada: Ganancia esperada en dinero ($)

    Cambia el título y el color según si la EM es positiva, negativa o cero.
    """
    # Calcular valores
    em = calcular_esperanza_matematica(df)
    ge = calcular_ganancia_esperada(df)

    # Determinar título según señal
    titulo = "Esperanza Matemática Positiva" if em > 0 else ("Esperanza Matemática Nula" if em == 0 else "Esperanza Matemática Negativa")
    st.sidebar.markdown(f"### {titulo}")

    if df.empty or 'Profit' not in df.columns:
        st.sidebar.markdown("_Sin datos disponibles_")
        return

    # Definir colores según valor
    def obtener_color(valor):
        if valor > 0:
            return "green"
        elif valor < 0:
            return "red"
        else:
            return "goldenrod"

    color_em = obtener_color(em)
    color_ge = obtener_color(ge)

    # Mostrar métricas en columnas, aplicando color manualmente
    col1, col2 = st.sidebar.columns(2)

    with col1:
        st.markdown(
            f"<div style='font-size:34px; color:{color_em}; text-align:center;'>{em:.2f}%</div>", 
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            f"<div style='font-size:34px; color:{color_ge}; text-align:center;'>${ge:.2f}</div>", 
            unsafe_allow_html=True
        )
