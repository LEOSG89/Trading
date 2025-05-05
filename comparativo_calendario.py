import os
import json
import calendar
from datetime import date

import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# Mapas de nombres para meses y días
month_names = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}
weekday_names = ["Dom", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"]

@st.cache_data
def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['Fecha / Hora'] = pd.to_datetime(df['Fecha / Hora'], errors='coerce')
    df['Fecha'] = df['Fecha / Hora'].dt.date
    df['year'] = df['Fecha'].apply(lambda d: d.year)
    df['month'] = df['Fecha'].apply(lambda d: d.month)

    df['Profit Tot.'] = pd.to_numeric(
        df['Profit Tot.'].astype(str)
          .str.replace(r'[^\d\.\-]', '', regex=True),
        errors='coerce'
    ).fillna(0)
    for col in ['Profit', 'Deposito', 'Retiro']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    df['C&P'] = df.get('C&P', '').fillna('').astype(str).str.upper()
    df['Activo'] = df.get('Activo', '').fillna('').astype(str)
    return df


def load_filters(chart_key: str) -> dict:
    fn = f"{chart_key}_filters.json"
    if os.path.exists(fn):
        try:
            return json.load(open(fn, 'r'))
        except json.JSONDecodeError:
            st.warning("Filtros corruptos, reinicializando.")
    return {}


def save_filters(chart_key: str, filters: dict) -> None:
    fn = f"{chart_key}_filters.json"
    to_store = {
        'year': int(filters.get('year', 0)),
        'month': int(filters.get('month', 0)),
        'asset': str(filters.get('asset', '')),
        'tipo': str(filters.get('tipo', 'AMBAS'))
    }
    json.dump(to_store, open(fn, 'w'))


def summary_by_year(df: pd.DataFrame) -> pd.DataFrame | None:
    df_dep = df[df['Deposito'] > 0].sort_values('Fecha')
    if df_dep.empty:
        st.warning("No se encontró un depósito inicial para el resumen anual.")
        return None
    first_dep = df_dep.iloc[0]
    base_year = first_dep['Fecha'].year
    base_amount = first_dep['Deposito']

    df2 = df[df['Fecha'] >= first_dep['Fecha']]
    ops = df2[df2['Deposito'] == 0]
    profit = ops.groupby('year')['Profit'].sum().rename('PnL')
    trades = ops.groupby('year')['Profit'].count().rename('Trades')
    deposits = df2.groupby('year')['Deposito'].sum().rename('Depósitos')

    summary = pd.concat([profit, trades, deposits], axis=1).fillna(0).sort_index()
    summary.at[base_year, 'Depósitos'] -= base_amount

    capital = base_amount
    pct = []
    for _, row in summary.iterrows():
        capital += row['Depósitos']
        pct.append(round((row['PnL'] / capital * 100) if capital else 0, 2))
        capital += row['PnL']
    summary['% Var'] = pct
    return summary.reset_index().rename(columns={'year':'Año'})[['Año','PnL','Trades','Depósitos','% Var']]


def summary_all_years(df: pd.DataFrame) -> pd.DataFrame | None:
    df_dep = df[df['Deposito'] > 0].sort_values('Fecha')
    if df_dep.empty:
        st.warning("No se encontró un depósito inicial en el historial.")
        return None
    first_dep = df_dep.iloc[0]
    base_amount = first_dep['Deposito']
    fy, fm = first_dep['Fecha'].year, first_dep['Fecha'].month

    df2 = df[df['Fecha'] >= first_dep['Fecha']]
    ops = df2[df2['Deposito'] == 0]
    g = ops.groupby(['year','month'])['Profit'].agg(PnL='sum', Trades='count')
    deps = df2.groupby(['year','month'])['Deposito'].sum().rename('Depósitos')
    summary = pd.concat([g, deps], axis=1).fillna(0).sort_index()
    summary.at[(fy,fm), 'Depósitos'] -= base_amount

    capital = base_amount
    pct = []
    for _, row in summary.iterrows():
        capital += row['Depósitos']
        pct.append(round((row['PnL'] / capital * 100) if capital else 0, 2))
        capital += row['PnL']
    summary['% Var'] = pct

    df_sum = summary.reset_index().rename(columns={'year':'Año','month':'MesNum'})
    df_sum['Mes'] = df_sum['MesNum'].map(month_names)
    return df_sum[['Año','MesNum','Mes','PnL','Trades','Depósitos','% Var']]


def calculate_daily(df: pd.DataFrame, year:int, month:int, asset:str, tipo:str) -> tuple[pd.DataFrame,float]:
    df_dep = df[df['Deposito']>0].sort_values('Fecha')
    if df_dep.empty:
        st.warning("No hay depósito inicial para calcular diario.")
        return pd.DataFrame(columns=['Fecha','profit','trades','pct']), 0.0
    first_dep = df_dep.iloc[0]
    fy, fm = first_dep['Fecha'].year, first_dep['Fecha'].month
    base_amount = first_dep['Deposito']

    if year == fy and month == fm:
        mask = df_dep['Fecha'].apply(lambda d: d.year == year and d.month == month)
        # Incluir depósito inicial para cálculo correcto de % los primeros días
        cap_start = df_dep.loc[mask, 'Deposito'].sum()
    else:
        first_of_month = date(year, month, 1)
        prev = df[(df['Fecha'] >= first_dep['Fecha']) & (df['Fecha'] < first_of_month) & (df['Deposito'] == 0)]['Profit'].sum()
        cap_start = base_amount + prev

    m = (df['year'] == year) & (df['month'] == month)
    if asset:
        m &= df['Activo'] == asset
    if tipo.upper() != 'AMBAS':
        m &= df['C&P'] == tipo.upper()

    monthly_ops = df[m & (df['Deposito'] == 0)]
    daily = (
        monthly_ops.groupby('Fecha')['Profit']
        .agg(profit='sum', trades='count')
        .reset_index()
        .sort_values('Fecha')
    )

    cap = cap_start
    pct_list = []
    for _, row in daily.iterrows():
        pct = (row['profit'] / cap * 100) if cap else 0
        pct_list.append(round(pct, 1))
        cap += row['profit']
    daily['pct'] = pct_list
    return daily, cap_start


def render_calendar(daily: pd.DataFrame, year:int, month:int) -> None:
    info = daily.set_index('Fecha')[['profit','trades','pct']].to_dict('index')
    matrix = calendar.Calendar(firstweekday=6).monthdayscalendar(year, month)
    n_weeks = len(matrix)
    fig = go.Figure()
    for wi, week in enumerate(matrix):
        for di, d in enumerate(week):
            fig.add_shape(type='rect', x0=di-0.5, x1=di+0.5,
                          y0=wi, y1=wi+1,
                          line=dict(color='rgba(200,200,200,0.1)', width=1),
                          fillcolor='rgba(0,0,0,0)', layer='below')
            if d == 0:
                continue
            dt = date(year, month, d)
            row = info.get(dt)
            wd = weekday_names[di]
            text = f"{wd} {d}" + (f"<br>${row['profit']:,.0f}<br>{row['trades']} ops<br>{row['pct']:+.1f}%" if row else "")
            color = 'green' if row and row['pct'] > 0 else 'red' if row and row['pct'] < 0 else '#888'
            fig.add_annotation(x=di, y=wi+0.5, text=text,
                               showarrow=False, font=dict(size=12, color=color),
                               align='center', yanchor='middle')
    fig.update_xaxes(range=[-0.5,6.5], tickmode='array',
                     tickvals=list(range(7)), ticktext=weekday_names,
                     side='top', showgrid=False, zeroline=False)
    fig.update_yaxes(range=[n_weeks,0], showgrid=False, zeroline=False, showticklabels=False)
    fig.update_layout(height=n_weeks*100+100, margin=dict(l=20,r=20,t=20,b=20),
                      plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar':False})


def mostrar_calendario(df_raw: pd.DataFrame, chart_key:str = "calendario") -> None:
    df = clean_data(df_raw)
    saved = load_filters(chart_key)

    df_dep = df[df['Deposito']>0].sort_values('Fecha')
    if not df_dep.empty:
        first_dep = df_dep.iloc[0]
        fy, fm = first_dep['Fecha'].year, first_dep['Fecha'].month
        base_amount = first_dep['Deposito']
    else:
        fy = fm = base_amount = None

    summary_annual = summary_by_year(df)
    summary_monthly = summary_all_years(df)

    tabs = st.tabs([
        "Años", "Mes", "Activo", "Tipo Op", "Tabla Anual", "Tabla Mensual"
    ])

    with tabs[0]:
        years = sorted(df['year'].unique())
        if not years:
            st.warning("No hay datos de años.")
            return
        saved_year = saved.get('year')
        default_idx = years.index(saved_year) if saved_year in years else len(years)-1
        year = st.selectbox("Año", years, index=default_idx, key=f"{chart_key}_year")

    with tabs[1]:
        months = sorted(df[df['year']==year]['month'].unique())
        if not months:
            st.warning("No hay meses.")
            return
        saved_month = saved.get('month')
        default_midx = months.index(saved_month) if saved_month in months else 0
        month = st.selectbox("Mes", months,
                             index=default_midx,
                             format_func=lambda m: month_names[m],
                             key=f"{chart_key}_month")

    with tabs[2]:
        assets = sorted(df['Activo'].unique())
        saved_asset = saved.get('asset')
        default_aidx = assets.index(saved_asset) if saved_asset in assets else 0
        asset = st.selectbox("Activo", assets, index=default_aidx, key=f"{chart_key}_asset")

    with tabs[3]:
        tipos = ["AMBAS","CALL","PUT"]
        saved_tipo = (saved.get('tipo') or "AMBAS").upper()
        default_tidx = tipos.index(saved_tipo) if saved_tipo in tipos else 0
        tipo = st.selectbox("Tipo Op", tipos, index=default_tidx, key=f"{chart_key}_tipo")

    save_filters(chart_key, {'year':year,'month':month,'asset':asset,'tipo':tipo})

    daily_df, cap_start = calculate_daily(df, year, month, asset, tipo)
    render_calendar(daily_df, year, month)

    profit_mes = daily_df['profit'].sum()
    trades_mes = int(daily_df['trades'].sum())
    pct_mes = (summary_monthly[(summary_monthly['Año']==year)&(summary_monthly['MesNum']==month)]['% Var'].iloc[0]
               if summary_monthly is not None and ((summary_monthly['Año']==year)&(summary_monthly['MesNum']==month)).any()
               else (profit_mes/cap_start*100) if cap_start else 0)
    c1, c2, c3 = st.columns(3)
    c1.metric('P&L Mes', f"${profit_mes:,.2f}")
    c2.metric('Trades Mes', f"{trades_mes}")
    c3.metric('Incremento Mes', f"{pct_mes:+.1f}%")

    if summary_annual is not None and year in summary_annual['Año'].values:
        row = summary_annual[summary_annual['Año']==year].iloc[0]
        c4, c5, c6 = st.columns(3)
        c4.metric('P&L Año', f"${row['PnL']:,.2f}")
        c5.metric('Trades Año', f"{int(row['Trades'])}")
        c6.metric('Incremento Año', f"{row['% Var']:+.1f}%")

    with tabs[4]:
        st.header("Tabla Resumen Anual (incluye depósito inicial)")
        if summary_annual is not None:
            ta = summary_annual.copy()
            ta['Depósitos'] += base_amount or 0
            st.dataframe(ta.style
                          .format({'PnL':'${:,.2f}','Depósitos':'${:,.2f}','% Var':'{:+.2f}%'}))

    with tabs[5]:
        st.header("Tabla Resumen Mensual (incluye depósito inicial)")
        if summary_monthly is not None:
            tm = summary_monthly.copy()
            if (fy, fm) == (year, month):
                tm.loc[(tm['Año']==fy)&(tm['MesNum']==fm), 'Depósitos'] += base_amount or 0
            st.dataframe(tm.style
                          .format({'PnL':'${:,.2f}','Depósitos':'${:,.2f}','% Var':'{:+.2f}%'}))
