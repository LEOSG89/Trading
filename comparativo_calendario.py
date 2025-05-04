import os
import json
import calendar
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

month_names = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}
weekday_names = ["Dom", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"]

def mostrar_calendario(df: pd.DataFrame, chart_key: str = "calendario"):
    # 1) Preparamos datos
    df = df.copy().reset_index(drop=True)
    df['Fecha'] = pd.to_datetime(df['Fecha / Hora']).dt.date

    # 2) Cargamos filtros previos
    filters_file = f"{chart_key}_filters.json"
    saved = {}
    if os.path.exists(filters_file):
        try:
            with open(filters_file, 'r') as f:
                saved = json.load(f)
        except:
            saved = {}

    # 3) UI de filtros en pestañas: Años, Todos los años, Mes, Activo, Tipo Op
    tab_anyo, tab_anyo_all, tab_mes, tab_activo, tab_tipo = st.tabs(
        ["Años", "Todos los años", "Mes", "Activo", "Tipo Op"]
    )

    # — Pestaña “Años”: selector de año —
    with tab_anyo:
        years = sorted(df['Fecha'].apply(lambda d: d.year).unique())
        st.selectbox(
            "Selecciona Año",
            years,
            index=years.index(saved.get("year", years[-1])),
            key=f"{chart_key}_year"
        )

    # — Pestaña “Todos los años”: tabla resumen anual —
    with tab_anyo_all:
        df_anyo = df.copy()
        df_anyo['MesNum'] = df_anyo['Fecha'].apply(lambda d: d.month)
        df_year = df_anyo.groupby('MesNum').agg(
            profit=('Profit', 'sum'),
            trades=('Profit', 'size')
        ).reset_index()
        df_year['% Var'] = df_year['profit'].pct_change().mul(100).round(1).fillna(0)
        disp = df_year.rename(columns={
            'MesNum': 'Mes', 'profit': 'P&L', 'trades': 'Trades'
        })
        disp['Mes'] = disp['Mes'].map(month_names)
        st.dataframe(
            disp[['Mes', 'P&L', 'Trades', '% Var']]
               .style
               .format({'P&L':'${:,.2f}', '% Var':'{:+.1f}%'})
               .applymap(lambda v: (
                   'color: green' if isinstance(v, (int, float)) and v > 0 else
                   'color: red'   if isinstance(v, (int, float)) and v < 0 else
                   ''
               ))
        )

    # — Pestaña “Mes”: selector de mes según el año —
    with tab_mes:
        sel_year = st.session_state.get(f"{chart_key}_year", years[-1])
        months = sorted(
            df[df['Fecha'].apply(lambda d: d.year) == sel_year]['Fecha']
              .apply(lambda d: d.month)
              .unique()
        )
        st.selectbox(
            "Selecciona Mes",
            months,
            index=months.index(saved.get("month", months[0])),
            format_func=lambda m: month_names[m],
            key=f"{chart_key}_month"
        )

    # — Pestaña “Activo” —
    with tab_activo:
        activos = sorted(df['Activo'].unique())
        st.selectbox(
            "Selecciona Activo",
            activos,
            index=activos.index(saved.get("asset", activos[0])),
            key=f"{chart_key}_asset"
        )

    # — Pestaña “Tipo Op” —
    with tab_tipo:
        tipos = ["Ambas", "CALL", "PUT"]
        st.selectbox(
            "Selecciona Tipo Op",
            tipos,
            index=tipos.index(saved.get("tipo", "Ambas")),
            key=f"{chart_key}_tipo"
        )

    # 4) Guardar filtros en JSON
    with open(filters_file, 'w') as f:
        json.dump({
            "year":  int(st.session_state[f"{chart_key}_year"]),
            "month": int(st.session_state[f"{chart_key}_month"]),
            "asset": st.session_state[f"{chart_key}_asset"],
            "tipo":  st.session_state[f"{chart_key}_tipo"]
        }, f)

    # 5) Aplicar filtros para el mes actual
    year  = st.session_state[f"{chart_key}_year"]
    month = st.session_state[f"{chart_key}_month"]
    asset = st.session_state[f"{chart_key}_asset"]
    tipo  = st.session_state[f"{chart_key}_tipo"]

    mask = (
        (df['Fecha'].apply(lambda d: d.year)  == year) &
        (df['Fecha'].apply(lambda d: d.month) == month) &
        (df['Activo'] == asset)
    )
    if tipo != "Ambas":
        mask &= (df['C&P'].str.upper() == tipo)
    mdf = df[mask]

    # Métricas diarias (para el calendario)
    daily = (
        mdf.groupby('Fecha')
           .agg(profit=('Profit','sum'), trades=('Profit','size'))
           .sort_index()
           .reset_index()
    )
    daily['pct'] = daily['profit'].pct_change().mul(100).round(1).fillna(0)
    info = {row['Fecha']: row for _, row in daily.iterrows()}

    # Matriz del mes
    cal = calendar.Calendar(firstweekday=6)
    matrix = cal.monthdayscalendar(year, month)
    n_weeks = len(matrix)

    # Gráfico de calendario
    fig = go.Figure()
    for wi in range(n_weeks):
        for di in range(7):
            fig.add_shape(
                type="rect",
                x0=di-0.5, x1=di+0.5,
                y0=wi, y1=wi+1,
                line=dict(color="rgba(200,200,200,0.009)", width=1),
                fillcolor="rgba(0,0,0,0)",
                layer="below"
            )
    base_font = 12; yoff = 0.5
    for wi, week in enumerate(matrix):
        for di, d in enumerate(week):
            if d == 0: continue
            date = pd.to_datetime(f"{year}-{month:02d}-{d:02d}").date()
            wd = weekday_names[di]
            row = info.get(date)
            if row is not None:
                txt = f"{wd} {d}<br>${row['profit']:,.0f}<br>{int(row['trades'])} ops<br>{row['pct']:+.1f}%"
                color = "green" if row['profit'] > 0 else ("red" if row['profit'] < 0 else "yellow")
            else:
                txt = f"{wd} {d}"; color = "#888"
            fig.add_annotation(
                x=di, y=wi + yoff,
                text=txt, showarrow=False,
                font=dict(size=base_font, color=color),
                align="center", yanchor="middle"
            )
    fig.update_xaxes(
        range=[-0.5, 6.5],
        tickmode="array", tickvals=list(range(7)),
        ticktext=weekday_names, side="top",
        showgrid=False, zeroline=False,
        showticklabels=True, tickfont=dict(size=12),
        ticklabelposition="outside top"
    )
    fig.update_yaxes(
        range=[n_weeks, 0],
        scaleanchor="x",
        showgrid=False, zeroline=False,
        showticklabels=False
    )
    fig.update_layout(
        height=n_weeks*100 + 100,
        margin=dict(l=20, r=20, t=20, b=20),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # 6) Resumen mensual con % incremento vs mes anterior
    # --- calculamos P&L actual ---
    cur_profit = mdf['Profit'].sum()
    # --- filtramos mes anterior ---
    prev_year  = year if month > 1 else year - 1
    prev_month = month - 1 if month > 1 else 12
    mask_prev = (
        (df['Fecha'].apply(lambda d: d.year)  == prev_year) &
        (df['Fecha'].apply(lambda d: d.month) == prev_month) &
        (df['Activo'] == asset)
    )
    if tipo != "Ambas":
        mask_prev &= (df['C&P'].str.upper() == tipo)
    prev_profit = df[mask_prev]['Profit'].sum()
    # --- evitamos división por cero ---
    if prev_profit != 0:
        inc = (cur_profit - prev_profit) / abs(prev_profit) * 100
    else:
        inc = 0.0

    c1, c2, c3 = st.columns(3)
    c1.metric("P&L Mes",    f"${cur_profit:,.2f}")
    c2.metric("Trades Mes", len(mdf))
    c3.metric("Win Rate",   f"{inc:+.1f}%")  # ahora muestra % de incremento vs mes pasado
