import numpy as np
import pandas as pd


import numpy as np
import pandas as pd

def calcular_tiempo_operacion_vectorizado(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula el tiempo operativo entre 'Fecha / Hora' y 'Fecha / Hora de Cierre',
    excluyendo fines de semana, con precisión por horas.
    Añade o actualiza la columna 'T. Op' con el formato 'Xd XXh XXm'.
    Si existe Depósito o Retiro, deja 'T. Op' vacío.
    """
    df = df.copy()
    df['T. Op'] = ''

    # Filtro para operaciones válidas
    mask = (
        df['Fecha / Hora'].notna() &
        df['Fecha / Hora de Cierre'].notna() &
        df['Deposito'].isna() &
        df['Retiro'].isna()
    )

    if not mask.any():
        return df

    def calcular_duracion(row):
        ini = row['Fecha / Hora']
        fin = row['Fecha / Hora de Cierre']
        if ini > fin:
            return ''
        
        # Rango de días hábiles
        dias_habiles = pd.date_range(start=ini.date(), end=fin.date(), freq='B')
        segundos = 0

        for dia in dias_habiles:
            dia = pd.Timestamp(dia)
            ini_dia = max(ini, dia)
            fin_dia = min(fin, dia + pd.Timedelta(days=1))
            if ini_dia < fin_dia:
                segundos += (fin_dia - ini_dia).total_seconds()

        delta = pd.to_timedelta(segundos, unit='s')
        d, h, m = delta.days, delta.seconds // 3600, (delta.seconds % 3600) // 60
        return f"{d}d {h:02d}h {m:02d}m" if d else f"{h:02d}h {m:02d}m"

    df.loc[mask, 'T. Op'] = df.loc[mask].apply(calcular_duracion, axis=1)

    return df


def calcular_dia_live(df: pd.DataFrame) -> pd.DataFrame:
    """
    Añade o actualiza la columna 'Dia LIVE':
      - Para operaciones abiertas (sin 'Fecha / Hora de Cierre'), calcula tiempo hábil
        excluyendo fines de semana desde 'Fecha / Hora' hasta ahora.
      - Para operaciones cerradas o sin 'Fecha / Hora', deja 'Dia LIVE' vacío.
    """
    df = df.copy()
    df['Dia LIVE'] = ''

    # Solo filas abiertas con Fecha / Hora válida
    mask = df['Fecha / Hora de Cierre'].isna() & df['Fecha / Hora'].notna()
    if not mask.any():
        return df

    now = pd.Timestamp.now()
    delta = now - df.loc[mask, 'Fecha / Hora']
    total_sec = delta.dt.total_seconds()
    days = delta.dt.days.fillna(0).astype(int)
    wd = df.loc[mask, 'Fecha / Hora'].dt.weekday.fillna(0).astype(int)

    # Matriz de contar sábados y domingos en j días desde wd
    extras = np.zeros((7,7), dtype=int)
    for w in range(7):
        for r in range(7):
            extras[w, r] = sum(
                1 for d in [(w + k) % 7 for k in range(r)] if d >= 5
            )

    weeks = days // 7
    rem = days % 7
    extras_list = [extras[w, r] for w, r in zip(wd, rem)]
    extras_series = pd.Series(extras_list, index=delta.index)
    weekend_days = weeks * 2 + extras_series

    sec_fds = weekend_days * 24 * 3600
    hab = (total_sec - sec_fds).clip(lower=0)

    dias = (hab // (24*3600)).astype(int)
    horas = ((hab % (24*3600)) // 3600).astype(int)
    minutos = ((hab % 3600) // 60).astype(int)

    df.loc[mask, 'Dia LIVE'] = (
        dias.astype(str) + 'd ' +
        horas.astype(str) + 'h ' +
        minutos.astype(str).str.zfill(2) + 'm'
    )
    return df

    now = pd.Timestamp.now()
    delta = now - df.loc[mask, 'Fecha / Hora']
    total_sec = delta.dt.total_seconds()
    days = delta.dt.days
    wd = df.loc[mask, 'Fecha / Hora'].dt.weekday

    # Matriz de contar sábados y domingos en j días desde wd
    extras = np.zeros((7,7), dtype=int)
    for w in range(7):
        for r in range(7):
            extras[w, r] = sum(
                1 for d in [(w + k) % 7 for k in range(r)] if d >= 5
            )

    weeks = days // 7
    rem = days % 7
    extras_list = [extras[int(w), int(r)] for w, r in zip(wd, rem)]
    extras_series = pd.Series(extras_list, index=delta.index)
    weekend_days = weeks * 2 + extras_series

    sec_fds = weekend_days * 24 * 3600
    hab = (total_sec - sec_fds).clip(lower=0)

    dias = (hab // (24*3600)).astype(int)
    horas = ((hab % (24*3600)) // 3600).astype(int)
    minutos = ((hab % 3600) // 60).astype(int)

    df.loc[mask, 'Dia LIVE'] = (
        dias.astype(str) + 'd ' +
        horas.astype(str) + 'h ' +
        minutos.astype(str).str.zfill(2) + 'm'
    )
    return df


def calcular_tiempo_dr(df: pd.DataFrame) -> pd.DataFrame:
    """
    Añade 'Tiempo D/R' donde 'Deposito' o 'Retiro' no es NaN y hay fecha de cierre.
    Excluye fines de semana de forma vectorizada.
    """
    df = df.copy()
    mask = (
        (df['Deposito'].notna() | df['Retiro'].notna()) &
        df['Fecha / Hora de Cierre'].notna()
    )
    df['Tiempo D/R'] = ''
    if not mask.any():
        return df

    delta = df.loc[mask, 'Fecha / Hora de Cierre'] - df.loc[mask, 'Fecha / Hora']
    total_sec = delta.dt.total_seconds()
    days = delta.dt.days
    wd = df.loc[mask, 'Fecha / Hora'].dt.weekday

    extras = np.zeros((7,7), dtype=int)
    for w in range(7):
        for r in range(7):
            extras[w, r] = sum(
                1 for d in [(w + k) % 7 for k in range(r)] if d >= 5
            )

    weeks = days // 7
    rem = days % 7
    extras_list = [extras[int(w), int(r)] for w, r in zip(wd, rem)]
    extras_series = pd.Series(extras_list, index=delta.index)
    weekend_days = weeks * 2 + extras_series

    sec_fds = weekend_days * 24 * 3600
    hab = (total_sec - sec_fds).clip(lower=0)

    dias = (hab // (24*3600)).astype(int)
    horas = ((hab % (24*3600)) // 3600).astype(int)
    minutos = ((hab % 3600) // 60).astype(int)

    df.loc[mask, 'Tiempo D/R'] = (
        dias.astype(str) + 'd ' +
        horas.astype(str) + 'h ' +
        minutos.astype(str).str.zfill(2) + 'm'
    )
    return df
