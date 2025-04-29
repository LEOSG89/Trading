# config.py

# Rutas y parámetros globales
COL_FILE = 'col_names.json'
TABLE_FILE = 'table_config.json'

# Columnas fijas por defecto en el DataFrame
FIXED_COLS = [
    'Activo', 'C&P', 'D', 'Día', 'Fecha / Hora',
    'Fecha / Hora de Cierre', '#Cont', 'STRK Buy', 'STRK Sell', 'Deposito', 'Retiro', 'Profit'
]

# Lista de activos disponibles
ASSETS = [
    'AMZN','AAPL','GOOG','TSLA','MSFT','META','NFLX',
    'AMD','MU','QCOM','NVDA','AVGO','TSM','SPY','QQQ','DIA','IWM',
    'DEP','RET'
]
