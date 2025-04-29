import pandas as pd
import streamlit as st
from datetime import datetime

def limpiar_columnas(df):
    """
    Limpia y formatea las columnas del DataFrame.
    - Convierte las columnas de fecha a tipo datetime
    - Convierte las columnas numéricas a tipo float
    - Calcula el Profit basado en STRK Buy, STRK Sell y #Cont
    - Formatea la columna D con el sufijo 'd'
    """
    # Crear una copia del DataFrame para no modificar el original
    df_limpio = df.copy()
    
    # Convertir 'None' strings a None tipo Python
    df_limpio = df_limpio.replace('None', None)
    
    # Identificar la última fila con datos reales
    ultima_fila_valida = None
    for idx in reversed(df_limpio.index):
        row = df_limpio.loc[idx]
        # Verificar si la fila tiene datos válidos (no None) en columnas importantes
        if (pd.notnull(row['Activo']) or pd.notnull(row['C&P']) or 
            pd.notnull(row['STRK Buy']) or pd.notnull(row['STRK Sell']) or
            (pd.notnull(row['Profit']) and row['Profit'] != 0) or
            pd.notnull(row['Deposito']) or pd.notnull(row['Retiro'])):
            ultima_fila_valida = idx
            break
    
    # Mantener solo hasta la última fila válida
    if ultima_fila_valida is not None:
        df_limpio = df_limpio.loc[:ultima_fila_valida]
    
    # Convertir las columnas de fecha a tipo datetime si no lo son
    if 'Fecha / Hora' in df_limpio.columns:
        df_limpio['Fecha / Hora'] = pd.to_datetime(df_limpio['Fecha / Hora'], errors='coerce')
    if 'Fecha / Hora de Cierre' in df_limpio.columns:
        df_limpio['Fecha / Hora de Cierre'] = pd.to_datetime(df_limpio['Fecha / Hora de Cierre'], errors='coerce')
    
    # Convertir columnas numéricas (excluyendo D)
    columnas_numericas = ['STRK Buy', 'STRK Sell', '#Cont', 'Deposito', 'Retiro']
    for col in columnas_numericas:
        if col in df_limpio.columns:
            df_limpio[col] = pd.to_numeric(df_limpio[col], errors='coerce')
    
    # Procesar depósitos y retiros
    for idx in df_limpio.index:
        # Si hay un valor en Deposito, pasarlo a Profit
        if 'Deposito' in df_limpio.columns and pd.notnull(df_limpio.loc[idx, 'Deposito']):
            df_limpio.loc[idx, 'Profit'] = df_limpio.loc[idx, 'Deposito']
            continue  # Saltamos al siguiente registro para no procesar más este
        
        # Si hay un valor en Retiro, pasarlo a Profit como negativo
        if 'Retiro' in df_limpio.columns and pd.notnull(df_limpio.loc[idx, 'Retiro']):
            retiro = float(df_limpio.loc[idx, 'Retiro'])
            df_limpio.loc[idx, 'Profit'] = -abs(retiro)  # Asegurar que sea negativo
            continue  # Saltamos al siguiente registro para no procesar más este
        
        # Solo procesar el Profit si no es un depósito o retiro
        if all(col in df_limpio.columns for col in ['STRK Buy', 'STRK Sell', '#Cont']):
            try:
                strk_buy = float(df_limpio.loc[idx, 'STRK Buy']) if pd.notnull(df_limpio.loc[idx, 'STRK Buy']) else 0
                strk_sell = float(df_limpio.loc[idx, 'STRK Sell']) if pd.notnull(df_limpio.loc[idx, 'STRK Sell']) else 0
                num_cont = float(df_limpio.loc[idx, '#Cont']) if pd.notnull(df_limpio.loc[idx, '#Cont']) else 0
                
                if pd.isnull(df_limpio.loc[idx, 'Profit']):
                    df_limpio.loc[idx, 'Profit'] = (strk_sell - strk_buy) * num_cont
            except (ValueError, TypeError):
                df_limpio.loc[idx, 'Profit'] = 0
    
    # Convertir Profit a numérico antes de los cálculos
    df_limpio['Profit'] = pd.to_numeric(df_limpio['Profit'], errors='coerce')
    
    # Calcular el porcentaje de profit y formatear con % y 2 decimales
    if all(col in df_limpio.columns for col in ['Profit', 'STRK Buy', '#Cont']):
        df_limpio['% Profit. Op'] = df_limpio.apply(
            lambda row: f"{((row['Profit'] / (row['STRK Buy'] * row['#Cont'])) * 100):.2f}%" 
            if pd.notnull(row['Profit']) and pd.notnull(row['STRK Buy']) and pd.notnull(row['#Cont']) 
            and row['STRK Buy'] != 0 and row['#Cont'] != 0 
            else "", 
            axis=1
        )
    
    # Calcular el Profit Total como suma acumulativa
    df_limpio['Profit Tot.'] = df_limpio['Profit'].cumsum()
    
    # Formatear Profit y Profit Tot. con 2 decimales y sin ceros innecesarios
    def formatear_sin_ceros(x):
        if pd.isnull(x):
            return ""
        try:
            num = float(x)
            if num.is_integer():
                return str(int(num))
            return str(float(f"{num:.2f}")).rstrip('0').rstrip('.')
        except:
            return str(x)
    
    df_limpio['Profit'] = pd.to_numeric(df_limpio['Profit'], errors='coerce').apply(formatear_sin_ceros)
    df_limpio['Profit Tot.'] = pd.to_numeric(df_limpio['Profit Tot.'], errors='coerce').apply(formatear_sin_ceros)
    
    # Formatear la columna D con el sufijo 'd'
    if 'D' in df_limpio.columns:
        def formatear_d(x):
            if pd.isnull(x) or pd.isna(x) or str(x).strip() in ['', '.']:
                return ""
            try:
                # Intentar convertir a float primero para manejar decimales
                valor = float(x)
                # Convertir a entero y agregar 'd'
                return f"{int(valor)}d"
            except (ValueError, TypeError):
                # Si no se puede convertir, devolver el valor original
                return str(x)
        
        df_limpio['D'] = df_limpio['D'].apply(formatear_d)
    
    return df_limpio

