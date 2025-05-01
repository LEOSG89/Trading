import numpy as np
import pandas as pd

# Zona horaria local de Miami
TZ_LOCAL = "America/New_York"


def calcular_tiempo_operacion_vectorizado(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula el tiempo operativo entre 'Fecha / Hora' y 'Fecha / Hora de Cierre',
    excluyendo fines de semana, de forma completamente vectorizada.
    Añade o actualiza la columna 'T. Op' con el formato 'Xd Yh ZZm'.
    Si existe Deposito o Retiro, deja 'T. Op' vacío.
    """
    df = df.copy()
    df['T. Op'] = ''

    mask = (
        df['Fecha / Hora de Cierre'].notna() &
        df['Deposito'].isna() &
        df['Retiro'].isna()
    )
    if not mask.any():
        return df

    # Asegurar que las fechas estén en la zona local
    df.loc[mask, 'Fecha / Hora'] = (
        df.loc[mask, 'Fecha / Hora']
          .dt.tz_localize('UTC', ambiguous='infer')
          .dt.tz_convert(TZ_LOCAL)
    )
    df.loc[mask, 'Fecha / Hora de Cierre'] = (
        df.loc[mask, 'Fecha / Hora de Cierre']
          .dt.tz_localize('UTC', ambiguous='infer')
          .dt.tz_convert(TZ_LOCAL)
    )

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

    df.loc[mask, 'T. Op'] = (
        dias.astype(str) + 'd ' +
        horas.astype(str) + 'h ' +
        minutos.astype(str).str.zfill(2) + 'm'
    )
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

    mask = df['Fecha / Hora de Cierre'].isna() & df['Fecha / Hora'].notna()
    if not mask.any():
        return df

    # “Ahora” en zona Miami
    now = pd.Timestamp.now(tz=TZ_LOCAL)

    # Asegurar que la apertura esté en UTC→Miami
    df.loc[mask, 'Fecha / Hora'] = (
        df.loc[mask, 'Fecha / Hora']
          .dt.tz_localize('UTC', ambiguous='infer')
          .dt.tz_convert(TZ_LOCAL)
    )

    delta = now - df.loc[mask, 'Fecha / Hora']
    total_sec = delta.dt.total_seconds()
    days = delta.dt.days.fillna(0).astype(int)
    wd = df.loc[mask, 'Fecha / Hora'].dt.weekday.fillna(0).astype(int)

    extras = np.zeros((7,7), dtype=int)
    for w in range(7):
        for r in range(7):
            extras[w, r] = sum(
                1 for d in [(w + k) % 7 for k in range(r)] if d >= 5
            )

    weeks = days // 7
    rem = days % 7
    extras_list = [extras[w, r] for w, r in zip(wd, rem)]
    extras_series = pd.Series(extras_list, index=df.loc[mask].index)
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

