import pandas as pd
import streamlit as st
from typing import Optional

# Funciones de pintado…
def pintar_profit_t(val):
    try:
        if isinstance(val, str) and val.endswith('%'):
            num = float(val.strip('%'))
        else:
            num = float(val)
        if num > 0:      return 'color: green'
        elif num < 0:    return 'color: red'
        else:            return 'color: goldenrod'
    except:
        return ''

def pintar_dd_max(val):
    try:
        if isinstance(val, str) and val.endswith('%'):
            num = float(val.strip('%'))
        else:
            num = float(val)
        if num > 0:      return 'color: green'
        elif num < 0:    return 'color: red'
        else:            return 'color: goldenrod'
    except:
        return ''

def pintar_iv_rank(val):
    try:
        if isinstance(val, str) and val.endswith('%'):
            num = float(val.strip('%'))
        else:
            num = float(val)
        if num == 0:     return 'color: green'
        elif num == 50:  return 'color: goldenrod'
        elif num == 100: return 'color: red'
        else:            return ''
    except:
        return ''

def pintar_violeta(val):
    return 'color: violet'

def pintar_azul(val):
    return 'color: blue'

def aplicar_color_general(df: pd.DataFrame):
    if not st.session_state.get('pintar_colores', True):
        return None

    columnas_requeridas = [
        'C&P', 'Profit', 'Retiro', 'Deposito',
        'Profit Tot.', 'Profit T.', 'DD/Max', 'IV Rank',
        '% Alcanzado', 'Profit Alcanzado',
        '% Media', 'Profit Media',
        '#Cont', 'STRK Buy', 'STRK Sell'
    ]
    if not all(col in df.columns for col in columnas_requeridas):
        st.warning(f"Faltan columnas necesarias: {', '.join(columnas_requeridas)}.")
        return None

    def style_row(row):
        styles = [''] * len(row)
        profit = pd.to_numeric(row['Profit'], errors='coerce')
        c_p = row['C&P']
        retiro = row['Retiro']
        deposito = row['Deposito']

        hay_retiro   = pd.notna(retiro)   and retiro   != 0
        hay_deposito = pd.notna(deposito) and deposito != 0

        # Colorear fila si hay Retiro o Deposito
        if hay_retiro or hay_deposito:
            color_texto = 'color: hotpink'   if hay_retiro   else 'color: deepskyblue'
            pintar = False
            for idx, col in enumerate(row.index):
                if col == 'Activo': pintar = True
                if pintar:           styles[idx] = color_texto
                if col == 'Profit Tot.': pintar = False

        # Colorear por valor de Profit
        if not (hay_retiro or hay_deposito):
            color_profit = ''
            if pd.notna(profit):
                if profit > 0:   color_profit = 'color: green'
                elif profit < 0: color_profit = 'color: red'
                else:            color_profit = 'color: goldenrod'

            aplicar = False
            for idx, col in enumerate(row.index):
                if col == 'Activo': aplicar = True
                if aplicar and col != 'C&P':
                    styles[idx] = color_profit
                if col == '% Profit. Op':
                    aplicar = False

        # Colorear C&P
        if isinstance(c_p, str):
            idx_c_p = row.index.get_loc('C&P')
            styles[idx_c_p] = 'color: green' if c_p.upper()=='CALL' else 'color: red'

        # Colorear Profit Tot.
        if not hay_retiro and not hay_deposito:
            idx_tot = row.index.get_loc('Profit Tot.')
            val_tot = pd.to_numeric(row['Profit Tot.'], errors='coerce')
            if pd.notna(val_tot):
                if val_tot > 0:   styles[idx_tot] = 'color: green'
                elif val_tot < 0: styles[idx_tot] = 'color: red'
                else:             styles[idx_tot] = 'color: goldenrod'

        return styles

    styled_df = (
        df.style
          .apply(style_row, axis=1)
          .applymap(pintar_profit_t, subset=['Profit T.'])
          .applymap(pintar_dd_max,   subset=['DD/Max'])
          .applymap(pintar_iv_rank,  subset=['IV Rank'])
          .applymap(pintar_violeta,  subset=['% Alcanzado','Profit Alcanzado'])
          .applymap(pintar_azul,     subset=['% Media','Profit Media'])
          # ➡️ Aquí quitamos los decimales de las columnas numéricas:
          .format({
              '#Cont':     '{:.0f}',
              'STRK Buy':  '{:.0f}',
              'STRK Sell': '{:.0f}',
              'Profit':    '{:.0f}'
          })
    )
    return styled_df
