import streamlit as st
import pandas as pd
import plotly.graph_objects as go


def comparativo_dona_call_put(df: pd.DataFrame, chart_key: str = "dona_dual") -> None:
    if 'C&P' not in df.columns or 'Profit' not in df.columns:
        st.warning("Faltan columnas necesarias ('C&P' o 'Profit') en el DataFrame.")
        return

    df = df.copy()
    df = df[df['Profit'] != 0]

    col1, col2, col3 = st.columns(3)

    for tipo, color, col in [('CALL', 'green', col1), ('PUT', 'red', col2)]:
        df_tipo = df[df['C&P'].str.upper() == tipo]
        ganadas = (df_tipo['Profit'] > 0).sum()
        perdidas = (df_tipo['Profit'] < 0).sum()
        total = ganadas + perdidas

        if total == 0:
            with col:
                st.info(f"No hay suficientes datos para {tipo}.")
            continue

        porcentaje = round((ganadas / total) * 100, 1)

        fig = go.Figure(go.Pie(
            labels=['Ganadas', 'Perdidas'],
            values=[ganadas, perdidas],
            hole=0.6,
            marker_colors=[color, 'rgba(0,0,0,0)'],
            textinfo='none',
            hoverinfo='label+percent+value'
        ))

        fig.update_layout(
            title_text=f"% Aciertos - {tipo}",
            title_font_size=14,
            annotations=[dict(text=f"{porcentaje}%", x=0.5, y=0.5, font_size=24, font_color=color, showarrow=False)],
            showlegend=False,
            height=400,
            width=300
        )

        with col:
            st.plotly_chart(fig, use_container_width=True, key=f"{chart_key}_{tipo.lower()}")
            st.markdown(f"**Total {tipo}:** {total} operaciones")

    # Gráfico adicional de distribución total de operaciones
    df_call = df[df['C&P'].str.upper() == 'CALL']
    df_put = df[df['C&P'].str.upper() == 'PUT']
    total_ops = len(df_call) + len(df_put)

    if total_ops > 0:
        valores = [len(df_call), len(df_put)]
        etiquetas = ['CALL', 'PUT']
        colores = ['green', 'red']

        fig_total = go.Figure(go.Pie(
            labels=etiquetas,
            values=valores,
            hole=0.5,
            marker_colors=colores,
            textinfo='percent',
            hoverinfo='label+value+percent'
        ))

        fig_total.update_layout(
            title_text="     CALL vs PUT",
            title_font_size=14,
            showlegend=False,
            height=400,
            width=300
        )

        with col3:
            st.plotly_chart(fig_total, use_container_width=True, key=f"{chart_key}_total")
            st.markdown(f"**CALL:** {valores[0]} ({round((valores[0]/total_ops)*100, 1)}%)  |  **PUT:** {valores[1]} ({round((valores[1]/total_ops)*100, 1)}%)")
