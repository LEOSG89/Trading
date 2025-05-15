import time
from io import BytesIO
import streamlit as st
from gestor_archivos_s3 import update_file
from datetime import datetime

# Flag por defecto para autoguardado
if 'auto_save_enabled' not in st.session_state:
    st.session_state.auto_save_enabled = True

AUTOSAVE_INTERVAL = 60  # segundos

def maybe_autosave():
    """
    Si st.session_state.data_modified es True, el autoguardado está habilitado y hace más de AUTOSAVE_INTERVAL
    segundos que guardamos por última vez, ejecuta la misma lógica que
    el botón manual de 'Guardar cambios en S3', sin mostrar toasts.
    """
    # Solo si el autoguardado está activado
    if not st.session_state.get('auto_save_enabled', True):
        return

    ahora = time.time()
    last = st.session_state.get("last_auto_save", 0)
    archivo = st.session_state.get("selector_archivo")

    if (
        archivo
        and archivo != "↑ Subir nuevo ↑"
        and st.session_state.get("data_modified", False)
        and (ahora - last) > AUTOSAVE_INTERVAL
    ):
        buf = BytesIO()
        st.session_state.datos.to_csv(buf, index=False, encoding="utf-8")
        buf.seek(0)
        try:
            update_file(archivo, buf.getvalue())
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Actualiza el timestamp en sesión, sin toasts
            st.session_state.last_auto_save = ts
            st.session_state.data_modified = False
        except Exception as e:
            # En caso de error, guarda mensaje de error en sesión
            st.session_state.last_auto_save = f"ERROR: {e}"


def save_current_file():
    """
    Guarda inmediatamente en S3 el DataFrame actual sin interrumpir la UI,
    solo si el autoguardado está habilitado. Actualiza el timestamp en sesión sin toasts.
    """
    # Solo si el autoguardado está activado
    if not st.session_state.get('auto_save_enabled', True):
        return

    archivo = st.session_state.get("selector_archivo")
    if not archivo or archivo == "↑ Subir nuevo ↑":
        return
    buf = BytesIO()
    st.session_state.datos.to_csv(buf, index=False, encoding="utf-8")
    buf.seek(0)
    try:
        update_file(archivo, buf.getvalue())
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.last_auto_save = ts
        st.session_state.data_modified = False
    except Exception as e:
        st.session_state.last_auto_save = f"ERROR: {e}"