def borrar_columna(df, col_borrar):
    df.drop(columns=[col_borrar], inplace=True)
    return df

def vaciar_columna(df, col_limpiar):
    df[col_limpiar] = ""
    return df

def vaciar_fila(df, fila_limpiar):
    df.iloc[fila_limpiar] = ""
    return df

def eliminar_fila(df, fila_eliminar):
    df.drop(index=fila_eliminar, inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df

def agregar_contador(df):
    # Agregar la columna "Contador" solo a la tabla editable y comenzando desde 0
    df['Contador'] = range(0, len(df))  # Empezar desde 0
    
    # Asegurarnos de que la columna "Contador" esté siempre en la primera columna
    cols = ['Contador'] + [col for col in df.columns if col != 'Contador']
    df = df[cols]
    
    return df

def agregar_fila(df):
    # Inicializar el estado de visibilidad
    if "mostrar_formulario" not in st.session_state:
        st.session_state.mostrar_formulario = False

    # Botón para mostrar u ocultar el formulario
    if st.button("Mostrar/Ocultar formulario de operación"):
        st.session_state.mostrar_formulario = not st.session_state.mostrar_formulario  # Alterna el estado

    if st.session_state.mostrar_formulario:
        index_editar = st.number_input("¿Deseás editar una fila existente? (Dejá en blanco o pon -1 para agregar nueva)", 
                                       min_value=-1, max_value=len(df)-1, value=-1, step=1)

        if index_editar >= 0 and index_editar < len(df):
            fila_actual = df.iloc[index_editar]
            modo_edicion = True
        else:
            fila_actual = {}
            modo_edicion = False

        activo = st.selectbox("Activo", ["SPY", "QQQ", "AMZN", "AAPL"], 
                               index=["SPY", "QQQ", "AMZN", "AAPL"].index(fila_actual.get("Activo", "SPY") if fila_actual.get("Activo") else "SPY"))

        valor_cp = fila_actual.get("C&P") or "CALL"
        c_p = st.selectbox("C&P", ["CALL", "PUT"], index=["CALL", "PUT"].index(valor_cp))

        valor_dias = fila_actual.get("D", 1)
        dias = st.number_input("D", min_value=1, max_value=10, value=valor_dias)

        valor_fecha_entrada = fila_actual.get("Fecha / Hora", pd.Timestamp.today())
        fecha_entrada = st.date_input("Fecha / Hora de entrada", value=valor_fecha_entrada.date())
        hora_entrada = st.time_input("Hora de entrada", value=valor_fecha_entrada.time())
        fecha_hora_entrada = pd.Timestamp.combine(fecha_entrada, hora_entrada)

        valor_fecha_cierre = fila_actual.get("Fecha / Hora de Cierre", pd.Timestamp.today())
        fecha_cierre = st.date_input("Fecha / Hora de Cierre", value=valor_fecha_cierre.date())
        hora_cierre = st.time_input("Hora de Cierre", value=valor_fecha_cierre.time())
        fecha_hora_cierre = pd.Timestamp.combine(fecha_cierre, hora_cierre)

        # Calcular la diferencia de tiempo
        tiempo_operacion = fecha_hora_cierre - fecha_hora_entrada
        dia_live = tiempo_operacion.total_seconds() / (60 * 60 * 24)

        # Guardar operación
        if st.button("💾 Guardar operación"):
            nueva_fila = {
                "Activo": activo,
                "C&P": c_p,
                "D": dias,
                "Fecha / Hora": fecha_hora_entrada,
                "Fecha / Hora de Cierre": fecha_hora_cierre,
                "T. Op": str(tiempo_operacion),
                "Dia LIVE": dia_live,
                # Otros campos necesarios...
            }

            if modo_edicion:
                for k, v in nueva_fila.items():
                    df.at[index_editar, k] = v
            else:
                df = pd.concat([df, pd.DataFrame([nueva_fila])], ignore_index=True)

    return df

def actualizar_tabla(df):
    """Actualiza la tabla y recalcula las fechas."""
    try:
        # Asegurarnos de que las columnas de fecha existan
        columnas_requeridas = ['Fecha / Hora', 'Fecha / Hora de Cierre']
        if not all(col in df.columns for col in columnas_requeridas):
            st.error("Faltan columnas de fecha necesarias")
            return df

        # Hacer una copia limpia del DataFrame
        df_actualizado = df.copy()
        
        # Forzar la conversión de las columnas de fecha a datetime
        for col in columnas_requeridas:
            df_actualizado[col] = pd.to_datetime(df_actualizado[col], errors='coerce')
        
        # Recalcular las fechas usando el módulo de fechas
        df_actualizado = agregar_tiempo_operacion(df_actualizado)
        
        # Limpiar y formatear las columnas
        df_actualizado = limpiar_columnas(df_actualizado)
        
        # Formatear la columna D como último paso
        df_actualizado = formatear_columna_d(df_actualizado)
        
        # Asegurarnos de que los cambios se guarden en la sesión
        if 'df' in st.session_state:
            st.session_state['df'] = df_actualizado
        
        return df_actualizado
    except Exception as e:
        st.error(f"Error al actualizar la tabla: {str(e)}")
        return df

def aplicar_cambios(df, cambios):
    """Aplica los cambios a la tabla y recalcula las fechas."""
    try:
        # Aplicar los cambios
        for indice, valor in cambios.items():
            fila, columna = indice
            df.at[fila, columna] = valor
        
        # Recalcular las fechas después de aplicar los cambios
        df_actualizado = actualizar_tabla(df)
        
        # Asegurarnos de que los cambios se guarden en la sesión
        if 'df' in st.session_state:
            st.session_state['df'] = df_actualizado
        
        return df_actualizado
    except Exception as e:
        st.error(f"Error al aplicar cambios: {str(e)}")
        return df

def mostrar_tabla_editable(df):
    """Muestra la tabla editable."""
    # Crear una copia editable del DataFrame
    df_editable = df.copy()
    
    # Función para formatear números sin ceros innecesarios
    def formatear_sin_ceros(x):
        if pd.isnull(x):
            return ""
        try:
            num = float(x)
            if num.is_integer():
                return str(int(num))
            return str(float(f"{num:.2f}")).rstrip('0').rstrip('.')
        except:
            return str(x)
    
    # Aplicar formato a las columnas numéricas
    columnas_numericas = ['STRK Buy', 'STRK Sell', '#Cont', 'Profit', 'Profit Tot.', 'Deposito', 'Retiro']
    for col in columnas_numericas:
        if col in df_editable.columns:
            df_editable[col] = pd.to_numeric(df_editable[col], errors='coerce')
            df_editable[col] = df_editable[col].apply(formatear_sin_ceros)
    
    # Mostrar la tabla editable
    tabla_editada = st.data_editor(df_editable, 
                                 num_rows="dynamic",
                                 key="tabla_editable")
    
    # Botones para actualizar y aplicar cambios
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Actualizar Tabla"):
            st.session_state['df'] = tabla_editada
            st.experimental_rerun()
    
    with col2:
        if st.button("Aplicar Cambios"):
            # Obtener los cambios realizados
            cambios = {}
            if 'tabla_editable' in st.session_state:
                for indice, valor in st.session_state['tabla_editable'].items():
                    if isinstance(indice, tuple):
                        cambios[indice] = valor
            
            # Aplicar los cambios
            if cambios:
                for indice, valor in cambios.items():
                    fila, columna = indice
                    df.at[fila, columna] = valor
                st.session_state['df'] = df
                st.experimental_rerun()
    
    return tabla_editada

def calcular_tiempo_operacion(fecha_entrada, fecha_cierre):
    tiempo_operacion = fecha_cierre - fecha_entrada
    dia_live = tiempo_operacion.total_seconds() / (60 * 60 * 24)
    return tiempo_operacion, dia_live

def agregar_tiempo_operacion(df):
    df['Día'] = df['Fecha / Hora'].dt.strftime('%a').str[:2]
    df['T. Op'] = df.apply(lambda row: calcular_tiempo_operacion(row['Fecha / Hora'], row['Fecha / Hora de Cierre']), axis=1)
    
    # Calculamos el % Profit. Op
    df['% Profit. Op'] = (df['Profit'] / (df['STRK Buy'] * df['#Cont'])) * 100
    df['% Profit. Op'] = df['% Profit. Op'].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else "")
    
    return df

