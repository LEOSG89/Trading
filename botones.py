import streamlit as st
from operations import agregar_operacion, agregar_iv_rank


def crear_botones_trading():
    """
    Crea de forma compacta los botones de trading en una sola fila.
    """
    # Dividir la UI en dos columnas: botones y espacio para la tabla
    colA, colB = st.columns([5, 10], gap="small")
    with colA:
        # CSS para compactar botones y eliminar márgenes
        st.markdown("""
        <style>
        [data-testid="column"] { padding: 0 !important; margin: 0 !important; }
        .stButton>button {
            font-size: 6px !important;
            padding: 0.1rem 0.3rem !important;
            margin: 0 !important;
            height: auto !important;
            min-height: 18px !important;
            line-height: 1.2 !important;
            width: 100% !important;
        }
        """, unsafe_allow_html=True)

        # Crear 5 subcolumnas para los botones CALL/PUT
        col1, col2, col3, col4, col5 = st.columns(5, gap="small")

        # CALL positivos
        with col1:
            st.button(
                "🟢 C 100%", key="call_100",
                on_click=agregar_operacion,
                args=(st.session_state.datos, 100, 'CALL')
            )
            st.button(
                "🟢 C 50%", key="call_50",
                on_click=agregar_operacion,
                args=(st.session_state.datos, 50, 'CALL')
            )

        # CALL negativos
        with col2:
            st.button(
                "🔴 C -100%", key="call_menos_100",
                on_click=agregar_operacion,
                args=(st.session_state.datos, -100, 'CALL')
            )
            st.button(
                "🔴 C -50%", key="call_menos_50",
                on_click=agregar_operacion,
                args=(st.session_state.datos, -50, 'CALL')
            )

        # Neutral (CALL y PUT neutrales)
        with col3:
            st.button(
                "🟡 C 0%", key="call_0",
                on_click=agregar_operacion,
                args=(st.session_state.datos, 0, 'CALL')
            )
            st.button(
                "🟡 P 0%", key="put_0",
                on_click=agregar_operacion,
                args=(st.session_state.datos, 0, 'PUT')
            )

        # PUT positivos
        with col4:
            st.button(
                "🟢 P 100%", key="put_100",
                on_click=agregar_operacion,
                args=(st.session_state.datos, 100, 'PUT')
            )
            st.button(
                "🟢 P 50%", key="put_50",
                on_click=agregar_operacion,
                args=(st.session_state.datos, 50, 'PUT')
            )

        # PUT negativos
        with col5:
            st.button(
                "🔴 P -100%", key="put_menos_100",
                on_click=agregar_operacion,
                args=(st.session_state.datos, -100, 'PUT')
            )
            st.button(
                "🔴 P -50%", key="put_menos_50",
                on_click=agregar_operacion,
                args=(st.session_state.datos, -50, 'PUT')
            )


def crear_botones_iv_rank():
    """
    Crea tres botones de IV Rank alineados con los botones CALL/PUT.
    """
    # Reutiliza la misma columna A para consistencia de layout
    colA, colB = st.columns([5, 10], gap="small")
    with colA:
        # CSS para compactar botones
        st.markdown("""
        <style>
        [data-testid="column"] { padding: 0 !important; margin: 0 !important; }
        .stButton>button {
            font-size: 6px !important;
            padding: 0.1rem 0.3rem !important;
            margin: 0 !important;
            height: auto !important;
            min-height: 18px !important;
            line-height: 1.2 !important;
            width: 100% !important;
        }
        """, unsafe_allow_html=True)
        # Tres botones IV Rank con colores según rango
        iv1, iv2, iv3 = st.columns(3, gap="small")
        iv1.button(
            "🟢 IV Rank 0%", key="iv_rank_0",
            on_click=agregar_iv_rank,
            args=(st.session_state.datos, "0%")
        )
        iv2.button(
            "🟡 IV Rank 50%", key="iv_rank_50",
            on_click=agregar_iv_rank,
            args=(st.session_state.datos, "50%")
        )
        iv3.button(
            "🔴 IV Rank 100%", key="iv_rank_100",
            on_click=agregar_iv_rank,
            args=(st.session_state.datos, "100%")
        )