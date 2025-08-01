import os
import streamlit as st
from datetime import datetime
import groq

CHAT_DIR = "chats"

def setup_chat_directory():
    """Asegura que el directorio de chats existe"""
    if not os.path.exists(CHAT_DIR):
        os.makedirs(CHAT_DIR)

def generate_filename(client, initial_message):
    """Genera un nombre de archivo basado en el tema del chat"""
    try:
        response = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {"role": "system", "content": "Genera un nombre de archivo muy corto (2-4 palabras) en español que capture el tema principal. Solo responde con el nombre, sin texto adicional."},
                {"role": "user", "content": initial_message}
            ],
            temperature=0.3
        )
        topic = response.choices[0].message.content.strip().replace(" ", "_")
        timestamp = datetime.now().strftime("%Y-%m-%d")
        return f"{timestamp}_{topic[:30]}.txt"
    except:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        return f"chat_{timestamp}.txt"

def save_chat(messages, client, immediate=False):
    """Guarda el chat en un archivo"""
    if not messages:
        return
        
    setup_chat_directory()
    
    chat_file = st.session_state.get("chat_file")
    if not chat_file:
        first_user_message = next((msg["content"] for msg in messages if msg["role"] == "user"), "")
        chat_file = generate_filename(client, first_user_message)
        st.session_state.chat_file = chat_file
    
    path = os.path.join(CHAT_DIR, chat_file)
    with open(path, "w", encoding="utf-8") as f:
        for msg in messages:
            f.write(f"[{msg['role'].upper()}] {msg['content']}\n")
    
    if immediate:
        st.toast(f"💾 Chat guardado como: {chat_file}")

def load_chat(path):
    """Carga un chat desde un archivo"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        new_messages = []
        for line in lines:
            if line.startswith("[USER]"):
                new_messages.append({"role": "user", "content": line[7:].strip()})
            elif line.startswith("[ASSISTANT]"):
                new_messages.append({"role": "assistant", "content": line[12:].strip()})
        
        st.session_state.messages = new_messages
        st.session_state.current_chat_loaded = True
        
    except Exception as e:
        st.error(f"Error al cargar chat: {str(e)}")
        st.session_state.messages = []

def get_chat_history():
    """Obtiene la lista de chats guardados"""
    setup_chat_directory()
    return sorted(
        [f for f in os.listdir(CHAT_DIR) if f.endswith('.txt')],
        key=lambda x: os.path.getmtime(os.path.join(CHAT_DIR, x)),
        reverse=True
    ) if os.path.exists(CHAT_DIR) else []