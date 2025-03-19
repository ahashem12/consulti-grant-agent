import streamlit as st
import pandas as pd
from typing import Dict, Any
from config.constants import GRANT_PROGRAMS

def render_eligibility_results():
    """Render eligibility results in the main area"""
    if st.session_state.eligibility_results:
        st.markdown("<h2 class='sub-header'>Eligibility Results</h2>", unsafe_allow_html=True)

        # Create summary table
        summary_data = []
        for project_name, result in st.session_state.eligibility_results.items():
            summary_data.append({
                "Project": project_name,
                "Eligible": "✅ Yes" if result["eligible"] else "❌ No",
                "Met Criteria": sum(1 for c in result["criteria"] if c["meets_criterion"]),
                "Failed Criteria": sum(1 for c in result["criteria"] if not c["meets_criterion"]),
                "Summary": result["summary"]
            })

        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df, use_container_width=True)

        # Show detailed results for each project
        for project_name, result in st.session_state.eligibility_results.items():
            with st.expander(f"Detailed Eligibility for: {project_name}"):
                st.markdown(f"**Overall Status: {'Eligible ✅' if result['eligible'] else 'Not Eligible ❌'}**")
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
        st.info("No eligibility results available. Use the sidebar to check eligibility.")