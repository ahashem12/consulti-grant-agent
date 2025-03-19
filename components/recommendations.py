import streamlit as st
import pandas as pd

def render_recommendations():
    """Render recommendations in the main area"""
    if st.session_state.recommendations:
        st.markdown("<h2 class='sub-header'>Funding Recommendations</h2>", unsafe_allow_html=True)
        
        # Create summary table
        summary_data = []
        for project_name, rec in st.session_state.recommendations.items():
            if "error" not in rec:
                # Get funding decision and add appropriate emoji
                funding_decision = rec.get("funding_decision", "Pending")
                if funding_decision == "Fund":
                    decision_display = "✅ Fund"
                elif funding_decision == "Do Not Fund":
                    decision_display = "❌ Do Not Fund"
                elif funding_decision == "Partially Fund":
                    decision_display = "⚠️ Partially Fund"
                else:
                    decision_display = "❓ Pending"
                
                summary_data.append({
                    "Project": project_name,
                    "Decision": decision_display,
                    "Generated": rec["timestamp"],
                    "Summary": rec["recommendation"][:200] + "..."
                })
                
        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df, use_container_width=True)
            
        # Show detailed recommendations
        for project_name, rec in st.session_state.recommendations.items():
            with st.expander(f"Detailed Recommendation for: {project_name}"):
                if "error" in rec:
                    st.error(f"Error generating recommendation: {rec['error']}")
                else:
                    st.markdown(f"**Funding Decision:** {rec.get('funding_decision', 'Pending')}")
                    st.markdown("**Detailed Analysis:**")
                    st.markdown(rec["recommendation"])
    else:
        st.info("No recommendations available. Use the sidebar to generate recommendations.")