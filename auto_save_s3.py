import threading
from io import BytesIO
import streamlit as st
from gestor_archivos_s3 import update_file
from datetime import datetime

# Aseguramos flag por defecto para autoguardado
if 'auto_save_enabled' not in st.session_state:
    st.session_state.auto_save_enabled = True

def schedule_auto_save(delay_s: int = 60):
    """
    Programa un guardado silencioso en S3 pasados delay_s segundos,
    solo si el autoguardado está habilitado, sin forzar reruns ni recargas.
    """
    # Solo si el autoguardado está activado
    if not st.session_state.get('auto_save_enabled', True):
        return

    # Solo si hay cambios pendientes y no está ya programado
    if not st.session_state.get("data_modified", False):
        return
    if st.session_state.get("save_scheduled", False):
        return

    archivo = st.session_state.get("selector_archivo")
    if archivo in (None, "↑ Subir nuevo ↑"):
        return

    # Preparamos snapshot y marcamos el hilo como programado
    df_snapshot = st.session_state.datos.copy()
    st.session_state.save_scheduled = True

    def _do_save(file_name, df):
        try:
            buf = BytesIO()
            df.to_csv(buf, index=False, encoding="utf-8")
            buf.seek(0)
            update_file(file_name, buf.getvalue())

            # Actualizamos el timestamp en sesión
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.last_auto_save = ts

        except Exception as e:
            # Puedes loguear errores si lo deseas
            st.session_state.last_auto_save = f"ERROR: {e}"
        finally:
            # Permitimos futuros guardados
            st.session_state.save_scheduled = False
            st.session_state.data_modified = False

    timer = threading.Timer(delay_s, _do_save, args=(archivo, df_snapshot))
    timer.daemon = True
    # Guardamos el timer para que no lo elimine el recolector
    st.session_state.auto_save_timer = timer
    timer.start()
