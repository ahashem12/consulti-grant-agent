import streamlit as st
from datetime import datetime

def render_project_dashboard():
    """Render the project dashboard with metrics and status"""
    st.markdown("<h2 class='main-header'>Project Dashboard</h2>", unsafe_allow_html=True)
    
    if not st.session_state.selected_projects:
        st.info("Please select projects in the sidebar to view dashboard.")
        return
    
    # Display overall metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Projects",
            len(st.session_state.selected_projects)
        )
    
    with col2:
        st.metric(
            "Ingested Projects",
            len(st.session_state.ingested_projects)
        )
    
    with col3:
        st.metric(
            "Checked Projects",
            len(st.session_state.eligibility_checked_projects)
        )
    
    with col4:
        if st.session_state.is_processing:
            st.warning(f"⚡ {st.session_state.current_operation}")
    
    # Project Cards
    st.markdown("### Project Status")
    
    for project in st.session_state.selected_projects:
        with st.container():
            st.markdown(f"<div class='card'>", unsafe_allow_html=True)
            
            # Project header with status
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"#### {project}")
            with col2:
                status = "🟢" if project in st.session_state.ingested_projects else "🔴"
                st.markdown(f"Status: {status}")
            
            # Project details in columns
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # File counts and processing metrics
                metrics = st.session_state.processing_metrics.get(project, {})
                st.markdown(f"**Documents:** {metrics.get('Documents Processed', 0)}")
                st.markdown(f"**Chunks:** {metrics.get('Chunks Stored', 0)}")
            
            with col2:
                # Processing times
                st.markdown(f"**Processing Time:** {metrics.get('Processing Time', 'N/A')}")
                st.markdown(f"**Avg. Time/Doc:** {metrics.get('Average Time per Document', 'N/A')}")
            
            with col3:
                # Operation timestamps
                timestamps = st.session_state.operation_timestamps.get(project, {})
                if timestamps:
                    for operation, timestamp in timestamps.items():
                        st.markdown(f"**{operation}:** {timestamp}")
            
            st.markdown("</div>", unsafe_allow_html=True)
            
    # If no projects are selected
    if not st.session_state.selected_projects:
        st.warning("No projects selected. Please select projects from the sidebar.") 