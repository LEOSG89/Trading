import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def comparativo_racha_dd_max(df: pd.DataFrame, chart_key: str = "racha_dd_max") -> None:
    # 0) Salida temprana si no hay datos
    if df.empty:
        st.warning("No hay datos disponibles para mostrar Racha Operaciones DD/Max.")
        return

    # 1) Verificar columnas necesarias
    required = {'DD/Max', 'Profit'}
    missing_cols = required - set(df.columns)
    if missing_cols:
        st.warning(f"Faltan columnas necesarias para el cálculo: {', '.join(missing_cols)}.")
        return

    # 2) Preparar DataFrame y conservar índice original
    df = df.copy()
    df['Original_Index'] = df.index
    df.reset_index(drop=True, inplace=True)
    df["Index"] = df.index
    df['es_deposito'] = df.get('Deposito', 0).notna() & (df.get('Deposito', 0) != 0)
    df['es_retiro']   = df.get('Retiro', 0).notna() & (df.get('Retiro', 0) != 0)

    df['dd_val'] = pd.to_numeric(
        df['DD/Max'].astype(str).str.rstrip('%'),
        errors='coerce'
    )


    df['signo_dd'] = df['dd_val'].apply(lambda v: 1 if v>0 else -1 if v<0 else 0)
    df['run_id_dd'] = (df['signo_dd'] != df['signo_dd'].shift()).cumsum()

    for col in ['Fecha / Hora', 'Fecha / Hora de Cierre']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # 3) Resumen de rachas DD/Max
    resumen = (
        df.groupby(['run_id_dd', 'signo_dd'])
          .apply(lambda g: pd.Series({
              'run_id_dd': g['run_id_dd'].iloc[0],
              'signo_dd': g['signo_dd'].iloc[0],
              'Racha_Ops': g.shape[0],
              'DD_Maximo_Drawdown': g['dd_val'].min(),
              'DD_Maximo_Drawup':    g['dd_val'].max(),
              'Duracion': (
                  pd.to_timedelta(
                      g['Fecha / Hora de Cierre'].iloc[-1] 
                      - g['Fecha / Hora'].iloc[0]
                  ) if pd.notna(g['Fecha / Hora de Cierre'].iloc[-1]) 
                        and pd.notna(g['Fecha / Hora'].iloc[0])
                  else pd.Timedelta(0)
              )
          }))
          .reset_index(drop=True)
    )

    # 3.1) Calcular Media_Ops con seguridad
    if resumen.empty:
        resumen['Media_Ops'] = None
    else:
        try:
            resumen['Media_Ops'] = resumen.groupby('signo_dd')['Racha_Ops'].transform('mean')
        except KeyError as e:
            st.warning(f"No se pudo calcular la media de operaciones: {e}")
            resumen['Media_Ops'] = None

    top_pos = resumen[resumen['signo_dd'] == 1].nlargest(5, 'Racha_Ops')
    top_neg = resumen[resumen['signo_dd'] == -1].nlargest(5, 'Racha_Ops')

    # 4) Checkbox para mostrar/ocultar tablas
    mostrar_tablas = st.checkbox("Mostrar tablas de rachas", value=True, key=f"{chart_key}_tbl_chk")

    # 5) Construir gráfico de rachas
    shapes = []
    destacados = set(top_pos['run_id_dd']).union(top_neg['run_id_dd'])
    for run, grupo in df.groupby('run_id_dd'):
        if run in destacados:
            color = 'green' if grupo['signo_dd'].iloc[0] > 0 else 'red'
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

        if grupo['Index'].iloc[0] > 0:
            prev = grupo['Index'].iloc[0] - 1
            x_vals = [prev] + grupo['Index'].tolist()
            y_vals = [df.loc[prev, 'dd_val']] + grupo['dd_val'].tolist()
        else:
            x_vals = grupo['Index'].tolist()
            y_vals = grupo['dd_val'].tolist()

        marker_colors = []
        for idx in x_vals:
            dep  = df.at[idx, 'Deposito'] if 'Deposito' in df.columns else None
            ret  = df.at[idx, 'Retiro']   if 'Retiro' in df.columns else None
            if pd.notna(dep) and dep != 0:
                marker_colors.append('#3399FF')
            elif pd.notna(ret) and ret != 0:
                marker_colors.append('#FF69B4')
            else:
                p = df.at[idx, 'Profit']
                marker_colors.append('green' if p>0 else 'red' if p<0 else 'yellow')

        custom_idx = [df.loc[idx, 'Original_Index'] for idx in x_vals]
        fig.add_trace(go.Scatter(
            x=x_vals,
            y=y_vals,
            mode="lines+markers",
            line=dict(color=line_color),
            marker=dict(color=marker_colors, size=12),
            customdata=custom_idx,
            hovertemplate="Fila real: %{customdata}<br>Valor: %{y:.2f}%<extra></extra>",
            showlegend=False
        ))

    fig.update_layout(
        xaxis_title="Índice de Operación",
        yaxis_title="DD/Max (%)",
        template='plotly_dark',
        height=400
    )
    st.plotly_chart(fig, use_container_width=True, key=chart_key)

    if not mostrar_tablas:
        return

    def fmt_pct(v): return f"{v:.2f}%"
    def fmt_td(td):
        if pd.isna(td): return "NaT"
        days, secs = td.days, td.seconds
        hrs = secs // 3600
        mins = (secs % 3600) // 60
        return f"{days}d {hrs:02d}h {mins:02d}m" if days else f"{hrs:02d}h {mins:02d}m"

    df_pos = top_pos[['Racha_Ops','DD_Maximo_Drawdown','DD_Maximo_Drawup','Duracion','Media_Ops']].copy()
    df_neg = top_neg[['Racha_Ops','DD_Maximo_Drawdown','DD_Maximo_Drawup','Duracion','Media_Ops']].copy()

    for d in (df_pos, df_neg):
        d['DD_Maximo_Drawdown'] = d['DD_Maximo_Drawdown'].map(fmt_pct)
        d['DD_Maximo_Drawup']   = d['DD_Maximo_Drawup'].map(fmt_pct)
        d['Duracion']           = d['Duracion'].map(fmt_td)
        d['Media_Ops']          = d['Media_Ops'].map(lambda v: f"{v:.2f}" if pd.notna(v) else "")

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

    df_pf = df.copy()
    df_pf['signo_pf'] = df_pf['Profit'].apply(lambda v: 1 if v>0 else -1 if v<0 else 0)
    df_pf['run_id_pf'] = (df_pf['signo_pf'] != df_pf['signo_pf'].shift()).cumsum()
    resumen_pf = df_pf.groupby(['run_id_pf','signo_pf'], as_index=False).agg(Racha_Profit=('Index','count'))
    up = resumen_pf[resumen_pf['signo_pf']==1].nlargest(5,'Racha_Profit')['Racha_Profit'].tolist()
    dw = resumen_pf[resumen_pf['signo_pf']==-1].nlargest(5,'Racha_Profit')['Racha_Profit'].tolist()

    n_pos, n_neg = len(df_pos), len(df_neg)
    df_pos['Racha Positiva'] = up[:n_pos] + [None]*(n_pos - len(up))
    df_neg['Racha Negativa'] = dw[:n_neg] + [None]*(n_neg - len(dw))

    tab1, tab2 = st.tabs(["Top 5 Positivas","Top 5 Negativas"])
    with tab1:
        sty_pos = df_pos.style.applymap(lambda _: 'color: green;', subset=['Racha Positiva','Maximo Drawup'])
        st.dataframe(sty_pos, use_container_width=True)
    with tab2:
        sty_neg = df_neg.style.applymap(lambda _: 'color: red;', subset=['Racha Negativa','Maximo Drawdown'])
        st.dataframe(sty_neg, use_container_width=True)
