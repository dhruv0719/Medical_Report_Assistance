# frontend/streamlit_app.py
import streamlit as st
from pathlib import Path
import sys
import time

# Add project root to path to allow imports from backend
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.orchestrator.pipeline import MedicalReportPipeline
from config.logging_config import setup_logging

# Setup logging
setup_logging()

# --- Page Configuration ---
st.set_page_config(
    page_title="Medical Report Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- App State ---
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False
if 'pipeline_result' not in st.session_state:
    st.session_state.pipeline_result = None

# --- UI Components ---

def render_header():
    """Renders the main header and disclaimer."""
    st.title("🏥 Medical Report Assistant")
    st.markdown("""
    ### AI-Powered Lab Report Explainer
    Upload your lab report to get simple explanations, identify abnormal values, and understand potential next steps.
    """)
    st.warning("""
    ⚠️ **IMPORTANT DISCLAIMER**: This tool provides educational information only. 
    It is **NOT** a substitute for professional medical advice, diagnosis, or treatment. 
    **Always consult your healthcare provider** with any questions about your health.
    """)

def render_sidebar():
    """Renders the sidebar with information and settings."""
    with st.sidebar:
        st.header("About This Assistant")
        st.info("""
        This AI-powered tool is designed to help you understand your medical lab reports. It uses a combination of rule-based systems and advanced language models (powered by Groq) to:
        - **Extract** key information from your report.
        - **Identify** values that are outside of normal ranges.
        - **Explain** what each test measures in plain language.
        - **Provide context** from a built-in medical knowledge base.
        - **Suggest** general next steps.
        """)
        
        st.header("🔒 Privacy")
        st.success("Your data is safe. Reports are processed in memory and are **not** stored or saved after you close the session.")
        
        st.markdown("---")
        st.caption("Developed as an MVP project.")

def render_results(result):
    """Renders the complete analysis result in organized tabs."""
    
    # --- Critical Alerts (Top Priority) ---
    if result.triage_result.critical_count > 0:
        st.error(f"""
        ### 🚨 CRITICAL ALERT DETECTED 🚨
        **{result.triage_result.recommendation}**
        
        The following results require immediate attention:
        """)
        for alert in result.triage_result.get_critical_alerts():
            st.markdown(f"- **{alert.test_name}**: {alert.value} {alert.unit} - {alert.message}")
        st.markdown("---")

    # --- Tabs for Organized Display ---
    tab_results, tab_explanations, tab_next_steps, tab_details = st.tabs([
        "📊 **Results Summary**", 
        "💬 **Explanations**", 
        "📋 **Next Steps**", 
        "🔍 **Full Details**"
    ])

    # --- Tab 1: Results Summary ---
    with tab_results:
        st.subheader("Your Test Results at a Glance")
        
        # Key metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Tests Analyzed", len(result.parsed_report.tests))
        col2.metric("Normal Results", len(result.parsed_report.get_normal_tests()))
        col3.metric("Abnormal Results", len(result.parsed_report.get_abnormal_tests()))
        
        st.markdown("---")
        
        # Detailed test table
        for test in result.parsed_report.tests:
            with st.container():
                cols = st.columns([3, 2, 3, 1])
                
                # Test Name with status icon
                status_icon = "✅" if not test.is_abnormal else "🔴"
                cols[0].markdown(f"**{status_icon} {test.name}**")
                
                # Value
                cols[1].markdown(f"**{test.value}** {test.unit}")
                
                # Reference Range
                cols[2].markdown(f"*Normal: {test.reference_range}*")
                
                # Flag
                if test.flag:
                    cols[3].warning(f"**{test.flag}**")

    # --- Tab 2: Explanations ---
    with tab_explanations:
        st.subheader("What Your Results Mean")
        if not result.explanations:
            st.info("No detailed explanations were generated for this report.")
        
        for test_name, explanation in result.explanations.items():
            # Expand abnormal results by default
            with st.expander(f"**{test_name}**", expanded=explanation.is_abnormal):
                st.markdown(explanation.explanation_text)
                if explanation.sources_used:
                    st.caption(f"📚 *Sources: {', '.join(explanation.sources_used)}*")

    # --- Tab 3: Next Steps ---
    with tab_next_steps:
        st.subheader("Recommended Next Steps")
        
        urgency_map = {
            "CRITICAL": ("error", "🚨"),
            "HIGH": ("warning", "⚠️"),
            "MODERATE": ("info", "🟡"),
            "ROUTINE": ("success", "✅"),
        }
        urgency_color, urgency_icon = urgency_map.get(result.triage_result.overall_urgency, ("secondary", "⚪"))
        
        st.markdown(f"### Overall Urgency: <span style='color:{urgency_color};'>{urgency_icon} {result.triage_result.overall_urgency}</span>", unsafe_allow_html=True)
        st.markdown(f"**Recommendation**: {result.triage_result.recommendation}")
        
        st.markdown("---")

        for step in result.triage_result.next_steps:
            st.markdown(f"- {step}")

    # --- Tab 4: Full Details ---
    with tab_details:
        st.subheader("Technical & Report Details")
        
        col1, col2 = st.columns(2)
        with col1:
            st.info("**Report Information**")
            st.json({
                "Patient ID": result.parsed_report.patient_id,
                "Report Date": result.parsed_report.report_date,
                "Lab Name": result.parsed_report.lab_name,
                "Report Type": result.parsed_report.report_type.value,
            })
        
        with col2:
            st.info("**Processing Metadata**")
            st.json({
                "Session ID": result.session_id,
                "Processing Time (s)": round(result.processing_time, 2),
                "Extraction Method": result.extraction_metadata.get('extraction_method'),
            })
        
        if result.parsed_report.impression:
            st.subheader("Clinical Impression from Report")
            st.text_area("", result.parsed_report.impression, height=150)
        
        st.subheader("Raw Extracted Text")
        st.text_area("", result.extracted_text, height=300)

# --- Main App Logic ---

def main():
    render_header()
    render_sidebar()
    
    # Create temp directory for uploads
    temp_dir = Path("temp_uploads")
    temp_dir.mkdir(exist_ok=True)
    
    uploaded_file = st.file_uploader(
        "Upload your lab report (PDF or TXT)",
        type=["pdf", "txt"],
        help="Drag and drop or click to upload."
    )
    
    if uploaded_file:
        # Save file temporarily
        temp_path = temp_dir / uploaded_file.name
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getvalue())
            
        # Process the file
        with st.spinner("🔬 Analyzing your report... This may take up to 30 seconds."):
            try:
                # Initialize the pipeline
                pipeline = MedicalReportPipeline(enable_llm=True, enable_audit=True)
                
                # Run the complete pipeline
                start_time = time.time()
                result = pipeline.process_file(temp_path)
                end_time = time.time()
                
                st.session_state.pipeline_result = result
                st.session_state.processing_complete = True
                
                st.success(f"Analysis complete in {end_time - start_time:.2f} seconds!")

            except Exception as e:
                st.error(f"An error occurred during processing: {e}")
                st.exception(e) # Display full traceback for debugging
            finally:
                # Clean up the temporary file
                if temp_path.exists():
                    temp_path.unlink()

    # Display results if processing is complete
    if st.session_state.processing_complete and st.session_state.pipeline_result:
        render_results(st.session_state.pipeline_result)

if __name__ == "__main__":
    main()