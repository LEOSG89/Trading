import pandas as pd
import streamlit as st
from datetime import datetime
from modulo_fechas_new import calcular_diferencia  # Importa la función de cálculo de fechas

def agregar_fila(df):
    """
    Agrega una nueva fila al DataFrame con los datos ingresados por el usuario.
    """
    if df is None or df.empty:
        return None

    # Crear una copia del DataFrame
    df_nuevo = df.copy()

    # Obtener la última fila
    ultima_fila = df_nuevo.iloc[-1] if not df_nuevo.empty else None

    # Valores por defecto
    valores_defecto = {
        'Activo': 'SPY',
        'C&P': 'CALL',
        'D': '1d',
        'Día': '',
        'Fecha / Hora': '',
        'Fecha / Hora de Cierre': '',
        'T. Op': '',
        'Día LIVE': '',
        'Deposito': '',
        'Retiro': '',
        '#Cont': 1,
        'STRK Buy': 0.0,
        'STRK Sell': 0.0,
        'Profit': 0.0,
        '% Profit. Op': '',
        'Profit Tot.': ultima_fila['Profit Tot.'] if ultima_fila is not None and 'Profit Tot.' in df_nuevo.columns else 0.0,
        'DD/Max': '',
        '% Profit Tot.': ''
    }

    # Crear el formulario
    with st.form("agregar_fila"):
        st.subheader("📝 Agregar nueva operación")
        
        # Primera fila de campos
        col1, col2, col3 = st.columns(3)
        
        with col1:
            activo = st.selectbox("Activo", ["SPY", "QQQ", "AMZN", "AAPL"])
            cp = st.selectbox("C&P", ["CALL", "PUT"])
            num_d = st.number_input("D", min_value=1, max_value=10, value=1, step=1)
            
        with col2:
            fecha_hora = st.text_input("Fecha / Hora (dd/mm/yyyy HH:MM AM/PM)")
            fecha_hora_cierre = st.text_input("Fecha / Hora de Cierre (dd/mm/yyyy HH:MM AM/PM)")
            deposito = st.number_input("Depósito", value=0.0, step=1.0)
            
        with col3:
            retiro = st.number_input("Retiro", value=0.0, step=1.0)
            num_cont = st.number_input("#Cont", min_value=1, step=1)
            strk_buy = st.number_input("STRK Buy", min_value=0.0, step=1.0)
            strk_sell = st.number_input("STRK Sell", min_value=0.0, step=1.0)
        
        # Botón para enviar el formulario
        submitted = st.form_submit_button("💾 Guardar operación")
        
        if submitted:
            try:
                # Convertir las fechas a datetime
                fecha_hora = pd.to_datetime(fecha_hora, format="%d/%m/%Y %I:%M %p")
                fecha_hora_cierre = pd.to_datetime(fecha_hora_cierre, format="%d/%m/%Y %I:%M %p")
                
                # Calcular el día de la semana
                dia = fecha_hora.strftime("%a")[:2]
                
                # Calcular el tiempo de operación
                tiempo_operacion = fecha_hora_cierre - fecha_hora
                dia_live = tiempo_operacion.total_seconds() / (60 * 60 * 24)  # Convertir a días
                
                # Calcular el profit
                profit = (strk_sell - strk_buy) * num_cont
                
                # Calcular el porcentaje de profit
                if strk_buy != 0 and num_cont != 0:
                    profit_percentage = (profit / (strk_buy * num_cont)) * 100
                    profit_percentage = f"{profit_percentage:.2f}%"
                else:
                    profit_percentage = ""
                
                # Crear la nueva fila
                nueva_fila = {
                    "Activo": activo,
                    "C&P": cp,
                    "D": f"{num_d}d",
                    "Día": dia,
                    "Fecha / Hora": fecha_hora,
                    "Fecha / Hora de Cierre": fecha_hora_cierre,
                    "T. Op": tiempo_operacion,
                    "Día LIVE": dia_live,
                    "Deposito": deposito if deposito != 0 else "",
                    "Retiro": retiro if retiro != 0 else "",
                    "#Cont": num_cont,
                    "STRK Buy": strk_buy,
                    "STRK Sell": strk_sell,
                    "Profit": profit,
                    "% Profit. Op": profit_percentage
                }
                
                # Agregar la nueva fila al DataFrame
                df_nuevo = pd.concat([df_nuevo, pd.DataFrame([nueva_fila])], ignore_index=True)
                
                st.success("✅ Nueva operación agregada correctamente")
                return df_nuevo
                
            except Exception as e:
                st.error(f"❌ Error al agregar la operación: {str(e)}")
                return df_nuevo
    
    return df_nuevo
