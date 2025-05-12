import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st
import os
import json
import re

def mostrar_tiempo_puntos(df: pd.DataFrame, chart_key: str) -> None:
    # 1) Validar columnas
    for col in ['T. Op', 'Profit', 'Deposito', 'Retiro']:
        if col not in df.columns:
            st.warning(f"Falta la columna requerida: '{col}'.")
            return

    # 2) Estilos
    st.markdown("""
    <style>
    [data-testid="column"] { padding:0 !important; margin:0 !important; }
    .stCheckbox>div { margin-bottom:0.2rem; }
    .stCheckbox input[type="checkbox"] { margin:0 4px 0 0; transform:scale(1.3); }
    </style>
    """, unsafe_allow_html=True)

    # 3) Índices y archivos de configuración
    df_idx      = list(df.index)
    settings    = f"{chart_key}_excl.json"
    points_file = f"{chart_key}_excl_puntos.json"

    # Cargar configuración previa
    if os.path.exists(settings):
        with open(settings, 'r') as f:
            excl_data = json.load(f) or {}
    else:
        excl_data = {}
    excl_data.setdefault('deposito', False)
    excl_data.setdefault('retiro',   False)
    excl_data.setdefault('cero',     False)
    excl_data.setdefault('positivo', False)
    excl_data.setdefault('negativo', False)

    # Excluir puntos manuales
    if os.path.exists(points_file):
        excl_points = json.load(open(points_file)) or []
    else:
        excl_points = []
    excl_points = [i for i in excl_points if i in df_idx]

    # 4) Convertir 'T. Op' a minutos y preparar formato
    tiempo_str = df['T. Op'].astype(str)
    def to_min(t):
        d = int(re.search(r"(\d+)d", t).group(1)) if re.search(r"(\d+)d", t) else 0
        h = int(re.search(r"(\d+)h", t).group(1)) if re.search(r"(\d+)h", t) else 0
        m = int(re.search(r"(\d+)m", t).group(1)) if re.search(r"(\d+)m", t) else 0
        return d*1440 + h*60 + m
    tiempo_min = tiempo_str.apply(to_min)
    tiempo_fmt = {
        i: f"{tiempo_min[i]//1440}d {((tiempo_min[i]%1440)//60):02d}:{(tiempo_min[i]%60):02d}"
        for i in df_idx
    }

    # 5) Valores numéricos
    profit_num   = pd.to_numeric(df['Profit'].astype(str).str.replace(',', ''), errors='coerce')
    deposito_num = pd.to_numeric(df['Deposito'].astype(str), errors='coerce').fillna(0)
    retiro_num   = pd.to_numeric(df['Retiro'].astype(str), errors='coerce').fillna(0)

    # 6) Crear pestañas
    tabs = st.tabs([
        "Depósitos/Retiros", "Por Color", "Por Puntos",
        "Franja Verde", "Franja Roja", "Franja Amarilla"
    ])

    # 7) Depósitos/Retiros
    with tabs[0]:
        c1, c2 = st.columns(2, gap="small")
        ex_dep = c1.checkbox("Excluir Depósitos", value=excl_data['deposito'], key=f"dep_{chart_key}")
        ex_ret = c2.checkbox("Excluir Retiros",   value=excl_data['retiro'],   key=f"ret_{chart_key}")

    # 8) Por Color
    with tabs[1]:
        c1, c2, c3 = st.columns(3, gap="small")
        ex_cero = c1.checkbox("🟡", value=excl_data['cero'],     key=f"cer_{chart_key}")
        ex_pos  = c2.checkbox("🟢", value=excl_data['positivo'], key=f"pos_{chart_key}")
        ex_neg  = c3.checkbox("🔴", value=excl_data['negativo'], key=f"neg_{chart_key}")

    # 9) Por Puntos manuales
    with tabs[2]:
        excl_points = st.multiselect(
            "Excluir puntos manualmente:", df_idx,
            default=excl_points, key=f"pts_{chart_key}"
        )

    show_dep  = not ex_dep
    show_ret  = not ex_ret
    show_cero = not ex_cero
    show_pos  = not ex_pos
    show_neg  = not ex_neg

    # 10) Bines de 4h para franjas por defecto
    bin_size = 4 * 60
    edges    = np.arange(0, tiempo_min.max() + bin_size, bin_size)

    def get_max_bin(mask):
        datos = [tiempo_min[i] for i in df_idx if mask(i)]
        if not datos:
            return 0
        counts, _ = np.histogram(datos, bins=edges)
        if counts.sum() == 0:
            return 0
        return counts.argmax()

    def get_bin_range(bin_idx):
        if len(edges) < 2:
            return edges[0], edges[0]
        if bin_idx + 1 < len(edges):
            return edges[bin_idx], edges[bin_idx + 1]
        return edges[-2], edges[-1]

    mask_neg  = lambda i: profit_num[i] < 0 and deposito_num[i] == 0 and retiro_num[i] == 0 and i not in excl_points
    mask_pos  = lambda i: profit_num[i] > 0 and deposito_num[i] == 0 and retiro_num[i] == 0 and i not in excl_points
    mask_zero = lambda i: profit_num[i] == 0 and deposito_num[i] == 0 and retiro_num[i] == 0 and i not in excl_points

    bin_pos  = get_max_bin(mask_pos)
    bin_neg  = get_max_bin(mask_neg)
    bin_zero = get_max_bin(mask_zero)

    default_green  = get_bin_range(bin_pos)
    default_red    = get_bin_range(bin_neg)
    default_yellow = get_bin_range(bin_zero)

    # 11) Slider Franjas (con chequeo de valores por defecto)
    def create_slider(tab, label, key, default_range):
        with tab:
        # 1) Generar opciones formateadas
            opts = [
                f"{int(e//1440)}d {int((e%1440)//60):02d}:{int(e%60):02d}"
                for e in edges
            ]

        # 2) Cadena formateada de default_range
            low_str  = f"{int(default_range[0]//1440)}d {int((default_range[0]%1440)//60):02d}:{int(default_range[0]%60):02d}"
            high_str = f"{int(default_range[1]//1440)}d {int((default_range[1]%1440)//60):02d}:{int(default_range[1]%60):02d}"

        # 3) Si ambos son cero, no crear slider
            if default_range[0] == 0 and default_range[1] == 0:
                st.markdown(f"**{label}**: {low_str}")
                return (low_str, high_str)

        # 4) Recuperar valores previos o usar los por defecto
            raw_def = excl_data.get(key, (low_str, high_str))
            start   = raw_def[0] if raw_def[0] in opts else low_str
            end     = raw_def[1] if raw_def[1] in opts else high_str

        # 5) Crear el slider
            return st.select_slider(
                label,
                options=opts,
                value=(start, end),
                key=f"slider_{key}_{chart_key}"
            )

    selected_green  = create_slider(tabs[3], "Rango franja verde:",   'green',  default_green)
    selected_red    = create_slider(tabs[4], "Rango franja roja:",    'red',    default_red)
    selected_yellow = create_slider(tabs[5], "Rango franja amarilla:", 'yellow', default_yellow)

    # 12) Convertir labels slider a minutos
    def label_to_min(lbl):
        parts = list(map(int, re.findall(r"(\d+)", lbl)))
        return parts[0]*1440 + parts[1]*60 + parts[2]

    y0_green,  y1_green  = label_to_min(selected_green[0]),  label_to_min(selected_green[1])
    y0_red,    y1_red    = label_to_min(selected_red[0]),    label_to_min(selected_red[1])
    y0_yellow, y1_yellow = label_to_min(selected_yellow[0]), label_to_min(selected_yellow[1])

    # 13) Plot de puntos
    fig = go.Figure()
    if show_dep:
        mask = (deposito_num > 0) & ~pd.Series(df_idx).isin(excl_points)
        xs   = [i for i in df_idx if mask.loc[i]]
        ys   = [tiempo_min[i] for i in xs]
        custom = [[deposito_num[i], tiempo_fmt[i]] for i in xs]
        texts  = [str(deposito_num[i]) for i in xs]
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode='markers+text',
            marker=dict(color='lightblue', size=25),
            text=texts, textposition='middle center', textfont=dict(size=10),
            customdata=custom,
            hovertemplate="Depósito: %{customdata[0]}<br>Tiempo: %{customdata[1]}<br>Índice: %{x}",
            showlegend=False
        ))
    if show_ret:
        mask = (retiro_num > 0) & ~pd.Series(df_idx).isin(excl_points)
        xs   = [i for i in df_idx if mask.loc[i]]
        ys   = [tiempo_min[i] for i in xs]
        custom = [[retiro_num[i], tiempo_fmt[i]] for i in xs]
        texts  = [str(retiro_num[i]) for i in xs]
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode='markers+text',
            marker=dict(color='pink', size=25),
            text=texts, textposition='middle center', textfont=dict(size=10),
            customdata=custom,
            hovertemplate="Retiro: %{customdata[0]}<br>Tiempo: %{customdata[1]}<br>Índice: %{x}",
            showlegend=False
        ))
    for cond, show, col in [
        (profit_num == 0, show_cero,   'yellow'),
        (profit_num > 0, show_pos,     'green'),
        (profit_num < 0, show_neg,     'red')
    ]:
        if show:
            mask = cond & (deposito_num == 0) & (retiro_num == 0) & ~pd.Series(df_idx).isin(excl_points)
            xs   = [i for i in df_idx if mask.loc[i]]
            ys   = [tiempo_min[i] for i in xs]
            custom = [[profit_num[i], tiempo_fmt[i]] for i in xs]
            texts  = [str(int(profit_num[i])) for i in xs]
            fig.add_trace(go.Scatter(
                x=xs, y=ys, mode='markers+text',
                marker=dict(color=col, size=25),
                text=texts, textposition='middle center', textfont=dict(size=10),
                customdata=custom,
                hovertemplate="Profit: %{customdata[0]}<br>Tiempo: %{customdata[1]}<br>Índice: %{x}",
                showlegend=False
            ))

    # 14) Franjas
    for y0, y1, color in [
        (y0_green,  y1_green,  'green'),
        (y0_red,    y1_red,    'red'),
        (y0_yellow, y1_yellow, 'yellow'),
    ]:
        fig.add_shape(
            type='rect', xref='paper', x0=0, x1=1, yref='y',
            y0=y0, y1=y1, fillcolor=color,
            opacity=0.2, layer='below', line_width=0
        )

    # 15) Persistencia
    excl_data.update({
        'deposito': ex_dep, 'retiro': ex_ret,
        'cero': ex_cero,   'positivo': ex_pos, 'negativo': ex_neg,
        'green': selected_green,
        'red':   selected_red,
        'yellow':selected_yellow
    })
    with open(settings, 'w') as f:
        json.dump(excl_data, f)
    with open(points_file, 'w') as f:
        json.dump(excl_points, f)

    # Mostrar figura
    fig.update_layout(
        xaxis_title='Índice', yaxis_title='Tiempo (min)',
        template='plotly_dark', showlegend=False,
        margin=dict(t=40, b=40, l=40, r=40)
    )
    st.plotly_chart(fig, use_container_width=True, key=f"{chart_key}_tiempo")

