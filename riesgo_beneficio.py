import pandas as pd
import streamlit as st


def calcular_medias_operaciones(df: pd.DataFrame) -> tuple[float, float]:
    """
    Calcula las medias de las ganancias positivas y de las pérdidas absolutas,
    excluyendo operaciones de depósito/retiro.

    Parámetros:
    -----------
    df : pd.DataFrame
        DataFrame que debe contener la columna 'Profit' y opcionalmente 'Deposito'/'Retiro'.

    Retorna:
    --------
    (media_positiva, media_negativa)
    - media_positiva: media de todos los Profit > 0 (0.0 si no hay).
    - media_negativa: media de todos los abs(Profit < 0) (0.0 si no hay).
    """
    if 'Profit' not in df.columns:
        return 0.0, 0.0

    # Normalizar y filtrar Profit
    profits = pd.to_numeric(df['Profit'], errors='coerce').fillna(0.0)
    # Excluir depósitos y retiros
    if 'Deposito' in df.columns and 'Retiro' in df.columns:
        mask = df[['Deposito', 'Retiro']].notna().any(axis=1)
        profits = profits.loc[~mask]

    positivas = profits[profits > 0]
    negativas = profits[profits < 0].abs()

    return (
        positivas.mean() if not positivas.empty else 0.0,
        negativas.mean() if not negativas.empty else 0.0
    )


def calcular_ratio_riesgo_beneficio(media_negativa: float, media_positiva: float) -> float:
    """
    Calcula el ratio riesgo/beneficio como media_negativa / media_positiva.
    Devuelve inf si media_positiva es cero para evitar división por cero.
    """
    return media_negativa / media_positiva if media_positiva != 0 else float('inf')


def calcular_beneficio_por_riesgo(ratio: float) -> float:
    """
    Dado un ratio riesgo/beneficio, retorna el beneficio por unidad de riesgo.
    Si ratio es cero, devuelve inf.
    """
    return 1 / ratio if ratio != 0 else float('inf')


import pandas as pd

def calcular_profit_final(df: pd.DataFrame) -> float:
    """
    Retorna el ratio entre la suma de todos los valores positivos de 'Profit' 
    y la suma absoluta de todos los valores negativos de 'Profit',
    excluyendo aquellas filas que correspondan a depósitos o retiros.

    Fórmula:
      positivos = sum(Profit_i > 0)
      negativos = sum(|Profit_j| for Profit_j < 0)
      ratio = positivos / negativos

    Si no hay pérdidas (negativos == 0), devuelve float('inf').
    """
    if 'Profit' not in df.columns:
        return 0.0

    # Convertir Profit a numérico y rellenar NaN con 0
    profits = pd.to_numeric(df['Profit'], errors='coerce').fillna(0.0)

    # Excluir filas que son depósitos o retiros
    if 'Deposito' in df.columns and 'Retiro' in df.columns:
        mask_excluir = df['Deposito'].notna() | df['Retiro'].notna()
        profits = profits[~mask_excluir]

    # Suma de positivos y de negativos (en valor absoluto)
    suma_positivos = profits[profits > 0].sum()
    suma_negativos = profits[profits < 0].abs().sum()

    # Evitar división por cero
    if suma_negativos == 0:
        return float('inf')

    return suma_positivos / suma_negativos



def render_riesgo_beneficio(df: pd.DataFrame) -> None:
    """
    Renderiza la tabla de Riesgo / Beneficio en la sidebar:
      - Riesgo: ratio de pérdidas medias sobre ganancias medias. (color rojo)
      - Beneficio: beneficio por unidad de riesgo. (color verde)
      - Profit F.: profit final. (color amarillo)
    Todo formateado con 2 decimales y centrado.
    """
    st.sidebar.markdown("### Riesgo / Beneficio")
    tabla = pd.DataFrame({
        'Riesgo':    ['0.00'],
        'Beneficio': ['0.00'],
        'Profit F.': ['0.00']
    })

    if not df.empty and 'Profit' in df.columns:
        media_pos, media_neg = calcular_medias_operaciones(df)
        ratio = calcular_ratio_riesgo_beneficio(media_neg, media_pos)
        beneficio = calcular_beneficio_por_riesgo(ratio)
        profit_final = calcular_profit_final(df)
        tabla.loc[0] = [
            f"{ratio:.2f}",
            f"{beneficio:.2f}",
            f"{profit_final:.2f}"
        ]

    # Función para aplicar estilos por columna
    def estilo_columna(val, col):
        if col == 'Riesgo':
            return 'color: red; text-align: center;'
        elif col == 'Beneficio':
            return 'color: green; text-align: center;'
        elif col == 'Profit F.':
            return 'color: goldenrod; text-align: center;'
        else:
            return 'text-align: center;'

    styled_table = tabla.style \
        .applymap(lambda v: estilo_columna(v, 'Riesgo'), subset=['Riesgo']) \
        .applymap(lambda v: estilo_columna(v, 'Beneficio'), subset=['Beneficio']) \
        .applymap(lambda v: estilo_columna(v, 'Profit F.'), subset=['Profit F.']) \
        .set_properties(**{'text-align': 'center'})

    st.sidebar.dataframe(styled_table, hide_index=True, use_container_width=True)

