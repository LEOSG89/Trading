import pandas as pd
import numpy as np

def calcular_porcentaje_profit_op(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula la columna '% Profit. Op' como:
      (STRK Sell - STRK Buy) / STRK Buy * 100, con 2 decimales y sufijo '%'.
    Solo se añade para filas válidas; deja vacías las demás.
    - El resultado exacto 0.00% se muestra como '0.00%'.
    - '-0.00%' se normaliza a '0.00%'.
    - Solo calcula cuando ambos STRK Buy y STRK Sell tienen valor y STRK Buy != 0.
    """
    df = df.copy()
    # Asegurarse de que existan ambas columnas
    if 'STRK Buy' in df.columns and 'STRK Sell' in df.columns:
        # Máscara para filas con valores ambos no nulos y STRK Buy distinto de cero
        mask = (
            df['STRK Buy'].notna() &
            df['STRK Sell'].notna() &
            (df['STRK Buy'] != 0)
        )
        pct = pd.Series('', index=df.index, dtype=str)
        # Cálculo solo en filas válidas
        dif = df.loc[mask, 'STRK Sell'] - df.loc[mask, 'STRK Buy']
        pct_vals_num = dif.div(df.loc[mask, 'STRK Buy']).mul(100)
        pct_str = pct_vals_num.map(lambda x: f"{x:.2f}%")
        # Normalizar '-0.00%' a '0.00%'
        pct_str = pct_str.astype(str).str.replace(r'^-0\\.00%$', '0.00%', regex=True)
        pct.loc[mask] = pct_str
        df['% Profit. Op'] = pct
    return df




def calcular_profit_operacion(df: pd.DataFrame) -> pd.DataFrame:
    """
    Recalcula la columna 'Profit' como:
      (STRK Sell - STRK Buy) * #Cont, vectorizado.
    Solo se aplica si existen las tres columnas.
    """
    df = df.copy()
    cols_req = ['STRK Buy', 'STRK Sell', '#Cont']
    if all(col in df.columns for col in cols_req):
        numeric = df[['STRK Buy', 'STRK Sell', '#Cont']].apply(pd.to_numeric, errors='coerce')
        df[['STRK Buy', 'STRK Sell', '#Cont']] = numeric
        df['Profit'] = (df['STRK Sell'] - df['STRK Buy']) * df['#Cont']
    return df


def calcular_profit_total(df: pd.DataFrame) -> pd.DataFrame:
    """
    Añade al DataFrame una columna 'Profit Tot.' con la suma acumulativa
    de la columna 'Profit', formateada sin ceros innecesarios.
    Si 'Profit' es None o NaN, deja el valor correspondiente como None.
    """
    df = df.copy()
    if 'Profit' in df.columns:
        profit = pd.to_numeric(df['Profit'], errors='coerce')
        tot = profit.cumsum()
        res = pd.Series([None] * len(df), index=df.index, dtype=object)
        for idx in df.index:
            if pd.isna(df.loc[idx, 'Profit']) or df.loc[idx, 'Profit'] is None:
                res.loc[idx] = None
            else:
                val = tot.loc[idx]
                res.loc[idx] = int(val) if val == int(val) else round(val, 2)
        df['Profit Tot.'] = res
    return df


import pandas as pd

def calcular_dd_max(df: pd.DataFrame) -> pd.DataFrame:
    """
    Añade al DataFrame una columna 'DD/Max' que indica, para cada fila,
    la caída máxima (drawdown) desde el máximo histórico del balance
    acumulado ('Profit Tot.'), expresada como porcentaje negativo o None
    (solo en la última fila si 'Profit Tot.' es None).
    Solo calcula drawdown si 'Profit Tot.' tiene valor; para valores vacíos
    en filas intermedias deja cadena vacía, y None solo en la última fila.
    """
    if 'Profit Tot.' not in df.columns:
        raise KeyError("Falta la columna 'Profit Tot.'")

    df = df.copy()
    orig = df['Profit Tot.']
    balances = pd.to_numeric(df['Profit Tot.'], errors='coerce')

    max_balance = 0.0
    dd_list = []
    n = len(orig)
    for i, (val, bal) in enumerate(zip(orig, balances)):
        # Si 'Profit Tot.' es None o cadena vacía
        if pd.isna(val) or (isinstance(val, str) and val.strip() == ''):
            # Solo asignar None en la última fila, cadena vacía en resto
            dd_list.append(None if i == n-1 else '')
            continue

        # Cálculo normal de drawdown
        if bal > max_balance:
            max_balance = bal
            dd_list.append('')
        else:
            if max_balance > 0:
                dd = ((max_balance - bal) / max_balance) * 100
                dd_list.append(f"-{dd:.2f}%" if dd != 0 else '')
            else:
                dd_list.append('')

    df['DD/Max'] = dd_list
    return df



import pandas as pd

def calcular_dd_up(df: pd.DataFrame) -> pd.DataFrame:
    """
    Igual que antes: mantiene la lógica de máximo histórico y no sobreescribe
    valores previos de 'DD/Max'. Ahora, además, cada vez que el raw_dd sea
    0 o negativo, reinicia el acumulado de porcentaje para mostrar los picos
    de cada racha alcista.
    """
    if 'Profit Tot.' not in df.columns:
        raise KeyError("Falta la columna 'Profit Tot.'")
    df = df.copy()

    # 1) Convertir balances
    balances = pd.to_numeric(df['Profit Tot.'], errors='coerce').fillna(0.0)

    # 2) Calcular raw_dd con respecto al máximo histórico (puede ser + o −)
    max_balance_prev = 0.0
    raw_dd = []
    for bal in balances:
        if max_balance_prev > 0:
            dd = (bal - max_balance_prev) / max_balance_prev * 100
            raw_dd.append(dd)
        else:
            raw_dd.append(None)
        if bal > max_balance_prev:
            max_balance_prev = bal

    # 3) Acumular solo los positivos, y resetear cuando dd <= 0
    acumulado = 0.0
    cum_dd = []
    for dd in raw_dd:
        if dd is None:
            # primera fila o balance 0
            cum_dd.append(None)
        elif dd > 0:
            acumulado += dd
            cum_dd.append(acumulado)
        else:
            # dd == 0 o negativo => resetea el acumulado a ese valor
            acumulado = dd
            cum_dd.append(acumulado)

    # 4) Formatear como cadena con dos decimales y sufijo '%'
    formatted_dd = [
        f"{x:.2f}%" if x is not None else ''
        for x in cum_dd
    ]

    # 5) No sobreescribir valores manuales o anteriores en 'DD/Max'
    orig_dd = df.get('DD/Max', pd.Series('', index=df.index))
    new_dd = []
    for orig, nuevo in zip(orig_dd, formatted_dd):
        if nuevo and orig in ['', '0%', '0.00%']:
            new_dd.append(nuevo)
        else:
            new_dd.append(orig)

    df['DD/Max'] = new_dd
    return df



import numpy as np
import pandas as pd

def calcular_profit_t(df: pd.DataFrame) -> pd.DataFrame:
    """
    Añade o actualiza la columna 'Profit T.' con el porcentaje de variación
    de 'Profit Tot.' respecto a la fila anterior, formateado con dos decimales
    y sin signo '+' en los positivos.

    - La primera fila (o si hay menos de 2 filas) se marca como '0%' si existe valor previo.
    - Cualquier '0.00%' se normaliza a '0%'.
    - Si 'Profit Tot.' está vacío o es NaN, se deja '' en 'Profit T.'.
    - Se evitan infinidad(es) convirtiéndolas en 0.
    """
    if 'Profit Tot.' not in df.columns:
        raise KeyError("Falta la columna 'Profit Tot.'")
    df = df.copy()

    # Máscara para filas sin valor en 'Profit Tot.' (NaN o cadena vacía)
    orig = df['Profit Tot.']
    mask_empty = orig.isna() | orig.astype(str).str.strip().eq('')

    # 1) Extraer y limpiar la serie numérica
    tot = (
        orig.astype(str)
            .str.replace('[,%]', '', regex=True)
            .pipe(pd.to_numeric, errors='coerce')
    )

    # 2) Cálculo de porcentaje solo si al menos 2 valores numéricos
    pct = tot.diff().divide(tot.shift(1))
    pct = pct.replace([np.inf, -np.inf], np.nan).fillna(0).mul(100).round(2)

    # 3) Formateo: siempre con dos decimales y %, sin '+' para positivos
    formatted = pct.map(lambda x: f"{x:.2f}%").replace({'0.00%': '0%'})

    # 4) Asignar resultados: en filas vacías, dejar cadena vacía;
    #    en la primera fila (sin anterior), si no está vacío, poner '0%'
    resultado = formatted.copy()
    # Primera fila
    if len(resultado) >= 1 and not mask_empty.iloc[0]:
        resultado.iloc[0] = '0%'
    # Filas vacías quedan ''
    resultado[mask_empty] = ''

    df['Profit T.'] = resultado
    return df



def calcular_profit_alcanzado_vectorizado(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula la columna 'Profit Alcanzado' de forma vectorizada:
      - Profit Alcanzado[0] = Profit Tot.[0]
      - Para i > 0:
          Profit Alcanzado[i] = Profit Alcanzado[i‑1]
                               + STRK Buy[i] * (% Alcanzado[i] / 100) * #Cont[i]
    """
    required = ['Profit Tot.', 'STRK Buy', '% Alcanzado', '#Cont']
    for col in required:
        if col not in df.columns:
            raise KeyError(f"Falta la columna '{col}'")
    df = df.copy()
    # Normalizar y convertir
    tot = pd.to_numeric(
        df['Profit Tot.'].astype(str).str.replace('[,%]', '', regex=True),
        errors='coerce'
    ).fillna(0.0)
    buy = pd.to_numeric(df['STRK Buy'], errors='coerce').fillna(0.0)
    pct_alc = (
        df['% Alcanzado'].astype(str)
          .str.rstrip('%')
          .replace('', '0')
          .astype(float)
          .div(100)
          .fillna(0.0)
    )
    cont = pd.to_numeric(df['#Cont'], errors='coerce').fillna(0.0)
    # Incremento por fila vectorizado
    inc = buy.mul(pct_alc).mul(cont)
    cumsum_inc = inc.cumsum()
    primera_meta = tot.iloc[0] if len(tot) > 0 else 0.0
    ajuste = cumsum_inc.iloc[0] if len(cumsum_inc) > 0 else 0.0
    df['Profit Alcanzado'] = (
        (cumsum_inc - ajuste + primera_meta)
        .round(2)
        .map(lambda x: f"{x:.2f}")
    )
    return df


def calcular_profit_media_vectorizado(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula la columna 'Profit Media' de forma vectorizada:
      - Profit Media[0] = Profit Tot.[0]
      - Para i > 0:
          Profit Media[i] = Profit Media[i‑1]
                              + STRK Buy[i] * (% Media[i] / 100) * #Cont[i]
    """
    required = ['Profit Tot.', 'STRK Buy', '% Media', '#Cont']
    for col in required:
        if col not in df.columns:
            raise KeyError(f"Falta la columna '{col}'")
    df = df.copy()
    # Normalizar y convertir
    tot = pd.to_numeric(
        df['Profit Tot.'].astype(str).str.replace('[,%]', '', regex=True),
        errors='coerce'
    ).fillna(0.0)
    buy = pd.to_numeric(df['STRK Buy'], errors='coerce').fillna(0.0)
    pct_med = (
        df['% Media'].astype(str)
          .str.rstrip('%')
          .replace('', '0')
          .astype(float)
          .div(100)
          .fillna(0.0)
    )
    cont = pd.to_numeric(df['#Cont'], errors='coerce').fillna(0.0)
    # Incremento por fila vectorizado
    inc = buy.mul(pct_med).mul(cont)
    cumsum_inc = inc.cumsum()
    primera_meta = tot.iloc[0] if len(tot) > 0 else 0.0
    ajuste = cumsum_inc.iloc[0] if len(cumsum_inc) > 0 else 0.0
    df['Profit Media'] = (
        (cumsum_inc - ajuste + primera_meta)
        .round(2)
        .map(lambda x: f"{x:.2f}")
    )
    return df
