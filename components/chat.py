import time
import streamlit as st
import asyncio
from datetime import datetime
from grant_rag import GrantAssessmentSystem

async def render_chat_interface():
    """Render enhanced chat interface for asking questions about projects"""
    print("[DEBUG] Starting chat interface render")
    st.markdown("<h2 class='sub-header'>Project Chat Interface</h2>", unsafe_allow_html=True)
    
    if not st.session_state.selected_projects:
        print("[DEBUG] No projects selected in session state")
        st.info("Please select projects in the sidebar to start chatting.")
        return
    
    print(f"[DEBUG] Selected projects: {st.session_state.selected_projects}")
    
    # Initialize chat history if not present
    if "messages" not in st.session_state:
        print("[DEBUG] Initializing chat history with test message")
        test_project = st.session_state.selected_projects[0] if st.session_state.selected_projects else "test_project"
        st.session_state.messages = [
            {
                "role": "user",
                "content": "This is a test message",
                "project": test_project,
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "assistant",
                "content": "This is a test response",
                "project": test_project,
                "sources": ["test_source_1", "test_source_2"],
                "timestamp": datetime.now().isoformat()
            }
        ]
        print(f"[DEBUG] Initialized messages with test messages: {st.session_state.messages}")
    
    print(f"[DEBUG] Current messages: {st.session_state.messages}")
    
    # Chat mode selection with radio buttons styled as tabs
    chat_mode = st.radio(
        "Chat Mode",
        ["Single Project", "Multi-Project Comparison"],
        key="chat_mode",
        index=0  # Default to Single Project
    )
    print(f"[DEBUG] Selected chat mode: {chat_mode}")
    
    # Create chat container
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
    
    # Display chat history inside the container
    if chat_mode == "Single Project":
        # Display single project chat history
        project_messages = [msg for msg in st.session_state.messages if msg.get("project") in st.session_state.selected_projects]
        print(f"[DEBUG] Found {len(project_messages)} messages")
        
        for msg in project_messages:
            print(f"[DEBUG] Displaying message: {msg}")
            if msg["role"] == "user":
                st.markdown(f"<div class='user-message'><strong>You:</strong> {msg['content']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='system-message'><strong>{msg['project']}:</strong> {msg['content']}</div>", unsafe_allow_html=True)
                if msg.get("sources"):
                    st.markdown(f"<div class='system-message'><em>Sources: {', '.join(msg['sources'])}</em></div>", unsafe_allow_html=True)
    
    else:  # Multi-Project Comparison
        # Display multi-project chat history
        comparison_messages = [msg for msg in st.session_state.messages if msg.get("comparison")]
        print(f"[DEBUG] Found {len(comparison_messages)} comparison messages")
        
        for msg in comparison_messages:
            print(f"[DEBUG] Displaying comparison message: {msg}")
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
    
    # Project selection
    if chat_mode == "Single Project":
        # Project selection for single chat
        chat_project = st.selectbox(
            "Select a project to chat with",
            options=st.session_state.selected_projects,
            key="chat_project_selector"
        )
        print(f"[DEBUG] Selected project for chat: {chat_project}")
    else:
        # Select projects for comparison
        comparison_projects = st.multiselect(
            "Select projects to compare",
            options=st.session_state.selected_projects,
            default=st.session_state.selected_projects[:2] if len(st.session_state.selected_projects) >= 2 else [],
            key="comparison_projects"
        )
        print(f"[DEBUG] Selected projects for comparison: {comparison_projects}")
    
    # Chat input at the bottom
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
        print(f"[DEBUG] Processing new message: {chat_input}")
        try:
            if chat_mode == "Single Project":
                if not chat_project:
                    print("[DEBUG] No project selected for single project chat")
                    st.error("Please select a project to chat with.")
                    return
                
                print(f"[DEBUG] Grant system status: {st.session_state.get('grant_system')}")
                if "grant_system" not in st.session_state:
                    print("[DEBUG] Initializing grant system")
                    st.session_state.grant_system = GrantAssessmentSystem()
                
                # Add user message to history
                user_message = {
                    "role": "user",
                    "content": chat_input,
                    "project": chat_project,
                    "timestamp": datetime.now().isoformat()
                }
                print(f"[DEBUG] Adding user message to history: {user_message}")
                st.session_state.messages.append(user_message)
                
                # Get response from project
                print(f"[DEBUG] Getting response from project: {chat_project}")
                with st.spinner(f"Getting response from {chat_project}..."):
                    response = await st.session_state.grant_system.ask_project(chat_project, chat_input)
                print(f"[DEBUG] Received response: {response}")
                
                # Add assistant response to history
                assistant_message = {
                    "role": "assistant",
                    "content": response.get("answer", "Error: No response generated"),
                    "project": chat_project,
                    "sources": response.get("sources", []),
                    "timestamp": datetime.now().isoformat()
                }
                print(f"[DEBUG] Adding assistant message to history: {assistant_message}")
                st.session_state.messages.append(assistant_message)
            
            else:  # Multi-Project Comparison
                if len(comparison_projects) < 2:
                    print("[DEBUG] Not enough projects selected for comparison")
                    st.error("Please select at least 2 projects for comparison.")
                    return
                
                # Add user message to history
                user_message = {
                    "role": "user",
                    "content": chat_input,
                    "comparison": True,
                    "timestamp": datetime.now().isoformat()
                }
                print(f"[DEBUG] Adding user message to history: {user_message}")
                st.session_state.messages.append(user_message)
                
                # Get comparison results
                print(f"[DEBUG] Getting comparison results for projects: {comparison_projects}")
                with st.spinner("Generating comparative analysis..."):
                    results = await st.session_state.grant_system.chat_with_projects(
                        chat_input, comparison_projects
                    )
                print(f"[DEBUG] Received comparison results: {results}")
                
                # Add assistant response to history
                assistant_message = {
                    "role": "assistant",
                    "comparison": True,
                    "responses": results["responses"],
                    "comparison": results["comparison"],
                    "timestamp": datetime.now().isoformat()
                }
                print(f"[DEBUG] Adding assistant message to history: {assistant_message}")
                st.session_state.messages.append(assistant_message)
            
            print(f"[DEBUG] Final messages: {st.session_state.messages}")
            # Clear input and rerun to show updated chat
            print("[DEBUG] Rerunning to show updated chat")
            st.rerun()
            
        except Exception as e:
            print(f"[ERROR] Exception in chat processing: {str(e)}")
            st.error(f"Error processing chat: {str(e)}")

# Wrapper function for synchronous calls
def render_chat_interface_sync():
    """Synchronous wrapper for the chat interface"""
    print("[DEBUG] Starting synchronous chat interface")
    asyncio.run(render_chat_interface()) 