import streamlit as st
from typing import Dict, Any
from GrantRAG.config.constants import GRANT_PROGRAMS

def render_settings():
    """Render the settings interface with program management options"""
    st.markdown("<h2 class='main-header'>Program Settings</h2>", unsafe_allow_html=True)
    
    if not st.session_state.selected_program:
        st.warning("Please select a grant program first.")
        return
        
    program = st.session_state.selected_program
    
    # Create tabs for different settings
    tab1, tab2 = st.tabs(["Eligibility Criteria", "Report Questions"])
    
    with tab1:
        render_eligibility_settings(program)
        
    with tab2:
        render_report_settings(program)
        
    # Add session persistence toggle
    st.markdown("---")
    st.markdown("### Session Management")
    
    persistence = st.toggle(
        "Enable Session Persistence",
        value=st.session_state.persistence_enabled,
        key="persistence_toggle"
    )
    
    if persistence != st.session_state.persistence_enabled:
        st.session_state.persistence_enabled = persistence
        if persistence:
            st.success("Session persistence enabled. Your settings will be saved.")
        else:
            st.warning("Session persistence disabled. Settings will not be saved between sessions.")
            
    if st.button("Clear Current Session"):
        st.session_state.clear()
        st.success("Session cleared successfully!")
        st.rerun()

def render_eligibility_settings(program: str):
    """Render eligibility criteria settings"""
    st.markdown("### Eligibility Criteria Management")
    
    # Initialize session state for criteria
    if "eligibility_criteria" not in st.session_state:
        st.session_state.eligibility_criteria = {
            prog: GRANT_PROGRAMS[prog]["eligibility_criteria"].copy() 
            for prog in GRANT_PROGRAMS
        }
    
    criteria = st.session_state.eligibility_criteria[program]
    
    # Display and edit existing criteria
    for name, criterion in criteria.items():
        with st.container():
            st.markdown(f'<div class="criteria-box">', unsafe_allow_html=True)
            col1, col2 = st.columns([0.9, 0.1])
            
            with col1:
                edited_criterion = st.text_area(
                    f"{name}",
                    value=criterion,
                    key=f"criterion_{program}_{name}",
                    height=100
                )
                if edited_criterion != criterion:
                    criteria[name] = edited_criterion
                    st.success("Criterion updated successfully!")
                    
            with col2:
                if st.button("Delete", key=f"delete_{program}_{name}"):
                    if st.button("Confirm Delete", key=f"confirm_delete_{program}_{name}"):
                        del criteria[name]
                        st.success("Criterion deleted successfully!")
                        st.rerun()
                        
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Add new criterion
    st.markdown("### Add New Criterion")
    new_name = st.text_input("Criterion Name", key=f"new_criterion_name_{program}")
    new_criterion = st.text_area("Criterion Question", key=f"new_criterion_question_{program}")
    
    if st.button("Add Criterion"):
        if new_name and new_criterion:
            criteria[new_name] = new_criterion
            st.success("New criterion added successfully!")
            st.rerun()
        else:
            st.warning("Please enter both a name and a criterion.")

def render_report_settings(program: str):
    """Render report questions settings"""
    st.markdown("### Report Questions Management")
    
    # Initialize session state for questions
    if "report_questions" not in st.session_state:
        st.session_state.report_questions = {
            prog: GRANT_PROGRAMS[prog]["report_questions"].copy() 
            for prog in GRANT_PROGRAMS
        }
    
    questions = st.session_state.report_questions[program]
    
    # Display and edit existing questions
    for i, question in enumerate(questions):
        with st.container():
            st.markdown(f'<div class="question-box">', unsafe_allow_html=True)
            col1, col2 = st.columns([0.9, 0.1])
            
            with col1:
                edited_question = st.text_area(
                    f"Question {i+1}",
                    value=question,
                    key=f"question_{program}_{i}",
                    height=100
                )
                if edited_question != question:
                    questions[i] = edited_question
                    st.success("Question updated successfully!")
                    
            with col2:
                if st.button("Delete", key=f"delete_q_{program}_{i}"):
                    if st.button("Confirm Delete", key=f"confirm_delete_q_{program}_{i}"):
                        questions.pop(i)
                        st.success("Question deleted successfully!")
                        st.rerun()
                        
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Add new question
    st.markdown("### Add New Question")
    new_question = st.text_area("New Question", key=f"new_question_{program}")
    
    if st.button("Add Question"):
        if new_question:
            questions.append(new_question)
            st.success("New question added successfully!")
            st.rerun()
        else:
            st.warning("Please enter a question.") 