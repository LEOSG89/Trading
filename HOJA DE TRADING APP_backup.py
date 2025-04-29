import streamlit as st
from funciones.cargar_archivo import cargar_archivo
from funciones.mostrar_grafico import (
    mostrar_grafico_barras, 
    mostrar_grafico_area, 
    mostrar_grafico_area_dd_max_negativo, 
    mostrar_grafico_tendencia_profit, 
    mostrar_grafico_puntos, 
    mostrar_grafico_tiempo_operacion
)
from funciones.agregar_fila import agregar_fila
from funciones.tabla_editable_gestion_funciones import (
    limpiar_columnas_deposito_retiro,
    quitar_ceros_tabla,
    limpiar_valores_activo,
    asignar_dep_ret_activo,
    formatear_columna_d,
    calcular_porcentaje_profit_tot,
    color_profit_t,
    calcular_profit_alcanzado,
    calcular_profit_media,
    procesar_depositos_retiros,
    limpiar_columnas,
    color_profit_alcanzado_media,
    color_porcentajes_alcanzado_media,
    calcular_operaciones_ganadoras_perdedoras
)
from funciones.modulo_fechas_new import agregar_tiempo_operacion
from funciones.colores import mostrar_tabla_con_colores
import pandas as pd
import os
import subprocess
from datetime import datetime
import plotly.graph_objects as go
import numpy as np
import plotly.express as px
import time
import re
import math
from PIL import Image
import base64
import io
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings
import random
warnings.filterwarnings('ignore')

def calcular_deposito(df):
    """Calcula y actualiza los valores de la columna Deposito."""
    try:
        # Convertir la columna Deposito a numérico
        df['Deposito'] = pd.to_numeric(df['Deposito'], errors='coerce')
        
        # Reemplazar NaN por 0
        df['Deposito'] = df['Deposito'].fillna(0)
        
        return df
    except Exception as e:
        print(f"Error en calcular_deposito: {str(e)}")
        return df

def calcular_retiro(df):
    """Calcula y actualiza los valores de la columna Retiro."""
    try:
        # Convertir la columna Retiro a numérico
        df['Retiro'] = pd.to_numeric(df['Retiro'], errors='coerce')
        
        # Reemplazar NaN por 0
        df['Retiro'] = df['Retiro'].fillna(0)
        
        return df
    except Exception as e:
        print(f"Error en calcular_retiro: {str(e)}")
        return df

def generar_combinaciones_contratos(numero_contratos):
    """
    Genera combinaciones aleatorias de contratos según las condiciones especificadas.
    Args:
        numero_contratos: Número total de contratos a distribuir
    Returns:
        tuple: Dos listas con las combinaciones para cada columna
    """
    if numero_contratos < 2:
        return [0, 0, 0, 0], [0, 0, 0, 0]
    
    def generar_combinacion(n, num_elementos):
        """Genera una combinación válida de n elementos que sumen numero_contratos"""
        if n == 2:
            if num_elementos < 2:
                return [num_elementos, 0]
            a = random.randint(1, num_elementos-1)
            b = num_elementos - a
            return sorted([a, b])
        elif n == 3:
            if num_elementos < 3:
                return [num_elementos, 0, 0]
            a = random.randint(1, max(1, num_elementos-2))
            b = random.randint(1, max(1, num_elementos-a-1))
            c = num_elementos - a - b
            return sorted([a, b, c])
        else:  # n == 4
            if num_elementos < 4:
                return [num_elementos, 0, 0, 0]
            a = random.randint(1, max(1, num_elementos-3))
            b = random.randint(1, max(1, num_elementos-a-2))
            c = random.randint(1, max(1, num_elementos-a-b-1))
            d = num_elementos - a - b - c
            return sorted([a, b, c, d])
    
    def es_combinacion_valida(combinacion, combinaciones_previas, permitir_iguales=False):
        """Verifica si la combinación es válida y diferente a las anteriores"""
        if not combinacion:
            return False
        if any(x < 0 for x in combinacion):
            return False
        if len(combinacion) > 1 and combinacion[0] > min(combinacion[1:]):
            return False
        if not permitir_iguales:
            return combinacion not in combinaciones_previas
        return True
    
    # Para números pequeños (menos de 5), permitir combinaciones iguales
    permitir_iguales = numero_contratos < 5
    
    # Límite de intentos para evitar bucles infinitos
    max_intentos = 100
    
    # Generar combinaciones para la primera columna
    num_elementos1 = random.choice([2, 3, 4])
    combinacion1 = generar_combinacion(num_elementos1, numero_contratos)
    
    # Generar combinaciones para la segunda columna
    num_elementos2 = random.choice([2, 3, 4])
    while num_elementos2 == num_elementos1 and not permitir_iguales:
        num_elementos2 = random.choice([2, 3, 4])
    
    # Intentar generar una combinación válida para la segunda columna
    intentos = 0
    combinacion2 = generar_combinacion(num_elementos2, numero_contratos)
    while not es_combinacion_valida(combinacion2, [combinacion1], permitir_iguales):
        intentos += 1
        if intentos >= max_intentos:
            # Si se excede el límite de intentos, reiniciar el proceso
            num_elementos1 = random.choice([2, 3, 4])
            combinacion1 = generar_combinacion(num_elementos1, numero_contratos)
            num_elementos2 = random.choice([2, 3, 4])
            while num_elementos2 == num_elementos1 and not permitir_iguales:
                num_elementos2 = random.choice([2, 3, 4])
            combinacion2 = generar_combinacion(num_elementos2, numero_contratos)
            intentos = 0
        else:
            combinacion2 = generar_combinacion(num_elementos2, numero_contratos)
    
    # Rellenar con ceros hasta tener 4 elementos
    while len(combinacion1) < 4:
        combinacion1.append(0)
    while len(combinacion2) < 4:
        combinacion2.append(0)
    
    return combinacion1, combinacion2

def calcular_porcentajes_acierto_error(df):
    """Calcula el porcentaje de acierto y error basado en las operaciones ganadoras y perdedoras."""
    # Contar valores en Deposito y Retiro
    num_depositos = len(df[df['Deposito'].notna() & (df['Deposito'] != '')])
    num_retiros = len(df[df['Retiro'].notna() & (df['Retiro'] != '')])
    
    # Convertir Profit a numérico
    df['Profit'] = pd.to_numeric(df['Profit'], errors='coerce')
    
    # Contar operaciones ganadoras y perdedoras
    num_ganadoras = len(df[df['Profit'] > 0]) - num_depositos
    num_perdedoras = len(df[df['Profit'] < 0]) - num_retiros
    
    # Asegurar que no tengamos valores negativos
    num_ganadoras = max(0, num_ganadoras)
    num_perdedoras = max(0, num_perdedoras)
    
    # Calcular total de operaciones
    total_operaciones = num_ganadoras + num_perdedoras
    
    # Calcular porcentajes
    if total_operaciones > 0:
        porcentaje_acierto = (num_ganadoras / total_operaciones) * 100
        porcentaje_error = (num_perdedoras / total_operaciones) * 100
    else:
        porcentaje_acierto = 0
        porcentaje_error = 0
    
    return porcentaje_acierto, porcentaje_error

def calcular_medias_operaciones(df):
    """Calcula la media de las operaciones positivas y negativas, excluyendo depósitos y retiros."""
    # Convertir Profit a numérico
    df['Profit'] = pd.to_numeric(df['Profit'], errors='coerce')
    
    # Filtrar operaciones que no son depósitos ni retiros
    operaciones_validas = df[
        (df['Deposito'].isna() | (df['Deposito'] == '')) & 
        (df['Retiro'].isna() | (df['Retiro'] == ''))
    ]
    
    # Filtrar operaciones positivas y negativas
    operaciones_positivas = operaciones_validas[operaciones_validas['Profit'] > 0]['Profit']
    operaciones_negativas = operaciones_validas[operaciones_validas['Profit'] < 0]['Profit']
    
    # Calcular medias
    media_positiva = operaciones_positivas.mean() if not operaciones_positivas.empty else 0
    media_negativa = operaciones_negativas.mean() if not operaciones_negativas.empty else 0
    
    return media_positiva, media_negativa

# Función para calcular el Drawdown máximo
def calcular_dd_max(df):
    if 'Profit Tot.' not in df.columns:
        print("Error: No se encontró la columna 'Profit Tot.'")
        return df
    
    max_balance_current = 0
    dd_max_list = []
    
    print("Columnas antes de agregar DD/Max:", df.columns.tolist())
    
    for i in range(len(df)):
        try:
            # Obtener el valor actual de Profit Tot.
            balance_actual = float(df['Profit Tot.'].iloc[i]) if pd.notnull(df['Profit Tot.'].iloc[i]) else 0
            
            # Para el primer valor, establecer 0
            if i == 0:
                dd_max_list.append("0%")
                max_balance_current = balance_actual
                continue
            
            # Actualizar max_balance_current si el valor actual es mayor
            if balance_actual > max_balance_current:
                max_balance_current = balance_actual
                dd_max_list.append("0%")  # No hay drawdown cuando el balance aumenta
            else:
                # Calcular el drawdown solo cuando el balance disminuye
                if max_balance_current > 0:
                    dd = ((max_balance_current - balance_actual) / max_balance_current) * 100
                    if dd > 0:
                        dd_max_list.append(f"-{dd:.2f}%")
                    else:
                        dd_max_list.append("0%")
                else:
                    dd_max_list.append("0%")
            
        except Exception as e:
            print(f"Error en fila {i}: {e}")
            dd_max_list.append("0%")
    
    # Asegurarse de que la longitud de dd_max_list coincida con el DataFrame
    while len(dd_max_list) < len(df):
        dd_max_list.append("0%")
    
    # Crear o actualizar la columna DD/Max
    df['DD/Max'] = dd_max_list
    print("Columnas después de agregar DD/Max:", df.columns.tolist())
    print("Primeros 5 valores de DD/Max:", df['DD/Max'].head().tolist())
    return df

