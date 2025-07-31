import streamlit as st
import groq
import os
from archivos import file_upload_button, save_uploaded_file, extract_text_from_file, ALLOWED_EXTENSIONS
from history import save_chat, load_chat, get_chat_history, setup_chat_directory, CHAT_DIR

MODELS = ['llama3-8b-8192', 'llama3-70b-8192', 'mixtral-8x7b-32768']

# Asegurar que el directorio de chats existe
setup_chat_directory()

# PAGE SETUP
def configure_page():
    st.set_page_config(
        page_title="P.A.I.",
        layout="wide",
        page_icon="icons\logo.png"
    )
    st.title("Bienvenidos al asistente personal inteligente (A.P.I.)")

# CLIENT SETUP
def create_groq_client():
    try:
        api_key = st.secrets.get("GROQ_API_KEY")
        if not api_key:
            st.error("Missing GROQ_API_KEY in .streamlit/secrets.toml")
            st.stop()
        return groq.Groq(api_key=api_key)
    except Exception as e:
        st.error(f"Error al crear cliente Groq: {str(e)}")
        st.stop()

# INITIALIZE CHAT STATE
def initialize_chat_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "chat_file" not in st.session_state:
        st.session_state.chat_file = None
    if "current_chat_loaded" not in st.session_state:
        st.session_state.current_chat_loaded = False

# DISPLAY MESSAGES
def display_previous_messages():
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# SIDEBAR
from bot_profile import get_profile, BOT_PROFILES

def show_sidebar(client):
    st.sidebar.title("Modelo e Historial")
    #Selector de Modelo
    model = st.sidebar.selectbox("Seleccionar Modelo", MODELS, index=0)
    st.sidebar.write(f"**Modelo seleccionado:** {model}")
    #Selector de perfil
    profile_name = st.sidebar.selectbox("Seleccionar Perfil", list(BOT_PROFILES.keys()), index=0)
    st.sidebar.write(f"**Perfil seleccionado:** {profile_name}")
    st.session_state.profile_name = profile_name
    #Historial
    chats = get_chat_history()
    
    if st.sidebar.button("➕ Nuevo Chat"):
        st.session_state.messages = []
        st.session_state.chat_file = None
        st.session_state.current_chat_loaded = False
        st.rerun()

    selected = st.sidebar.selectbox("Cargar chat anterior", ["(Nuevo chat)"] + chats)
    
    if selected != "(Nuevo chat)":
        if not st.session_state.current_chat_loaded or st.session_state.chat_file != selected:
            load_chat(os.path.join(CHAT_DIR, selected))
            st.session_state.chat_file = selected
            st.session_state.current_chat_loaded = True
            st.rerun()

    return model

# USER INPUT
def get_user_input():
    """Obtiene entrada del usuario con el ícono integrado"""
    with st.container():
        cols = st.columns([1, 20, 1])
        
        with cols[1]:
            user_input = st.chat_input("Escribe tu mensaje...")
        
        with cols[2]:
            file_upload_button()
        
        uploaded_file = st.file_uploader(
            "Subir archivo",
            type=list(ALLOWED_EXTENSIONS),
            accept_multiple_files=False,
            key="chat_file_uploader",
            label_visibility="collapsed"
        )
    
    if uploaded_file:
        file_path = save_uploaded_file(uploaded_file)
        if file_path:
            file_content = extract_text_from_file(file_path)
            if file_content:
                return f"[ARCHIVO: {uploaded_file.name}]\n{file_content}"
    
    return user_input

# ADD MESSAGE
def add_message(role, content):
    st.session_state.messages.append({"role": role, "content": content})
    with st.chat_message(role):
        st.markdown(content)

# GET MODEL RESPONSE
def get_model_response(client, model, messages):
    try:
        last_user_message = messages[-1]["content"]
        
        res = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": get_profile(st.session_state.get("profile_name", "Perfil1"))["system_prompt"]
                },
                *messages
            ],
            temperature=get_profile(st.session_state.get("profile_name", "Perfil1"))["temperature"],
            top_p=0.9
        )

        return res.choices[0].message.content

    except Exception as e:
        return f"¡ERROR! {str(e).upper()} ¡ERROR!"

# MAIN APP
def run_chat():
    configure_page()
    client = create_groq_client()
    model = show_sidebar(client)
    initialize_chat_state()
    
    display_previous_messages()

    user_input = get_user_input()
    if user_input:
        add_message("user", user_input)
        assistant_response = get_model_response(client, model, st.session_state.messages)
        add_message("assistant", assistant_response)
        save_chat(st.session_state.messages, client, immediate=True)

    st.divider()
    if st.button("💾 Guardar chat ahora"):
        save_chat(st.session_state.messages, client, immediate=True)
        st.rerun()

if __name__ == "__main__":
    run_chat()