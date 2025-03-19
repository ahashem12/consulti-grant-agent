import streamlit as st
import asyncio
from datetime import datetime

async def render_chat_interface():
    """Render enhanced chat interface for asking questions about projects"""
    st.markdown("<h2 class='sub-header'>Project Chat Interface</h2>", unsafe_allow_html=True)
    
    if not st.session_state.selected_projects:
        st.info("Please select projects in the sidebar to start chatting.")
        return
    
    # Initialize chat history if not present
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Chat mode selection with radio buttons styled as tabs
    chat_mode = st.radio(
        "Chat Mode",
        ["Single Project", "Multi-Project Comparison"],
        key="chat_mode",
        index=0  # Default to Single Project
    )
    
    # Create chat container
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
    
    if chat_mode == "Single Project":
        # Project selection for single chat
        chat_project = st.selectbox(
            "Select a project to chat with",
            options=st.session_state.selected_projects,
            key="chat_project_selector"
        )
        
        # Display single project chat history
        if chat_project:
            for msg in st.session_state.chat_history:
                if msg.get("project") == chat_project:
                    if msg["role"] == "user":
                        st.markdown(f"<div class='user-message'><strong>You:</strong> {msg['content']}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='system-message'><strong>{chat_project}:</strong> {msg['content']}</div>", unsafe_allow_html=True)
                        if msg.get("sources"):
                            st.markdown(f"<div class='system-message'><em>Sources: {', '.join(msg['sources'])}</em></div>", unsafe_allow_html=True)
    
    else:  # Multi-Project Comparison
        # Select projects for comparison
        comparison_projects = st.multiselect(
            "Select projects to compare",
            options=st.session_state.selected_projects,
            default=st.session_state.selected_projects[:2] if len(st.session_state.selected_projects) >= 2 else [],
            key="comparison_projects"
        )
        
        # Display multi-project chat history
        for msg in st.session_state.chat_history:
            if msg.get("comparison"):
                if msg["role"] == "user":
                    st.markdown(f"<div class='user-message'><strong>You:</strong> {msg['content']}</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='system-message'>", unsafe_allow_html=True)
                    for project, response in msg["responses"].items():
                        st.markdown(f"<strong>{project}:</strong> {response['answer']}", unsafe_allow_html=True)
                        if response.get("sources"):
                            st.markdown(f"<em>Sources: {', '.join(response['sources'])}</em></div>", unsafe_allow_html=True)
                        st.markdown("<br>", unsafe_allow_html=True)
                    if msg.get("comparison"):
                        st.markdown(f"<strong>Comparative Analysis:</strong><br>{msg['comparison']}", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Chat input
    with st.container():
        col1, col2 = st.columns([5,1])
        with col1:
            chat_input = st.text_input(
                "Ask a question:",
                key="chat_input",
                placeholder="Type your message here..."
            )
        with col2:
            send_button = st.button("Send", key="send_chat", use_container_width=True)
    
    if send_button and chat_input:
        try:
            if chat_mode == "Single Project":
                if not chat_project:
                    st.error("Please select a project to chat with.")
                    return
                
                # Add user message to history
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": chat_input,
                    "project": chat_project,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Get response from project
                with st.spinner(f"Getting response from {chat_project}..."):
                    response = await st.session_state.grant_system.ask_project(chat_project, chat_input)
                
                # Add assistant response to history
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response.get("answer", "Error: No response generated"),
                    "project": chat_project,
                    "sources": response.get("sources", []),
                    "timestamp": datetime.now().isoformat()
                })
            
            else:  # Multi-Project Comparison
                if len(comparison_projects) < 2:
                    st.error("Please select at least 2 projects for comparison.")
                    return
                
                # Add user message to history
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": chat_input,
                    "comparison": True,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Get comparison results
                with st.spinner("Generating comparative analysis..."):
                    results = await st.session_state.grant_system.chat_with_projects(
                        chat_input, comparison_projects
                    )
                
                # Add assistant response to history
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "comparison": True,
                    "responses": results["responses"],
                    "comparison": results["comparison"],
                    "timestamp": datetime.now().isoformat()
                })
            
            # Clear input and rerun to show updated chat
            st.rerun()
            
        except Exception as e:
            st.error(f"Error processing chat: {str(e)}")

# Wrapper function for synchronous calls
def render_chat_interface_sync():
    """Synchronous wrapper for the chat interface"""
    asyncio.run(render_chat_interface()) 