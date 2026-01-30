import streamlit as st
import sys
import os
import asyncio
from pathlib import Path

# Add src to python path to allow imports from api and utilidades
sys.path.append(str(Path(__file__).resolve().parents[1]))

from api.api import app_graph
from utilidades import utils

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Asistente RAG Bizkaia",
    page_icon="",
    layout="wide",
)

ST_STYLE = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #3B1E1E; /* Slate 800 */
    }
    
    #MainMenu, footer {visibility: hidden;}
    
    header[data-testid="stHeader"] {
        background: transparent !important;
        z-index: 100 !important;
    }
    
    .block-container {
        padding-bottom: 2rem !important;
        padding-top: 2rem !important;
    }

    .stApp {
        background-color: #FCF8F8; /* Slate 50 */
        background-image: 
            radial-gradient(circle at 50% 0%, rgba(246 59 59 / 0.05) 0%, transparent 50%);
        background-attachment: fixed;
    }

    h1 {
        background: linear-gradient(135deg, #FF0000 0%, #FC7171 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 250 !important;
        font-size: 2.5rem !important;
        margin-bottom: -1.5rem !important;
        letter-spacing: -0.5px;
    }
    h2 {
        background: linear-gradient(135deg, #FC7171 0%, #FFD5D5 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 500 !important;
        font-size: 3rem !important;
        margin-top: -1.5rem !important;
        margin-bottom: 1rem !important;
        letter-spacing: -0.5px;
    }

    section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #F0E2E2; /* Borde gris claro */
        box-shadow: 2px 0 10px rgba(0,0,0,0.03); /* Sombra muy ligera */
    }
    
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #2A0F0F !important;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #694747;
    }

    .user-bubble {
        background-color: #FFFFFF;
        color: #3B1E1E;
        padding: 1rem 1.5rem;
        border-radius: 18px 18px 4px 18px;
        margin: 10px 0;
        max-width: 80%;
        margin-left: auto;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        border: 1px solid #FFC9C9;
    }

    .ai-bubble {
        background-color: #FFFFFF;
        color: #553333;
        padding: 1.5rem;
        border-radius: 18px 18px 18px 4px;
        margin: 15px 0;
        max-width: 85%;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        border: 1px solid #FFC9C9;
        border-left: 2px solid #FF6767;
    }
    
    /* INPUT FLOTANTE (ADAPTIVE) */
    .stChatInput {
        /* Eliminamos posicionamiento forzado para que respete el sidebar nativamente */
        bottom: 40px !important;
        background: transparent !important;
    }
    
    div[data-testid="stChatInput"] {
        /* Estilo Isla centrado en su contenedor */
        max-width: 800px !important; 
        margin: 0 auto !important;
        
        background: #FFFFFF !important;
        border-radius: 0.6rem !important;
        border: 2px solid #E1CBCB !important;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05) !important;
    }

    .source-chip {
        display: inline-flex;
        align-items: center;
        background: #FFF0F0;
        border: 1px solid #FDBABA;
        color: #A10303;
        padding: 5px 12px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 6px;
        margin-top: 8px;
        text-decoration: none;
        transition: transform 0.1s ease;
    }
    
    .source-chip:hover {
        background: #FEE0E0;
        transform: translateY(-1px);
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    @keyframes pulseBorder {
        0% { 
            box-shadow: 0 0 0 0 rgba(246 59 59 / 0.4); 
            border-color: #FD9393;
        }
        70% { 
            box-shadow: 0 0 0 12px rgba(246 59 59 / 0); 
            border-color: #F63B3B;
        }
        100% { 
            box-shadow: 0 0 0 0 rgba(246 59 59 / 0); 
            border-color: #FD9393;
        }
    }

    .thinking-bubble {
        background-color: #FFFFFF;
        padding: 1rem 1.5rem;
        border-radius: 18px 18px 18px 4px;
        margin: 15px 0;
        width: fit-content;
        border: 2px solid #F63B3B;
        animation: pulseBorder 1.5s infinite ease-in-out;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .thinking-dots {
        display: flex;
        gap: 6px;
    }
    .dot {
        width: 8px;
        height: 8px;
        background: #F63B3B;
        border-radius: 50%;
        animation: simpleBounce 1s infinite ease-in-out both;
    }
    .dot:nth-child(1) { animation-delay: -0.32s; }
    .dot:nth-child(2) { animation-delay: -0.16s; }
    
    @keyframes simpleBounce {
        0%, 80%, 100% { transform: scale(0); }
        40% { transform: scale(1); }
    }
</style>
"""
st.markdown(ST_STYLE, unsafe_allow_html=True)

def render_message(role, content, sources=None):
    """Renderiza un mensaje con estilos HTML personalizados."""
    if role == "user":
        st.markdown(f'<div class="user-bubble">{content}</div>', unsafe_allow_html=True)
    else:
        
        with st.container():
            st.markdown(f"""
            <div class="ai-bubble">
                <div style="margin-bottom: 10px;">{content}</div>
                {"".join([f'<a href="#" class="source-chip">{s.get("archivo", "Doc")} ({s.get("chunk_id", "?")})</a>' for s in (sources or [])])}
            </div>
            """, unsafe_allow_html=True)

import urllib.request
import json

def check_api_health():
    """Verifica si la API externa está respondiendo."""
    url = "http://127.0.0.1:8000/health"
    try:
        with urllib.request.urlopen(url, timeout=1) as response:
            if response.getcode() == 200:
                data = json.loads(response.read().decode())
                return f"Conectado"
    except:
        pass
    return "Desconectado"

def main():
    st.markdown("<h1>&nbsp;Hola,</h1>", unsafe_allow_html=True)
    st.markdown("<h2>¿En qué puedo ayudarte?</h2>", unsafe_allow_html=True)
    
    # Check API Status on load
    if "api_status" not in st.session_state or st.session_state.api_status.startswith("Conectado"):
        st.session_state.api_status = check_api_health()

    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "debug_logs" not in st.session_state:
        st.session_state.debug_logs = []
        
    if "api_status" not in st.session_state:
        st.session_state.api_status = "Conectado"

    # --- HISTORIAL ---
    # Contenedor para scroll
    chat_container = st.container()
    
    with chat_container:
        for msg in st.session_state.messages:
            render_message(msg["role"], msg["content"], msg.get("sources"))

    # --- INPUT ---
    if prompt := st.chat_input("Escribe tu consulta..."):
        with chat_container:
            render_message("user", prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # 2. Thinking State + Siri Animation
        with chat_container:
            thinking_placeholder = st.empty()
            siri_style_placeholder = st.empty()
            
            # Inyectar CSS para animación SUPER FLUIDA y LIGERA (Solo cambio de color sutil)
            siri_style_placeholder.markdown("""
                <style>
                @keyframes subtlePulse {
                    0% { background-color: #FCF8F8; }
                    50% { background-color: #FEF2F2; }
                    100% { background-color: #FCF8F8; }
                }
                .stApp {
                    animation: subtlePulse 2s infinite ease-in-out;
                }
                </style>
            """, unsafe_allow_html=True)
                
            thinking_placeholder.markdown("""
                <div class="thinking-bubble">
                    <span style="color: #8B6464; font-size: 0.9rem; font-weight: 500;">Pensando</span>
                    <div class="thinking-dots">
                        <div class="dot"></div><div class="dot"></div><div class="dot"></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            try:
                st.session_state.api_status = "Procesando"
                inputs = {
                    "pregunta": prompt,
                    "historial": st.session_state.messages[:-1], 
                    "contexto_docs": [],
                    "contexto_fuentes": [],
                    "respuesta_final": "",
                    "debug_pipeline": [],
                    "destino": None,
                    "categoria_detectada": "otros"
                }

                result = asyncio.run(app_graph.ainvoke(inputs))
                
                st.session_state.api_status = check_api_health()
                    
                response_text = result["respuesta_final"]
                sources = result.get("contexto_fuentes", [])
                debug_info = result.get("debug_pipeline", [])
                    
                # Stop animations
                thinking_placeholder.empty()
                siri_style_placeholder.empty() # Esto devuelve el fondo a la normalidad
                
                render_message("assistant", response_text, sources)
                
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response_text,
                    "sources": sources
                })

                st.session_state.debug_logs.append({
                    "query": prompt,
                    "pipeline": debug_info,
                    "category": result.get("categoria_detectada")
                })

            except Exception as e:
                thinking_placeholder.empty()
                st.session_state.api_status = "Desconectado"
                st.error(f"Lo siento, ocurrió un error: {e}")

    with st.sidebar:
        match st.session_state.api_status:
            case "Conectado":
                st.success(f"**Estado de la API:** {st.session_state.api_status}")
            case "Desconectado":
                st.error(f"**Estado de la API:** {st.session_state.api_status}")
            case "Procesando":
                st.warning(f"**Estado de la API:** {st.session_state.api_status}")
        
        if st.session_state.debug_logs:
            last_log = st.session_state.debug_logs[-1]
            st.caption(f"**Categoría:** {last_log.get('category')}")
            
            with st.expander("Traza de Ejecución", expanded=True):
                for i, step in enumerate(last_log.get("pipeline", [])):
                    st.caption(f"{i+1}. {step}")
        else:
            st.markdown("*Esperando consultas...*")

if __name__ == "__main__":
    main()