def color_depositos_retiros(df):
    """
    Colorea las filas que tienen valores en las columnas Deposito y Retiro.
    - Morado para filas con Deposito
    - Rosa para filas con Retiro
    """
    # Crear un DataFrame de colores con el mismo tamaño que df
    color_df = pd.DataFrame('', index=df.index, columns=df.columns)
    
    # Iterar sobre cada fila
    for idx in df.index:
        # Si hay un valor en Deposito, colorear toda la fila de morado
        if ('Deposito' in df.columns and 
            pd.notnull(df.loc[idx, 'Deposito']) and 
            str(df.loc[idx, 'Deposito']).strip() != ''):
            for col in df.columns:
                color_df.loc[idx, col] = 'background-color: #E6E6FA'  # Morado claro
        
        # Si hay un valor en Retiro, colorear toda la fila de rosa
        elif ('Retiro' in df.columns and 
              pd.notnull(df.loc[idx, 'Retiro']) and 
              str(df.loc[idx, 'Retiro']).strip() != ''):
            for col in df.columns:
                color_df.loc[idx, col] = 'background-color: #FFB6C1'  # Rosa claro
    
    return color_df

def procesar_depositos_retiros(df):
    """
    Procesa los valores de Deposito y Retiro:
    - Asegura que los valores en Deposito sean positivos
    - Asegura que los valores en Retiro sean negativos
    - Limpia las columnas #Cont, STRK Buy y STRK Sell cuando hay valores en Deposito o Retiro
    """
    # Hacer una copia del DataFrame para no modificar el original
    df_procesado = df.copy()
    
    # Columnas a limpiar cuando hay depósito o retiro
    columnas_a_limpiar = ['#Cont', 'STRK Buy', 'STRK Sell']
    
    # Iterar sobre cada fila
    for idx in df_procesado.index:
        # Procesar Deposito
        if 'Deposito' in df_procesado.columns and pd.notnull(df_procesado.loc[idx, 'Deposito']):
            # Asegurar que el valor sea positivo
            valor_deposito = float(df_procesado.loc[idx, 'Deposito'])
            df_procesado.loc[idx, 'Deposito'] = abs(valor_deposito)
            
            # Limpiar las columnas especificadas
            for col in columnas_a_limpiar:
                if col in df_procesado.columns:
                    df_procesado.loc[idx, col] = ""
        
        # Procesar Retiro
        if 'Retiro' in df_procesado.columns and pd.notnull(df_procesado.loc[idx, 'Retiro']):
            # Asegurar que el valor sea negativo
            valor_retiro = float(df_procesado.loc[idx, 'Retiro'])
            df_procesado.loc[idx, 'Retiro'] = -abs(valor_retiro)
            
            # Limpiar las columnas especificadas
            for col in columnas_a_limpiar:
                if col in df_procesado.columns:
                    df_procesado.loc[idx, col] = ""
    
    return df_procesado

