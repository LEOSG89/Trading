import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def comparativo_racha_dd_max(df: pd.DataFrame, chart_key: str = "racha_dd_max") -> None:
    # 1) Verificar columnas necesarias
    if 'DD/Max' not in df.columns or 'Profit' not in df.columns:
        st.warning("Faltan columnas necesarias ('DD/Max' o 'Profit').")
        return

    # 2) Preparar DataFrame
    df = df.copy().reset_index(drop=True)
    df["Index"] = df.index
    # Identificar depósitos y retiros
    df['es_deposito'] = df['Deposito'].notna() & (df['Deposito'] != 0)
    df['es_retiro']   = df['Retiro'].notna() & (df['Retiro'] != 0)

    df['dd_val'] = (
        df['DD/Max']
          .astype(str)
          .str.rstrip('%')
          .replace('', '0')
          .astype(float)
    )
    df['signo_dd'] = df['dd_val'].apply(lambda v: 1 if v>0 else -1 if v<0 else 0)
    df['run_id_dd'] = (df['signo_dd'] != df['signo_dd'].shift()).cumsum()
    if 'Fecha / Hora' in df.columns:
        df['Fecha / Hora'] = pd.to_datetime(df['Fecha / Hora'], errors='coerce')
    if 'Fecha / Hora de Cierre' in df.columns:
        df['Fecha / Hora de Cierre'] = pd.to_datetime(df['Fecha / Hora de Cierre'], errors='coerce')

