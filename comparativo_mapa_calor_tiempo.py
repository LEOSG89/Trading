import pandas as pd
import plotly.graph_objects as go
import streamlit as st

def mostrar_heatmaps_dia_hora(df: pd.DataFrame, chart_key: str):
    # 1) COLUMNAS NECESARIAS
    if not {'Fecha / Hora', 'Profit', 'C&P'}.issubset(df.columns):
        st.warning("Tu DataFrame debe tener las columnas 'Fecha / Hora', 'Profit' y 'C&P'.")
        return

    # 2) FILTRO CALL / PUT / AMBAS
    tipo = st.selectbox(
        "Filtrar por tipo de operación:",
        ["Ambas", "CALL", "PUT"],
        key=f"filtro_{chart_key}"
    )
    df_filtrado = df.copy()
    if tipo == "CALL":
        df_filtrado = df_filtrado[
            df_filtrado['C&P'].astype(str).str.strip().str.upper() == 'CALL'
        ]
    elif tipo == "PUT":
        df_filtrado = df_filtrado[
            df_filtrado['C&P'].astype(str).str.strip().str.upper() == 'PUT'
        ]

    # 3) EXTRAER DÍA y HORA
    df_filtrado['Fecha / Hora'] = pd.to_datetime(df_filtrado['Fecha / Hora'])
    df_filtrado['Day']  = df_filtrado['Fecha / Hora'].dt.day_name()
    df_filtrado['Hour'] = df_filtrado['Fecha / Hora'].dt.hour

    def make_pivot(subdf: pd.DataFrame) -> pd.DataFrame:
        p = subdf.groupby(['Day','Hour']).size().unstack(fill_value=0)
        return p.reindex(
            ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'],
            fill_value=0
        )

    # 4) PREPARAMOS HEATMAPS: todas, ganadoras y perdedoras
    pivots = {
        "Todas":      make_pivot(df_filtrado),
        "Ganadoras":  make_pivot(df_filtrado[df_filtrado['Profit'] > 0]),
        "Perdedoras": make_pivot(df_filtrado[df_filtrado['Profit'] < 0]),
    }

    # 5) MOSTRAR HEATMAPS EN PESTAÑAS
    tabs = st.tabs(list(pivots.keys()))
    for tab, (titulo, pivot) in zip(tabs, pivots.items()):
        with tab:
            fig = go.Figure(go.Heatmap(
                z=pivot.values,
                x=pivot.columns,
                y=pivot.index,
                colorscale='Viridis',
                colorbar=dict(title="# Ops")
            ))
            ticktext = [f"{(h%12 or 12)}{'AM' if h<12 else 'PM'}" for h in pivot.columns]
            fig.update_xaxes(tickmode='array', tickvals=list(pivot.columns), ticktext=ticktext)
            fig.data[0].customdata = [ticktext] * len(pivot.index)
            fig.data[0].hovertemplate = (
                "Día: %{y}<br>"
                "Hora: %{customdata}<br>"
                "Operaciones: %{z}<extra></extra>"
            )
            fig.update_layout(
                title=f"{titulo} — {tipo}",
                xaxis_title="Hora",
                yaxis_title="Día de la Semana",
                template="plotly_dark"
            )
            st.plotly_chart(fig, use_container_width=True, key=f"{chart_key}_{titulo}")

    # 6) PREPARAMOS TABLAS DE RESUMEN Y TOP 3
    total = len(df_filtrado)
    w = (df_filtrado['Profit'] > 0).sum()
    l = (df_filtrado['Profit'] < 0).sum()
    wr = (w/total*100) if total else 0
    summary_global = pd.DataFrame({
        "Métrica": ["Total ops","Ganadoras","Perdedoras","Win rate (%)"],
        "Valor":   [total, w, l, round(wr,1)]
    })
    top_days = df_filtrado['Day'].value_counts().nlargest(3)
    days_global = pd.DataFrame({"Día": top_days.index, "Operaciones": top_days.values})
    top_hours = df_filtrado['Hour'].value_counts().nlargest(3)
    hours_global = pd.DataFrame({
        "Hora": [f"{(h%12 or 12)}{'AM' if h<12 else 'PM'}" for h in top_hours.index],
        "Operaciones": top_hours.values
    })

    # 7) TABLAS CALL y PUT INDEPENDIENTES
    df_all = df.copy()
    df_all['Fecha / Hora'] = pd.to_datetime(df_all['Fecha / Hora'])
    df_all['Day']  = df_all['Fecha / Hora'].dt.day_name()
    df_all['Hour'] = df_all['Fecha / Hora'].dt.hour

    def gen(subdf):
        t = len(subdf)
        w = (subdf['Profit'] > 0).sum()
        l = (subdf['Profit'] < 0).sum()
        wr = (w/t*100) if t else 0
        sum_df = pd.DataFrame({
            "Métrica": ["Total ops","Ganadoras","Perdedoras","Win rate (%)"],
            "Valor":   [t, w, l, round(wr,1)]
        })
        td = subdf['Day'].value_counts().nlargest(3)
        days_df = pd.DataFrame({"Día": td.index, "Operaciones": td.values})
        th = subdf['Hour'].value_counts().nlargest(3)
        hours_df = pd.DataFrame({
            "Hora":[f"{(h%12 or 12)}{'AM' if h<12 else 'PM'}" for h in th.index],
            "Operaciones": th.values
        })
        return sum_df, days_df, hours_df

    sum_call, days_call, hours_call = gen(df_all[df_all['C&P'].str.upper()=="CALL"])
    sum_put,  days_put,  hours_put  = gen(df_all[df_all['C&P'].str.upper()=="PUT"])

    # 8) SEIS PESTAÑAS DE TABLAS
    tabs2 = st.tabs([
        "Resumen",
        "Top 3 Días",
        "Top 3 Horas",
        "Resumen CALL/PUT",
        "Top 3 Días CALL/PUT",
        "Top 3 Horas CALL/PUT"
    ])

    # (1) Resumen global
    with tabs2[0]:
        st.table(summary_global)

    # (2) Top 3 Días global
    with tabs2[1]:
        st.table(days_global)

    # (3) Top 3 Horas global
    with tabs2[2]:
        st.table(hours_global)

    # (4) Resumen CALL / PUT lado a lado
    with tabs2[3]:
        col1, col2 = st.columns(2, gap="large")
        with col1:
            st.header("CALL")
            st.table(sum_call)
        with col2:
            st.header("PUT")
            st.table(sum_put)

    # (5) Top 3 Días CALL / PUT lado a lado
    with tabs2[4]:
        col1, col2 = st.columns(2, gap="large")
        with col1:
            st.header("CALL")
            st.table(days_call)
        with col2:
            st.header("PUT")
            st.table(days_put)

    # (6) Top 3 Horas CALL / PUT lado a lado
    with tabs2[5]:
        col1, col2 = st.columns(2, gap="large")
        with col1:
            st.header("CALL")
            st.table(hours_call)
        with col2:
            st.header("PUT")
            st.table(hours_put) 