def limpiar_columnas_deposito_retiro(df):
    """
    Cuando hay valores en Deposito o Retiro:
    1. Limpia las columnas #Cont, STRK Buy, STRK Sell, C&P y D
    2. Actualiza Activo a 'DEP' para depósitos o 'RET' para retiros
    """
    # Hacer una copia del DataFrame para no modificar el original
    df_limpio = df.copy()
    
    # Columnas a limpiar (incluyendo D)
    columnas_a_limpiar = ['#Cont', 'STRK Buy', 'STRK Sell', 'C&P', 'D']
    
    # Iterar sobre cada fila
    for idx in df_limpio.index:
        # Procesar Deposito
        if 'Deposito' in df_limpio.columns and pd.notnull(df_limpio.loc[idx, 'Deposito']):
            # Limpiar todas las columnas especificadas
            for col in columnas_a_limpiar:
                if col in df_limpio.columns:
                    df_limpio.loc[idx, col] = ""
            # Actualizar Activo a DEP
            if 'Activo' in df_limpio.columns:
                df_limpio.loc[idx, 'Activo'] = 'DEP'
            continue
        
        # Procesar Retiro
        if 'Retiro' in df_limpio.columns and pd.notnull(df_limpio.loc[idx, 'Retiro']):
            # Limpiar todas las columnas especificadas
            for col in columnas_a_limpiar:
                if col in df_limpio.columns:
                    df_limpio.loc[idx, col] = ""
            # Actualizar Activo a RET
            if 'Activo' in df_limpio.columns:
                df_limpio.loc[idx, 'Activo'] = 'RET'
            continue
    
    return df_limpio

