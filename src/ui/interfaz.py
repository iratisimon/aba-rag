import streamlit as st
import sys
import os
import asyncio
from pathlib import Path

# Add src to python path to allow imports from api and utilidades
sys.path.append(str(Path(__file__).resolve().parents[1]))

from api.api import app_graph
from utilidades import utils

st.set_page_config(
    page_title="Asistente RAG Bizkaia",
    page_icon="",
    layout="wide"
)

def main():
    st.title("Asistente Virtual - Hacienda Bizkaia")
    st.markdown("---")

    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "debug_logs" not in st.session_state:
        st.session_state.debug_logs = []

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "sources" in msg and msg["sources"]:
                with st.expander("Fuentes consultadas"):
                    for source in msg["sources"]:
                        st.markdown(f"- **{source['archivo']}** (Pág/Chunk {source['chunk_id']})")
    
    # Chat input
    if prompt := st.chat_input("Escribe tu duda sobre normativa..."):
        # Display user message
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Prepare inputs for RAG
        # We transform session messages to the format expected by the graph if needed,
        # but the current graph seems to care mostly about 'pregunta' and internal 'historial'
        # simpler to just pass the question for now or implement full history mapping later.
        inputs = {
            "pregunta": prompt,
            "historial": st.session_state.messages[:-1], # pass previous history
            "contexto_docs": [],
            "contexto_fuentes": [],
            "respuesta_final": "",
            "debug_pipeline": [],
            "destino": None,
            "categoria_detectada": "otros"
        }

        # Run RAG
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            with st.spinner("Consultando normativa foral..."):
                try:
                    # Run async graph in sync streamlit
                    result = asyncio.run(app_graph.ainvoke(inputs))
                    
                    response_text = result["respuesta_final"]
                    sources = result.get("contexto_fuentes", [])
                    debug_info = result.get("debug_pipeline", [])
                    
                    # Display response
                    message_placeholder.markdown(response_text)
                    
                    # Store response in session
                    msg_data = {
                        "role": "assistant", 
                        "content": response_text,
                        "sources": sources
                    }
                    st.session_state.messages.append(msg_data)
                    
                    # Show sources immediately for this turn
                    if sources:
                        with st.expander("Fuentes consultadas"):
                            for source in sources:
                                st.markdown(f"- **{source['archivo']}** (Chunk {source['chunk_id']})")

                    # Update debug logs
                    st.session_state.debug_logs.append({
                        "query": prompt,
                        "pipeline": debug_info,
                        "category": result.get("categoria_detectada")
                    })

                except Exception as e:
                    st.error(f"Error procesando la solicitud: {e}")

    # Sidebar for debug info
    with st.sidebar:
        st.header("Debug Info")
        if st.session_state.debug_logs:
            last_log = st.session_state.debug_logs[-1]
            st.subheader("Última consulta")
            st.write(f"**Categoría:** {last_log.get('category')}")
            with st.expander("Pipeline Trace"):
                for step in last_log.get("pipeline", []):
                    st.code(step, language="text")
        else:
            st.info("Realiza una consulta para ver los logs del sistema.")

if __name__ == "__main__":
    main()