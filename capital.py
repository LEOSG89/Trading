import pandas as pd
import streamlit as st


def calcular_total_depositos(df: pd.DataFrame) -> float:
    if 'Deposito' not in df.columns:
        return 0.0
    return pd.to_numeric(df['Deposito'], errors='coerce').fillna(0.0).sum()


def calcular_total_retiros(df: pd.DataFrame) -> float:
    if 'Retiro' not in df.columns:
        return 0.0
    return pd.to_numeric(df['Retiro'], errors='coerce').fillna(0.0).abs().sum()


def calcular_ganancias_totales(df: pd.DataFrame) -> float:
    profits = pd.to_numeric(df.get('Profit', pd.Series(dtype=float)), errors='coerce').fillna(0.0).sum()
    deps = calcular_total_depositos(df)
    rets = calcular_total_retiros(df)
    return profits - deps + rets


def calcular_porcentaje_ganancia(tot_dep: float, tot_gan: float) -> float:
    return (tot_gan / tot_dep * 100) if tot_dep != 0 else float('inf')


def render_tabla_capital(df: pd.DataFrame) -> None:
    st.sidebar.markdown("### Capital")
    tabla = pd.DataFrame({
        'I. T. Capital':  ['$0.00'],
        'Retiros':        ['$0.00'],
        'Ganancias Tot.': ['$0.00'],
        '% Ganancia T.':  ['0%']
    })

    if not df.empty:
        tot_dep = calcular_total_depositos(df)
        tot_ret = calcular_total_retiros(df)
        tot_gan = calcular_ganancias_totales(df)
        pct_gan = calcular_porcentaje_ganancia(tot_dep, tot_gan)
        tabla.loc[0] = [
            f"${tot_dep:.2f}",
            f"${tot_ret:.2f}",
            f"${tot_gan:.2f}",
            f"{pct_gan:.2f}%"
        ]

    # Funciones de color por columna
    def estilo_columna(val, col):
        try:
            if col == 'I. T. Capital':
                return 'color: deepskyblue; text-align: center;'
            elif col == 'Retiros':
                return 'color: hotpink; text-align: center;'
            elif col == 'Ganancias Tot.':
                num = float(val.replace('$', '').replace(',', ''))
                if num > 0:
                    return 'color: green; text-align: center;'
                elif num < 0:
                    return 'color: red; text-align: center;'
                else:
                    return 'color: goldenrod; text-align: center;'
            elif col == '% Ganancia T.':
                num = float(val.replace('%', '').replace(',', ''))
                if num > 0:
                    return 'color: green; text-align: center;'
                elif num < 0:
                    return 'color: red; text-align: center;'
                else:
                    return 'color: goldenrod; text-align: center;'
        except:
            return 'text-align: center;'

    # Aplicar estilo a cada columna
    styled_table = tabla.style \
        .applymap(lambda v: estilo_columna(v, 'I. T. Capital'), subset=['I. T. Capital']) \
        .applymap(lambda v: estilo_columna(v, 'Retiros'), subset=['Retiros']) \
        .applymap(lambda v: estilo_columna(v, 'Ganancias Tot.'), subset=['Ganancias Tot.']) \
        .applymap(lambda v: estilo_columna(v, '% Ganancia T.'), subset=['% Ganancia T.']) \
        .set_properties(**{'text-align': 'center'})

    st.sidebar.dataframe(styled_table, hide_index=True, use_container_width=True)