def quitar_ceros_tabla(df):
    """
    Quita los ceros innecesarios después del punto decimal en todas las columnas numéricas.
    No afecta a los colores ni a la lógica de la tabla.
    """
    # Hacer una copia del DataFrame para no afectar el original
    df_formateado = df.copy()
    
    def formatear_numero(valor):
        if pd.isnull(valor) or valor == "":
            return valor
        try:
            num = float(valor)
            if num.is_integer():
                return str(int(num))
            # Convertir a string con 2 decimales y quitar ceros innecesarios
            return '{:.2f}'.format(num).rstrip('0').rstrip('.')
        except:
            return valor

    # Lista de columnas numéricas que queremos formatear (excluyendo D)
    columnas_numericas = [
        'STRK Buy', 'STRK Sell', '#Cont', 'Profit', 'Profit Tot.',
        'Deposito', 'Retiro'
    ]
    
    # Aplicar el formato solo a las columnas numéricas que existen en el DataFrame
    for col in columnas_numericas:
        if col in df_formateado.columns:
            # Convertir a numérico primero para asegurar que podemos formatear
            df_formateado[col] = pd.to_numeric(df_formateado[col], errors='coerce')
            # Aplicar el formato
            df_formateado[col] = df_formateado[col].apply(formatear_numero)
    
    return df_formateado

def modificar_activo_deposito_retiro(df):
    """
    Modifica la columna 'Activo' basado en valores en 'Deposito' y 'Retiro'.
    Si hay un valor en 'Deposito', establece 'Activo' como 'DEP'.
    Si hay un valor en 'Retiro', establece 'Activo' como 'RET'.
    En ambos casos, limpia la columna 'C&P'.
    """
    df_mod = df.copy()
    
    for idx in df_mod.index:
        if pd.notnull(df_mod.loc[idx, 'Deposito']) and float(str(df_mod.loc[idx, 'Deposito']).strip() or 0) != 0:
            df_mod.loc[idx, 'Activo'] = 'DEP'
            df_mod.loc[idx, 'C&P'] = ''
        elif pd.notnull(df_mod.loc[idx, 'Retiro']) and float(str(df_mod.loc[idx, 'Retiro']).strip() or 0) != 0:
            df_mod.loc[idx, 'Activo'] = 'RET'
            df_mod.loc[idx, 'C&P'] = ''
    
    return df_mod

def limpiar_valores_activo(df):
    """
    Limpia la columna 'C&P' cuando el valor de 'Activo' es 'DEP' o 'RET'.
    """
    df_mod = df.copy()
    
    for idx in df_mod.index:
        if df_mod.loc[idx, 'Activo'] in ['DEP', 'RET']:
            df_mod.loc[idx, 'C&P'] = ''
    
    return df_mod

def asignar_dep_ret_activo(df):
    """
    Asigna 'DEP' o 'RET' en la columna Activo según los valores en Deposito o Retiro.
    """
    df_mod = df.copy()
    
    # Iterar sobre cada fila
    for idx in df_mod.index:
        try:
            # Obtener valores de Deposito y Retiro
            deposito = df_mod.loc[idx, 'Deposito']
            retiro = df_mod.loc[idx, 'Retiro']
            
            # Convertir a string y eliminar espacios
            deposito_str = str(deposito).strip() if pd.notna(deposito) else ''
            retiro_str = str(retiro).strip() if pd.notna(retiro) else ''
            
            # Verificar si hay valor en Deposito
            if deposito_str and deposito_str != '0' and deposito_str != '0.0':
                df_mod.loc[idx, 'Activo'] = 'DEP'
            
            # Verificar si hay valor en Retiro
            if retiro_str and retiro_str != '0' and retiro_str != '0.0':
                df_mod.loc[idx, 'Activo'] = 'RET'
        except:
            continue
    
    return df_mod

