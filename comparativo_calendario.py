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
    return {}


def save_filters(chart_key: str, filters: dict) -> None:
    fn = f"{chart_key}_filters.json"
    serializable = {k: (int(v) if isinstance(v, int) else str(v)) for k, v in filters.items()}
    json.dump(serializable, open(fn, 'w'))


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

    summary = pd.concat([profit, trades, deposits], axis=1).fillna(0)
    if base_year in summary.index:
        summary.at[base_year, 'Depósitos'] -= base_amount

    summary = summary.sort_index()
    capital = base_amount
    pct = []
    for y, row in summary.iterrows():
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

    df2 = df[df['Fecha'] >= first_dep['Fecha']]
    ops = df2[df2['Deposito'] == 0]
    g = ops.groupby(['year', 'month'])['Profit'].agg(PnL='sum', Trades='count')
    deps = df2.groupby(['year', 'month'])['Deposito'].sum().rename('Depósitos')
    summary = pd.concat([g, deps], axis=1).fillna(0).sort_index()

    # En el primer mes dejamos el total de depósitos tal como viene (incluye el depósito inicial y otros adicionales)
    # Eliminamos la asignación a cero para mostrar correctamente el total de depósitos del mes inicial
    # first_year = first_dep['Fecha'].year
    # first_month = first_dep['Fecha'].month
    # if (first_year, first_month) in summary.index:
    #     summary.at[(first_year, first_month), 'Depósitos'] = 0

    capital = base_amount
    pct_list = []
    for (y, m), row in summary.iterrows():
        capital += row['Depósitos']
        pct_list.append(round((row['PnL'] / capital * 100) if capital else 0, 2))
        capital += row['PnL']
    summary['% Var'] = pct_list

    df_sum = summary.reset_index().rename(columns={'year': 'Año', 'month': 'MesNum'})
    df_sum['Mes'] = df_sum['MesNum'].map(month_names)
    return df_sum[['Año', 'MesNum', 'Mes', 'PnL', 'Trades', 'Depósitos', '% Var']][['Año', 'MesNum', 'Mes', 'PnL', 'Trades', 'Depósitos', '% Var']]


def calculate_daily(df: pd.DataFrame, year: int, month: int, asset: str, tipo: str) -> tuple[pd.DataFrame, float]:
    # Obtén el depósito inicial y su fecha
    df_dep = df[df['Deposito'] > 0].sort_values('Fecha')
    if df_dep.empty:
        st.warning("No hay depósito inicial para calcular diario.")
        return pd.DataFrame(columns=['Fecha','profit','trades','pct']), 0.0
    first_dep = df_dep.iloc[0]
    dep_year = first_dep['Fecha'].year
    dep_month = first_dep['Fecha'].month
    base_amount = first_dep['Deposito']

    # Capital de inicio para el mes
    if year == dep_year and month == dep_month:
        # Primer mes: capital inicial más todos los depósitos de ese mes
        mask_month = df_dep['Fecha'].apply(lambda d: d.year == year and d.month == month)
        total_deps = df_dep.loc[mask_month, 'Deposito'].sum()
        cap_start = total_deps
    else:
        # Mes posterior: capital inicial + ganancias previas
        first_of_month = date(year, month, 1)
        prev_profit = df[(df['Fecha'] >= first_dep['Fecha']) & \
                         (df['Fecha'] < first_of_month) & (df['Deposito'] == 0)]['Profit'].sum()
        cap_start = base_amount + prev_profit

    # Filtrado de operaciones del mes
    mask = (df['year'] == year) & (df['month'] == month)
    if asset:
        mask &= df['Activo'] == asset
    if tipo.upper() != 'AMBAS':
        mask &= df['C&P'] == tipo.upper()

    monthly_ops = df[mask & (df['Deposito'] == 0)]
    # Cálculo diario
    daily = (
        monthly_ops
        .groupby('Fecha')['Profit']
        .agg(profit='sum', trades='count')
        .reset_index().sort_values('Fecha')
    )

    cap = cap_start
    pct_list = []
    for _, row in daily.iterrows():
        pct = (row['profit'] / cap * 100) if cap else 0
        pct_list.append(round(pct, 1))
        cap += row['profit']
    daily['pct'] = pct_list
    return daily, cap_start


