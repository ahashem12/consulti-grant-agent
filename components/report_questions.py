import streamlit as st
import time
from typing import List, Dict, Any

def render_reports():
   """Render detailed reports in the main area"""
   if st.session_state.reports:
      st.markdown("<h2 class='sub-header'>Detailed Project Reports</h2>", unsafe_allow_html=True)

      for project_name, report in st.session_state.reports.items():
         with st.expander(f"Report for: {project_name}"):
               st.markdown(f"**Project:** {project_name}")
               st.markdown(f"**Generated on:** {report['timestamp']}")

               for section in report["sections"]:
                  st.markdown(f"**Q: {section['question']}**")
                  st.markdown(f"{section['answer']}")

                  if section.get("sources"):
                     st.markdown(f"**Sources:** {', '.join(section['sources'])}")
   else:
      st.info("No reports available. Use the sidebar to generate reports.")