def formatear_columna_d(df):
    """
    Asegura que los valores en la columna D se muestren con el sufijo 'd'.
    Ejemplo: 1 -> '1d', 2 -> '2d', etc.
    """
    if 'D' not in df.columns:
        return df
        
    df_mod = df.copy()
    
    for idx in df_mod.index:
        valor = df_mod.loc[idx, 'D']
        # Si el valor ya tiene el formato 'd', no hacer nada
        if isinstance(valor, str) and valor.endswith('d'):
            continue
            
        # Si el valor es nulo o vacío, dejarlo como está
        if pd.isnull(valor) or str(valor).strip() == '':
            continue
            
        try:
            # Convertir a float primero para manejar decimales
            valor_float = float(valor)
            # Convertir a entero y agregar 'd'
            valor_formateado = f"{int(valor_float)}d"
            df_mod.loc[idx, 'D'] = valor_formateado
        except (ValueError, TypeError):
            # Si no se puede convertir, dejar el valor original
            pass
                
    return df_mod

def calcular_porcentaje_profit_tot(df):
    """
    Calcula el porcentaje de cambio en la columna Profit T. basado en la fórmula:
    Profit T. = (ValorActual de Profit Tot. - ValorAnterior de Profit Tot.) / ValorAnterior de Profit Tot. * 100
    """
    # Hacer una copia del DataFrame para no modificar el original
    df_mod = df.copy()
    
    # Asegurarse de que Profit Tot. sea numérico y limpiar la columna
    df_mod['Profit Tot.'] = pd.to_numeric(df_mod['Profit Tot.'].astype(str).str.replace(',', '').str.replace('%', ''), errors='coerce')
    
    # Crear o limpiar la columna Profit T.
    df_mod['Profit T.'] = ''
    
    # Calcular el porcentaje de cambio para cada fila
    for i in range(len(df_mod)):
        try:
            if i == 0:
                df_mod.at[i, 'Profit T.'] = '0%'
            else:
                valor_actual = float(df_mod.at[i, 'Profit Tot.'])
                valor_anterior = float(df_mod.at[i-1, 'Profit Tot.'])
                
                if valor_anterior != 0:
                    porcentaje = ((valor_actual - valor_anterior) / abs(valor_anterior)) * 100
                    df_mod.at[i, 'Profit T.'] = f"{porcentaje:+.2f}%"
                else:
                    df_mod.at[i, 'Profit T.'] = '0%'
        except (ValueError, TypeError, ZeroDivisionError):
            df_mod.at[i, 'Profit T.'] = '0%'
            continue
    
    return df_mod

def color_profit_t(df):
    """
    Colorea la columna Profit T. según los valores:
    - Amarillo para 0%
    - Verde para valores positivos
    - Rojo para valores negativos
    """
    # Crear un DataFrame vacío para los colores
    color_map = pd.DataFrame('', index=df.index, columns=df.columns)
    
    # Iterar sobre cada fila
    for idx in df.index:
        try:
            if 'Profit T.' in df.columns:
                valor = df.loc[idx, 'Profit T.']
                color = ''
                
                if valor == '0%':
                    color = 'color: yellow'
                elif valor.startswith('+'):
                    color = 'color: green'
                elif valor.startswith('-'):
                    color = 'color: red'
                
                color_map.loc[idx, 'Profit T.'] = color
        except:
            continue
    
    return color_map

def color_profit_alcanzado_media(df):
    """
    Colorea las columnas:
    - Profit Alcanzado y % Alcanzado en violeta
    - Profit Media y % Media en azul claro
    """
    # Crear un DataFrame vacío para los colores
    color_map = pd.DataFrame('', index=df.index, columns=df.columns)
    
    # Iterar sobre cada fila
    for idx in df.index:
        # Colorear Profit Alcanzado y % Alcanzado en violeta
        if 'Profit Alcanzado' in df.columns:
            color_map.loc[idx, 'Profit Alcanzado'] = 'color: #8A2BE2'  # Violeta
        if '% Alcanzado' in df.columns:
            color_map.loc[idx, '% Alcanzado'] = 'color: #8A2BE2'  # Violeta
        
        # Colorear Profit Media y % Media en azul claro
        if 'Profit Media' in df.columns:
            color_map.loc[idx, 'Profit Media'] = 'color: #00BFFF'  # Azul claro
        if '% Media' in df.columns:
            color_map.loc[idx, '% Media'] = 'color: #00BFFF'  # Azul claro
    
    return color_map

