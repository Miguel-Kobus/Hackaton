
import streamlit as st
from utils.supabase_client import supabase

def autenticar_usuario():
    if "usuario" in st.session_state:
        return st.session_state.usuario

    st.sidebar.subheader("🔐 Login")
    usuario = st.sidebar.text_input("Usuário")
    senha = st.sidebar.text_input("Senha", type="password")

    if st.sidebar.button("Entrar"):
        result = supabase.table("usuarios").select("*").eq("usuario", usuario).eq("senha", senha).execute()
        if result.data:
            st.session_state.usuario = usuario
            st.success("Login realizado com sucesso!")
            return usuario
        else:
            st.error("Usuário ou senha incorretos.")
    return None
