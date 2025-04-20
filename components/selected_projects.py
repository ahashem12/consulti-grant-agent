import streamlit as st
import pandas as pd
from typing import Dict, Any
from config.constants import GRANT_PROGRAMS

def render_selected_projects():
    """Render selected projects in the main area"""
    print(f"[debug] st.session_state.selection_results {st.session_state.selection_results}")
    if st.session_state.selection_results:
        st.markdown("<h2 class='sub-header'>Selected Projects</h2>", unsafe_allow_html=True)

        # Create summary table
        summary_data = []
        print(f"[debug] -> st.session_state.selection_results -> {st.session_state.selection_results}")
        for project_name, result in st.session_state.selection_results.items():
            summary_data.append({
                "Project": project_name,
                "Selected": "✅ Yes" if result["selected"] else "❌ No",
                "Met Criteria": sum(1 for c in result["criteria"] if c["meets_criterion"]),
                "Failed Criteria": sum(1 for c in result["criteria"] if not c["meets_criterion"]),
                "Summary": result["summary"]
            })

        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df, use_container_width=True)

        # Show detailed results for each project
        for project_name, result in st.session_state.selection_results.items():
            with st.expander(f"Detailed Selection for: {project_name}"):
                st.markdown(f"**Overall Status: {'Selected ✅' if result['selected'] else 'Not Selected ❌'}**")
                st.markdown(f"**Summary:** {result['summary']}")

                # Create criteria table
                criteria_data = []
                for criterion in result["criteria"]:
                    criteria_data.append({
                        "Criterion": criterion["name"],
                        "Question": criterion["question"],
                        "Status": "✅ Met" if criterion["meets_criterion"] else "❌ Not Met",
                        "Evidence": criterion["answer"]
                    })

                if criteria_data:
                    criteria_df = pd.DataFrame(criteria_data)
                    st.dataframe(criteria_df, use_container_width=True)
    else:
        st.info("No Selected projects results available. Use the sidebar to Select Project.")