def color_porcentajes_alcanzado_media(df):
    """
    Colorea las columnas:
    - % Alcanzado en violeta (#8A2BE2)
    - % Media en azul claro (#00BFFF)
    """
    # Crear un DataFrame vacío para los colores
    color_map = pd.DataFrame('', index=df.index, columns=df.columns)
    
    # Iterar sobre cada fila
    for idx in df.index:
        # Colorear % Alcanzado en violeta
        if '% Alcanzado' in df.columns:
            color_map.loc[idx, '% Alcanzado'] = 'color: #8A2BE2'  # Violeta
        
        # Colorear % Media en azul claro
        if '% Media' in df.columns:
            # Verificar si hay un valor en la celda
            valor = df.loc[idx, '% Media']
            if pd.notnull(valor) and str(valor).strip() != '':
                color_map.loc[idx, '% Media'] = 'color: #00BFFF'  # Azul claro
    
    return color_map

def calcular_profit_alcanzado(df):
    """
    Calcula el Profit Alcanzado usando la fórmula:
    Profit Alcanzado = (STRK Buy * % Alcanzado) + Profit Alcanzado de la fila anterior
    El primer valor será igual al primer valor de Profit Tot.
    """
    try:
        # Crear una copia del DataFrame para no modificar el original
        df_temp = df.copy()
        
        # Asegurarse de que las columnas necesarias existen
        if 'STRK Buy' in df_temp.columns and '% Alcanzado' in df_temp.columns and 'Profit Tot.' in df_temp.columns:
            # Convertir columnas a numérico
            df_temp['STRK Buy'] = pd.to_numeric(df_temp['STRK Buy'], errors='coerce')
            df_temp['Profit Tot.'] = pd.to_numeric(df_temp['Profit Tot.'], errors='coerce')
            
            # Iterar sobre cada fila para realizar el cálculo
            for idx in df_temp.index:
                try:
                    # Para el primer valor, usar directamente Profit Tot.
                    if idx == 0:
                        profit_tot = float(df_temp.loc[idx, 'Profit Tot.']) if pd.notnull(df_temp.loc[idx, 'Profit Tot.']) else 0
                        df_temp.loc[idx, 'Profit Alcanzado'] = f"{profit_tot:.2f}"
                        continue
                    
                    # Para los demás valores, usar la fórmula con Profit Alcanzado de la fila anterior
                    strk_buy = float(df_temp.loc[idx, 'STRK Buy']) if pd.notnull(df_temp.loc[idx, 'STRK Buy']) else 0
                    profit_alcanzado_anterior = float(df_temp.loc[idx-1, 'Profit Alcanzado']) if pd.notnull(df_temp.loc[idx-1, 'Profit Alcanzado']) else 0
                    
                    # Convertir el porcentaje a decimal (500% -> 5)
                    porc_alcanzado_str = str(df_temp.loc[idx, '% Alcanzado']).replace('%', '').strip()
                    porc_alcanzado = float(porc_alcanzado_str) / 100 if porc_alcanzado_str else 0
                    
                    # Realizar el cálculo: (STRK Buy * % Alcanzado) + Profit Alcanzado anterior
                    profit_alcanzado = (strk_buy * porc_alcanzado) + profit_alcanzado_anterior
                    
                    # Formatear el resultado con 2 decimales
                    df_temp.loc[idx, 'Profit Alcanzado'] = f"{profit_alcanzado:.2f}"
                except Exception as e:
                    print(f"Error en fila {idx}: {e}")
                    df_temp.loc[idx, 'Profit Alcanzado'] = "0"
    except Exception as e:
        print(f"Error al calcular Profit Alcanzado: {str(e)}")
    
    return df_temp

