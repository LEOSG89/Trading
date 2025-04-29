import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def comparativo_profit_dia_semana(df: pd.DataFrame, chart_key: str = "profit_dia_semana") -> None:
    if 'Día' not in df.columns or 'Profit' not in df.columns or 'C&P' not in df.columns:
        st.warning("Faltan columnas necesarias ('Día', 'Profit' o 'C&P') en el DataFrame.")
        return

    df = df.copy()
    df = df[df['C&P'].str.strip() != ""]  # excluir depósitos/retiros

    dias_orden = ['Lu', 'Ma', 'Mi', 'Ju', 'Vi', 'Sa', 'Do']
    df = df[df['Día'].isin(dias_orden)]

    resumen = df.groupby('Día')['Profit'].sum().reindex(dias_orden).fillna(0)
    colores = ['green' if val >= 0 else 'red' for val in resumen]

    fig = go.Figure(go.Bar(
        x=resumen.index,
        y=resumen.values,
        marker_color=colores,
        hovertemplate='Día: %{x}<br>Profit Total: %{y}<extra></extra>'
    ))

    fig.update_layout(
        title="Profit Total por Día de la Semana",
        xaxis_title="Día",
        yaxis_title="Profit Total",
        height=400,
        width=900,
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True, key=chart_key) 