# Función para calcular el Drawdown Up
def calcular_dd_up(df):
    if 'Profit Tot.' not in df.columns:
        print("Error: No se encontró la columna 'Profit Tot.'")
        return df
    
    max_balance_prev = 0
    dd_up_list = []
    
    print("Columnas antes de agregar DD Up:", df.columns.tolist())
    
    for i in range(len(df)):
        try:
            # Obtener el valor actual de Profit Tot.
            balance_actual = float(df['Profit Tot.'].iloc[i]) if pd.notnull(df['Profit Tot.'].iloc[i]) else 0
            
            # Calcular DD Up solo cuando el precio incrementa
            if balance_actual > max_balance_prev and max_balance_prev > 0:
                dd_up = ((balance_actual - max_balance_prev) / max_balance_prev) * 100
                if dd_up > 0:
                    dd_up_list.append(f"+{dd_up:.2f}%")
                else:
                    dd_up_list.append("0%")
            else:
                dd_up_list.append("0%")
            
            # Actualizar max_balance_prev si el valor actual es mayor
            if balance_actual > max_balance_prev:
                max_balance_prev = balance_actual
            
        except Exception as e:
            print(f"Error en fila {i}: {e}")
            dd_up_list.append("0%")
    
    # Asegurarse de que la longitud de dd_up_list coincida con el DataFrame
    while len(dd_up_list) < len(df):
        dd_up_list.append("0%")
    
    # Combinar los resultados con la columna DD/Max existente
    for i in range(len(df)):
        if dd_up_list[i] != "0%" and df['DD/Max'].iloc[i] == "0%":
            df['DD/Max'].iloc[i] = dd_up_list[i]
    
    print("Columnas después de agregar DD Up:", df.columns.tolist())
    print("Primeros 5 valores de DD/Max:", df['DD/Max'].head().tolist())
    return df

# Función para colorear la columna DD/Max
def color_dd_max(df):
    color_map = pd.DataFrame('', index=df.index, columns=df.columns)
    
    for idx in df.index:
        try:
            if 'DD/Max' in df.columns:
                dd_max = df.loc[idx, 'DD/Max']
                color = ''
                if dd_max == "0%":
                    color = 'color: yellow'
                elif dd_max.startswith('+'):
                    color = 'color: green'
                elif dd_max.startswith('-'):
                    color = 'color: red'
                else:
                    color = ''
                color_map.loc[idx, 'DD/Max'] = color
        except:
            continue
    
    return color_map

# Función para agregar CALL 50%
def agregar_call_50(df):
    """Agrega una nueva fila con una operación CALL 50%"""
    # Crear una copia del DataFrame
    df_nuevo = df.copy()
    
    # Obtener la fecha actual
    fecha_actual = datetime.now()
    dia_semana = ['Lu', 'Ma', 'Mi', 'Ju', 'Vi', 'Sa', 'Do'][fecha_actual.weekday()]
    
    # Crear la nueva fila
    nueva_fila = {
        'Activo': 'SPY',
        'C&P': 'CALL',
        'D': '1d',
        'Día': dia_semana,
        'Fecha / Hora': fecha_actual.strftime('%Y-%m-%d %H:%M:%S'),
        'Fecha / Hora de Cierre': fecha_actual.strftime('%Y-%m-%d %H:%M:%S'),
        '#Cont': 1,
        'STRK Buy': 30.0,
        'STRK Sell': 45.0  # 50% de profit sobre STRK Buy (30 + 15 = 45)
    }
    
    # Agregar la nueva fila al DataFrame
    df_nuevo = pd.concat([df_nuevo, pd.DataFrame([nueva_fila])], ignore_index=True)
    
    return df_nuevo

# Función para agregar CALL 0%
def agregar_call_0(df):
    """Agrega una nueva fila con una operación CALL 0%"""
    # Crear una copia del DataFrame
    df_nuevo = df.copy()
    
    # Obtener la fecha actual
    fecha_actual = datetime.now()
    dia_semana = ['Lu', 'Ma', 'Mi', 'Ju', 'Vi', 'Sa', 'Do'][fecha_actual.weekday()]
    
    # Crear la nueva fila
    nueva_fila = {
        'Activo': 'SPY',
        'C&P': 'CALL',
        'D': '1d',
        'Día': dia_semana,
        'Fecha / Hora': fecha_actual.strftime('%Y-%m-%d %H:%M:%S'),
        'Fecha / Hora de Cierre': fecha_actual.strftime('%Y-%m-%d %H:%M:%S'),
        '#Cont': 1,
        'STRK Buy': 30.0,
        'STRK Sell': 30.0  # 0% de profit sobre STRK Buy (30 = 30)
    }
    
    # Agregar la nueva fila al DataFrame
    df_nuevo = pd.concat([df_nuevo, pd.DataFrame([nueva_fila])], ignore_index=True)
    
    return df_nuevo

# Función para agregar PUT 0%
def agregar_put_0(df):
    """Agrega una nueva fila con una operación PUT 0%"""
    # Crear una copia del DataFrame
    df_nuevo = df.copy()
    
    # Obtener la fecha actual
    fecha_actual = datetime.now()
    dia_semana = ['Lu', 'Ma', 'Mi', 'Ju', 'Vi', 'Sa', 'Do'][fecha_actual.weekday()]
    
    # Crear la nueva fila
    nueva_fila = {
        'Activo': 'PUT',
        'C&P': 'PUT',
        'D': '1d',
        'Día': dia_semana,
        'Fecha / Hora': fecha_actual.strftime('%Y-%m-%d %H:%M:%S'),
        'Fecha / Hora de Cierre': fecha_actual.strftime('%Y-%m-%d %H:%M:%S'),
        '#Cont': 1,
        'STRK Buy': 30.0,
        'STRK Sell': 30.0  # 0% de profit sobre STRK Buy (30 = 30)
    }
    
    # Agregar la nueva fila al DataFrame
    df_nuevo = pd.concat([df_nuevo, pd.DataFrame([nueva_fila])], ignore_index=True)
    
    return df_nuevo

# Función para agregar CALL -100%
def agregar_call_menos_100(df):
    """Agrega una nueva fila con una operación CALL -100%"""
    # Crear una copia del DataFrame
    df_nuevo = df.copy()
    
    # Obtener la fecha actual
    fecha_actual = datetime.now()
    dia_semana = ['Lu', 'Ma', 'Mi', 'Ju', 'Vi', 'Sa', 'Do'][fecha_actual.weekday()]
    
    # Crear la nueva fila
    nueva_fila = {
        'Activo': 'CALL',
        'C&P': 'CALL',
        'D': '1d',
        'Día': dia_semana,
        'Fecha / Hora': fecha_actual.strftime('%Y-%m-%d %H:%M:%S'),
        'Fecha / Hora de Cierre': fecha_actual.strftime('%Y-%m-%d %H:%M:%S'),
        '#Cont': 1,
        'STRK Buy': 30.0,
        'STRK Sell': 0.0  # -100% de profit sobre STRK Buy (0 = 30 - 100%)
    }
    
    # Agregar la nueva fila al DataFrame
    df_nuevo = pd.concat([df_nuevo, pd.DataFrame([nueva_fila])], ignore_index=True)
    
    return df_nuevo

# Función para agregar CALL -50%
def agregar_call_menos_50(df):
    """Agrega una nueva fila con una operación CALL -50%"""
    # Crear una copia del DataFrame
    df_nuevo = df.copy()
    
    # Obtener la fecha actual
    fecha_actual = datetime.now()
    dia_semana = ['Lu', 'Ma', 'Mi', 'Ju', 'Vi', 'Sa', 'Do'][fecha_actual.weekday()]
    
    # Crear la nueva fila
    nueva_fila = {
        'Activo': 'CALL',
        'C&P': 'CALL',
        'D': '1d',
        'Día': dia_semana,
        'Fecha / Hora': fecha_actual.strftime('%Y-%m-%d %H:%M:%S'),
        'Fecha / Hora de Cierre': fecha_actual.strftime('%Y-%m-%d %H:%M:%S'),
        '#Cont': 1,
        'STRK Buy': 30.0,
        'STRK Sell': 15.0  # -50% de profit sobre STRK Buy (15 = 30 - 50%)
    }
    
    # Agregar la nueva fila al DataFrame
    df_nuevo = pd.concat([df_nuevo, pd.DataFrame([nueva_fila])], ignore_index=True)
    
    return df_nuevo

# Función para agregar PUT 100%
def agregar_put_100(df):
    """Agrega una nueva fila con una operación PUT 100%"""
    # Crear una copia del DataFrame
    df_nuevo = df.copy()
    
    # Obtener la fecha actual
    fecha_actual = datetime.now()
    dia_semana = ['Lu', 'Ma', 'Mi', 'Ju', 'Vi', 'Sa', 'Do'][fecha_actual.weekday()]
    
    # Crear la nueva fila
    nueva_fila = {
        'Activo': 'PUT',
        'C&P': 'PUT',
        'D': '1d',
        'Día': dia_semana,
        'Fecha / Hora': fecha_actual.strftime('%Y-%m-%d %H:%M:%S'),
        'Fecha / Hora de Cierre': fecha_actual.strftime('%Y-%m-%d %H:%M:%S'),
        '#Cont': 1,
        'STRK Buy': 30.0,
        'STRK Sell': 60.0  # 100% de profit sobre STRK Buy (60 = 30 + 100%)
    }
    
    # Agregar la nueva fila al DataFrame
    df_nuevo = pd.concat([df_nuevo, pd.DataFrame([nueva_fila])], ignore_index=True)
    
    return df_nuevo

# Función para agregar PUT 50%
def agregar_put_50(df):
    """Agrega una nueva fila con una operación PUT 50%"""
    # Crear una copia del DataFrame
    df_nuevo = df.copy()
    
    # Obtener la fecha actual
    fecha_actual = datetime.now()
    dia_semana = ['Lu', 'Ma', 'Mi', 'Ju', 'Vi', 'Sa', 'Do'][fecha_actual.weekday()]
    
    # Crear la nueva fila
    nueva_fila = {
        'Activo': 'PUT',
        'C&P': 'PUT',
        'D': '1d',
        'Día': dia_semana,
        'Fecha / Hora': fecha_actual.strftime('%Y-%m-%d %H:%M:%S'),
        'Fecha / Hora de Cierre': fecha_actual.strftime('%Y-%m-%d %H:%M:%S'),
        '#Cont': 1,
        'STRK Buy': 30.0,
        'STRK Sell': 45.0  # 50% de profit sobre STRK Buy (45 = 30 + 50%)
    }
    
    # Agregar la nueva fila al DataFrame
    df_nuevo = pd.concat([df_nuevo, pd.DataFrame([nueva_fila])], ignore_index=True)
    
    return df_nuevo