def calcular_profit_media(df):
    """
    Calcula el Profit Media usando la fórmula:
    Profit Media = (STRK Buy * % Media) + Profit Media de la fila anterior
    El primer valor será igual al primer valor de Profit Tot.
    """
    try:
        # Crear una copia del DataFrame para no modificar el original
        df_temp = df.copy()
        
        # Asegurarse de que las columnas necesarias existen
        if 'STRK Buy' in df_temp.columns and '% Media' in df_temp.columns and 'Profit Tot.' in df_temp.columns:
            # Convertir columnas a numérico
            df_temp['STRK Buy'] = pd.to_numeric(df_temp['STRK Buy'], errors='coerce')
            df_temp['Profit Tot.'] = pd.to_numeric(df_temp['Profit Tot.'], errors='coerce')
            
            # Iterar sobre cada fila para realizar el cálculo
            for idx in df_temp.index:
                try:
                    # Para el primer valor, usar directamente Profit Tot.
                    if idx == 0:
                        profit_tot = float(df_temp.loc[idx, 'Profit Tot.']) if pd.notnull(df_temp.loc[idx, 'Profit Tot.']) else 0
                        df_temp.loc[idx, 'Profit Media'] = f"{profit_tot:.2f}"
                        continue
                    
                    # Para los demás valores, usar la fórmula con Profit Media de la fila anterior
                    strk_buy = float(df_temp.loc[idx, 'STRK Buy']) if pd.notnull(df_temp.loc[idx, 'STRK Buy']) else 0
                    profit_media_anterior = float(df_temp.loc[idx-1, 'Profit Media']) if pd.notnull(df_temp.loc[idx-1, 'Profit Media']) else 0
                    
                    # Convertir el porcentaje a decimal (500% -> 5)
                    porc_media_str = str(df_temp.loc[idx, '% Media']).replace('%', '').strip()
                    porc_media = float(porc_media_str) / 100 if porc_media_str else 0
                    
                    # Realizar el cálculo: (STRK Buy * % Media) + Profit Media anterior
                    profit_media = (strk_buy * porc_media) + profit_media_anterior
                    
                    # Formatear el resultado con 2 decimales
                    df_temp.loc[idx, 'Profit Media'] = f"{profit_media:.2f}"
                except Exception as e:
                    print(f"Error en fila {idx}: {e}")
                    df_temp.loc[idx, 'Profit Media'] = "0"
    except Exception as e:
        print(f"Error al calcular Profit Media: {str(e)}")
    
    return df_temp

def calcular_operaciones_ganadoras_perdedoras(df):
    """Calcula el número de operaciones ganadoras y perdedoras basado en la columna Profit."""
    try:
        print("\n=== Inicio de cálculo de operaciones ganadoras/perdedoras ===")
        print(f"Total de filas en el DataFrame: {len(df)}")
        
        # Asegurarse de que Profit sea numérico
        df['Profit'] = pd.to_numeric(df['Profit'], errors='coerce')
        
        # Contar operaciones ganadoras (Profit > 0)
        operaciones_ganadoras = df[df['Profit'] > 0]
        num_ganadoras = len(operaciones_ganadoras)
        
        # Restar operaciones que tienen valor en Deposito
        depositos = df[df['Deposito'].notna() & (df['Deposito'] != '')]
        num_depositos = len(depositos)
        num_ganadoras = num_ganadoras - num_depositos
        print(f"Número de operaciones ganadoras: {num_ganadoras} (después de restar {num_depositos} depósitos)")
        print("Ejemplo de operaciones ganadoras:")
        print(operaciones_ganadoras[['Activo', 'Profit', 'Deposito']].head())
        
        # Contar operaciones perdedoras (Profit < 0)
        operaciones_perdedoras = df[df['Profit'] < 0]
        num_perdedoras = len(operaciones_perdedoras)
        
        # Restar operaciones que tienen valor en Retiro
        retiros = df[df['Retiro'].notna() & (df['Retiro'] != '')]
        num_retiros = len(retiros)
        num_perdedoras = num_perdedoras - num_retiros
        print(f"Número de operaciones perdedoras: {num_perdedoras} (después de restar {num_retiros} retiros)")
        print("Ejemplo de operaciones perdedoras:")
        print(operaciones_perdedoras[['Activo', 'Profit', 'Retiro']].head())
        
        # Crear DataFrame con los resultados
        df_resultado = pd.DataFrame({
            'Op. Ganadoras': [num_ganadoras],
            'Op. Perdedoras': [num_perdedoras]
        })
        
        print("\nResultado final:")
        print(df_resultado)
        print("=== Fin de cálculo de operaciones ganadoras/perdedoras ===\n")
        
        return df_resultado
        
    except Exception as e:
        print(f"Error en calcular_operaciones_ganadoras_perdedoras: {str(e)}")
        # En caso de error, devolver un DataFrame con ceros
        return pd.DataFrame({
            'Op. Ganadoras': [0],
            'Op. Perdedoras': [0]
        })
