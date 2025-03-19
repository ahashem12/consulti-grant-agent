import streamlit as st
import os
import asyncio
from datetime import datetime
from GrantRAG.config.constants import GRANT_PROGRAMS
from GrantRAG.utils import save_session_state
from typing import Dict, Any
import time

async def check_eligibility(project_names, criteria):
    """Check eligibility for selected projects"""
    with st.spinner("Checking eligibility..."):
        results = {}
        for project_name in project_names:
            if project_name in st.session_state.grant_system.projects:
                result = await st.session_state.grant_system.projects[project_name].check_eligibility(criteria)
                results[project_name] = result
        st.session_state.eligibility_results = results
        return results

async def generate_reports(project_names, questions):
    """Generate detailed reports for selected projects"""
    with st.spinner("Generating detailed reports..."):
        results = {}
        for project_name in project_names:
            if project_name in st.session_state.grant_system.projects:
                report = await st.session_state.grant_system.projects[project_name].generate_detailed_report(questions)
                results[project_name] = report
        st.session_state.reports = results
        return results

async def generate_recommendations(project_names):
    """Generate recommendations for selected projects"""
    with st.spinner("Generating recommendations..."):
        results = {}
        program = st.session_state.selected_program
        criteria = GRANT_PROGRAMS[program]["eligibility_criteria"]
        questions = GRANT_PROGRAMS[program]["report_questions"]
        
        for project_name in project_names:
            if project_name in st.session_state.grant_system.projects:
                # Check if we already have eligibility results
                if project_name in st.session_state.eligibility_results:
                    eligibility = st.session_state.eligibility_results[project_name]
                else:
                    eligibility = await st.session_state.grant_system.projects[project_name].check_eligibility(criteria)
                
                # Check if we already have report
                if project_name in st.session_state.reports:
                    report = st.session_state.reports[project_name]
                else:
                    report = await st.session_state.grant_system.projects[project_name].generate_detailed_report(questions)
                
                # Generate recommendation
                recommendation = await st.session_state.grant_system.projects[project_name].generate_recommendation(
                    eligibility, report
                )
                results[project_name] = recommendation
        
        st.session_state.recommendations = results
        return results

