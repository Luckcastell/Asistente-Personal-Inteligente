import os
import tempfile
import streamlit as st
from PIL import Image
import PyPDF2
import shutil
import base64

# Directorio donde se guardarán los archivos subidos
UPLOAD_DIR = "uploads"
# Extensiones de archivo permitidas para subir (ahora incluye py, html, css, js, etc.)
ALLOWED_EXTENSIONS = {
    'pdf', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'svg',
    'py', 'html', 'css', 'js', 'json', 'xml', 'csv', 'md'
}

def setup_upload_dir():
    """Crea el directorio de subidas si no existe."""
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)

def allowed_file(filename):
    """Verifica si la extensión del archivo está permitida."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(uploaded_file):
    """Guarda el archivo subido en el directorio de subidas y devuelve su ruta."""
    setup_upload_dir()

    if uploaded_file is None:
        return None

    if not allowed_file(uploaded_file.name):
        st.error(f"Tipo de archivo no permitido. Extensiones permitidas: {', '.join(ALLOWED_EXTENSIONS)}")
        return None

    file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

def extract_text_from_file(file_path):
    """Extrae el texto de un archivo según su extensión."""
    if not file_path:
        return None

    ext = file_path.split('.')[-1].lower()
    try:
        if ext == 'pdf':
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = "\n".join([page.extract_text() for page in reader.pages])
                return text
        elif ext == 'docx':
            try:
                from docx import Document
                doc = Document(file_path)
                return "\n".join([para.text for para in doc.paragraphs])
            except ImportError:
                st.error("Para leer archivos DOCX, instala python-docx: pip install python-docx")
                return f"[Documento Word: {os.path.basename(file_path)}]"
        elif ext == 'txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        # ✅ Nuevo: Leer como texto plano archivos de código o datos
        elif ext in {'py', 'html', 'css', 'js', 'json', 'xml', 'csv', 'md'}:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        elif ext in {'jpg', 'jpeg', 'png'}:
            return f"[Imagen: {os.path.basename(file_path)}]"
        elif ext == 'svg':
            return f"[Archivo SVG: {os.path.basename(file_path)}]"
    except Exception as e:
        st.error(f"Error al procesar archivo: {str(e)}")
        return None

def file_upload_button():
    """Agrega un botón personalizado de subida de archivos dentro de la interfaz de chat."""
    st.markdown("""
    <style>
        div[data-testid="stChatInputContainer"] {
            position: relative;
        }
        .chat-upload-icon {
            position: absolute;
            right: 15px;
            bottom: 15px;
            z-index: 2;
            cursor: pointer;
        }
        .chat-upload-icon img {
            width: 24px;
            height: 24px;
            opacity: 0.7;
            transition: opacity 0.2s;
        }
        .chat-upload-icon img:hover {
            opacity: 1;
        }
        .chat-file-input {
            display: none;
        }
    </style>
    """, unsafe_allow_html=True)

def clean_uploads():
    """Elimina los archivos antiguos del directorio de subidas."""
    setup_upload_dir()
    for filename in os.listdir(UPLOAD_DIR):
        file_path = os.path.join(UPLOAD_DIR, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            st.error(f"Error al eliminar {file_path}: {e}")
