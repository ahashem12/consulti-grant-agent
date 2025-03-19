import streamlit as st
from typing import Dict, Any, List
import time
from GrantRAG.config.constants import GRANT_PROGRAMS

def render_eligibility_criteria(program: str) -> None:
    """Render the eligibility criteria management interface."""
    if program not in GRANT_PROGRAMS:
        st.error("Invalid program selected.")
        return
        
    st.markdown('<h2 class="main-header">Eligibility Criteria Management</h2>', 
                unsafe_allow_html=True)
    
    # Initialize session state for criteria
    if "eligibility_criteria" not in st.session_state:
        st.session_state.eligibility_criteria = {
            prog: GRANT_PROGRAMS[prog]["eligibility_criteria"].copy() 
            for prog in GRANT_PROGRAMS
        }
    
    criteria = st.session_state.eligibility_criteria[program]
    
    # Display and edit existing criteria
    for i, (name, criterion) in enumerate(criteria.items()):
        with st.container():
            st.markdown(f'<div class="question-box">', unsafe_allow_html=True)
            col1, col2 = st.columns([0.9, 0.1])
            
            with col1:
                edited_criterion = st.text_area(
                    f"{name}",
                    value=criterion,
                    key=f"criterion_{program}_{i}_edit",
                    height=100
                )
                if edited_criterion != criterion:
                    criteria[name] = edited_criterion
                    st.success("Criterion updated successfully!")
                    
            with col2:
                if st.button("Delete", key=f"delete_criterion_{program}_{i}"):
                    if st.button("Confirm Delete", 
                               key=f"confirm_delete_criterion_{program}_{i}"):
                        del criteria[name]
                        st.success("Criterion deleted successfully!")
                        st.experimental_rerun()
                        
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Add new criterion
    st.markdown("### Add New Criterion")
    new_name = st.text_input("Criterion Name", key=f"new_criterion_name_{program}")
    new_criterion = st.text_area(
        "Criterion Question",
        key=f"new_criterion_input_{program}"
    )
    
    if st.button("Add Criterion", key=f"add_criterion_{program}"):
        if new_name.strip() and new_criterion.strip():
            criteria[new_name] = new_criterion
            st.success("New criterion added successfully!")
            st.experimental_rerun()
        else:
            st.warning("Please enter both a name and a criterion before adding.")

def render_report_questions(program: str) -> None:
    """Render the report questions management interface."""
    if program not in GRANT_PROGRAMS:
        st.error("Invalid program selected.")
        return
        
    st.markdown('<h2 class="main-header">Report Questions Management</h2>', 
                unsafe_allow_html=True)
    
    # Initialize session state for questions
    if "report_questions" not in st.session_state:
        st.session_state.report_questions = {
            prog: GRANT_PROGRAMS[prog]["report_questions"].copy() 
            for prog in GRANT_PROGRAMS
        }
    
    questions = st.session_state.report_questions[program]
    timestamp = int(time.time())  # Unique timestamp for keys
    
    # Display and edit existing questions
    for i, question in enumerate(questions):
        with st.container():
            st.markdown(f'<div class="question-box">', unsafe_allow_html=True)
            col1, col2 = st.columns([0.9, 0.1])
            
            with col1:
                edited_question = st.text_area(
                    f"Question {i+1}",
                    value=question,
                    key=f"report_question_{program}_{i}_edit_{timestamp}",
                    height=100
                )
                if edited_question != question:
                    questions[i] = edited_question
                    st.success("Question updated successfully!")
                    
            with col2:
                if st.button("Delete", key=f"delete_question_{program}_{i}_{timestamp}"):
                    if st.button("Confirm Delete", 
                               key=f"confirm_delete_question_{program}_{i}_{timestamp}"):
                        questions.pop(i)
                        st.success("Question deleted successfully!")
                        st.experimental_rerun()
                        
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Add new question
    st.markdown("### Add New Question")
    new_question = st.text_area(
        "Enter new question",
        key=f"new_report_question_input_{program}_{timestamp}"
    )
    
    if st.button("Add Question", key=f"add_question_{program}_{timestamp}"):
        if new_question.strip():
            questions.append(new_question)
            st.success("New question added successfully!")
            st.experimental_rerun()
        else:
            st.warning("Please enter a question before adding.")

def render_program_management() -> None:
    """Render the program management interface with tabs."""
    if st.session_state.selected_program is None:
        st.warning("Please select a grant program from the sidebar to manage program details.")
        return
        
    program = st.session_state.selected_program
    
    # Create tabs for different management sections
    tab1, tab2 = st.tabs(["Eligibility Criteria", "Report Questions"])
    
    with tab1:
        render_eligibility_criteria(program)
        
    with tab2:
        render_report_questions(program) 