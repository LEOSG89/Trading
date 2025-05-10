import pandas as pd
from dateutil import parser
from datetime import datetime

def convertir_fechas(df: pd.DataFrame, cols, dayfirst=False, yearfirst=False) -> pd.DataFrame:
    """
    Convierte de forma robusta múltiples formatos de fecha en las columnas indicadas.

    Parámetros:
    - df: DataFrame original.
    - cols: lista de nombres de columnas a convertir.
    - dayfirst: interpretar día antes del mes.
    - yearfirst: interpretar año al inicio.

    Para cada valor aplica:
      1) pd.to_datetime con inferencia rápida;
      2) si falla, dateutil.parser.parse con 'fuzzy';
      3) si sigue fallando, asigna NaT.

    Retorna:
    - DataFrame con las columnas convertidas a datetime.
    """
    df = df.copy()
    for col in cols:
        if col in df.columns:
            def robust_parse(val):
                # Mantener nulos
                if pd.isna(val):
                    return pd.NaT
                # Si ya es datetime
                if isinstance(val, (pd.Timestamp, datetime)):
                    return val
                s = str(val).strip()
                # Intento rápido con pandas
                try:
                    return pd.to_datetime(
                        s,
                        infer_datetime_format=True,
                        dayfirst=dayfirst,
                        yearfirst=yearfirst,
                        errors='raise'
                    )
                except Exception:
                    # Fallback a dateutil
                    try:
                        return parser.parse(
                            s,
                            dayfirst=dayfirst,
                            yearfirst=yearfirst,
                            fuzzy=True
                        )
                    except Exception:
                        return pd.NaT
            # Aplicar parse robusto
            df[col] = df[col].apply(robust_parse)
            # Asegurar dtype datetime64
            df[col] = pd.to_datetime(df[col], errors='coerce')
    return df

