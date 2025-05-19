import os, boto3, streamlit as st

AWS_KEY    = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET = os.getenv("AWS_SECRET_ACCESS_KEY")
REGION     = os.getenv("AWS_REGION")
BUCKET     = os.getenv("AWS_BUCKET_NAME")

if not all([AWS_KEY, AWS_SECRET, REGION, BUCKET]):
    st.error("🔑 Faltan credenciales de AWS en el entorno.")
    st.stop()

session = boto3.Session(
    aws_access_key_id=AWS_KEY,
    aws_secret_access_key=AWS_SECRET,
    region_name=REGION
)
s3 = session.client("s3")




def list_saved_files():
    """
    Lista todos los objetos bajo 'uploads/' en el bucket.
    Devuelve [{'name':…, 'path':…},…].
    """
    resp = s3.list_objects_v2(Bucket=BUCKET, Prefix="uploads/")
    contents = resp.get("Contents", [])
    return [
        {"name": obj["Key"].split("/", 1)[1], "path": obj["Key"]}
        for obj in contents
    ]


def save_uploaded_file(uploaded_file):
    """
    Opción B: sube el UploadedFile de Streamlit a S3 dentro de uploads/,
    y solo rerunea UNA vez tras la primera subida.
    """
    # Si ya subimos en este ciclo, no repetimos
    if st.session_state.get("ya_subido", False):
        return

    key = f"uploads/{uploaded_file.name}"
    try:
        st.write(f"🔄 Subiendo a S3: bucket={BUCKET}, key={key} …")
        s3.upload_fileobj(uploaded_file, BUCKET, key)
        st.success(f"✅ Subida OK: {key}")
        # Marcamos flag para que no vuelva a subir en este rerun
        st.session_state["ya_subido"] = True
        st.rerun()
    except Exception as e:
        st.error(f"❌ Error al subir a S3: {e}")


def load_file_df(name):
    """
    Descarga uploads/{name} desde S3 y devuelve un DataFrame.
    Soporta .csv y .xlsx.
    """
    key = f"uploads/{name}"
    obj = s3.get_object(Bucket=BUCKET, Key=key)
    data = obj["Body"].read()
    if name.lower().endswith(".csv"):
        return pd.read_csv(BytesIO(data))
    return pd.read_excel(BytesIO(data))


def delete_saved_file(name):
    """
    Borra el objeto uploads/{name} en S3 y recarga la app.
    """
    key = f"uploads/{name}"
    try:
        s3.delete_object(Bucket=BUCKET, Key=key)
        st.success(f"🗑️ Eliminado OK: {key}")
    except Exception as e:
        st.error(f"❌ Error al eliminar de S3: {e}")
    finally:
        st.rerun()
def update_file(name: str, data_bytes: bytes):
    """
    Reemplaza en S3 el objeto uploads/{name} con los bytes pasados.
    """
    key = f"uploads/{name}"
    # Puedes usar put_object o upload_fileobj
    s3.put_object(Bucket=BUCKET, Key=key, Body=data_bytes)
       
