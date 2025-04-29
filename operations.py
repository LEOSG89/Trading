import streamlit as st
import pandas as pd
from datetime import datetime
import config


def agregar_operacion(df: pd.DataFrame, porcentaje: float, tipo_op: str) -> pd.DataFrame:
    """
    Lógica unificada para agregar operaciones CALL, PUT, DEP, RET,
    con día de semana abreviado, timestamp real y cálculo de STRK Buy/Sell y Profit.
    """
    # Usar timestamp real de pandas para mejor compatibilidad como datetime
    ahora = pd.Timestamp.now()
    dias = ['Lu', 'Ma', 'Mi', 'Ju', 'Vi', 'Sa', 'Do']
    dia_sem = dias[ahora.weekday()]

    asset = st.session_state.get('selected_asset', '')
    val = float(st.session_state.get('input_valor', '0') or 0)

    # Inicializar fila con None
    row = {col: None for col in config.FIXED_COLS}
    row['Activo'] = asset
    row['Fecha / Hora'] = ahora
    row['Fecha / Hora de Cierre'] = ahora
    row['Día'] = dia_sem

    if asset == 'DEP':
        row['Deposito'] = val
        row['Profit'] = val
    elif asset == 'RET':
        row['Retiro'] = -val
        row['Profit'] = -val
    else:
        # CALL o PUT
        row['C&P'] = tipo_op
        row['D'] = '3d'
        strike_buy = st.session_state.get('monto_invertir', 0.0)
        row['#Cont'] = 1
        row['STRK Buy'] = strike_buy
        row['STRK Sell'] = strike_buy * (1 + porcentaje / 100)
        row['Profit'] = (row['STRK Sell'] - row['STRK Buy']) * row['#Cont']

    nueva = pd.DataFrame([row])
    df0 = df.dropna(how='all')
    df_final = pd.concat([df0, nueva], ignore_index=True)
    # Guardar en sesión
    st.session_state.datos = df_final
    return df_final


def procesar_deposito_retiro(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    mask_dep = df['Deposito'].notna()
    mask_ret = df['Retiro'].notna()
    df.loc[mask_dep, 'Profit'] = df.loc[mask_dep, 'Deposito']
    df.loc[mask_ret, 'Retiro'] = -df.loc[mask_ret, 'Retiro'].abs()
    df.loc[mask_ret, 'Profit'] = df.loc[mask_ret, 'Retiro']
    df.loc[mask_dep, 'Activo'] = 'DEP'
    df.loc[mask_ret, 'Activo'] = 'RET'
    cols_limpieza = ['C&P', 'D', '#Cont', 'STRK Buy', 'STRK Sell']
    for col in cols_limpieza:
        if col in df.columns:
            df.loc[mask_dep | mask_ret, col] = pd.NA
    return df


def agregar_iv_rank(df: pd.DataFrame, rank_str: str) -> pd.DataFrame:
    """
    Asigna el valor de IV Rank a la última fila del DataFrame sin crear filas nuevas.
    """
    df = df.copy()
    if not df.empty:
        last_idx = df.index[-1]
        df.at[last_idx, 'IV Rank'] = rank_str
    st.session_state.datos = df
    return df
