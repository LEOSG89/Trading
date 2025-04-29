import pandas as pd
import numpy as np

def calcular_porcentaje_exito(df):
    """Calcula el porcentaje de operaciones exitosas."""
    total_operaciones = len(df)
    if total_operaciones == 0:
        return 0
    
    operaciones_exitosas = len(df[df['Resultado'] > 0])
    return (operaciones_exitosas / total_operaciones) * 100

def calcular_ratio_beneficio_riesgo(df):
    """Calcula el ratio beneficio/riesgo promedio."""
    ganancias = df[df['Resultado'] > 0]['Resultado'].mean()
    perdidas = abs(df[df['Resultado'] < 0]['Resultado'].mean())
    
    if perdidas == 0:
        return float('inf')
    return ganancias / perdidas

def calcular_estadisticas(df):
    """Calcula todas las estadísticas importantes del trading."""
    stats = {
        'Total Operaciones': len(df),
        'Porcentaje Éxito': calcular_porcentaje_exito(df),
        'Ratio Beneficio/Riesgo': calcular_ratio_beneficio_riesgo(df),
        'Ganancia Total': df['Resultado'].sum(),
        'Ganancia Promedio': df[df['Resultado'] > 0]['Resultado'].mean(),
        'Pérdida Promedio': df[df['Resultado'] < 0]['Resultado'].mean(),
        'Máxima Ganancia': df['Resultado'].max(),
        'Máxima Pérdida': df['Resultado'].min()
    }
    return stats
