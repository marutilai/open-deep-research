"""
M&A Hypothesis Research Viewer
Executive-level visualization of deep research hypotheses for due diligence
"""

import streamlit as st
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="M&A Hypothesis Research Viewer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for executive presentation
st.markdown("""
<style>
    /* Main title styling */
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1e3a5f;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
    }
    
    /* Subtitle styling */
    .subtitle {
        font-size: 1.1rem;
        color: #6b7280;
        margin-bottom: 2rem;
    }
    
    /* Section headers */
    .section-header {
        font-size: 1.3rem;
        font-weight: 600;
        color: #2d5016;
        margin-top: 2rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e5e7eb;
    }
    
    /* Hypothesis cards */
    .hypothesis-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        border: 1px solid #e5e7eb;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        transition: all 0.3s ease;
    }
    
    .hypothesis-card:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        transform: translateY(-2px);
    }
    
    .hypothesis-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #1e3a5f;
        margin-bottom: 0.5rem;
    }
    
    .hypothesis-statement {
        font-size: 1rem;
        color: #374151;
        line-height: 1.6;
        margin-bottom: 1rem;
    }
    
    .rationale {
        font-size: 0.95rem;
        color: #6b7280;
        font-style: italic;
        margin-bottom: 1rem;
        padding-left: 1rem;
        border-left: 3px solid #ddd6fe;
    }
    
    .impact-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 0.5rem;
    }
    
    .impact-high {
        background-color: #fee2e2;
        color: #991b1b;
    }
    
    .impact-medium {
        background-color: #fef3c7;
        color: #92400e;
    }
    
    .impact-low {
        background-color: #dbeafe;
        color: #1e40af;
    }
    
    .priority-indicator {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        background-color: #f3f4f6;
        color: #374151;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 500;
    }
    
    .questions-section {
        margin-top: 1rem;
        padding-top: 1rem;
        border-top: 1px solid #e5e7eb;
    }
    
    .question-item {
        font-size: 0.9rem;
        color: #4b5563;
        margin-bottom: 0.5rem;
        padding-left: 1.5rem;
        position: relative;
    }
    
    .question-item:before {
        content: "▸";
        position: absolute;
        left: 0;
        color: #9ca3af;
    }
    
    /* Stats cards */
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        padding: 1.5rem;
        color: white;
        text-align: center;
    }
    
    .stat-number {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }
    
    .stat-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    
    /* Section filter pills */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 9999px;
        padding: 0.5rem 1.5rem;
        background-color: #f3f4f6;
        border: none;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #e5e7eb;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #4f46e5 !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# Constants
OUTPUT_BASE_DIR = Path("output/hypothesis_research")
SECTION_NAMES = {
    "company_overview": "Company Overview",
    "market_position_industry_dynamics": "Market Position & Industry",
    "customer_revenue_drivers": "Customer & Revenue",
    "geographic_footprint_exposure": "Geographic Footprint",
    "regulatory_policy_environment": "Regulatory Environment",
    "macroeconomic_environmental_social": "Macro & ESG Factors",
    "technology_operational_dependencies": "Technology & Operations",
    "strategic_partnerships_vendors": "Partnerships & Vendors",
    "recent_news_notable_events": "Recent News & Events",
    "forward_looking_risks_catalysts": "Forward-Looking Risks"
}

def load_available_companies() -> List[str]:
    """Load list of companies with hypothesis data"""
    companies = []
    if OUTPUT_BASE_DIR.exists():
        for company_dir in OUTPUT_BASE_DIR.iterdir():
            if company_dir.is_dir():
                # Check if there are hypothesis files
                hypothesis_files = list(company_dir.glob("*_hypotheses_list_*.json"))
                if hypothesis_files:
                    company_name = company_dir.name.replace("_", " ").title()
                    companies.append(company_name)
    return sorted(companies)

def load_company_hypotheses(company_name: str) -> Dict[str, List]:
    """Load all hypotheses for a company organized by section"""
    company_slug = company_name.lower().replace(" ", "_")
    company_dir = OUTPUT_BASE_DIR / company_slug
    
    hypotheses_by_section = {}
    
    if company_dir.exists():
        # Load all hypothesis files
        hypothesis_files = sorted(company_dir.glob("*_hypotheses_list_*.json"))
        
        for file_path in hypothesis_files:
            # Extract section name from filename
            filename = file_path.stem
            for section_key in SECTION_NAMES.keys():
                if filename.startswith(section_key):
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        hypotheses_by_section[section_key] = data.get('hypotheses', [])
                    break
    
    return hypotheses_by_section

def display_hypothesis_card(hypothesis: Dict, index: int):
    """Display a single hypothesis in a card format"""
    with st.container():
        st.markdown(f'<div class="hypothesis-card">', unsafe_allow_html=True)
        
        # Title
        title = hypothesis.get('title', f'Hypothesis {index}')
        st.markdown(f'<div class="hypothesis-title">📊 {title}</div>', unsafe_allow_html=True)
        
        # Hypothesis statement
        statement = hypothesis.get('hypothesis', '')
        if statement:
            st.markdown(f'<div class="hypothesis-statement">{statement}</div>', unsafe_allow_html=True)
        
        # Rationale
        rationale = hypothesis.get('rationale', '')
        if rationale:
            st.markdown(f'<div class="rationale">💡 {rationale}</div>', unsafe_allow_html=True)
        
        # Impact and Priority badges
        col1, col2, col3 = st.columns([2, 2, 8])
        
        with col1:
            impact = hypothesis.get('potential_impact', 'Medium')
            impact_class = f"impact-{impact.lower()}"
            st.markdown(
                f'<span class="impact-badge {impact_class}">Impact: {impact}</span>',
                unsafe_allow_html=True
            )
        
        with col2:
            priority = hypothesis.get('research_priority', 3)
            st.markdown(
                f'<span class="priority-indicator">Priority: {priority}/5</span>',
                unsafe_allow_html=True
            )
        
        # Research questions
        questions = hypothesis.get('testable_questions', [])
        if questions:
            st.markdown('<div class="questions-section">', unsafe_allow_html=True)
            st.markdown("**Research Questions:**")
            for question in questions:
                st.markdown(f'<div class="question-item">{question}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

def main():
    # Header
    st.markdown('<h1 class="main-header">M&A Hypothesis Research Platform</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Deep due diligence insights through AI-powered hypothesis generation and research</p>', unsafe_allow_html=True)
    
    # Load available companies
    companies = load_available_companies()
    
    if not companies:
        st.warning("No hypothesis data found. Please run the hypothesis generation scripts first.")
        st.info("Expected location: `output/hypothesis_research/`")
        return
    
    # Sidebar for company selection
    with st.sidebar:
        st.markdown("### 🏢 Company Selection")
        selected_company = st.selectbox(
            "Choose a company to view hypotheses:",
            companies,
            format_func=lambda x: x.upper() if x.lower() == "ideals" else x
        )
        
        st.markdown("---")
        
        # Load hypotheses for selected company
        hypotheses_data = load_company_hypotheses(selected_company)
        
        # Statistics
        st.markdown("### 📊 Overview Statistics")
        
        total_sections = len(hypotheses_data)
        total_hypotheses = sum(len(hyps) for hyps in hypotheses_data.values())
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Sections", total_sections)
        with col2:
            st.metric("Hypotheses", total_hypotheses)
        
        # Section breakdown
        if hypotheses_data:
            st.markdown("### 📋 Section Breakdown")
            section_stats = []
            for section, hyps in hypotheses_data.items():
                section_name = SECTION_NAMES.get(section, section)
                section_stats.append({
                    "Section": section_name,
                    "Count": len(hyps)
                })
            
            df = pd.DataFrame(section_stats)
            st.dataframe(df, hide_index=True, use_container_width=True)
    
    # Main content area
    if not hypotheses_data:
        st.info(f"No hypothesis data found for {selected_company}")
        return
    
    # Company header
    st.markdown(f"## 🎯 {selected_company}")
    st.markdown("---")
    
    # Create tabs for each section
    tab_names = []
    tab_sections = []
    
    # Add "All" tab first
    tab_names.append("📑 All Sections")
    tab_sections.append("all")
    
    # Add individual section tabs
    for section_key, section_name in SECTION_NAMES.items():
        if section_key in hypotheses_data:
            tab_names.append(f"{section_name}")
            tab_sections.append(section_key)
    
    tabs = st.tabs(tab_names)
    
    # All sections tab
    with tabs[0]:
        for section_key in hypotheses_data.keys():
            section_name = SECTION_NAMES.get(section_key, section_key)
            hypotheses = hypotheses_data[section_key]
            
            if hypotheses:
                st.markdown(f'<div class="section-header">{section_name}</div>', unsafe_allow_html=True)
                
                for i, hypothesis in enumerate(hypotheses, 1):
                    display_hypothesis_card(hypothesis, i)
    
    # Individual section tabs
    for tab, section_key in zip(tabs[1:], tab_sections[1:]):
        with tab:
            hypotheses = hypotheses_data.get(section_key, [])
            
            if hypotheses:
                # Section statistics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Hypotheses", len(hypotheses))
                
                with col2:
                    high_impact = sum(1 for h in hypotheses if h.get('potential_impact') == 'High')
                    st.metric("High Impact", high_impact)
                
                with col3:
                    priority_1 = sum(1 for h in hypotheses if h.get('research_priority') == 1)
                    st.metric("Priority 1", priority_1)
                
                st.markdown("---")
                
                # Display hypotheses
                for i, hypothesis in enumerate(hypotheses, 1):
                    display_hypothesis_card(hypothesis, i)
            else:
                st.info(f"No hypotheses found for {SECTION_NAMES[section_key]}")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #6b7280; font-size: 0.9rem; margin-top: 2rem;'>
        Generated by Open Deep Research | M&A Hypothesis Analysis Platform<br>
        <em>AI-powered due diligence insights for strategic decision-making</em>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()