def render_calendar(daily: pd.DataFrame, year: int, month: int) -> None:
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
            if row:
                txt = f"{wd} {d}<br>${row['profit']:,.0f}<br>{row['trades']} ops<br>{row['pct']:+.1f}%"
                color = 'green' if row['pct']>0 else 'red' if row['pct']<0 else '#888'
            else:
                txt = f"{wd} {d}"
                color = '#888'
            fig.add_annotation(x=di, y=wi+0.5, text=txt,
                               showarrow=False, font=dict(size=12, color=color),
                               align='center', yanchor='middle')
    fig.update_xaxes(range=[-0.5,6.5], tickmode='array',
                     tickvals=list(range(7)), ticktext=weekday_names,
                     side='top', showgrid=False, zeroline=False)
    fig.update_yaxes(range=[n_weeks,0], showgrid=False, zeroline=False, showticklabels=False)
    fig.update_layout(height=n_weeks*100+100, margin=dict(l=20,r=20,t=20,b=20),
                      plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar':False})


def mostrar_calendario(df_raw: pd.DataFrame, chart_key: str = "calendario") -> None:
    df = clean_data(df_raw)
    saved = load_filters(chart_key)
    summary_annual = summary_by_year(df)
    summary_monthly = summary_all_years(df)

    tabs = st.tabs(["Años","Res Anual","Res Mensual","Mes","Activo","Tipo Op"])
    # Año
    with tabs[0]:
        years = sorted(df['year'].unique())
        if not years:
            st.warning("No hay datos de años disponibles.")
            return
        default_year = saved.get('year', None)
        if default_year not in years:
            default_year = years[-1]
        year = st.selectbox("Selecciona Año", years, index=years.index(default_year), key=f"{chart_key}_year")
    # Pestaña Anual
    with tabs[1]:
        if summary_annual is not None:
            st.dataframe(
                summary_annual.style
                    .format({'PnL':'${:,.2f}','Depósitos':'${:,.2f}','% Var':'{:+.2f}%'} )
                    .applymap(lambda v: 'color: green' if isinstance(v,(int,float)) and v>0 else 'color: red' if isinstance(v,(int,float)) and v<0 else '')
            )
    # Pestaña Mensual
    with tabs[2]:
        if summary_monthly is not None:
            st.dataframe(
                summary_monthly.style
                    .format({'PnL':'${:,.2f}','Depósitos':'${:,.2f}','% Var':'{:+.2f}%'} )
                    .applymap(lambda v: 'color: green' if isinstance(v,(int,float)) and v>0 else 'color: red' if isinstance(v,(int,float)) and v<0 else '')
            )
    # Mes, Activo, Tipo tabs como antes
    with tabs[3]:
        months = sorted(df[df['year']==year]['month'].unique())
        default_month = saved.get('month', None)
        if default_month not in months:
            default_month = months[0] if months else None
        month = st.selectbox("Selecciona Mes", months, index=months.index(default_month), format_func=lambda m: month_names[m], key=f"{chart_key}_month")
    with tabs[4]:
        assets = sorted(df['Activo'].unique())
        default_asset = saved.get('asset', None)
        if default_asset not in assets:
            default_asset = assets[0] if assets else None
        asset = st.selectbox("Selecciona Activo", assets, index=assets.index(default_asset), key=f"{chart_key}_asset")
    with tabs[5]:
        tipos = ["AMBAS","CALL","PUT"]
        default_tipo = saved.get('tipo','AMBAS').upper()
        if default_tipo not in tipos:
            default_tipo = 'AMBAS'
        tipo = st.selectbox("Selecciona Tipo Op", tipos, index=tipos.index(default_tipo), key=f"{chart_key}_tipo")

    save_filters(chart_key, {'year':year,'month':month,'asset':asset,'tipo':tipo})

    daily_df, cap_start = calculate_daily(df, year, month, asset, tipo)
    render_calendar(daily_df, year, month)

    # Métricas como antes...
    profit_mes = daily_df['profit'].sum()
    trades_mes = int(daily_df['trades'].sum())
    if summary_monthly is not None and ((summary_monthly['Año']==year)&(summary_monthly['MesNum']==month)).any():
        pct_mes = summary_monthly[(summary_monthly['Año']==year)&(summary_monthly['MesNum']==month)]['% Var'].iloc[0]
    else:
        pct_mes = (profit_mes/cap_start*100) if cap_start else 0
    c1,c2,c3 = st.columns(3)
    c1.metric('P&L Mes',f"${profit_mes:,.2f}")
    c2.metric('Trades Mes',f"{trades_mes}")
    c3.metric('Incremento Mes',f"{pct_mes:+.1f}%")

    if summary_annual is not None and year in summary_annual['Año'].values:
        row_yr = summary_annual[summary_annual['Año']==year].iloc[0]
        c4,c5,c6 = st.columns(3)
        c4.metric('P&L Año',f"${row_yr['PnL']:,.2f}")
        c5.metric('Trades Año',f"{int(row_yr['Trades'])}")
        c6.metric('Incremento Año',f"{row_yr['% Var']:+.1f}%")

# Para usar:
#df = pd.read_csv('tus_datos.csv')
#mostrar_calendario(df)
