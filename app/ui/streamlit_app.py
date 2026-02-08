"""
Streamlit Frontend for Healthcare Compliance Copilot.

This module provides the user interface for document submission and results display.
"""

import streamlit as st
import requests
import base64
from typing import Optional, Dict, Any

# Page configuration
st.set_page_config(
    page_title="Healthcare Compliance Copilot",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# API endpoint (configurable via environment or default to localhost)
API_URL = "http://localhost:8000"


def display_header():
    """Display application header with title, description, and warnings."""
    st.title("🏥 Healthcare Compliance Copilot")
    
    st.markdown("""
    ### AI-Powered Document Analysis for Healthcare Compliance
    
    This tool analyzes healthcare documents for privacy and compliance risks, 
    identifying sensitive data exposure, compliance gaps, and missing safeguards.
    """)
    
    # Prominent warning
    st.warning(
        "⚠️ **IMPORTANT:** Use only synthetic or public data. "
        "Never upload real protected health information (PHI) or patient data."
    )
    
    # Disclaimer at top
    with st.expander("📋 Disclaimer - Please Read"):
        st.markdown("""
        **DISCLAIMER:** This tool is for educational and internal compliance awareness purposes only. 
        It does not constitute legal advice, medical advice, or professional compliance consultation. 
        Results are based on automated analysis and may not capture all risks. 
        Always consult qualified legal and compliance professionals for official guidance.
        """)


def display_input_section() -> tuple[Optional[str], Optional[bytes], Optional[str]]:
    """
    Display input section for text or file upload.
    
    Returns:
        Tuple of (text_input, file_bytes, file_type)
    """
    st.header("📄 Document Input")
    
    # Input method selection
    input_method = st.radio(
        "Choose input method:",
        ["Paste Text", "Upload File"],
        horizontal=True
    )
    
    text_input = None
    file_bytes = None
    file_type = None
    
    if input_method == "Paste Text":
        text_input = st.text_area(
            "Paste your document text here:",
            height=300,
            placeholder="Enter healthcare document text for analysis..."
        )
        
        if text_input:
            char_count = len(text_input)
            st.caption(f"Character count: {char_count:,} / 50,000")
            
            if char_count > 50000:
                st.error("❌ Document exceeds 50,000 character limit")
            elif char_count < 10:
                st.warning("⚠️ Document must be at least 10 characters")
    
    else:  # Upload File
        uploaded_file = st.file_uploader(
            "Upload a document file:",
            type=["txt", "pdf"],
            help="Supported formats: .txt, .pdf (max 50,000 characters)"
        )
        
        if uploaded_file:
            file_bytes = uploaded_file.read()
            file_type = uploaded_file.name.split(".")[-1].lower()
            
            # Show file info
            st.success(f"✅ File uploaded: {uploaded_file.name} ({len(file_bytes):,} bytes)")
    
    return text_input, file_bytes, file_type


def call_analysis_api(
    text: Optional[str] = None,
    file_bytes: Optional[bytes] = None,
    file_type: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Call the FastAPI analysis endpoint.
    
    Args:
        text: Document text (if pasting text)
        file_bytes: File content bytes (if uploading file)
        file_type: File type ('txt' or 'pdf')
        
    Returns:
        Analysis results dictionary or None if error
    """
    try:
        # Prepare request payload
        if text:
            payload = {"text": text}
        else:
            # Encode file content as base64
            file_content_b64 = base64.b64encode(file_bytes).decode('utf-8')
            payload = {
                "file_content": file_content_b64,
                "file_type": file_type
            }
        
        # Call API
        response = requests.post(
            f"{API_URL}/analyze",
            json=payload,
            timeout=30
        )
        
        # Check response
        if response.status_code == 200:
            return response.json()
        else:
            error_detail = response.json().get("detail", "Unknown error")
            st.error(f"❌ Analysis failed: {error_detail}")
            return None
            
    except requests.exceptions.ConnectionError:
        st.error(
            "❌ Cannot connect to API server. "
            "Please ensure the FastAPI backend is running at " + API_URL
        )
        return None
    except requests.exceptions.Timeout:
        st.error("❌ Request timed out. Please try again with a shorter document.")
        return None
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        return None


def display_results(results: Dict[str, Any]):
    """
    Display analysis results in a structured format.
    
    Args:
        results: Analysis results dictionary from API
    """
    st.header("📊 Analysis Results")
    
    # Score and risk level in columns
    col1, col2, col3 = st.columns([2, 2, 3])
    
    with col1:
        score = results["compliance_score"]
        
        # Color code based on score
        if score >= 80:
            score_color = "green"
            score_emoji = "✅"
        elif score >= 50:
            score_color = "orange"
            score_emoji = "⚠️"
        else:
            score_color = "red"
            score_emoji = "❌"
        
        st.metric(
            label="Compliance Score",
            value=f"{score}/100"
        )
        st.markdown(f"<h2 style='color: {score_color};'>{score_emoji} {score}/100</h2>", unsafe_allow_html=True)
    
    with col2:
        risk_level = results["risk_level"]
        
        # Color code risk level
        if risk_level == "Low":
            risk_color = "green"
            risk_emoji = "✅"
        elif risk_level == "Medium":
            risk_color = "orange"
            risk_emoji = "⚠️"
        else:
            risk_color = "red"
            risk_emoji = "❌"
        
        st.metric(
            label="Risk Level",
            value=risk_level
        )
        st.markdown(f"<h2 style='color: {risk_color};'>{risk_emoji} {risk_level} Risk</h2>", unsafe_allow_html=True)
    
    with col3:
        st.metric(
            label="Processing Time",
            value=f"{results['processing_time_ms']}ms"
        )
        st.metric(
            label="Analysis Timestamp",
            value=results['timestamp'].split('T')[0]
        )
    
    st.divider()
    
    # Sensitive Data section
    st.subheader("🔍 Detected Sensitive Data")
    
    sensitive_data = results.get("sensitive_data", [])
    
    if sensitive_data:
        # Group by type for better display
        data_by_type = {}
        for item in sensitive_data:
            data_type = item["type"]
            if data_type not in data_by_type:
                data_by_type[data_type] = []
            data_by_type[data_type].append(item)
        
        # Display in expandable sections
        for data_type, items in data_by_type.items():
            with st.expander(f"📌 {data_type.replace('_', ' ').title()} ({len(items)} found)"):
                for item in items:
                    col_a, col_b, col_c = st.columns([3, 2, 2])
                    with col_a:
                        st.text(f"Value: {item['value']}")
                    with col_b:
                        st.text(f"Location: {item['location']}")
                    with col_c:
                        st.text(f"Confidence: {item['confidence']:.0%}")
    else:
        st.success("✅ No sensitive data detected")
    
    st.divider()
    
    # Compliance Risks section
    st.subheader("⚠️ Compliance Risks")
    
    compliance_risks = results.get("compliance_risks", [])
    
    if compliance_risks:
        for risk in compliance_risks:
            severity = risk["severity"]
            
            # Severity badge color
            if severity == "high":
                badge_color = "red"
                badge_emoji = "🔴"
            elif severity == "medium":
                badge_color = "orange"
                badge_emoji = "🟠"
            else:
                badge_color = "yellow"
                badge_emoji = "🟡"
            
            with st.expander(
                f"{badge_emoji} {risk['type'].replace('_', ' ').title()} - "
                f"{severity.upper()} Severity"
            ):
                st.markdown(f"**Description:** {risk['description']}")
                if risk.get('location'):
                    st.markdown(f"**Location:** {risk['location']}")
    else:
        st.success("✅ No compliance risks identified")
    
    st.divider()
    
    # Suggestions section
    st.subheader("💡 Improvement Suggestions")
    
    suggestions = results.get("suggestions", [])
    
    if suggestions:
        for i, suggestion in enumerate(suggestions, 1):
            st.markdown(f"{i}. {suggestion}")
    else:
        st.info("No specific suggestions at this time")
    
    st.divider()
    
    # Disclaimer at bottom
    st.subheader("📋 Disclaimer")
    st.info(results.get("disclaimer", ""))


def main():
    """Main application function."""
    # Display header
    display_header()
    
    st.divider()
    
    # Display input section
    text_input, file_bytes, file_type = display_input_section()
    
    # Analyze button
    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        analyze_button = st.button(
            "🔍 Analyze Document",
            type="primary",
            use_container_width=True
        )
    
    # Handle analysis
    if analyze_button:
        # Validate input
        if not text_input and not file_bytes:
            st.error("❌ Please provide document text or upload a file")
        elif text_input and len(text_input) < 10:
            st.error("❌ Document must be at least 10 characters")
        elif text_input and len(text_input) > 50000:
            st.error("❌ Document exceeds 50,000 character limit")
        else:
            # Show loading spinner
            with st.spinner("🔄 Analyzing document... This may take a few seconds."):
                # Call API
                results = call_analysis_api(text_input, file_bytes, file_type)
                
                if results:
                    # Display results
                    st.success("✅ Analysis complete!")
                    display_results(results)


if __name__ == "__main__":
    main()
