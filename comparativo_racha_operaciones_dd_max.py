import streamlit as st
import pandas as pd
import plotly.graph_objects as go


def comparativo_racha_dd_max(df: pd.DataFrame, chart_key: str = "racha_dd_max") -> None:
    # Verificar columnas necesarias
    if 'DD/Max' not in df.columns:
        st.warning("Falta la columna 'DD/Max' en el DataFrame.")
        return
    if 'Profit' not in df.columns:
        st.warning("Falta la columna 'Profit' en el DataFrame.")
        return

    # Preparar DataFrame
    df = df.copy().reset_index(drop=True)
    df["Index"] = df.index

    # Convertir DD/Max a float, sin '%'
    df['dd_val'] = (
        df['DD/Max']
        .astype(str)
        .str.rstrip('%')
        .replace('', '0')
        .astype(float)
    )

    # Detectar rachas en DD/Max
    df['signo_dd'] = df['dd_val'].apply(lambda v: 1 if v > 0 else -1 if v < 0 else 0)
    df['run_id_dd'] = (df['signo_dd'] != df['signo_dd'].shift()).cumsum()

    # Convertir fechas a datetime si existen
    if 'Fecha / Hora' in df.columns:
        df['Fecha / Hora'] = pd.to_datetime(df['Fecha / Hora'], errors='coerce')
    if 'Fecha / Hora de Cierre' in df.columns:
        df['Fecha / Hora de Cierre'] = pd.to_datetime(df['Fecha / Hora de Cierre'], errors='coerce')

    # Análisis cuantitativo de rachas DD/Max, incluyendo Duración
    resumen = (
        df.groupby(['run_id_dd', 'signo_dd'], as_index=False)
          .agg(
            Racha_Ops=('Index', 'count'),
            DD_Maximo_Drawdown=('dd_val', 'min'),
            DD_Maximo_Drawup=('dd_val', 'max'),
            Duracion=('Index', lambda idx: (
                df.loc[idx.max(), 'Fecha / Hora de Cierre'] - df.loc[idx.min(), 'Fecha / Hora']
            ) if 'Fecha / Hora de Cierre' in df.columns and 'Fecha / Hora' in df.columns else pd.Timedelta(0))
        )
    )
    resumen['Media_Ops'] = resumen.groupby('signo_dd')['Racha_Ops'].transform('mean')

    # Top 5 rachas DD/up y DD/dw
    top_pos = resumen[resumen['signo_dd'] == 1].nlargest(5, 'Racha_Ops')
    top_neg = resumen[resumen['signo_dd'] == -1].nlargest(5, 'Racha_Ops')

    # Construir gráfico de rachas (shapes)
    shapes = []
    for run, grupo in df.groupby('run_id_dd'):
        if run not in set(top_pos['run_id_dd']).union(top_neg['run_id_dd']):
            continue
        signo = grupo['signo_dd'].iloc[0]
        shapes.append(dict(
            type='rect', xref='x', yref='paper',
            x0=grupo['Index'].min(), x1=grupo['Index'].max(),
            y0=0, y1=1,
            fillcolor='green' if signo > 0 else 'red',
            opacity=0.1, layer='below', line_width=0
        ))

    fig = go.Figure()
    fig.update_layout(hovermode="x unified", shapes=shapes)

    # Trazas: líneas según DD/Max, puntos según Profit (todas las rachas)
    for run, grupo in df.groupby('run_id_dd'):
        # Color de la línea según DD/Max
        signo_dd = grupo['signo_dd'].iloc[0]
        line_color = 'green' if signo_dd > 0 else 'red' if signo_dd < 0 else 'yellow'

        # Preparar X e Y (incluyendo punto anterior para continuidad)
        if grupo['Index'].iloc[0] > 0:
            prev_idx = grupo['Index'].iloc[0] - 1
            x_vals = [prev_idx] + grupo['Index'].tolist()
            y_vals = [df.loc[prev_idx, 'dd_val']] + grupo['dd_val'].tolist()
        else:
            x_vals = grupo['Index'].tolist()
            y_vals = grupo['dd_val'].tolist()

        # Color de los marcadores según Profit
        profit_vals = df.loc[x_vals, 'Profit']
        marker_colors = [
            'green'  if v > 0 else
            'red'    if v < 0 else
            'yellow'
            for v in profit_vals
        ]

        # Añadir la traza con marcadores más grandes
        fig.add_trace(go.Scatter(
            x=x_vals,
            y=y_vals,
            mode="lines+markers",
            line=dict(color=line_color),
            marker=dict(color=marker_colors, size=12),  # tamaño aumentado
            showlegend=False
        ))

    st.plotly_chart(fig, use_container_width=True, key=chart_key)

    # Funciones de formateo
    def format_pct(v): return f"{v:.2f}%"
    def format_td(td):
        sec = int(td.total_seconds()); d, rem = divmod(sec, 86400)
        h, rem = divmod(rem, 3600); m, _ = divmod(rem, 60)
        return f"{d}d {h:02d}h {m:02d}m" if d else f"{h:02d}h {m:02d}m"

    # Preparar tablas originales con Duración y Media
    df_pos = top_pos[['Racha_Ops','DD_Maximo_Drawdown','DD_Maximo_Drawup','Duracion','Media_Ops']].copy()
    df_neg = top_neg[['Racha_Ops','DD_Maximo_Drawdown','DD_Maximo_Drawup','Duracion','Media_Ops']].copy()

    # Formatear porcentajes, duración y media
    for df_tab in (df_pos, df_neg):
        df_tab['DD_Maximo_Drawdown'] = df_tab['DD_Maximo_Drawdown'].map(format_pct)
        df_tab['DD_Maximo_Drawup']   = df_tab['DD_Maximo_Drawup'].map(format_pct)
        df_tab['Duracion']           = df_tab['Duracion'].map(format_td)
        df_tab['Media_Ops']          = df_tab['Media_Ops'].map(lambda v: f"{v:.2f}")

    # Detectar rachas en Profit para nuevas columnas
    df['signo_pf'] = df['Profit'].apply(lambda v: 1 if v > 0 else -1 if v < 0 else 0)
    df['run_id_pf'] = (df['signo_pf'] != df['signo_pf'].shift()).cumsum()
    resumen_pf = df.groupby(['run_id_pf','signo_pf'], as_index=False).agg(Racha_Profit=('Index','count'))
    top_pf_up = resumen_pf[resumen_pf['signo_pf']==1].nlargest(5,'Racha_Profit')['Racha_Profit'].reset_index(drop=True)
    top_pf_dw = resumen_pf[resumen_pf['signo_pf']==-1].nlargest(5,'Racha_Profit')['Racha_Profit'].reset_index(drop=True)

    # Reiniciar índice para alinear con top_pf
    df_pos.reset_index(drop=True, inplace=True)
    df_neg.reset_index(drop=True, inplace=True)

    # Renombrar encabezados y agregar nuevas columnas
    df_pos.rename(columns={
        'Racha_Ops':          'Racha D.up',
        'DD_Maximo_Drawdown': 'Maximo Drawdown',
        'DD_Maximo_Drawup':   'Maximo Drawup',
        'Media_Ops':          'Media Ops up'
    }, inplace=True)
    rp_up = top_pf_up.tolist()
    rp_up = rp_up[:len(df_pos)] + [None] * max(0, len(df_pos) - len(rp_up))
    df_pos['Racha Positiva'] = rp_up

    df_neg.rename(columns={
        'Racha_Ops':          'Racha D.dw',
        'DD_Maximo_Drawdown': 'Maximo Drawdown',
        'DD_Maximo_Drawup':   'Maximo Drawup',
        'Media_Ops':          'Media Ops dw'
    }, inplace=True)
    rp_dw = top_pf_dw.tolist()
    rp_dw = rp_dw[:len(df_neg)] + [None] * max(0, len(df_neg) - len(rp_dw))
    df_neg['Racha Negativa'] = rp_dw

    # Mostrar en pestañas con colores
    tab1, tab2 = st.tabs(["Top 5 Positivas", "Top 5 Negativas"])
    with tab1:
        sty_pos = df_pos.style.applymap(lambda v: 'color: green;', subset=['Racha Positiva', 'Maximo Drawup'])
        st.dataframe(sty_pos, use_container_width=True)
    with tab2:
        sty_neg = df_neg.style.applymap(lambda v: 'color: red;', subset=['Racha Negativa', 'Maximo Drawdown'])
        st.dataframe(sty_neg, use_container_width=True)