# 3) Resumen de rachas DD/Max
    resumen = (
      df.groupby(['run_id_dd', 'signo_dd'])
        .apply(lambda g: pd.Series({
          'run_id_dd': g['run_id_dd'].iloc[0],  # <- explícitamente incluimos
          'signo_dd': g['signo_dd'].iloc[0],
          'Racha_Ops': g.shape[0],
          'DD_Maximo_Drawdown': g['dd_val'].min(),
          'DD_Maximo_Drawup': g['dd_val'].max(),
          'Duracion': (
              pd.to_timedelta(g['Fecha / Hora de Cierre'].iloc[-1] - g['Fecha / Hora'].iloc[0])
              if pd.notna(g['Fecha / Hora de Cierre'].iloc[-1]) and pd.notna(g['Fecha / Hora'].iloc[0])
              else pd.Timedelta(0)
          )
      }))
      .reset_index(drop=True)
    )

    if not resumen.empty:
       resumen['Media_Ops'] = resumen.groupby('signo_dd')['Racha_Ops'].transform('mean')
    else:
       resumen['Media_Ops'] = None

       # PROTECCIÓN ANTES DE USAR nlargest
   if not resumen.empty and 'Racha_Ops' in resumen.columns:
       top_pos = resumen[resumen['signo_dd'] == 1].nlargest(5, 'Racha_Ops')
       top_neg = resumen[resumen['signo_dd'] == -1].nlargest(5, 'Racha_Ops')
   else:
    # Creamos DataFrames vacíos con las columnas que luego se usan
       cols = ['run_id_dd','signo_dd','Racha_Ops','DD_Maximo_Drawdown',
               'DD_Maximo_Drawup','Duracion','Media_Ops']
       top_pos = pd.DataFrame(columns=cols)
       top_neg = pd.DataFrame(columns=cols)

    
    top_pos = resumen[resumen['signo_dd']==1].nlargest(5,'Racha_Ops')
    top_neg = resumen[resumen['signo_dd']==-1].nlargest(5,'Racha_Ops')

    # 4) Checkbox para mostrar/ocultar tablas (encima del gráfico)
    mostrar_tablas = st.checkbox("Mostrar tablas de rachas", value=True, key=f"{chart_key}_tbl_chk")

    # 5) Construir gráfico
    shapes = []
    for run, grupo in df.groupby('run_id_dd'):
        if run in set(top_pos['run_id_dd']).union(top_neg['run_id_dd']):
            color = 'green' if grupo['signo_dd'].iloc[0]>0 else 'red'
            shapes.append(dict(
                type='rect', xref='x', yref='paper',
                x0=grupo['Index'].min(), x1=grupo['Index'].max(),
                y0=0, y1=1, fillcolor=color, opacity=0.1,
                layer='below', line_width=0
            ))

    fig = go.Figure().update_layout(hovermode="x unified", shapes=shapes)

    for run, grupo in df.groupby('run_id_dd'):
        signo = grupo['signo_dd'].iloc[0]
        line_color = 'green' if signo > 0 else 'red' if signo < 0 else 'yellow'

        # Incluir punto anterior para continuidad
        if grupo['Index'].iloc[0] > 0:
            prev = grupo['Index'].iloc[0] - 1
            x_vals = [prev] + grupo['Index'].tolist()
            y_vals = [df.loc[prev, 'dd_val']] + grupo['dd_val'].tolist()
        else:
            x_vals = grupo['Index'].tolist()
            y_vals = grupo['dd_val'].tolist()

        marker_colors = []
        for i in x_vals:
            deposito = df.loc[i, 'Deposito'] if 'Deposito' in df.columns else None
            retiro   = df.loc[i, 'Retiro'] if 'Retiro' in df.columns else None

            if pd.notna(deposito) and deposito != 0:
                marker_colors.append('#3399FF')  # 🔵 Azul medio
            elif pd.notna(retiro) and retiro != 0:
                marker_colors.append('#FF69B4')  # 🌺 HotPink (rosado intenso)
            else:
                profit_val = df.loc[i, 'Profit']
                if profit_val > 0:
                    marker_colors.append('green')
                elif profit_val < 0:
                    marker_colors.append('red')
                else:
                    marker_colors.append('yellow')

        fig.add_trace(go.Scatter(
            x=x_vals, y=y_vals, mode="lines+markers",
            line=dict(color=line_color),
            marker=dict(color=marker_colors, size=12),
            showlegend=False
        ))



    fig.update_layout(
        xaxis_title="Índice de Operación",
        yaxis_title="DD/Max (%)",
        template='plotly_dark',
        height=400
    )
    st.plotly_chart(fig, use_container_width=True, key=chart_key)

    # 6) Si no quiere ver tablas, terminamos aquí
    if not mostrar_tablas:
        return

    # 7) Formateadores
    def fmt_pct(v): return f"{v:.2f}%"
    def fmt_td(td):
       if pd.isna(td):
        return "NaT"
       try:
          days = int(td.days)
          secs = int(td.seconds)
          hrs = secs // 3600
          mins = (secs % 3600) // 60
          return f"{days}d {hrs:02d}h {mins:02d}m" if days else f"{hrs:02d}h {mins:02d}m"
       except Exception:
        return str(td)


    # 8) Preparar DataFrames de tablas
    df_pos = top_pos[['Racha_Ops','DD_Maximo_Drawdown','DD_Maximo_Drawup','Duracion','Media_Ops']].copy()
    df_neg = top_neg[['Racha_Ops','DD_Maximo_Drawdown','DD_Maximo_Drawup','Duracion','Media_Ops']].copy()

    for d in (df_pos, df_neg):
        d['DD_Maximo_Drawdown'] = d['DD_Maximo_Drawdown'].map(fmt_pct)
        d['DD_Maximo_Drawup']   = d['DD_Maximo_Drawup'].map(fmt_pct)
        d['Duracion']           = d['Duracion'].map(fmt_td)
        d['Media_Ops']          = d['Media_Ops'].map(lambda v: f"{v:.2f}")

    df_pos.rename(columns={
        'Racha_Ops':'Racha D.up',
        'DD_Maximo_Drawdown':'Maximo Drawdown',
        'DD_Maximo_Drawup':'Maximo Drawup',
        'Media_Ops':'Media Ops up'
    }, inplace=True)
    df_neg.rename(columns={
        'Racha_Ops':'Racha D.dw',
        'DD_Maximo_Drawdown':'Maximo Drawdown',
        'DD_Maximo_Drawup':'Maximo Drawup',
        'Media_Ops':'Media Ops dw'
    }, inplace=True)

    # 9) Añadir rachas de Profit y asegurar longitud correcta
    df_pf = df.copy()
    df_pf['signo_pf'] = df_pf['Profit'].apply(lambda v:1 if v>0 else -1 if v<0 else 0)
    df_pf['run_id_pf'] = (df_pf['signo_pf'] != df_pf['signo_pf'].shift()).cumsum()
    resumen_pf = df_pf.groupby(['run_id_pf','signo_pf'], as_index=False).agg(Racha_Profit=('Index','count'))
    up = resumen_pf[resumen_pf['signo_pf']==1].nlargest(5,'Racha_Profit')['Racha_Profit'].tolist()
    dw = resumen_pf[resumen_pf['signo_pf']==-1].nlargest(5,'Racha_Profit')['Racha_Profit'].tolist()

    n_pos = len(df_pos)
    n_neg = len(df_neg)
    up_vals = up[:n_pos]
    dw_vals = dw[:n_neg]
    df_pos['Racha Positiva'] = up_vals + [None]*(n_pos - len(up_vals))
    df_neg['Racha Negativa'] = dw_vals + [None]*(n_neg - len(dw_vals))

    # 10) Mostrar tablas en pestañas con color en celdas
    tab1, tab2 = st.tabs(["Top 5 Positivas","Top 5 Negativas"])
    with tab1:
        sty_pos = df_pos.style.applymap(
            lambda v: 'color: green;',
            subset=['Racha Positiva','Maximo Drawup']
        )
        st.dataframe(sty_pos, use_container_width=True)
    with tab2:
        sty_neg = df_neg.style.applymap(
            lambda v: 'color: red;',
            subset=['Racha Negativa','Maximo Drawdown']
        )
        st.dataframe(sty_neg, use_container_width=True)
