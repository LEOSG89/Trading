import pandas as pd
from datetime import datetime, timedelta

def contar_fines_semana(fecha_inicio, fecha_fin):
    """Cuenta los días de fin de semana entre dos fechas."""
    dias_fin_semana = 0
    fecha_actual = fecha_inicio
    
    while fecha_actual <= fecha_fin:
        # 5 = Sábado, 6 = Domingo
        if fecha_actual.weekday() in [5, 6]:
            dias_fin_semana += 1
        fecha_actual += timedelta(days=1)
    
    return dias_fin_semana

def formatear_tiempo(timedelta_obj):
    """Formatea un objeto timedelta en el formato 'X d Y h ZZ m'"""
    # Convertir a total de segundos
    total_segundos = int(timedelta_obj.total_seconds())
    
    # Calcular días, horas y minutos
    dias = total_segundos // (24 * 3600)
    horas = (total_segundos % (24 * 3600)) // 3600
    minutos = (total_segundos % 3600) // 60
    
    # Formatear en el estilo requerido
    return f"{dias} d {horas} h {minutos:02d} m"

def calcular_diferencia(fecha_entrada, fecha_cierre):
    """Calcula la diferencia entre la fecha de entrada y la fecha de cierre, excluyendo fines de semana."""
    if isinstance(fecha_entrada, pd.Timestamp) and isinstance(fecha_cierre, pd.Timestamp):
        # Calcular la diferencia total
        tiempo_total = fecha_cierre - fecha_entrada
        
        # Contar días de fin de semana
        dias_fin_semana = contar_fines_semana(fecha_entrada, fecha_cierre)
        
        # Restar los días de fin de semana
        tiempo_operacion = tiempo_total - pd.Timedelta(days=dias_fin_semana)
        
        # Formatear el resultado
        return formatear_tiempo(tiempo_operacion)
    return None

def agregar_tiempo_operacion(df):
    """Añade la columna 'T. Op' al DataFrame con la diferencia entre la fecha de entrada y la fecha de cierre."""
    # Convertir las fechas usando el formato correcto y especificando dayfirst=True
    df['Fecha / Hora'] = pd.to_datetime(df['Fecha / Hora'], 
                                      format='%d/%m/%Y %I:%M %p',
                                      dayfirst=True,
                                      errors='coerce')
    
    df['Fecha / Hora de Cierre'] = pd.to_datetime(df['Fecha / Hora de Cierre'],
                                                 format='%d/%m/%Y %I:%M %p',
                                                 dayfirst=True,
                                                 errors='coerce')
    
    # Calcular el tiempo de operación
    df['T. Op'] = df.apply(lambda row: calcular_diferencia(row['Fecha / Hora'], 
                                                          row['Fecha / Hora de Cierre']), 
                          axis=1)
    
    return df
