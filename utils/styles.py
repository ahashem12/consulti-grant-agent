import streamlit as st

def apply_custom_css():
    """Apply custom CSS styling"""
    st.markdown("""
        <style>
            /* Consulti branding */
            .consulti-brand {
                color: #1a5f7a;
                font-size: 2.8rem;
                font-weight: 700;
                margin-bottom: 0;
                padding-bottom: 0;
            }
            .consulti-subtitle {
                color: #666;
                font-size: 1.2rem;
                margin-top: 0;
                padding-top: 0;
            }
            .main-header {
                font-size: 2.5rem;
                color: #1a5f7a;
                margin-bottom: 1rem;
            }
            .sub-header {
                font-size: 1.8rem;
                color: #2c88a0;
                margin-bottom: 0.5rem;
            }
            .card {
                background-color: #f8f9fa;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                margin-bottom: 20px;
                border: 1px solid #e9ecef;
            }
            .info-box {
                background-color: #e5f6ff;
                border-left: 5px solid #1a5f7a;
                padding: 10px 15px;
                margin-bottom: 15px;
                border-radius: 4px;
            }
            .success-box {
                background-color: #d9f6e6;
                border-left: 5px solid #28a745;
                padding: 10px 15px;
                margin-bottom: 15px;
                border-radius: 4px;
            }
            .warning-box {
                background-color: #fff3cd;
                border-left: 5px solid #ffc107;
                padding: 10px 15px;
                margin-bottom: 15px;
                border-radius: 4px;
            }
            .danger-box {
                background-color: #f8d7da;
                border-left: 5px solid #dc3545;
                padding: 10px 15px;
                margin-bottom: 15px;
                border-radius: 4px;
            }
            .eligibility-met {
                color: #28a745;
                font-weight: bold;
            }
            .eligibility-not-met {
                color: #dc3545;
                font-weight: bold;
            }
            .chat-container {
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 15px;
                height: 400px;
                overflow-y: auto;
                margin-bottom: 10px;
                background-color: #fff;
            }
            .user-message {
                background-color: #e3f2fd;
                border-radius: 15px;
                padding: 8px 12px;
                margin: 5px 0;
                max-width: 80%;
                margin-left: auto;
                text-align: right;
            }
            .system-message {
                background-color: #f1f1f1;
                border-radius: 15px;
                padding: 8px 12px;
                margin: 5px 0;
                max-width: 80%;
            }
            /* Sidebar improvements */
            .css-1d391kg {
                background-color: #f8f9fa;
            }
            .stButton>button {
                width: 100%;
                border-radius: 4px;
                background-color: #1a5f7a;
                color: white;
            }
            .stButton>button:hover {
                background-color: #2c88a0;
            }
            /* Additional custom styles */
            .question-box {
                background-color: #f8f9fa;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 15px;
                border: 1px solid #e9ecef;
            }
            .question-box:hover {
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .original-question {
                color: #666;
                font-style: italic;
                margin-bottom: 10px;
            }
            .question-number {
                color: #1a5f7a;
                font-weight: bold;
                margin-right: 10px;
            }
            .tab-content {
                padding: 20px 0;
            }
        </style>
    """, unsafe_allow_html=True) 