# Función para agregar PUT -100%
def agregar_put_menos_100(df):
    """Agrega una nueva fila con una operación PUT -100%"""
    # Crear una copia del DataFrame
    df_nuevo = df.copy()
    
    # Obtener la fecha actual
    fecha_actual = datetime.now()
    dia_semana = ['Lu', 'Ma', 'Mi', 'Ju', 'Vi', 'Sa', 'Do'][fecha_actual.weekday()]
    
    # Crear la nueva fila
    nueva_fila = {
        'Activo': 'PUT',
        'C&P': 'PUT',
        'D': '1d',
        'Día': dia_semana,
        'Fecha / Hora': fecha_actual.strftime('%Y-%m-%d %H:%M:%S'),
        'Fecha / Hora de Cierre': fecha_actual.strftime('%Y-%m-%d %H:%M:%S'),
        '#Cont': 1,
        'STRK Buy': 30.0,
        'STRK Sell': 0.0  # -100% de profit sobre STRK Buy (0 = 30 - 100%)
    }
    
    # Agregar la nueva fila al DataFrame
    df_nuevo = pd.concat([df_nuevo, pd.DataFrame([nueva_fila])], ignore_index=True)
    
    return df_nuevo

# Función para agregar PUT -50%
def agregar_put_menos_50(df):
    """Agrega una nueva fila con una operación PUT -50%"""
    # Crear una copia del DataFrame
    df_nuevo = df.copy()
    
    # Obtener la fecha actual
    fecha_actual = datetime.now()
    dia_semana = ['Lu', 'Ma', 'Mi', 'Ju', 'Vi', 'Sa', 'Do'][fecha_actual.weekday()]
    
    # Crear la nueva fila
    nueva_fila = {
        'Activo': 'PUT',
        'C&P': 'PUT',
        'D': '1d',
        'Día': dia_semana,
        'Fecha / Hora': fecha_actual.strftime('%Y-%m-%d %H:%M:%S'),
        'Fecha / Hora de Cierre': fecha_actual.strftime('%Y-%m-%d %H:%M:%S'),
        '#Cont': 1,
        'STRK Buy': 30.0,
        'STRK Sell': 15.0  # -50% de profit sobre STRK Buy (15 = 30 - 50%)
    }
    
    # Agregar la nueva fila al DataFrame
    df_nuevo = pd.concat([df_nuevo, pd.DataFrame([nueva_fila])], ignore_index=True)
    
    return df_nuevo

def agregar_call_100(df):
    """Agrega una nueva fila con una operación CALL 100%"""
    # Crear una copia del DataFrame
    df_nuevo = df.copy()
    
    # Obtener la fecha actual
    fecha_actual = datetime.now()
    dia_semana = ['Lu', 'Ma', 'Mi', 'Ju', 'Vi', 'Sa', 'Do'][fecha_actual.weekday()]
    
    # Crear la nueva fila
    nueva_fila = {
        'Activo': 'SPY',
        'C&P': 'CALL',
        'D': '1d',
        'Día': dia_semana,
        'Fecha / Hora': fecha_actual.strftime('%Y-%m-%d %H:%M:%S'),
        'Fecha / Hora de Cierre': fecha_actual.strftime('%Y-%m-%d %H:%M:%S'),
        '#Cont': 1,
        'STRK Buy': 30.0,
        'STRK Sell': 60.0  # 100% de profit sobre STRK Buy (60 = 30 + 100%)
    }
    
    # Agregar la nueva fila al DataFrame
    df_nuevo = pd.concat([df_nuevo, pd.DataFrame([nueva_fila])], ignore_index=True)
    
    return df_nuevo

def calcular_total_depositos(df):
    """Calcula la suma total de los depósitos."""
    try:
        # Crear una copia de la columna Deposito para no modificar el DataFrame original
        depositos = df['Deposito'].copy()
        
        # Convertir a numérico
        depositos = pd.to_numeric(depositos, errors='coerce')
        
        # Reemplazar NaN por 0
        depositos = depositos.fillna(0)
        
        # Sumar todos los depósitos
        total_depositos = depositos.sum()
        
        return total_depositos
    except Exception as e:
        print(f"Error en calcular_total_depositos: {str(e)}")
        return 0

def calcular_ganancias_totales(df):
    """Calcula las ganancias totales excluyendo operaciones con depósitos o retiros."""
    try:
        # Crear copias de las columnas necesarias
        profit = df['Profit'].copy()
        deposito = df['Deposito'].copy()
        retiro = df['Retiro'].copy()
        
        # Convertir a numérico
        profit = pd.to_numeric(profit, errors='coerce')
        deposito = pd.to_numeric(deposito, errors='coerce')
        retiro = pd.to_numeric(retiro, errors='coerce')
        
        # Reemplazar NaN por 0
        profit = profit.fillna(0)
        deposito = deposito.fillna(0)
        retiro = retiro.fillna(0)
        
        # Filtrar operaciones donde no hay ni depósitos ni retiros
        operaciones_validas = (deposito == 0) & (retiro == 0)
        
        # Sumar solo los profits de las operaciones válidas
        total_profit = profit[operaciones_validas].sum()
        
        return total_profit
    except Exception as e:
        print(f"Error en calcular_ganancias_totales: {str(e)}")
        return 0

def calcular_porcentaje_ganancia(capital, ganancias_totales):
    """Calcula el porcentaje de ganancia basado en el capital y las ganancias totales."""
    if capital == 0:
        return 0
    return (ganancias_totales / capital) * 100

def calcular_total_retiros(df):
    """Calcula el total de retiros."""
    # Convertir columna a numérico
    df['Retiro'] = pd.to_numeric(df['Retiro'], errors='coerce')
    
    # Sumar los retiros válidos y asegurar que sea positivo
    total_retiros = abs(df['Retiro'].sum())
    
    return total_retiros

def calcular_ratio_riesgo_beneficio(media_negativa, media_positiva):
    """
    Calcula el ratio de riesgo/beneficio usando los valores absolutos.
    Args:
        media_negativa: Valor de la media de operaciones negativas
        media_positiva: Valor de la media de operaciones positivas
    Returns:
        float: Ratio de riesgo/beneficio
    """
    try:
        # Convertir a valores absolutos
        riesgo = abs(float(media_negativa))
        beneficio = float(media_positiva)
        
        # Evitar división por cero
        if beneficio == 0:
            return 0
            
        return riesgo / beneficio
    except:
        return 0

def calcular_beneficio_por_riesgo(ratio_riesgo):
    """
    Calcula el beneficio basado en el ratio de riesgo.
    Args:
        ratio_riesgo: Valor del ratio de riesgo
    Returns:
        float: Valor del beneficio
    """
    try:
        # Convertir a float y evitar división por cero
        riesgo = float(ratio_riesgo)
        if riesgo == 0:
            return 0
        return 1 / riesgo
    except:
        return 0

def calcular_profit_final(df):
    """
    Calcula el Profit F. basado en la suma de profits positivos y negativos,
    excluyendo operaciones con Retiro o Deposito.
    Args:
        df: DataFrame con los datos
    Returns:
        float: Ratio de profit positivo/negativo
    """
    try:
        # Filtrar operaciones que no son depósitos ni retiros
        df_filtrado = df[
            (df['Deposito'].isna() | (df['Deposito'] == '')) & 
            (df['Retiro'].isna() | (df['Retiro'] == ''))
        ].copy()
        
        # Convertir Profit a numérico
        df_filtrado['Profit'] = pd.to_numeric(df_filtrado['Profit'], errors='coerce')
        
        # Calcular suma de profits positivos y negativos
        profit_positivo = df_filtrado[df_filtrado['Profit'] > 0]['Profit'].sum()
        profit_negativo = abs(df_filtrado[df_filtrado['Profit'] < 0]['Profit'].sum())
        
        # Evitar división por cero
        if profit_negativo == 0:
            return 0
            
        return profit_positivo / profit_negativo
    except:
        return 0

def calcular_porcentaje_inversion(monto_invertir, capital_total, ganancias_totales):
    """
    Calcula el porcentaje de inversión basado en el monto a invertir y el capital total disponible.
    Fórmula: % Inversión = (Monto a invertir) / (I. T. Capital + Ganancias Tot.) * 100
    
    Args:
        monto_invertir (float): Monto que se desea invertir
        capital_total (float): Capital total inicial (I. T. Capital)
        ganancias_totales (float): Ganancias acumuladas
        
    Returns:
        float: Porcentaje de inversión
    """
    try:
        # Calcular el total disponible (I. T. Capital + Ganancias Tot.)
        total_disponible = capital_total + ganancias_totales
        
        # Evitar división por cero
        if total_disponible == 0:
            return 0
            
        # Calcular el porcentaje según la fórmula
        porcentaje = (monto_invertir / total_disponible) * 100
        
        return porcentaje
    except Exception as e:
        print(f"Error en calcular_porcentaje_inversion: {str(e)}")
        return 0

def calcular_numero_contratos(monto_invertir, valor_contrato):
    """
    Calcula el número de contratos basado en el monto a invertir y el valor del contrato.
    Args:
        monto_invertir: Valor del monto a invertir
        valor_contrato: Valor del contrato
    Returns:
        float: Número de contratos
    """
    try:
        # Convertir valores a numéricos
        monto = float(monto_invertir)
        valor = float(valor_contrato)
        
        # Evitar división por cero
        if valor == 0:
            return 0
            
        # Calcular el número de contratos
        numero_contratos = monto / valor
        
        return numero_contratos
    except:
        return 0

def guardar_ultimo_monto_invertir(monto):
    """Guarda el último valor de monto a invertir en un archivo."""
    try:
        with open('ultimo_monto.txt', 'w') as f:
            f.write(str(monto))
    except Exception as e:
        print(f"Error al guardar el último monto: {e}")

def obtener_ultimo_monto_invertir():
    """Obtiene el último valor de monto a invertir desde el archivo."""
    try:
        if os.path.exists('ultimo_monto.txt'):
            with open('ultimo_monto.txt', 'r') as f:
                return float(f.read())
        return 0.0
    except Exception as e:
        print(f"Error al leer el último monto: {e}")
        return 0.0

