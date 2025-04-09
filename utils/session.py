import os
import json
import streamlit as st
from datetime import datetime
from typing import Dict, Any

def init_session_state():
    """Initialize Streamlit session state variables"""
    # Try to load saved state first
    if os.path.exists("session_state.json"):
        load_session_state()
    
    # Initialize core variables if not present
    if "grant_system" not in st.session_state:
        st.session_state.grant_system = None
    if "selected_program" not in st.session_state:
        st.session_state.selected_program = None
    if "selected_projects" not in st.session_state:
        st.session_state.selected_projects = []
    if "eligibility_results" not in st.session_state:
        st.session_state.eligibility_results = {}
    if "reports" not in st.session_state:
        st.session_state.reports = {}
    if "recommendations" not in st.session_state:
        st.session_state.recommendations = {}
    if "comparative_analysis" not in st.session_state:
        st.session_state.comparative_analysis = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "projects_info" not in st.session_state:
        st.session_state.projects_info = {}
    if "persistence_enabled" not in st.session_state:
        st.session_state.persistence_enabled = True
    if "ingested_projects" not in st.session_state:
        st.session_state.ingested_projects = set()
    if "eligibility_checked_projects" not in st.session_state:
        st.session_state.eligibility_checked_projects = set()
    if "projects_passed_selection" not in st.session_state:
        st.session_state.projects_passed_selection = set()

    # Project tracking
    if "project_progress" not in st.session_state:
        st.session_state.project_progress = {}
    if "operation_timestamps" not in st.session_state:
        st.session_state.operation_timestamps = {}
    if "processing_metrics" not in st.session_state:
        st.session_state.processing_metrics = {}
    
    # Processing states
    if "is_processing" not in st.session_state:
        st.session_state.is_processing = False
    if "current_operation" not in st.session_state:
        st.session_state.current_operation = None
    
    # Save initial state if persistence is enabled
    if st.session_state.persistence_enabled:
        save_session_state()

def save_session_state() -> bool:
    """Save the current session state to a JSON file"""
    try:
        # Convert sets to lists for JSON serialization
        state_dict = {
            "selected_program": st.session_state.selected_program,
            "selected_projects": list(st.session_state.selected_projects),
            "ingested_projects": list(st.session_state.ingested_projects),
            "eligibility_checked_projects": list(st.session_state.eligibility_checked_projects),
            "projects_passed_selection": list(st.session_state.projects_passed_selection),
            "eligibility_results": st.session_state.eligibility_results,
            "reports": st.session_state.reports,
            "recommendations": st.session_state.recommendations,
            "comparative_analysis": st.session_state.comparative_analysis,
            "chat_history": st.session_state.chat_history,
            "projects_info": st.session_state.projects_info,
            "project_progress": st.session_state.project_progress,
            "operation_timestamps": st.session_state.operation_timestamps,
            "processing_metrics": st.session_state.processing_metrics,
            "persistence_enabled": st.session_state.persistence_enabled
        }
        
        # Save to file
        with open("session_state.json", "w") as f:
            json.dump(state_dict, f)
            
        # Also save project-specific stats
        if st.session_state.grant_system and st.session_state.grant_system.projects:
            project_stats = {}
            for project_name, project_rag in st.session_state.grant_system.projects.items():
                project_stats[project_name] = project_rag.stats
            
            with open("project_stats.json", "w") as f:
                json.dump(project_stats, f)
                
        return True
    except Exception as e:
        st.error(f"Failed to save session state: {str(e)}")
        return False

def load_session_state() -> bool:
    """Load session state from JSON file"""
    try:
        if os.path.exists("session_state.json"):
            with open("session_state.json", "r") as f:
                state_dict = json.load(f)
                
            # Restore session state
            st.session_state.selected_program = state_dict.get("selected_program")
            st.session_state.selected_projects = state_dict.get("selected_projects", [])
            st.session_state.ingested_projects = set(state_dict.get("ingested_projects", []))
            st.session_state.eligibility_checked_projects = set(state_dict.get("eligibility_checked_projects", []))
            st.session_state.projects_passed_selection = set(state_dict.get("projects_passed_selection", []))
            st.session_state.eligibility_results = state_dict.get("eligibility_results", {})
            st.session_state.reports = state_dict.get("reports", {})
            st.session_state.recommendations = state_dict.get("recommendations", {})
            st.session_state.comparative_analysis = state_dict.get("comparative_analysis")
            st.session_state.chat_history = state_dict.get("chat_history", [])
            st.session_state.projects_info = state_dict.get("projects_info", {})
            st.session_state.project_progress = state_dict.get("project_progress", {})
            st.session_state.operation_timestamps = state_dict.get("operation_timestamps", {})
            st.session_state.processing_metrics = state_dict.get("processing_metrics", {})
            st.session_state.persistence_enabled = state_dict.get("persistence_enabled", True)
            
        # Load project stats if available
        if os.path.exists("project_stats.json"):
            with open("project_stats.json", "r") as f:
                project_stats = json.load(f)
                
            # Store for later use when grant system is initialized
            st.session_state.saved_project_stats = project_stats
            
        return True
    except Exception as e:
        st.error(f"Failed to load session state: {str(e)}")
    return False

def clear_session_state():
    """Clear all session state variables and reinitialize"""
    # Remove saved state files
    if os.path.exists("session_state.json"):
        os.remove("session_state.json")
    if os.path.exists("project_stats.json"):
        os.remove("project_stats.json")
        
    # Clear all session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]
        
    # Reinitialize
    init_session_state()
    st.success("Session cleared!")
    st.rerun() 