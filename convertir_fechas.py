import pandas as pd
from dateutil import parser

# Módulo "convertir_fechas.py" con preservación de raw original para reconvertir siempre desde texto

def convertir_fechas(df: pd.DataFrame, cols, dayfirst=False, yearfirst=False) -> pd.DataFrame:
    """
    Convierte múltiples formatos de fecha en las columnas indicadas usando solo dateutil.parser.
    Preserva una columna "Raw" original para asegurar consistencia tras interacciones.

    Parámetros:
    - df: DataFrame original.
    - cols: lista de columnas a convertir.
    - dayfirst: interpretar día antes del mes (DD/MM/YYYY).
    - yearfirst: interpretar año al inicio (YYYY/MM/DD).

    Retorna:
    - DataFrame con las columnas convertidas a datetime64, siempre desde el texto raw.
    """
    df = df.copy()
    # 1) Asegurar columnas raw
    for col in cols:
        raw_col = f"{col} Raw"
        if raw_col not in df.columns:
            # Guardar texto original para reconvertir
            df[raw_col] = df[col].astype(str)

    # 2) Parsear siempre desde raw
    for col in cols:
        raw_col = f"{col} Raw"
        def robust_parse(val):
            if pd.isna(val) or str(val).strip() == '':
                return pd.NaT
            s = str(val).strip()
            try:
                return parser.parse(s, dayfirst=dayfirst, yearfirst=yearfirst, fuzzy=True)
            except Exception:
                return pd.NaT
        df[col] = df[raw_col].apply(robust_parse)
        # Asegurar dtype datetime64
        df[col] = pd.to_datetime(df[col], errors='coerce')
    return df