def guardar_ultimo_valor_contrato(valor):
    """Guarda el último valor del contrato en un archivo."""
    try:
        with open('ultimo_contrato.txt', 'w') as f:
            f.write(str(valor))
    except Exception as e:
        print(f"Error al guardar el último valor del contrato: {e}")

def obtener_ultimo_valor_contrato():
    """Obtiene el último valor del contrato desde el archivo."""
    try:
        if os.path.exists('ultimo_contrato.txt'):
            with open('ultimo_contrato.txt', 'r') as f:
                return float(f.read())
        return 0.0
    except Exception as e:
        print(f"Error al leer el último valor del contrato: {e}")
        return 0.0

# Configuración de la página
st.set_page_config(
    page_title="",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Agregar CSS personalizado para ocultar la franja gris del file uploader
st.markdown("""
    <style>
    /* Ocultar la franja gris y otros elementos */
    [data-testid="stFileUploadDropzone"] {
        min-height: 0 !important;
        max-height: none !important;
        height: auto !important;
        padding: 0 !important;
        background: none !important;
        border: none !important;
        width: auto !important;
    }
    [data-testid="stFileUploadDropzone"] > div:first-child {
        display: none !important;
    }
    [data-testid="stFileUploadDropzone"] > div > div:first-child {
        display: none !important;
    }
    .css-1cpxqw2 {
        display: none !important;
    }
    /* Estilo para el botón */
    [data-testid="stFileUploadDropzone"] button {
        padding: 0.25rem 0.75rem !important;
        margin: 0 !important;
    }
    </style>
""", unsafe_allow_html=True)

# Botón de subida de archivo al principio
archivo = st.file_uploader("", type=["xlsx", "csv"])

st.title("")

if archivo is not None:
    if "df" not in st.session_state:
        # Cargar y limpiar el archivo
        df_cargado = cargar_archivo(archivo)
        df_cargado = procesar_depositos_retiros(df_cargado)
        df_cargado = limpiar_columnas_deposito_retiro(df_cargado)
        df_cargado = limpiar_columnas(df_cargado)
        
        # Aplicamos el cálculo de la columna 'T. Op' y 'Día' después de limpiar
        df_cargado = agregar_tiempo_operacion(df_cargado)
        
        # Calcular DD/Max y DD Up
        df_cargado = calcular_dd_max(df_cargado)
        df_cargado = calcular_dd_up(df_cargado)
        
        # Calcular el porcentaje de cambio en Profit Tot.
        df_cargado = calcular_porcentaje_profit_tot(df_cargado)
        
        # Calcular el Profit Alcanzado
        df_cargado = calcular_profit_alcanzado(df_cargado)
        
        # Calcular el Profit Media
        df_cargado = calcular_profit_media(df_cargado)
        
        # Guardar el DataFrame en session_state
        st.session_state.df = df_cargado
        st.session_state.df_editado = df_cargado.copy()
        st.session_state.rango_filas = {
            'inicio': 0,
            'fin': len(df_cargado) - 1
        }

    # Inicializar el estado de Streamlit
    if 'df' not in st.session_state:
        st.session_state.df = pd.DataFrame()
    if 'df_editado' not in st.session_state:
        st.session_state.df_editado = pd.DataFrame()
    if 'valores_calculados' not in st.session_state:
        st.session_state.valores_calculados = {}
    if 'call_100_counter' not in st.session_state:
        st.session_state.call_100_counter = 0

    # Inicializar el estado de la sesión para el rango de filas si no existe
    if 'rango_graficos' not in st.session_state:
        st.session_state.rango_graficos = (1, 10)  # Rango inicial de 10 filas

    # Inicializar el tamaño de la tabla si no existe
    if 'tamaño_tabla' not in st.session_state:
        st.session_state.tamaño_tabla = {"width": 1000, "height": 400}

    # Función para guardar valores calculados
    def guardar_valores_calculados(df):
        """
        Guarda los valores calculados en el estado de la sesión.
        """
        if df is not None and not df.empty:
            # Guardar una copia del DataFrame completo
            st.session_state.valores_calculados['df'] = df.copy()
            
            # Guardar los valores individuales
            st.session_state.valores_calculados['dd_max'] = df['DD/Max'].iloc[-1] if 'DD/Max' in df.columns else None
            st.session_state.valores_calculados['dd_up'] = df['DD Up'].iloc[-1] if 'DD Up' in df.columns else None
            st.session_state.valores_calculados['profit_alcanzado'] = df['Profit Alcanzado'].iloc[-1] if 'Profit Alcanzado' in df.columns else None
            st.session_state.valores_calculados['profit_media'] = df['Profit Media'].iloc[-1] if 'Profit Media' in df.columns else None

    # Función para restaurar valores calculados
    def restaurar_valores_calculados(df):
        if st.session_state.valores_calculados:
            for columna, valores in st.session_state.valores_calculados.items():
                if columna in df.columns:
                    for idx, valor in valores.items():
                        if idx in df.index:
                            df.at[idx, columna] = valor
        return df

    # Función para sincronizar DataFrames
    def sincronizar_dataframes():
        """Sincroniza los DataFrames cuando hay cambios en cualquiera de ellos"""
        if 'df' not in st.session_state:
            st.session_state.df = pd.DataFrame()
        if 'df_editable' not in st.session_state:
            st.session_state.df_editable = st.session_state.df.copy()
        
        # Si los DataFrames son diferentes, actualizar ambos
        if not st.session_state.df.equals(st.session_state.df_editable):
            # Si el DataFrame editable tiene más filas, actualizar el no editable
            if len(st.session_state.df_editable) > len(st.session_state.df):
                st.session_state.df = st.session_state.df_editable.copy()
            # Si el DataFrame no editable tiene más filas, actualizar el editable
            elif len(st.session_state.df) > len(st.session_state.df_editable):
                st.session_state.df_editable = st.session_state.df.copy()
        
        # Procesar los cambios
        st.session_state.df = asignar_dep_ret_activo(st.session_state.df)
        st.session_state.df = limpiar_columnas_deposito_retiro(st.session_state.df)
        st.session_state.df = limpiar_columnas(st.session_state.df)
        st.session_state.df = agregar_tiempo_operacion(st.session_state.df)
        st.session_state.df = calcular_dd_max(st.session_state.df)
        st.session_state.df = calcular_dd_up(st.session_state.df)
        st.session_state.df = calcular_porcentaje_profit_tot(st.session_state.df)
        st.session_state.df = calcular_profit_alcanzado(st.session_state.df)
        st.session_state.df = calcular_profit_media(st.session_state.df)
        
        # Actualizar también la tabla editable
        st.session_state.df_editable = st.session_state.df.copy()

    # Función para actualizar la tabla
    def actualizar_tabla():
        """
        Actualiza la tabla con los cambios realizados y muestra un mensaje de éxito
        """
        if not st.session_state.df.equals(st.session_state.df_editable):
            # Si el DataFrame editable tiene más filas, actualizar el no editable
            if len(st.session_state.df_editable) > len(st.session_state.df):
                st.session_state.df = st.session_state.df_editable.copy()
            # Si el DataFrame no editable tiene más filas, actualizar el editable
            elif len(st.session_state.df) > len(st.session_state.df_editable):
                st.session_state.df_editable = st.session_state.df.copy()
        
        # Procesar los cambios
        st.session_state.df = asignar_dep_ret_activo(st.session_state.df)
        st.session_state.df = limpiar_columnas_deposito_retiro(st.session_state.df)
        st.session_state.df = limpiar_columnas(st.session_state.df)
        st.session_state.df = agregar_tiempo_operacion(st.session_state.df)
        st.session_state.df = calcular_dd_max(st.session_state.df)
        st.session_state.df = calcular_dd_up(st.session_state.df)
        st.session_state.df = calcular_porcentaje_profit_tot(st.session_state.df)
        st.session_state.df = calcular_profit_alcanzado(st.session_state.df)
        st.session_state.df = calcular_profit_media(st.session_state.df)
        
        # Actualizar también la tabla editable
        st.session_state.df_editable = st.session_state.df.copy()
        
        # Actualizar la última hora de actualización
        st.session_state.ultima_actualizacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Mostrar mensaje de éxito
        st.success("✅ Tabla actualizada correctamente")
        st.rerun()

    # Función para colorear solo la columna Profit Tot.
    def color_profit_tot(df):
        color_map = pd.DataFrame('', index=df.index, columns=df.columns)
        
        for idx in df.index:
            try:
                if 'Profit Tot.' in df.columns:
                    profit_tot = float(df.loc[idx, 'Profit Tot.']) if pd.notnull(df.loc[idx, 'Profit Tot.']) else 0
                    color = ''
                    if profit_tot > 0:
                        color = 'color: green'
                    elif profit_tot < 0:
                        color = 'color: red'
                    else:
                        color = 'color: yellow'
                    color_map.loc[idx, 'Profit Tot.'] = color
            except:
                continue
        
        return color_map

    # Función para colorear la tabla según el Profit
    def color_segun_profit(df):
        color_map = pd.DataFrame('', index=df.index, columns=df.columns)
        columnas_a_colorear = [
            'Activo', 'D', 'Día', 'Fecha / Hora', 'Fecha / Hora de Cierre',
            'T. Op', '#Cont', 'STRK Buy', 'STRK Sell', 'Profit', '% Profit. Op'
        ]
        
        for idx in df.index:
            try:
                # Colorear C&P específicamente
                if 'C&P' in df.columns:
                    c_p = df.loc[idx, 'C&P']
                    if c_p == 'CALL':
                        color_map.loc[idx, 'C&P'] = 'color: green'
                    elif c_p == 'PUT':
                        color_map.loc[idx, 'C&P'] = 'color: red'
                
                # Colorear el resto de columnas según Profit
                profit = float(df.loc[idx, 'Profit']) if pd.notnull(df.loc[idx, 'Profit']) else 0
                
                # Si hay un valor en Retiro, colorear de rojo
                if 'Retiro' in df.columns and pd.notnull(df.loc[idx, 'Retiro']):
                    color = 'color: red'
                # Si hay un valor en Deposito, colorear de verde
                elif 'Deposito' in df.columns and pd.notnull(df.loc[idx, 'Deposito']):
                    color = 'color: green'
                # Si no es ni Retiro ni Deposito, colorear según el valor de Profit
                else:
                    if profit > 0:
                        color = 'color: green'
                    elif profit < 0:
                        color = 'color: red'
                    else:
                        color = 'color: yellow'
                
                for col in columnas_a_colorear:
                    if col in df.columns:
                        color_map.loc[idx, col] = color
            except:
                continue
        
        return color_map

    # Función para recalcular fechas
    def recalcular_fechas():
        st.session_state.df = agregar_tiempo_operacion(st.session_state.df)
        st.session_state.df = limpiar_columnas(st.session_state.df)
        st.session_state.df_editado = st.session_state.df.copy()
        st.session_state.ultima_actualizacion = "fechas"

    # Función para aplicar cambios
    def aplicar_cambios():
        st.session_state.df = st.session_state.df_editado.copy()
        st.session_state.df = limpiar_columnas(st.session_state.df)
        st.session_state.df = agregar_tiempo_operacion(st.session_state.df)
        st.session_state.df = calcular_dd_max(st.session_state.df)  # Calcular DD/Max
        st.session_state.df = calcular_dd_up(st.session_state.df)  # Calcular DD Up
        st.session_state.df_editado = st.session_state.df.copy()
        st.session_state.ultima_actualizacion = "cambios"
        st.success("✅ Cambios aplicados correctamente. Por favor, ejecuta la aplicación para ver los cambios.")
        st.rerun()

    # Función para agregar fila
    def agregar_nueva_fila():
            df_nuevo = agregar_fila(st.session_state.df)
            if df_nuevo is not None and not df_nuevo.equals(st.session_state.df):
                st.session_state.df = limpiar_columnas(df_nuevo)
        st.session_state.df = agregar_tiempo_operacion(st.session_state.df)
        st.session_state.df = calcular_dd_max(st.session_state.df)  # Calcular DD/Max
        st.session_state.df = calcular_dd_up(st.session_state.df)  # Calcular DD Up
                st.session_state.df_editado = st.session_state.df.copy()
        st.session_state.ultima_actualizacion = "nueva_fila"
        st.success("✅ Nueva fila agregada correctamente. Por favor, ejecuta la aplicación para ver los cambios.")
                st.rerun()

    # Función para borrar columna
    def borrar_columna_seleccionada(col_borrar):
        st.session_state.df = borrar_columna(st.session_state.df, col_borrar)
        st.session_state.df_editado = st.session_state.df.copy()
        st.session_state.ultima_actualizacion = "borrar_columna"
        st.success(f"✅ Columna '{col_borrar}' eliminada correctamente. Por favor, ejecuta la aplicación para ver los cambios.")
        st.rerun()

    # Función para vaciar columna
    def vaciar_columna_seleccionada(col_limpiar):
        st.session_state.df = vaciar_columna(st.session_state.df, col_limpiar)
        st.session_state.df_editado = st.session_state.df.copy()
        st.session_state.ultima_actualizacion = "vaciar_columna"
        st.success(f"✅ Contenido de la columna '{col_limpiar}' vaciado. Por favor, ejecuta la aplicación para ver los cambios.")
        st.rerun()

    # Función para vaciar fila
    def vaciar_fila_seleccionada(fila_limpiar):
        st.session_state.df = vaciar_fila(st.session_state.df, fila_limpiar)
        st.session_state.df_editado = st.session_state.df.copy()
        st.session_state.ultima_actualizacion = "vaciar_fila"
        st.success(f"✅ Fila {fila_limpiar} vaciada. Por favor, ejecuta la aplicación para ver los cambios.")
        st.rerun()

    # Función para eliminar fila
    def eliminar_fila_seleccionada(fila_eliminar):
        st.session_state.df = eliminar_fila(st.session_state.df, fila_eliminar)
        st.session_state.df_editado = st.session_state.df.copy()
        st.session_state.ultima_actualizacion = "eliminar_fila"
        st.success(f"✅ Fila {fila_eliminar} eliminada correctamente. Por favor, ejecuta la aplicación para ver los cambios.")
        st.rerun()

    # Función para renombrar columna
    def renombrar_columna_seleccionada(col_a_renombrar, nuevo_nombre):
        st.session_state.df_editado.rename(columns={col_a_renombrar: nuevo_nombre}, inplace=True)
        st.session_state.df = st.session_state.df_editado.copy()
        st.session_state.ultima_actualizacion = "renombrar_columna"
        st.success(f"✅ Columna '{col_a_renombrar}' renombrada como '{nuevo_nombre}'. Por favor, ejecuta la aplicación para ver los cambios.")
        st.rerun()

    # Función para modificar la última fecha de cierre
    def modificar_ultima_fecha_cierre(df):
        if not df.empty and 'Fecha / Hora de Cierre' in df.columns:
            # Obtener la última fila con fecha de cierre
            ultima_fecha = df['Fecha / Hora de Cierre'].iloc[-1]
            if pd.notnull(ultima_fecha):
                # Alternar entre sumar y restar un segundo
                if st.session_state.sumar_segundo:
                    nueva_fecha = ultima_fecha + pd.Timedelta(seconds=1)
                else:
                    nueva_fecha = ultima_fecha - pd.Timedelta(seconds=1)
                # Cambiar el estado para la próxima vez
                st.session_state.sumar_segundo = not st.session_state.sumar_segundo
                df['Fecha / Hora de Cierre'].iloc[-1] = nueva_fecha
        return df

    # Función para colorear los depósitos y retiros
    def color_depositos_retiros(df):
        """
        Colorea los valores de las filas que tienen valores en las columnas Deposito y Retiro.
        - Morado para todos los valores en filas con Deposito
        - Rosa para todos los valores en filas con Retiro
        """
        # Crear un DataFrame de colores con el mismo tamaño que df
        color_map = pd.DataFrame('', index=df.index, columns=df.columns)
        
        # Iterar sobre cada fila
        for idx in df.index:
            # Si hay un valor en Deposito, colorear todos los valores de la fila de morado
            if 'Deposito' in df.columns and pd.notnull(df.loc[idx, 'Deposito']):
                for col in df.columns:
                    if pd.notnull(df.loc[idx, col]):
                        color_map.loc[idx, col] = 'color: #E6E6FA'  # Morado claro
            
            # Si hay un valor en Retiro, colorear todos los valores de la fila de rosa
            if 'Retiro' in df.columns and pd.notnull(df.loc[idx, 'Retiro']):
                for col in df.columns:
                    if pd.notnull(df.loc[idx, col]):
                        color_map.loc[idx, col] = 'color: #FFB6C1'  # Rosa claro
        
        return color_map

    # Botón de actualizar tabla
    if st.button("🔄 Actualizar tabla", key="actualizar_tabla_1"):
        st.session_state.df = st.session_state.df_editado.copy()
        st.session_state.df = limpiar_columnas(st.session_state.df)
        st.session_state.df = agregar_tiempo_operacion(st.session_state.df)
        st.session_state.df = calcular_dd_max(st.session_state.df)
        st.session_state.df = calcular_dd_up(st.session_state.df)
        st.session_state.df = calcular_profit_alcanzado(st.session_state.df)
        st.session_state.df = calcular_profit_media(st.session_state.df)
        guardar_valores_calculados(st.session_state.df)
        st.session_state.df_editado = st.session_state.df.copy()
        st.success("✅ Tabla actualizada correctamente")
        st.rerun()

    # Inicializar el estado de la sesión para el rango de filas si no existe
    if 'rango_graficos' not in st.session_state:
        st.session_state.rango_graficos = (1, len(st.session_state.df))

    def actualizar_rango():
        # Si el slider está pegado al extremo derecho, actualizar con la última operación
        if st.session_state.rango_graficos_widget[1] == len(st.session_state.df) - 1:
            nuevo_fin = len(st.session_state.df)
            st.session_state.rango_graficos = (st.session_state.rango_graficos_widget[0], nuevo_fin)
            st.session_state.rango_graficos_widget = (st.session_state.rango_graficos_widget[0], nuevo_fin)
        else:
            # Si no está pegado al extremo, mantener el rango seleccionado
            st.session_state.rango_graficos = st.session_state.rango_graficos_widget

    # Crear las pestañas
    tab1, tab2 = st.tabs([" Tabla No Editable", "✏️ Tabla Editable"])

    with tab1:
        # Crear dos columnas para la tabla y los botones
        col1, col2 = st.columns([1, 2])
        with col1:
            # Crear 5 columnas para los botones
            col1, col2, col3, col4, col5 = st.columns(5)
            
            # Primera columna
            with col1:
                st.button("🟢 C 100%", key="call_100_1")
                st.button("🟢 C 50%", key="call_50_1")

            # Segunda columna
            with col2:
                st.button("🔴 C -100%", key="call_menos_100_1")
                st.button("🔴 C -50%", key="call_menos_50_1")

            # Tercera columna
            with col3:
                st.button("🟡 C 0%", key="call_0_1")
                st.button("🟡 P 0%", key="put_0_1")

            # Cuarta columna
            with col4:
                st.button("🟢 P 100%", key="put_100_1")
                st.button("🟢 P 50%", key="put_50_1")

            # Quinta columna
            with col5:
                st.button("🔴 P -100%", key="put_menos_100_1")
                st.button("🔴 P -50%", key="put_menos_50_1")

            # Agregar CSS personalizado para reducir el tamaño de la fuente
            st.markdown("""
                <style>
                .stButton>button {
                    font-size: 6px !important;
                    padding: 0.1rem 0.3rem !important;
                    height: auto !important;
                    min-height: 18px !important;
                    line-height: 1.2 !important;
                }
                </style>
            """, unsafe_allow_html=True)

            # Lógica de los botones
            if st.session_state.get("call_100_1"):
                df_temp = agregar_call_100(st.session_state.df)
                if df_temp is not None:
                    st.session_state.df = df_temp.copy()
                    st.session_state.df_editado = df_temp.copy()
                    # Solo actualizar si la barra está pegada al final
                    if st.session_state.rango_graficos_widget[1] == len(st.session_state.df) - 1:
                        inicio_rango = st.session_state.rango_graficos[0]
                        st.session_state.rango_graficos = (inicio_rango, len(st.session_state.df))
                        st.session_state.rango_graficos_widget = (inicio_rango, len(st.session_state.df))

            if st.session_state.get("call_0_1"):
                df_temp = agregar_call_0(st.session_state.df)
                if df_temp is not None:
                    st.session_state.df = df_temp.copy()
                    st.session_state.df_editado = df_temp.copy()
                    # Solo actualizar si la barra está pegada al final
                    if st.session_state.rango_graficos_widget[1] == len(st.session_state.df) - 1:
                        inicio_rango = st.session_state.rango_graficos[0]
                        st.session_state.rango_graficos = (inicio_rango, len(st.session_state.df))
                        st.session_state.rango_graficos_widget = (inicio_rango, len(st.session_state.df))

            if st.session_state.get("call_50_1"):
                df_temp = agregar_call_50(st.session_state.df)
                if df_temp is not None:
                    st.session_state.df = df_temp.copy()
                    st.session_state.df_editado = df_temp.copy()
                    # Solo actualizar si la barra está pegada al final
                    if st.session_state.rango_graficos_widget[1] == len(st.session_state.df) - 1:
                        inicio_rango = st.session_state.rango_graficos[0]
                        st.session_state.rango_graficos = (inicio_rango, len(st.session_state.df))
                        st.session_state.rango_graficos_widget = (inicio_rango, len(st.session_state.df))

            if st.session_state.get("put_0_1"):
                df_temp = agregar_put_0(st.session_state.df)
                if df_temp is not None:
                    st.session_state.df = df_temp.copy()
                    st.session_state.df_editado = df_temp.copy()
                    # Solo actualizar si la barra está pegada al final
                    if st.session_state.rango_graficos_widget[1] == len(st.session_state.df) - 1:
                        inicio_rango = st.session_state.rango_graficos[0]
                        st.session_state.rango_graficos = (inicio_rango, len(st.session_state.df))
                        st.session_state.rango_graficos_widget = (inicio_rango, len(st.session_state.df))

            if st.session_state.get("put_100_1"):
                df_temp = agregar_put_100(st.session_state.df)
                if df_temp is not None:
                    st.session_state.df = df_temp.copy()
                    st.session_state.df_editado = df_temp.copy()
                    # Solo actualizar si la barra está pegada al final
                    if st.session_state.rango_graficos_widget[1] == len(st.session_state.df) - 1:
                        inicio_rango = st.session_state.rango_graficos[0]
                        st.session_state.rango_graficos = (inicio_rango, len(st.session_state.df))
                        st.session_state.rango_graficos_widget = (inicio_rango, len(st.session_state.df))

            if st.session_state.get("put_50_1"):
                df_temp = agregar_put_50(st.session_state.df)
                if df_temp is not None:
                    st.session_state.df = df_temp.copy()
                    st.session_state.df_editado = df_temp.copy()
                    # Solo actualizar si la barra está pegada al final
                    if st.session_state.rango_graficos_widget[1] == len(st.session_state.df) - 1:
                        inicio_rango = st.session_state.rango_graficos[0]
                        st.session_state.rango_graficos = (inicio_rango, len(st.session_state.df))
                        st.session_state.rango_graficos_widget = (inicio_rango, len(st.session_state.df))

            if st.session_state.get("call_menos_100_1"):
                df_temp = agregar_call_menos_100(st.session_state.df)
                if df_temp is not None:
                    st.session_state.df = df_temp.copy()
                    st.session_state.df_editado = df_temp.copy()
                    # Solo actualizar si la barra está pegada al final
                    if st.session_state.rango_graficos_widget[1] == len(st.session_state.df) - 1:
                        inicio_rango = st.session_state.rango_graficos[0]
                        st.session_state.rango_graficos = (inicio_rango, len(st.session_state.df))
                        st.session_state.rango_graficos_widget = (inicio_rango, len(st.session_state.df))

            if st.session_state.get("call_menos_50_1"):
                df_temp = agregar_call_menos_50(st.session_state.df)
                if df_temp is not None:
                    st.session_state.df = df_temp.copy()
                    st.session_state.df_editado = df_temp.copy()
                    # Solo actualizar si la barra está pegada al final
                    if st.session_state.rango_graficos_widget[1] == len(st.session_state.df) - 1:
                        inicio_rango = st.session_state.rango_graficos[0]
                        st.session_state.rango_graficos = (inicio_rango, len(st.session_state.df))
                        st.session_state.rango_graficos_widget = (inicio_rango, len(st.session_state.df))

            if st.session_state.get("put_menos_100_1"):
                df_temp = agregar_put_menos_100(st.session_state.df)
                if df_temp is not None:
                    st.session_state.df = df_temp.copy()
                    st.session_state.df_editado = df_temp.copy()
                    # Solo actualizar si la barra está pegada al final
                    if st.session_state.rango_graficos_widget[1] == len(st.session_state.df) - 1:
                        inicio_rango = st.session_state.rango_graficos[0]
                        st.session_state.rango_graficos = (inicio_rango, len(st.session_state.df))
                        st.session_state.rango_graficos_widget = (inicio_rango, len(st.session_state.df))

            if st.session_state.get("put_menos_50_1"):
                df_temp = agregar_put_menos_50(st.session_state.df)
                if df_temp is not None:
                    st.session_state.df = df_temp.copy()
                    st.session_state.df_editado = df_temp.copy()
                    # Solo actualizar si la barra está pegada al final
                    if st.session_state.rango_graficos_widget[1] == len(st.session_state.df) - 1:
                        inicio_rango = st.session_state.rango_graficos[0]
                        st.session_state.rango_graficos = (inicio_rango, len(st.session_state.df))
                        st.session_state.rango_graficos_widget = (inicio_rango, len(st.session_state.df))

        try:
            # Asegurarnos de que los DataFrames estén sincronizados antes de mostrar la tabla
            if not st.session_state.df.equals(st.session_state.df_editado):
                # Procesar los cambios
                st.session_state.df = asignar_dep_ret_activo(st.session_state.df)
                st.session_state.df = limpiar_columnas_deposito_retiro(st.session_state.df)
                st.session_state.df = limpiar_columnas(st.session_state.df)
                st.session_state.df = agregar_tiempo_operacion(st.session_state.df)
                st.session_state.df = calcular_dd_max(st.session_state.df)
                st.session_state.df = calcular_dd_up(st.session_state.df)
                st.session_state.df = calcular_porcentaje_profit_tot(st.session_state.df)
                st.session_state.df = calcular_profit_alcanzado(st.session_state.df)
                st.session_state.df = calcular_profit_media(st.session_state.df)
                
            # Formatear la columna D antes de quitar ceros
            st.session_state.df = formatear_columna_d(st.session_state.df)
            
            # Quitar ceros innecesarios
            df_sin_ceros = quitar_ceros_tabla(st.session_state.df)
            
            # Agregar el contador como primera columna
            df_sin_ceros.insert(0, '#', range(len(df_sin_ceros)))
            
            # Aplicar todos los estilos de color
            styled_df = df_sin_ceros.style
            styled_df = styled_df.apply(color_segun_profit, axis=None)
            styled_df = styled_df.apply(color_profit_tot, axis=None)
            styled_df = styled_df.apply(color_dd_max, axis=None)
            styled_df = styled_df.apply(color_depositos_retiros, axis=None)
            styled_df = styled_df.apply(color_profit_t, axis=None)
            styled_df = styled_df.apply(color_profit_alcanzado_media, axis=None)
            styled_df = styled_df.apply(color_porcentajes_alcanzado_media, axis=None)
            
            # Agregar CSS personalizado para la tabla
            st.markdown("""
                <style>
                .stDataFrame {
                    width: 100% !important;
                }
                </style>
            """, unsafe_allow_html=True)

            # Mostrar la tabla con todas las columnas
            st.dataframe(
                styled_df,
                use_container_width=True,
                hide_index=True
            )
                
        except Exception as e:
            st.error(f"❌ Error al mostrar la tabla: {e}")

        # Sección de gráficos
        st.markdown("---")

        # Agregar estilos CSS para centrar el contenido de las tablas y modificar el ancho de la barra lateral
        st.markdown("""
            <style>
            .stDataFrame {
                text-align: center !important;
            }
            .stDataFrame th, .stDataFrame td {
                text-align: center !important;
            }
            .stDataFrame div[data-testid="stDataFrame"] {
                text-align: center !important;
            }
            .stDataFrame div[data-testid="stDataFrame"] div {
                text-align: center !important;
            }
            .stDataFrame div[data-testid="stDataFrame"] table {
                margin: 0 auto !important;
            }
            .stDataFrame div[data-testid="stDataFrame"] th, 
            .stDataFrame div[data-testid="stDataFrame"] td {
                text-align: center !important;
                padding: 8px !important;
            }
            /* Estilos para la barra lateral */
            section[data-testid="stSidebar"] {
                width: 400px !important;
            }
            </style>
        """, unsafe_allow_html=True)

        # Agregar tabla en la barra lateral
        st.sidebar.markdown("### Riesgo / Beneficio")
        tabla_resumen = pd.DataFrame({
            'Riesgo': ['Valor 1'],
            'Beneficio': ['Valor 2'],
            'Profit F.': ['Valor 3']
        })

        # Calcular y mostrar los valores
        if 'df' in st.session_state and not st.session_state.df.empty:
            # Calcular medias
            media_positiva, media_negativa = calcular_medias_operaciones(st.session_state.df)
            
            # Calcular ratio de riesgo/beneficio
            ratio = calcular_ratio_riesgo_beneficio(media_negativa, media_positiva)
            tabla_resumen.loc[0, 'Riesgo'] = f"{ratio:.2f}"
            
            # Calcular beneficio basado en el riesgo
            beneficio = calcular_beneficio_por_riesgo(ratio)
            tabla_resumen.loc[0, 'Beneficio'] = f"{beneficio:.2f}"
            
            # Calcular Profit F.
            profit_f = calcular_profit_final(st.session_state.df)
            tabla_resumen.loc[0, 'Profit F.'] = f"{profit_f:.2f}"

        st.sidebar.dataframe(tabla_resumen, hide_index=True)

        # Tabla de % de Aciertos / Beneficios M.
        st.sidebar.markdown("### % de Aciertos / Beneficios M.")
        tabla_beneficios = pd.DataFrame({
            '% Acierto': ['Valor A'],
            '% Error': ['Valor B'],
            'Beneficio M.': ['Valor C'],
            'Riesgo M.': ['Valor D']
        })

        # Calcular y mostrar los porcentajes y medias
        if 'df' in st.session_state and not st.session_state.df.empty:
            # Calcular porcentajes
            porcentaje_acierto, porcentaje_error = calcular_porcentajes_acierto_error(st.session_state.df)
            tabla_beneficios.loc[0, '% Acierto'] = f"{porcentaje_acierto:.2f}%"
            tabla_beneficios.loc[0, '% Error'] = f"{porcentaje_error:.2f}%"
            
            # Calcular medias
            media_positiva, media_negativa = calcular_medias_operaciones(st.session_state.df)
            tabla_beneficios.loc[0, 'Beneficio M.'] = f"{media_positiva:.2f}"
            tabla_beneficios.loc[0, 'Riesgo M.'] = f"{media_negativa:.2f}"

        st.sidebar.dataframe(tabla_beneficios, hide_index=True, use_container_width=True)

        # Tabla de Capital
        st.sidebar.markdown("### Capital")
        
        # Crear la tabla de capital
        tabla_capital = pd.DataFrame({
            'I. T. Capital': ['$0.00'],
            'Ganancias Tot.': ['$0.00'],
            '% Ganancia T.': ['0%']
        })
        
        # Calcular valores para la tabla de capital
        if 'df' in st.session_state and not st.session_state.df.empty:
            total_depositos = calcular_total_depositos(st.session_state.df)
            ganancias_totales = calcular_ganancias_totales(st.session_state.df)
            
            # Calcular el porcentaje de ganancia
            porcentaje_ganancia = calcular_porcentaje_ganancia(total_depositos, ganancias_totales)
            
            # Actualizar la tabla de capital
            tabla_capital.loc[0, 'I. T. Capital'] = f"${total_depositos:.2f}"
            tabla_capital.loc[0, 'Ganancias Tot.'] = f"${ganancias_totales:.2f}"
            tabla_capital.loc[0, '% Ganancia T.'] = f"{porcentaje_ganancia:.2f}%"
        
        # Mostrar la tabla de capital
        st.sidebar.dataframe(tabla_capital, hide_index=True, use_container_width=True)
        
        # Tabla de Op. Ganadoras / Perdedoras
        st.sidebar.markdown("### Op. Ganadoras / Perdedoras")
        
        # Crear el DataFrame para operaciones ganadoras/perdedoras
        df_ganadoras_perdedoras = pd.DataFrame({
            'Op. Ganadoras': [0],
            'Op. Perdedoras': [0]
        })
        
        # Calcular operaciones ganadoras y perdedoras
        if 'df' in st.session_state and not st.session_state.df.empty:
            df_ganadoras_perdedoras = calcular_operaciones_ganadoras_perdedoras(st.session_state.df)
        
        # Mostrar la tabla de operaciones ganadoras/perdedoras
        st.sidebar.dataframe(df_ganadoras_perdedoras, hide_index=True, use_container_width=True)
        
        # Agregar cuarta tabla
        st.sidebar.markdown("### Inversión")
        
        # Crear la tabla de capital si no existe
        tabla_capital = pd.DataFrame({
            'I. T. Capital': ['$0.00'],
            'Ganancias Tot.': ['$0.00']
        })
        
        # Inicializar el estado de la sesión para los valores si no existen
        if 'monto_invertir' not in st.session_state:
            st.session_state.monto_invertir = obtener_ultimo_monto_invertir()
        if 'valor_contrato' not in st.session_state:
            st.session_state.valor_contrato = obtener_ultimo_valor_contrato()
        
        # Crear pestañas para la sección de inversión
        tab_inversion1, tab_inversion2, tab_inversion3 = st.sidebar.tabs(["Tabla", "Editar Monto", "Editar Contrato"])
        
        # Crear la tabla inicial
        tabla_inversion = pd.DataFrame({
            '% Invercion': ['0%'],
            'Monto a Invertir': [f"{st.session_state.monto_invertir:.2f}"],
            '$ Contrato': [f"{st.session_state.valor_contrato:.2f}"],
            'N. Contrato': ['0']
        })
        
        with tab_inversion2:
            monto_invertir = st.number_input(
                "Ingrese el monto a invertir:",
                min_value=0.0,
                value=st.session_state.monto_invertir,
                step=0.01,
                format="%.2f"
            )
            
            # Actualizar el estado de la sesión con el nuevo valor
            st.session_state.monto_invertir = monto_invertir
            # Guardar el último valor
            guardar_ultimo_monto_invertir(monto_invertir)
            
            # Calcular y actualizar el porcentaje de inversión
            if 'df' in st.session_state and not st.session_state.df.empty:
                # Actualizar la tabla_capital primero
                total_depositos = calcular_total_depositos(st.session_state.df)
                ganancias_totales = calcular_ganancias_totales(st.session_state.df)
                tabla_capital.loc[0, 'I. T. Capital'] = f"${total_depositos:.2f}"
                tabla_capital.loc[0, 'Ganancias Tot.'] = f"${ganancias_totales:.2f}"
                
                # Obtener valores de la tabla Capital
                capital_total = float(tabla_capital.loc[0, 'I. T. Capital'].replace('$', '').strip())
                ganancias_totales = float(tabla_capital.loc[0, 'Ganancias Tot.'].replace('$', '').strip())
                
                # Calcular el porcentaje
                porcentaje = calcular_porcentaje_inversion(monto_invertir, capital_total, ganancias_totales)
                
                # Actualizar la tabla
                tabla_inversion.loc[0, 'Monto a Invertir'] = f"{monto_invertir:.2f}"
                tabla_inversion.loc[0, '% Invercion'] = f"{porcentaje:.2f}%"
                
                # Calcular el número de contratos
                numero_contratos = calcular_numero_contratos(monto_invertir, st.session_state.valor_contrato)
                tabla_inversion.loc[0, 'N. Contrato'] = f"{numero_contratos:.2f}"
        
        with tab_inversion3:
            valor_contrato = st.number_input(
                "Ingrese el valor del contrato:",
                min_value=0.0,
                value=st.session_state.valor_contrato,
                step=0.01,
                format="%.2f"
            )
            
            # Actualizar el estado de la sesión con el nuevo valor
            st.session_state.valor_contrato = valor_contrato
            # Guardar el último valor
            guardar_ultimo_valor_contrato(valor_contrato)
            
            # Actualizar la tabla
            tabla_inversion.loc[0, '$ Contrato'] = f"{valor_contrato:.2f}"
            
            # Calcular el número de contratos
            numero_contratos = calcular_numero_contratos(st.session_state.monto_invertir, valor_contrato)
            tabla_inversion.loc[0, 'N. Contrato'] = f"{numero_contratos:.2f}"
        
        # Mostrar la tabla actualizada en la primera pestaña
        with tab_inversion1:
            st.dataframe(tabla_inversion, hide_index=True, use_container_width=True)

        # Agregar quinta tabla
        st.sidebar.markdown("### Combinaciones de Contratos")
        
        # Inicializar el estado de la sesión para las combinaciones si no existe
        if 'combinaciones_contratos' not in st.session_state:
            st.session_state.combinaciones_contratos = {
                'Combinaciones / contrato 1': [0, 0, 0, 0],
                'Combinaciones / contrato 2': [0, 0, 0, 0]
            }
        
        # Crear el DataFrame para las combinaciones
        tabla_combinaciones = pd.DataFrame(st.session_state.combinaciones_contratos)
        
        # Botón para generar nuevas combinaciones
        if st.sidebar.button("🔄 Generar Nuevas Combinaciones"):
            numero_contratos = float(tabla_inversion.loc[0, 'N. Contrato'])
            if numero_contratos >= 2:
                comb1, comb2 = generar_combinaciones_contratos(int(numero_contratos))
                st.session_state.combinaciones_contratos = {
                    'Combinaciones / contrato 1': comb1,
                    'Combinaciones / contrato 2': comb2
                }
                tabla_combinaciones = pd.DataFrame(st.session_state.combinaciones_contratos)
        
        st.sidebar.dataframe(tabla_combinaciones, hide_index=True)

        # Slider para controlar el rango de filas
        max_filas = len(st.session_state.df)
        filas_rango = st.sidebar.slider(
            'Selecciona el rango de filas a graficar:',
            min_value=1,
            max_value=max_filas,
            value=st.session_state.rango_graficos,
            step=1,
            key="rango_graficos_widget",
            on_change=actualizar_rango
        )

        # Crear dos columnas para los selectores
        sel1, sel2 = st.columns(2)

        with sel1:
            opcion_grafico1 = st.selectbox(
                "Selecciona el tipo de gráfico:",
                ["Gráfico de Barras", "Gráfico de Área", "Gráfico DD/Max Negativo", "Gráfico de Tendencia Profit", "Gráfico de Puntos", "Gráfico de Tiempos"],
                key="grafico1",
                label_visibility="collapsed"
            )

        with sel2:
            opcion_grafico2 = st.selectbox(
                "Selecciona el tipo de gráfico:",
                ["Gráfico de Barras", "Gráfico de Área", "Gráfico DD/Max Negativo", "Gráfico de Tendencia Profit", "Gráfico de Puntos", "Gráfico de Tiempos"],
                key="grafico2",
                label_visibility="collapsed"
            )

        # Crear una copia del DataFrame para los gráficos y aplicar el filtro de rango
        df_graficos = st.session_state.df.copy()
        df_graficos = df_graficos.iloc[st.session_state.rango_graficos[0]-1:st.session_state.rango_graficos[1]]

        # Crear dos columnas para los gráficos
        col1, col2 = st.columns(2)

        # Mostrar los gráficos seleccionados
        with col1:
            if opcion_grafico1 == "Gráfico de Barras":
                mostrar_grafico_barras(df_graficos, "Profit", 1)
            elif opcion_grafico1 == "Gráfico de Área":
                mostrar_grafico_area(df_graficos, "col1")
            elif opcion_grafico1 == "Gráfico DD/Max Negativo":
                mostrar_grafico_area_dd_max_negativo(df_graficos, "col1")
            elif opcion_grafico1 == "Gráfico de Tendencia Profit":
                mostrar_grafico_tendencia_profit(df_graficos, "col1")
            elif opcion_grafico1 == "Gráfico de Puntos":
                mostrar_grafico_puntos(df_graficos, "Profit", 1)
            elif opcion_grafico1 == "Gráfico de Tiempos":
                mostrar_grafico_tiempo_operacion(df_graficos, "col1")

        with col2:
            if opcion_grafico2 == "Gráfico de Barras":
                mostrar_grafico_barras(df_graficos, "Profit", 2)
            elif opcion_grafico2 == "Gráfico de Área":
                mostrar_grafico_area(df_graficos, "col2")
            elif opcion_grafico2 == "Gráfico DD/Max Negativo":
                mostrar_grafico_area_dd_max_negativo(df_graficos, "col2")
            elif opcion_grafico2 == "Gráfico de Tendencia Profit":
                mostrar_grafico_tendencia_profit(df_graficos, "col2")
            elif opcion_grafico2 == "Gráfico de Puntos":
                mostrar_grafico_puntos(df_graficos, "Profit", 2)
            elif opcion_grafico2 == "Gráfico de Tiempos":
                mostrar_grafico_tiempo_operacion(df_graficos, "col2")

    with tab2:
        col1, col2 = st.columns([1, 3])
        with col1:
            col_botones = st.columns(2)
            with col_botones[0]:
                if st.button("🔄 Actualizar tabla", key="actualizar_tabla_2"):
                    st.session_state.df = st.session_state.df_editado.copy()
                    st.session_state.df = limpiar_columnas(st.session_state.df)
                    st.session_state.df = agregar_tiempo_operacion(st.session_state.df)
                    st.session_state.df = calcular_dd_max(st.session_state.df)
                    st.session_state.df = calcular_dd_up(st.session_state.df)
                    st.session_state.df = calcular_profit_alcanzado(st.session_state.df)
                    st.session_state.df = calcular_profit_media(st.session_state.df)
                    guardar_valores_calculados(st.session_state.df)
                    st.session_state.df_editado = st.session_state.df.copy()
                    st.success("✅ Tabla actualizada correctamente")
                    st.rerun()

        try:
            # Agregar el contador como primera columna
            df_con_contador = st.session_state.df_editado.copy()
            df_con_contador.insert(0, '#', range(len(df_con_contador)))
            
            # Mostrar la tabla editable con la opción de agregar filas
            df_editado = st.data_editor(
                df_con_contador,
                use_container_width=True,
                num_rows="dynamic",  # Permite agregar filas directamente en la tabla
                column_config={
                    "#": st.column_config.NumberColumn(
                        "Nº",
                        help="Número de fila",
                        default=0,
                        format="%d",
                        step=1,
                        disabled=True
                    )
                }
            )
            
            # Eliminar la columna del contador antes de procesar
            if '#' in df_editado.columns:
                df_editado = df_editado.drop('#', axis=1)
            
            # Actualizar el DataFrame editado en el estado de la sesión y procesar cambios
            if not df_editado.equals(st.session_state.df_editado):
                # Verificar si hubo cambios en Deposito o Retiro
                deposito_cambio = False
                retiro_cambio = False
                
                if 'Deposito' in df_editado.columns and 'Deposito' in st.session_state.df_editado.columns:
                    deposito_cambio = not df_editado['Deposito'].equals(st.session_state.df_editado['Deposito'])
                if 'Retiro' in df_editado.columns and 'Retiro' in st.session_state.df_editado.columns:
                    retiro_cambio = not df_editado['Retiro'].equals(st.session_state.df_editado['Retiro'])
                
                # Guardar los cambios
                st.session_state.df_editado = df_editado.copy()
                st.session_state.df = df_editado.copy()
                
                # Si hubo cambios en Deposito o Retiro, aplicar funciones específicas
                if deposito_cambio:
                    st.session_state.df = calcular_deposito(st.session_state.df)
                if retiro_cambio:
                    st.session_state.df = calcular_retiro(st.session_state.df)
                
                # Aplicar el resto de las funciones
                st.session_state.df = limpiar_columnas(st.session_state.df)
                st.session_state.df = agregar_tiempo_operacion(st.session_state.df)
                st.session_state.df = calcular_dd_max(st.session_state.df)
                st.session_state.df = calcular_dd_up(st.session_state.df)
                st.session_state.df = calcular_porcentaje_profit_tot(st.session_state.df)
                st.session_state.df = calcular_profit_alcanzado(st.session_state.df)
                st.session_state.df = calcular_profit_media(st.session_state.df)
                
                # Actualizar el DataFrame editable con los cambios procesados
                st.session_state.df_editado = st.session_state.df.copy()
                st.rerun()
                
        except Exception as e:
            st.error(f"❌ Error al mostrar la tabla editable: {e}")

        st.markdown("---")
        
        # Botón para mostrar/ocultar operaciones de edición
        if st.button("🔧 Modificar/Ocultar operaciones de edición"):
            st.session_state.mostrar_edicion = not st.session_state.get('mostrar_edicion', False)

        if st.session_state.get('mostrar_edicion', False):
            st.markdown("### Operaciones de edición")
            
            # Operaciones con columnas
            columnas_disponibles = list(st.session_state.df.columns)
            col_borrar = st.selectbox("🧽 Selecciona una columna para borrar completamente", columnas_disponibles)
            if st.button("🗑️ Borrar columna"):
                st.session_state.df = borrar_columna(st.session_state.df, col_borrar)
                st.session_state.df_editado = st.session_state.df.copy()
                st.success(f"Columna '{col_borrar}' eliminada correctamente.")
                st.rerun()

            col_limpiar = st.selectbox("Selecciona una columna para vaciar su contenido", columnas_disponibles)
            if st.button("🧼 Vaciar columna"):
                st.session_state.df = vaciar_columna(st.session_state.df, col_limpiar)
                st.session_state.df_editado = st.session_state.df.copy()
                st.success(f"Contenido de la columna '{col_limpiar}' vaciado.")
                st.rerun()

            st.markdown("---")

            # Operaciones con filas
            fila_limpiar = st.number_input("Selecciona el número de fila a vaciar (inicia en 0)", 
                                         min_value=0, 
                                         max_value=len(st.session_state.df)-1, 
                                         step=1)
            if st.button("🧼 Vaciar fila"):
                st.session_state.df = vaciar_fila(st.session_state.df, fila_limpiar)
                st.session_state.df_editado = st.session_state.df.copy()
                st.success(f"Fila {fila_limpiar} vaciada.")
                st.rerun()

            fila_eliminar = st.number_input("Selecciona el número de fila a eliminar (inicia en 0)", 
                                          min_value=0, 
                                          max_value=len(st.session_state.df)-1, 
                                          step=1, 
                                          key="fila_eliminar")
            if st.button("🗑️ Eliminar fila"):
                st.session_state.df = eliminar_fila(st.session_state.df, fila_eliminar)
                st.session_state.df_editado = st.session_state.df.copy()
                st.success(f"Fila {fila_eliminar} eliminada correctamente.")
                st.rerun()

            st.markdown("---")

            # Renombrar columnas
            st.subheader("Renombrar columnas")
            columnas = list(st.session_state.df_editado.columns)
            col_a_renombrar = st.selectbox("✏️ Selecciona una columna existente:", columnas)
            nuevo_nombre = st.text_input("Nuevo nombre para la columna seleccionada:")
            if st.button("✅ Renombrar"):
                if nuevo_nombre.strip() == "":
                    i = 1
                    while f"Sin nombre {i}" in columnas:
                        i += 1
                    nuevo_nombre = f"Sin nombre {i}"
                st.session_state.df_editado.rename(columns={col_a_renombrar: nuevo_nombre}, inplace=True)
                st.session_state.df = st.session_state.df_editado.copy()
                st.success(f"✅ Columna '{col_a_renombrar}' renombrada como '{nuevo_nombre}'")
                st.rerun()

    def mostrar_tabla_editable(df):
        """Muestra la tabla editable con todos los estilos aplicados."""
        # Aplicar todos los estilos
        estilos = [
            color_profit_negativo(df),
            color_profit_positivo(df),
            color_dd_max(df),
            color_depositos_retiros(df)  # Agregar el nuevo estilo
        ]
        
        # Combinar todos los estilos
        estilos_combinados = pd.DataFrame('', index=df.index, columns=df.columns)
        for estilo in estilos:
            estilos_combinados = estilos_combinados.combine_first(estilo)
        
        # Mostrar la tabla con los estilos combinados
        st.dataframe(
            df.style.apply(lambda x: estilos_combinados, axis=None),
            use_container_width=True
        )

def calcular_deposito(df):
    """Calcula y actualiza los valores de la columna Deposito."""
    try:
        # Convertir la columna Deposito a numérico
        df['Deposito'] = pd.to_numeric(df['Deposito'], errors='coerce')
        
        # Reemplazar NaN por 0
        df['Deposito'] = df['Deposito'].fillna(0)
        
        return df
    except Exception as e:
        print(f"Error en calcular_deposito: {str(e)}")
        return df

def calcular_retiro(df):
    """Calcula y actualiza los valores de la columna Retiro."""
    try:
        # Convertir la columna Retiro a numérico
        df['Retiro'] = pd.to_numeric(df['Retiro'], errors='coerce')
        
        # Reemplazar NaN por 0
        df['Retiro'] = df['Retiro'].fillna(0)
        
        return df
    except Exception as e:
        print(f"Error en calcular_retiro: {str(e)}")
        return df

def asignar_dep_ret_activo(df):
    """
    Asigna 'DEP' o 'RET' en la columna Activo basado en los valores de Deposito o Retiro.
    Solo cambia el valor si no hay un valor existente en Activo.
    """
    if 'Deposito' in df.columns and 'Retiro' in df.columns and 'Activo' in df.columns:
        # Solo cambia el valor si Activo está vacío
        mask_deposito = (df['Deposito'].notna() & (df['Deposito'] != 0) & (df['Activo'].isna() | (df['Activo'] == '')))
        mask_retiro = (df['Retiro'].notna() & (df['Retiro'] != 0) & (df['Activo'].isna() | (df['Activo'] == '')))
        
        df.loc[mask_deposito, 'Activo'] = 'DEP'
        df.loc[mask_retiro, 'Activo'] = 'RET'
    
    return df

# Fin del archivo
