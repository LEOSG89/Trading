import pandas as pd
from dateutil import parser
from datetime import datetime

def _robust_parse(val: any, dayfirst: bool, yearfirst: bool) -> pd.Timestamp:
    """
    Fallback para parsear cadenas ambigüas usando dateutil.parser.
    Devuelve pd.NaT si no puede parsear.
    """
    if pd.isna(val) or str(val).strip() == "":
        return pd.NaT
    if isinstance(val, (pd.Timestamp, datetime)):
        return val
    try:
        return parser.parse(str(val), dayfirst=dayfirst, yearfirst=yearfirst, fuzzy=True)
    except Exception:
        return pd.NaT

def convertir_fechas(
    df: pd.DataFrame,
    cols: list[str],
    dayfirst: bool = False,
    yearfirst: bool = False
) -> pd.DataFrame:
    """
    Convierte las columnas indicadas a datetime64[ns], intentando:
      1) pd.to_datetime(..., errors='raise')
      2) .apply(_robust_parse) si falla el paso 1
    Al final fuerza dtype datetime o NaT con errors='coerce'.
    """
    df = df.copy()
    for col in cols:
        if col not in df.columns:
            continue

        # (Opcional) conservar raw
        # df[f"{col}_raw"] = df[col].astype(str)

        # 1) Intento rápido con pandas
        try:
            df[col] = pd.to_datetime(
                df[col],
                dayfirst=dayfirst,
                yearfirst=yearfirst,
                errors='raise'
            )
        except Exception:
            # 2) Fallback robusto
            df[col] = df[col].apply(lambda v: _robust_parse(v, dayfirst, yearfirst))

        # 3) Asegurar dtype final
        df[col] = pd.to_datetime(df[col], errors='coerce')

    return df
