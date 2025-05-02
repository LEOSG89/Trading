import pandas as pd
import pytz

def obtener_hora_local(zona: str = "America/New_York") -> pd.Timestamp:
    """
    Devuelve un Timestamp con la hora actual en la zona horaria especificada.
    """
    try:
        tz = pytz.timezone(zona)
        return pd.Timestamp.now(tz)
    except Exception:
        return pd.Timestamp.now()
