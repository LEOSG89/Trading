import os
import json
import pandas as pd
import streamlit as st
from config import UPLOADED_DIR, UPLOADED_INDEX

def init_storage() -> None:
    """
    Crea el directorio y el índice JSON si no existen.
    """
    os.makedirs(UPLOADED_DIR, exist_ok=True)
    if not os.path.exists(UPLOADED_INDEX):
        with open(UPLOADED_INDEX, "w") as f:
            json.dump([], f)

def list_saved_files() -> list[dict]:
    """
    Lee y devuelve la lista de archivos guardados:
      [{ 'name': ..., 'path': ... }, ...]
    """
    if not os.path.exists(UPLOADED_INDEX):
        return []
    with open(UPLOADED_INDEX, "r") as f:
        return json.load(f)

def save_uploaded_file(uploaded) -> None:
    """
    Guarda el UploadedFile en disco y actualiza el índice si es nuevo.
    """
    destino = os.path.join(UPLOADED_DIR, uploaded.name)
    # Escribir la copia en disco
    with open(destino, "wb") as f:
        f.write(uploaded.getbuffer())

    # Actualizar índice
    files = list_saved_files()
    if all(f["name"] != uploaded.name for f in files):
        files.append({"name": uploaded.name, "path": destino})
        with open(UPLOADED_INDEX, "w") as f:
            json.dump(files, f)

def load_file_df(name: str) -> pd.DataFrame:
    """
    Carga y devuelve el DataFrame del archivo guardado con ese nombre.
    """
    files = list_saved_files()
    entry = next((f for f in files if f["name"] == name), None)
    if not entry or not os.path.exists(entry["path"]):
        st.error(f"No existe el archivo guardado: {name}")
        return pd.DataFrame()
    if name.lower().endswith(".csv"):
        return pd.read_csv(entry["path"], dtype=str)
    return pd.read_excel(entry["path"], dtype=str)

def delete_saved_file(name: str) -> None:
    """
    Elimina el archivo del disco y su entrada en el índice.
    """
    files = list_saved_files()
    # Busca la entrada
    entry = next((f for f in files if f["name"] == name), None)
    if not entry:
        return
    # Borra del disco si existe
    try:
        if os.path.exists(entry["path"]):
            os.remove(entry["path"])
    except Exception as e:
        st.warning(f"No se pudo eliminar el archivo de disco: {e}")
    # Actualiza índice
    remaining = [f for f in files if f["name"] != name]
    with open(UPLOADED_INDEX, "w") as f:
        json.dump(remaining, f)
