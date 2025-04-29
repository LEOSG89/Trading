import pandas as pd
from datetime import datetime, timedelta

def obtener_dia_semana(fecha):
    if pd.isna(fecha):
        return ''
    dias = {0: 'Lu', 1: 'Ma', 2: 'Mi', 3: 'Ju', 4: 'Vi', 5: 'Sa', 6: 'Do'}
    return dias.get(fecha.weekday(), '')

def contar_fines_semana(fecha_inicio, fecha_fin):
    dias_fin_semana = 0
    fecha_actual = fecha_inicio.date()
    fecha_fin = fecha_fin.date()
    while fecha_actual <= fecha_fin:
        if fecha_actual.weekday() in [5, 6]:
            dias_fin_semana += 1
        fecha_actual += timedelta(days=1)
    return dias_fin_semana

def formatear_tiempo(timedelta_obj):
    total_segundos = int(timedelta_obj.total_seconds())
    dias = total_segundos // (24 * 3600)
    horas = (total_segundos % (24 * 3600)) // 3600
    minutos = (total_segundos % 3600) // 60
    return f'{dias} d {horas} h {minutos:02d} m'

def calcular_diferencia(fecha_entrada, fecha_cierre):
    if isinstance(fecha_entrada, pd.Timestamp) and isinstance(fecha_cierre, pd.Timestamp):
        tiempo_total = fecha_cierre - fecha_entrada
        
        # Solo contar días de fin de semana si la operación abarca más de un día
        if fecha_entrada.date() != fecha_cierre.date():
            dias_fin_semana = contar_fines_semana(fecha_entrada, fecha_cierre)
            tiempo_operacion = tiempo_total - pd.Timedelta(days=dias_fin_semana)
        else:
            tiempo_operacion = tiempo_total
            
        return formatear_tiempo(tiempo_operacion)
    return None

def agregar_tiempo_operacion(df):
    """Añade las columnas 'T. Op' y 'Día' al DataFrame."""
    # Convertir las fechas al formato correcto
    df['Fecha / Hora'] = pd.to_datetime(df['Fecha / Hora'], format='%d/%m/%Y %I:%M %p', dayfirst=True, errors='coerce')
    df['Fecha / Hora de Cierre'] = pd.to_datetime(df['Fecha / Hora de Cierre'], format='%d/%m/%Y %I:%M %p', dayfirst=True, errors='coerce')
    
    # Siempre recalcular la columna 'Día' con las dos primeras letras del día de la semana
    df['Día'] = df['Fecha / Hora'].apply(obtener_dia_semana)
    
    # Calcular el tiempo de operación
    df['T. Op'] = df.apply(lambda row: calcular_diferencia(row['Fecha / Hora'], row['Fecha / Hora de Cierre']), axis=1)
    
    return df
