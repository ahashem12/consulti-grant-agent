__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import os
import asyncio
import json
import streamlit as st
from typing import Dict, List, Any, Optional
import pandas as pd
from datetime import datetime
import time
import sys

# Add the GrantRAG directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import components and utils
from components import (
    render_program_management,
    render_sidebar,
    render_project_dashboard,
    render_chat_interface,
    render_eligibility_results,
    render_reports,
    render_recommendations,
    render_settings
)
from utils import (
    init_session_state,
    load_session_state,
    apply_custom_css
)
from config.constants import GRANT_PROGRAMS
from grant_rag import GrantAssessmentSystem

# Configure streamlit page
st.set_page_config(
    page_title="Consulti RAG System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

async def initialize_grant_system():
    """Initialize the grant system and projects"""
    if st.session_state.grant_system is None:
        with st.spinner("Initializing grant system..."):
            # Get the correct path to projects_data inside GrantRAG
            current_dir = os.path.dirname(os.path.abspath(__file__))
            projects_data_path = os.path.join(current_dir, "projects_data")
            
            st.session_state.grant_system = GrantAssessmentSystem(projects_data_path)
            await st.session_state.grant_system.initialize_projects()
            
            # Get initial project info
            if os.path.exists(projects_data_path):
                project_dirs = [d for d in os.listdir(projects_data_path) 
                              if os.path.isdir(os.path.join(projects_data_path, d))]
                for project_name in project_dirs:
                    project_path = os.path.join(projects_data_path, project_name)
                    file_count = sum([len(files) for _, _, files in os.walk(project_path)])
                    
                    st.session_state.projects_info[project_name] = {
                        "name": project_name,
                        "path": project_path,
                        "file_count": file_count,
                        "last_modified": datetime.fromtimestamp(os.path.getmtime(project_path)).strftime("%Y-%m-%d %H:%M:%S")
                    }
            
            # Restore project stats if available
            if hasattr(st.session_state, 'saved_project_stats'):
                for project_name, stats in st.session_state.saved_project_stats.items():
                    if project_name in st.session_state.grant_system.projects:
                        st.session_state.grant_system.projects[project_name].stats = stats
                # Clean up saved stats
                delattr(st.session_state, 'saved_project_stats')

def main():
    """Main function to run the Streamlit app"""
    # Initialize session state
    init_session_state()
    
    # Load saved session state automatically if enabled and file exists
    if st.session_state.get("persistence_enabled", True) and os.path.exists("session_state.json"):
        load_session_state()
    
    # Apply custom CSS
    apply_custom_css()
    
    # Initialize grant system
    asyncio.run(initialize_grant_system())
    
    # Create layout
    render_sidebar()
    
    # Main content area
    st.markdown("<h1 class='main-header'>Consulti Grant Application Analysis</h1>", unsafe_allow_html=True)
    
    # Global search
    st.text_input("🔍 Search across all projects", key="global_search", placeholder="Enter your search query...")
    if st.session_state.get("global_search"):
        with st.spinner("Searching..."):
            search_results = asyncio.run(st.session_state.grant_system.search_across_projects(st.session_state.global_search))
            if search_results:
                for project, results in search_results.items():
                    with st.expander(f"Results from {project}"):
                        st.markdown(results)
            else:
                st.info("No results found")
    
    # Show grant program info
    if st.session_state.selected_program:
        program = st.session_state.selected_program
        st.markdown(f"<div class='info-box'><h3>Selected Program: {program}</h3><p>{GRANT_PROGRAMS[program]['description']}</p></div>", unsafe_allow_html=True)
    
    # Create tabs for different views
    tabs = st.tabs([
        "📊 Dashboard",
        "✅ Eligibility Results",
        "📝 Reports",
        "💡 Recommendations",
        "🔄 Comparative Analysis",
        "💬 Chat",
        "⚙️ Settings"
    ])
    
    with tabs[0]:
        render_project_dashboard()
        
    with tabs[1]:
        render_eligibility_results()
        
    with tabs[2]:
        render_reports()
        
    with tabs[3]:
        render_recommendations()
        
    with tabs[4]:
        render_comparative_analysis()
        
    with tabs[5]:
        render_chat_interface()
        
    with tabs[6]:
        render_settings()

def render_comparative_analysis():
    """Render comparative analysis in the main area"""
    if st.session_state.comparative_analysis:
        st.markdown("<h2 class='sub-header'>Comparative Analysis</h2>", unsafe_allow_html=True)
        
        analysis = st.session_state.comparative_analysis
        
        if "error" in analysis:
            st.error(f"Error generating comparative analysis: {analysis['error']}")
        else:
            # Create comparison table
            if "responses" in analysis:
                comparison_data = []
                for project, response in analysis["responses"].items():
                    comparison_data.append({
                        "Project": project,
                        "Response": response.get("answer", "No response"),
                        "Sources": ", ".join(response.get("sources", []))
                    })
                
                if comparison_data:
                    st.markdown("### Project Responses")
                    comparison_df = pd.DataFrame(comparison_data)
                    st.dataframe(comparison_df, use_container_width=True)
            
            st.markdown("### Analysis Summary")
            st.markdown(analysis.get("comparison", "No comparative analysis available."))
    else:
        st.info("No comparative analysis available. Select multiple projects and use the sidebar to generate analysis.")

if __name__ == "__main__":
    main() 