async def generate_comparative(eligible_only=True):
    """Generate comparative analysis of selected projects"""
    with st.spinner("Generating comparative analysis..."):
        try:
            # Filter to only selected projects
            original_projects = st.session_state.grant_system.projects.copy()
            filtered_projects = {p: original_projects[p] for p in st.session_state.selected_projects if p in original_projects}
            
            # If eligible_only is True, filter to only eligible projects
            if eligible_only:
                eligible_projects = {}
                for project_name, project in filtered_projects.items():
                    if project_name in st.session_state.eligibility_results:
                        if st.session_state.eligibility_results[project_name]["eligible"]:
                            eligible_projects[project_name] = project
                filtered_projects = eligible_projects
            
            # Temporarily update the grant system's projects
            st.session_state.grant_system.projects = filtered_projects
            
            # Generate analysis
            analysis = await st.session_state.grant_system.generate_comparative_analysis(eligible_only)
            
            # Restore original projects
            st.session_state.grant_system.projects = original_projects
            
            # Store in session state
            st.session_state.comparative_analysis = analysis
            return analysis
            
        except Exception as e:
            st.error(f"Error generating comparative analysis: {str(e)}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

def render_sidebar():
    """Render the sidebar with project selection and actions"""
    st.sidebar.title("Grant RAG System")
    
    # 1. Select Grant Program
    st.sidebar.markdown("### 1. Select Grant Program")
    program = st.sidebar.selectbox(
        "Grant Program",
        options=list(GRANT_PROGRAMS.keys()),
        key="program_selector"
    )
    
    if program:
        st.session_state.selected_program = program
        st.sidebar.markdown(f"**Description:** {GRANT_PROGRAMS[program]['description']}")
    
    # 2. Select Projects
    st.sidebar.markdown("### 2. Select Projects")
    
    # Get available projects
    projects_data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "projects_data")
    available_projects = []
    
    if os.path.exists(projects_data_path):
        available_projects = [d for d in os.listdir(projects_data_path) 
                            if os.path.isdir(os.path.join(projects_data_path, d))]
    
    if not available_projects:
        st.sidebar.warning("No projects found in projects_data directory")
    else:
        # Project selection
        selected_projects = st.sidebar.multiselect(
            "Select projects to analyze",
            options=available_projects,
            default=st.session_state.selected_projects,
            key="project_selector"
        )
        
        # Update selected projects in session state
        st.session_state.selected_projects = selected_projects
        
        if selected_projects:
            # Ingest button with progress tracking
            if st.sidebar.button("Ingest Selected Projects", use_container_width=True):
                st.session_state.is_processing = True
                st.session_state.current_operation = "Ingesting Projects"
                
                progress_bar = st.sidebar.progress(0)
                status_text = st.sidebar.empty()
                
                for idx, project in enumerate(selected_projects, 1):
                    status_text.text(f"Ingesting {project}...")
                    progress = idx / len(selected_projects)
                    progress_bar.progress(progress)
                    
                    # Initialize metrics for the project
                    if project not in st.session_state.processing_metrics:
                        st.session_state.processing_metrics[project] = {
                            "Documents Processed": 0,
                            "Chunks Stored": 0,
                            "Processing Time": "N/A",
                            "Average Time per Document": "N/A"
                        }
                    
                    if project not in st.session_state.operation_timestamps:
                        st.session_state.operation_timestamps[project] = {}
                    
                    # Perform ingestion
                    start_time = time.time()
                    success = asyncio.run(st.session_state.grant_system.ingest_project(project))
                    
                    if success:
                        st.session_state.ingested_projects.add(project)
                        st.session_state.operation_timestamps[project]["Last Ingestion"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                progress_bar.empty()
                status_text.empty()
                st.session_state.is_processing = False
                st.session_state.current_operation = None
                st.sidebar.success(f"Ingested {len(selected_projects)} projects")
                
                # Save session state and trigger rerun
                save_session_state()
                st.rerun()
            
            # Show ingestion status for each project
            st.sidebar.markdown("### Project Status")
            for project in selected_projects:
                status = "🟢 Ingested" if project in st.session_state.ingested_projects else "🔴 Not Ingested"
                st.sidebar.text(f"{project}: {status}")
                
                # Show metrics if available
                if project in st.session_state.processing_metrics:
                    metrics = st.session_state.processing_metrics[project]
                    with st.sidebar.expander(f"{project} Details"):
                        st.markdown(f"**Documents:** {metrics['Documents Processed']}")
                        st.markdown(f"**Chunks:** {metrics['Chunks Stored']}")
                        st.markdown(f"**Processing Time:** {metrics['Processing Time']}")
                        
    # 3. Analysis Actions
    if st.session_state.selected_projects:
        st.sidebar.markdown("### 3. Analysis Actions")
        
        # Check Eligibility
        if st.sidebar.button("Check Eligibility", use_container_width=True):
            st.session_state.is_processing = True
            st.session_state.current_operation = "Checking Eligibility"
            criteria = GRANT_PROGRAMS[st.session_state.selected_program]["eligibility_criteria"]
            results = asyncio.run(check_eligibility(st.session_state.selected_projects, criteria))
            st.session_state.is_processing = False
            st.session_state.current_operation = None
            if results:
                st.session_state.eligibility_checked_projects.update(st.session_state.selected_projects)
                save_session_state()
                st.rerun()
        
        # Generate Reports
        if st.sidebar.button("Generate Reports", use_container_width=True):
            st.session_state.is_processing = True
            st.session_state.current_operation = "Generating Reports"
            questions = GRANT_PROGRAMS[st.session_state.selected_program]["report_questions"]
            results = asyncio.run(generate_reports(st.session_state.selected_projects, questions))
            st.session_state.is_processing = False
            st.session_state.current_operation = None
            if results:
                save_session_state()
                st.rerun()
        
        # Generate Recommendations
        if st.sidebar.button("Generate Recommendations", use_container_width=True):
            st.session_state.is_processing = True
            st.session_state.current_operation = "Generating Recommendations"
            results = asyncio.run(generate_recommendations(st.session_state.selected_projects))
            st.session_state.is_processing = False
            st.session_state.current_operation = None
            if results:
                save_session_state()
                st.rerun()
        
        # Comparative Analysis
        if len(st.session_state.selected_projects) > 1:
            if st.sidebar.button("Comparative Analysis", use_container_width=True):
                st.session_state.is_processing = True
                st.session_state.current_operation = "Generating Comparative Analysis"
                analysis = asyncio.run(generate_comparative())
                st.session_state.is_processing = False
                st.session_state.current_operation = None
                if analysis:
                    save_session_state()
                    st.rerun()

    # Add Import Projects section
    st.sidebar.markdown("### Import Projects")
    
    # File uploader for zip files
    uploaded_files = st.sidebar.file_uploader(
        "Upload project files (ZIP)",
        type=["zip"],
        accept_multiple_files=True,
        key="project_file_uploader"
    )
    
    # Folder path input
    folder_path = st.sidebar.text_input(
        "Or enter folder path:",
        key="project_folder_path"
    )
    
    # Import button
    if st.sidebar.button("Import Projects", use_container_width=True):
        if uploaded_files:
            for uploaded_file in uploaded_files:
                try:
                    # Create temporary directory for the zip file
                    import tempfile
                    import shutil
                    import zipfile
                    
                    with tempfile.TemporaryDirectory() as temp_dir:
                        # Save zip file
                        zip_path = os.path.join(temp_dir, uploaded_file.name)
                        with open(zip_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        # Extract zip
                        project_name = os.path.splitext(uploaded_file.name)[0]
                        extract_path = os.path.join(temp_dir, project_name)
                        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                            zip_ref.extractall(extract_path)
                        
                        # Add project using existing function
                        success = asyncio.run(st.session_state.grant_system.add_project_folder(extract_path))
                        if success:
                            st.sidebar.success(f"Successfully imported project: {project_name}")
                            # Update session state
                            if project_name not in st.session_state.projects_info:
                                st.session_state.projects_info[project_name] = {
                                    "name": project_name,
                                    "path": os.path.join(st.session_state.grant_system.projects_dir, project_name),
                                    "file_count": sum([len(files) for _, _, files in os.walk(extract_path)]),
                                    "last_modified": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                }
                        else:
                            st.sidebar.error(f"Failed to import project: {project_name}")
                except Exception as e:
                    st.sidebar.error(f"Error processing zip file: {str(e)}")
        
        if folder_path and os.path.exists(folder_path):
            try:
                success = asyncio.run(st.session_state.grant_system.add_project_folder(folder_path))
                if success:
                    project_name = os.path.basename(folder_path)
                    st.sidebar.success(f"Successfully imported project: {project_name}")
                    # Update session state
                    if project_name not in st.session_state.projects_info:
                        st.session_state.projects_info[project_name] = {
                            "name": project_name,
                            "path": os.path.join(st.session_state.grant_system.projects_dir, project_name),
                            "file_count": sum([len(files) for _, _, files in os.walk(folder_path)]),
                            "last_modified": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                else:
                    st.sidebar.error(f"Failed to import project: {os.path.basename(folder_path)}")
            except Exception as e:
                st.sidebar.error(f"Error importing folder: {str(e)}")
        elif folder_path:
            st.sidebar.error("Folder path does not exist")
            
        # Save session state and trigger rerun
        save_session_state()
        st.rerun()