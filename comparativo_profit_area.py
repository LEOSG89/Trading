import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import os
import json


def mostrar_profit_area(df: pd.DataFrame, chart_key: str) -> None:
    """
    Gráfico de área para la columna 'Profit Tot.', con franjas para depósitos y retiros y exclusiones persistentes.
    También muestra una tabla con las últimas 5 operaciones y sus valores de Profit.
    """
    if 'Profit Tot.' not in df.columns:
        st.warning("Falta la columna 'Profit Tot.' en el DataFrame.")
        return

    # Indices y archivo de exclusión
    df_idx = list(df.index)
    json_file = f"{chart_key}_excl.json"
    excl = []
    if os.path.exists(json_file):
        try:
            with open(json_file,'r') as f: excl = json.load(f)
        except: excl = []
    else:
        excl = [0] if 0 in df_idx else []
        with open(json_file,'w') as f: json.dump(excl,f)

    excl = st.multiselect("Excluir índices Profit Tot.:", df_idx, default=excl, key=f"ms_{chart_key}_profit")
    try:
        with open(json_file,'w') as f: json.dump(excl,f)
    except: pass

    # Series para gráfico y tabla
    profit_plot_str = df['Profit Tot.'].astype(str)
    profit_plot_num = pd.to_numeric(profit_plot_str.str.rstrip('%'), errors='coerce').fillna(0)
    profit_tbl_str = df['Profit T.'].astype(str) if 'Profit T.' in df.columns else profit_plot_str

    # Filtrar índices
    plot_idx = [i for i in df_idx if i not in excl]
    x_vals = plot_idx
    y_vals = profit_plot_num.loc[plot_idx]
    text_vals = profit_plot_str.loc[plot_idx]

    # Crear gráfico de área
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_vals, y=y_vals,
        mode='lines', fill='tozeroy', line=dict(color='green'),
        text=text_vals, hovertemplate='Índice: %{x}<br>Profit Tot.: %{text}',
        name='Profit Tot.'
    ))
    # Franjas para Depósito y Retiro
    for idx in x_vals:
        prev = idx - 1
        if prev < 0: continue
        if 'Deposito' in df.columns and pd.notna(df.loc[idx,'Deposito']):
            fig.add_shape(type='rect', xref='x', yref='paper', x0=prev, x1=idx,
                          y0=0, y1=1, fillcolor='lightblue', opacity=0.3, layer='below', line_width=0)
        if 'Retiro' in df.columns and pd.notna(df.loc[idx,'Retiro']):
            fig.add_shape(type='rect', xref='x', yref='paper', x0=prev, x1=idx,
                          y0=0, y1=1, fillcolor='pink', opacity=0.3, layer='below', line_width=0)

    fig.update_layout(xaxis_title='Índice', yaxis_title='Profit Tot.', template='plotly_dark', showlegend=False)
    st.plotly_chart(fig, use_container_width=True, key=chart_key)

    # Tabla últimos 5 Depósitos y Retiros
    movs = df.loc[df.get('Deposito',pd.NA).notna() | df.get('Retiro',pd.NA).notna(), ['Deposito','Retiro']].copy()
    if movs.empty:
        st.info("No hay movimientos de Depósito o Retiro.")
        return
    movs = movs.reset_index().rename(columns={'index':'Índice'})
    ult_dep = movs.loc[movs['Deposito'].notna(), ['Índice','Deposito']].tail(5)
    ult_ret = movs.loc[movs['Retiro'].notna(), ['Índice','Retiro']].tail(5)
    n = max(len(ult_dep), len(ult_ret))

    # Construir tabla
    dep_idxs = list(ult_dep['Índice']) + ['']*(n-len(ult_dep))
    dep_vals = list(ult_dep['Deposito']) + ['']*(n-len(ult_dep))
    ret_idxs = list(ult_ret['Índice']) + ['']*(n-len(ult_ret))
    ret_vals = list(ult_ret['Retiro']) + ['']*(n-len(ult_ret))

    tabla = pd.DataFrame({
        'Índice Depósito': dep_idxs,
        'Últimos 5 Depósitos': dep_vals,
        'Deposito D up': ['']*n,
        'Índice Retiro': ret_idxs,
        'Últimos 5 Retiros': ret_vals,
        'Retiro D dw': ['']*n
    })
    # Llenar Profit en nuevas columnas
    for i, ix in enumerate(tabla['Índice Depósito']):
        if ix!='' and ix in profit_tbl_str.index:
            tabla.at[i,'Deposito D up'] = profit_tbl_str.loc[ix]
    for i, ix in enumerate(tabla['Índice Retiro']):
        if ix!='' and ix in profit_tbl_str.index:
            tabla.at[i,'Retiro D dw'] = profit_tbl_str.loc[ix]

    # Totales
    total_dep = ult_dep['Deposito'].sum()
    total_ret = ult_ret['Retiro'].sum()
    totals = {'Índice Depósito':'Total', 'Últimos 5 Depósitos':total_dep, 'Deposito D up':'',
              'Índice Retiro':'Total','Últimos 5 Retiros':total_ret,'Retiro D dw':''}
    tabla = pd.concat([tabla, pd.DataFrame([totals])], ignore_index=True)

    # Formatear sin decimales
    def fmt(v):
        try: return str(int(v))
        except: return v
    tabla['Últimos 5 Depósitos'] = tabla['Últimos 5 Depósitos'].apply(fmt)
    tabla['Últimos 5 Retiros'] = tabla['Últimos 5 Retiros'].apply(fmt)

    # Colorear
    sty = tabla.style
    sty = sty.applymap(lambda _: 'color: lightblue;', subset=['Últimos 5 Depósitos','Deposito D up'])
    sty = sty.applymap(lambda _: 'color: pink;', subset=['Últimos 5 Retiros','Retiro D dw'])
    st.dataframe(sty, use_container_width=True)
