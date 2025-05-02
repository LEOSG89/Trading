import streamlit as st
import pandas as pd
from datetime import datetime
import config
from combertir_hora_local import obtener_hora_local

def agregar_operacion(df: pd.DataFrame, porcentaje: float, tipo_op: str) -> pd.DataFrame:
    """
    Agrega una operación CALL, PUT, DEP o RET con timestamp y día local correcto.
    """
    ahora = obtener_hora_local()  # por defecto: America/New_York
    dias = ['Lu', 'Ma', 'Mi', 'Ju', 'Vi', 'Sa', 'Do']
    dia_sem = dias[ahora.weekday()]

    asset = st.session_state.get('selected_asset', '')
    val = float(st.session_state.get('input_valor', '0') or 0)

    row = {col: None for col in config.FIXED_COLS}
    row['Activo'] = asset
    # ⚠️ Convertir a string plano antes de crear el DataFrame
    row['Fecha / Hora'] = ahora.strftime('%Y-%m-%d %H:%M:%S')
    row['Fecha / Hora de Cierre'] = ahora.strftime('%Y-%m-%d %H:%M:%S')

    row['Día'] = dia_sem

    if asset == 'DEP':
        row['Deposito'] = val
        row['Profit'] = val
    elif asset == 'RET':
        row['Retiro'] = -val
        row['Profit'] = -val
    else:
        row['C&P'] = tipo_op
        row['D'] = '3d'
        strike_buy = st.session_state.get('monto_invertir', 0.0)
        row['#Cont'] = 1
        row['STRK Buy'] = strike_buy
        row['STRK Sell'] = strike_buy * (1 + porcentaje / 100)
        row['Profit'] = (row['STRK Sell'] - row['STRK Buy']) * row['#Cont']

    nueva = pd.DataFrame([row])

    # ✅ Reparar columnas de hora
    for col in ['Fecha / Hora', 'Fecha / Hora de Cierre']:
        nueva[col] = pd.to_datetime(nueva[col], errors='coerce')

    df0 = df.dropna(how='all')
    df_final = pd.concat([df0, nueva], ignore_index=True)

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
