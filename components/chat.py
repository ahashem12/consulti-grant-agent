import asyncio
import streamlit as st
from datetime import datetime
from grant_rag import GrantAssessmentSystem

async def render_chat_interface():
    """Render enhanced chat interface for asking questions about projects"""
    st.markdown("<h2 class='sub-header'>Project Chat Interface</h2>", unsafe_allow_html=True)
    # Initialize session state if missing
    if "selected_projects" not in st.session_state:
        st.session_state.selected_projects = []

    if not st.session_state.selected_projects:
        st.info("Please select projects in the sidebar to start chatting.")
        return

    # Chat mode selection
    chat_mode = st.radio("Chat Mode", ["Single Project", "Multi-Project Comparison"], index=0)

    if chat_mode == "Single Project":
        chat_project = st.selectbox("Select a project to chat with", options=st.session_state.selected_projects, key="chat_project")
        if chat_project != st.session_state.get("current_project"):
            st.session_state.current_project = chat_project
            st.session_state.messages = []  # Reset chat history when switching projects
    else:
        comparison_projects = st.multiselect("Select projects to compare", options=st.session_state.selected_projects, key="comparison_projects")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Create a container for the chat area
    chat_area = st.container()
    
    # Create a container for the input area
    input_area = st.container()

    # Display chat messages in the chat area
    with chat_area:
        # Add custom CSS for the chat area
        st.markdown("""
            <style>
            .stContainer {
                height: 600px;
                overflow-y: auto;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
                margin-bottom: 20px;
                color: black;
            }
            </style>
        """, unsafe_allow_html=True)

        # Create a container for messages
        messages_container = st.container()
        with messages_container:
            for msg in st.session_state.messages:
                role = msg["role"]
                with st.chat_message("user" if role == "user" else "assistant"):
                    st.write(msg["content"])
                    if "sources" in msg:
                        st.caption(f"Sources: {', '.join(msg['sources'])}")
    
    # Handle user input in the input area
    with input_area:
        user_input = st.chat_input("Type your message here...")
        if user_input:
            await handle_user_input(user_input, chat_mode)
            st.rerun()
    

async def handle_user_input(user_input, chat_mode):
    """Handle user input for chat interaction."""
    try:
        if chat_mode == "Single Project" and st.session_state.get("chat_project"):
            chat_project = st.session_state.chat_project
            st.session_state.messages.append({"role": "user", "content": user_input, "project": chat_project, "timestamp": datetime.now().isoformat()})
            with st.spinner("Getting response..."):
                
                response = await st.session_state.grant_system.ask_project(chat_project, user_input)
                # response = {
                #     "answer": "answer",
                #     "sources": "sources",
                #     "timestamp": datetime.now().isoformat(),
                #     "context_used": len("context_chunks")
                # }
                print("[info] response from ", chat_project, " is ", response)
            st.session_state.messages.append({
                "role": "assistant",
                "content": response.get("answer", "No response") + "\n\n" + response.get("chunks") + "\n",
                "project": chat_project,
                "sources": response.get("sources", []),
                "timestamp": datetime.now().isoformat()
            })

        elif chat_mode == "Multi-Project Comparison" and len(st.session_state.get("comparison_projects", [])) >= 2:
            st.session_state.messages.append({"role": "user", "content": user_input, "comparison": True, "timestamp": datetime.now().isoformat()})

            with st.spinner("Generating comparison..."):
                results = await st.session_state.grant_system.chat_with_projects(user_input, st.session_state.comparison_projects)

            st.session_state.messages.append({
                "role": "assistant",
                "comparison": True,
                "responses": results["responses"],
                "comparison": results["comparison"],
                "timestamp": datetime.now().isoformat()
            })

    except Exception as e:
        st.error(f"Error processing message: {str(e)}")

def render_chat_interface_sync():
    """Run the async chat interface inside Streamlit."""
    asyncio.run(render_chat_interface())
