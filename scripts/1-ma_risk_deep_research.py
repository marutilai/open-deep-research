#!/usr/bin/env python3
"""
ma_risk_deep_research.py - M&A-focused deep research using local Open Deep Research API
Generates deal-relevant external context for VDR risk analysis
"""

import argparse
import json
import os
import sys
import time
import traceback
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import hashlib
import asyncio
import aiohttp
import requests
from tqdm import tqdm
from pydantic import BaseModel, Field

# Local API configuration
API_BASE_URL = "http://127.0.0.1:2024"
ASSISTANT_ID = "Deep Researcher"

# Model configurations for local API
MODEL_CONFIGS = {
    "fast": {
        "research_model": "openai:gpt-4.1-mini",
        "final_report_model": "openai:gpt-4.1-mini",
        "max_researcher_iterations": 2,
        "max_concurrent_research_units": 3
    },
    "balanced": {
        "research_model": "openai:gpt-4.1",
        "final_report_model": "openai:gpt-4.1",
        "max_researcher_iterations": 3,
        "max_concurrent_research_units": 5
    },
    "comprehensive": {
        "research_model": "openai:gpt-4.1",
        "final_report_model": "openai:gpt-4.1",
        "max_researcher_iterations": 4,
        "max_concurrent_research_units": 5
    }
}

def load_sample_companies() -> List[str]:
    """Load sample companies from sample_companies.txt"""
    sample_file = Path(__file__).parent / "sample_companies.txt"
    companies = []
    if sample_file.exists():
        with open(sample_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    companies.append(line)
    return companies

# M&A-focused research angles
MA_RESEARCH_ANGLES = [
    "external_risk_summary",
    "risk_landscape_matrix", 
    "watch_factors",
    "red_flag_detection",
    "company_context"
]

# M&A-focused prompts
MA_PROMPTS = {
    "external_risk_summary": """Act as a due diligence analyst preparing background context for a potential M&A deal. 
Provide a detailed summary of potential external risks that would affect the valuation or operations of {company_name}, including:
- Regulatory changes and compliance requirements
- Geopolitical risks affecting operations or markets
- Supply chain vulnerabilities and dependencies
- Market competition and competitive threats
- Financial health signals from public filings or analyst sentiment
- Recent lawsuits, investigations, or regulatory actions
- Technology disruption risks
- ESG concerns and reputational risks

Cite sources with URLs when available. Focus on material risks that could impact deal value or integration success.""",

    "risk_landscape_matrix": """Generate a comprehensive 2x2 risk landscape matrix for {company_name}, categorizing external factors by:
- Likelihood (High/Low)
- Impact (High/Low)

Include:
- Industry-specific risks
- Macroeconomic conditions
- Geopolitical issues
- Regulatory changes
- Technology disruptions
- Market dynamics
- ESG factors

For each quadrant, list 3-5 specific risks with:
1. Brief description of the risk
2. Why it belongs in this quadrant
3. Potential financial or operational impact
4. Relevant news headlines or events

Provide sources and citations when available.""",

    "watch_factors": """Based on extensive public source research, list the top 5-7 external developments an M&A analyst should monitor 
that could influence the future performance and valuation of {company_name} in the next 12-18 months. 

For each development:
1. Describe the specific development or trend
2. Explain why it matters for M&A valuation
3. Classify as risk or opportunity
4. Identify specific signals or triggers to watch
5. Estimate timeline for potential impact
6. Quantify potential impact if possible (revenue %, market share, etc.)
7. Provide relevant sources

Focus on actionable intelligence that would affect deal timing, structure, or valuation.""",

    "red_flag_detection": """You are an M&A red flag analyst conducting deep due diligence. Using all available public information, identify anything in the last 24 months 
that could represent a material concern to potential acquirers of {company_name}. 

Investigate and report on:
- Legal actions, lawsuits, or settlements
- Regulatory investigations or enforcement actions  
- Executive turnover (especially CFO, CEO, or other C-suite)
- Financial restatements or accounting irregularities
- Unusual revenue recognition patterns
- Major customer losses or concentration issues
- Product recalls, safety issues, or quality problems
- Data breaches, security incidents, or IP theft
- Activist investor campaigns or proxy battles
- Auditor changes, going concern warnings, or qualified opinions
- Whistleblower complaints or internal investigations
- Supply chain disruptions or vendor issues
- Environmental violations or incidents
- Labor disputes or union actions

For each red flag found:
- Provide specific dates and timeline
- Include direct sources and links
- Rate severity as Critical/High/Medium
- Estimate potential financial impact
- Note any ongoing or unresolved issues""",

    "company_context": """Position {company_name} comprehensively within its business ecosystem for M&A evaluation. Provide detailed analysis of:

1. **Competitive Landscape**
   - Top 5-10 direct competitors with market share data
   - Competitive advantages and moats
   - Market position trends (gaining/losing share)
   - Emerging competitive threats

2. **Geographic and Market Dependencies**
   - Revenue breakdown by geography
   - Key market dependencies and concentration
   - Regulatory requirements by jurisdiction
   - Political/economic risks by region

3. **Industry Analysis**
   - Industry growth rates and projections
   - Key industry headwinds and tailwinds
   - Technology disruption threats
   - Regulatory trends affecting the industry

4. **External Dependencies**
   - Critical suppliers and supply chain risks
   - Technology platform dependencies
   - Key partnership dependencies
   - Infrastructure dependencies

5. **Stakeholder Sentiment**
   - Recent analyst ratings and price targets
   - Institutional investor changes
   - Employee sentiment (Glassdoor, layoffs, etc.)
   - Customer satisfaction trends

6. **Customer Dynamics**
   - Customer concentration (% revenue from top customers)
   - Customer churn indicators
   - Contract renewal risks
   - Pricing power trends

7. **Regulatory Environment**
   - Key regulatory bodies and oversight
   - Compliance requirements and costs
   - Pending regulatory changes
   - Historical compliance issues

Include recent developments, data points, and forward-looking assessments with sources."""
}

class RiskFinding(BaseModel):
    """Individual risk or opportunity finding"""
    category: str = Field(description="Risk, Opportunity, or Neutral")
    severity: str = Field(description="Critical, High, Medium, Low")
    likelihood: Optional[str] = Field(default=None, description="High, Medium, Low (for risk matrix)")
    impact: Optional[str] = Field(default=None, description="High, Medium, Low (for risk matrix)")
    title: str = Field(description="Brief title of the finding")
    description: str = Field(description="Detailed description")
    timeline: Optional[str] = Field(default=None, description="Timeline for impact")
    signals: Optional[List[str]] = Field(default=None, description="Signals to watch for")
    sources: List[str] = Field(description="Source URLs or citations")
    date: Optional[str] = Field(default=None, description="Date of the event/finding")
    confidence: str = Field(description="High, Medium, Low")

class MAResearch(BaseModel):
    """M&A-focused research output"""
    company_name: str = Field(description="Official company name")
    ticker: Optional[str] = Field(default=None, description="Stock ticker if public")
    research_angle: str = Field(description="The M&A research angle")
    summary: str = Field(description="Executive summary")
    findings: List[RiskFinding] = Field(description="List of findings")
    risk_matrix: Optional[Dict[str, List[Dict]]] = Field(default=None, description="2x2 risk matrix")
    data_points: Dict[str, Any] = Field(description="Key data points")
    sources_consulted: List[str] = Field(description="All sources consulted")
    research_timestamp: str = Field(description="Timestamp of research")
    research_quality: str = Field(description="Comprehensive, Good, Limited")
    raw_research: Optional[str] = Field(default=None, description="Raw research report")

def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="M&A-focused deep research using local API")
    ap.add_argument("--company", help="Company name to research")
    ap.add_argument("--sample", type=int, metavar="N",
                    help="Use company N from sample_companies.txt (1-based index)")
    ap.add_argument("--list-samples", action="store_true",
                    help="List all sample companies")
    ap.add_argument("--angles", nargs="+", choices=MA_RESEARCH_ANGLES + ["all"],
                    default=["external_risk_summary"],
                    help="Research angles to explore")
    ap.add_argument("--mode", choices=["fast", "balanced", "comprehensive"],
                    default="balanced",
                    help="Research mode (affects depth and model selection)")
    ap.add_argument("--output-dir", default="output/ma_deep_research",
                    help="Output directory")
    ap.add_argument("--cache-dir", default="cache/ma_deep_research",
                    help="Cache directory")
    ap.add_argument("--force-refresh", action="store_true",
                    help="Ignore cache and re-research")
    ap.add_argument("--api-url", default=API_BASE_URL,
                    help="Local API URL")
    ap.add_argument("--timeout", type=int, default=600,
                    help="API timeout in seconds")
    ap.add_argument("--create-integration", action="store_true",
                    help="Create system_context.md for VDR integration")
    return ap.parse_args()

def get_cache_key(company: str, angle: str, mode: str) -> str:
    """Generate cache key for a research query"""
    key_string = f"{company}|{angle}|{mode}|local_v1".lower()
    return hashlib.md5(key_string.encode()).hexdigest()

def load_from_cache(cache_dir: Path, cache_key: str) -> Optional[Dict]:
    """Load research from cache if available"""
    cache_file = cache_dir / f"{cache_key}.json"
    if cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load cache: {e}")
    return None

def save_to_cache(cache_dir: Path, cache_key: str, research: Dict):
    """Save research to cache"""
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{cache_key}.json"
    try:
        with open(cache_file, 'w') as f:
            json.dump(research, f, indent=2)
    except Exception as e:
        print(f"Warning: Failed to save cache: {e}")

def extract_findings_from_report(report: str, angle: str) -> List[RiskFinding]:
    """Extract structured findings from the research report"""
    findings = []
    
    # Simple extraction based on common patterns in research reports
    lines = report.split('\n')
    current_finding = None
    
    # Keywords that indicate findings
    risk_indicators = ['risk', 'concern', 'issue', 'problem', 'challenge', 'threat', 'vulnerability']
    opportunity_indicators = ['opportunity', 'advantage', 'benefit', 'strength', 'potential']
    severity_indicators = {
        'critical': ['critical', 'severe', 'major', 'significant'],
        'high': ['high', 'important', 'substantial'],
        'medium': ['medium', 'moderate', 'notable'],
        'low': ['low', 'minor', 'small']
    }
    
    for line in lines:
        line_lower = line.lower()
        
        # Check if this line contains a finding
        is_risk = any(indicator in line_lower for indicator in risk_indicators)
        is_opportunity = any(indicator in line_lower for indicator in opportunity_indicators)
        
        if (is_risk or is_opportunity) and len(line) > 20:
            # Determine severity
            severity = 'Medium'  # default
            for sev_level, keywords in severity_indicators.items():
                if any(keyword in line_lower for keyword in keywords):
                    severity = sev_level.capitalize()
                    break
            
            # Create finding
            title = line.strip()[:100]  # First 100 chars as title
            if ':' in title:
                title = title.split(':', 1)[0]
            
            finding = RiskFinding(
                category='Risk' if is_risk else 'Opportunity',
                severity=severity,
                title=title.strip(),
                description=line.strip(),
                sources=[],  # Would need more sophisticated parsing for sources
                confidence='Medium'
            )
            findings.append(finding)
    
    # If no findings extracted, create a general one
    if not findings and len(report) > 100:
        findings.append(RiskFinding(
            category='Neutral',
            severity='Medium',
            title=f'{angle.replace("_", " ").title()} Analysis',
            description=report[:500] + '...' if len(report) > 500 else report,
            sources=[],
            confidence='Medium'
        ))
    
    return findings

async def conduct_ma_research(api_url: str, company: str, angle: str, mode: str, timeout: int) -> MAResearch:
    """Conduct M&A-focused research using local API"""
    
    # Prepare the research prompt
    research_prompt = MA_PROMPTS.get(angle, "").format(company_name=company)
    
    # Get configuration for the selected mode
    config = MODEL_CONFIGS[mode]
    
    # Prepare API request
    url = f"{api_url}/runs/stream"
    payload = {
        "assistant_id": ASSISTANT_ID,
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": research_prompt
                }
            ]
        },
        "config": {
            "configurable": {
                "search_api": "openai",  # or "tavily" if you have API key
                "allow_clarification": False,
                **config
            }
        },
        "stream_mode": ["values"]
    }
    
    print(f"    Starting {angle} research with {mode} mode...")
    
    # Log payload size
    payload_str = json.dumps(payload)
    print(f"    Payload size: {len(payload_str)} chars, {len(payload_str.encode('utf-8'))} bytes")
    
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            async with session.post(url, json=payload) as response:
                print(f"    Response status: {response.status}")
                print(f"    Response headers: {dict(response.headers)}")
                
                if response.status != 200:
                    error_text = await response.text()
                    print(f"    Error response body: {error_text[:1000]}")  # First 1000 chars
                    raise Exception(f"API error {response.status}: {error_text}")
                
                # Process streaming response
                final_report = None
                research_notes = []
                line_count = 0
                total_bytes = 0
                
                async for line in response.content:
                    line_count += 1
                    total_bytes += len(line)
                    
                    try:
                        line_str = line.decode('utf-8').strip()
                    except UnicodeDecodeError as e:
                        print(f"    WARNING: Unicode decode error on line {line_count}: {e}")
                        continue
                    
                    if line_str.startswith('data:'):
                        data_str = line_str.split(':', 1)[1].strip()
                        try:
                            data = json.loads(data_str)
                            
                            # Log significant events
                            if "final_report" in data:
                                final_report = data["final_report"]
                                print(f"    Final report received: {len(final_report)} chars")
                                
                            if "notes" in data and data["notes"]:
                                research_notes.extend(data["notes"])
                                print(f"    Research notes received: {len(data['notes'])} items")
                                
                        except json.JSONDecodeError as e:
                            print(f"    WARNING: JSON decode error on line {line_count}: {e}")
                            print(f"    Data string: {data_str[:100]}...")
                            continue
                
                print(f"    Processed {line_count} lines, {total_bytes} bytes total")
                
                if not final_report:
                    raise Exception("No final report received from API")
                
                print(f"    Research completed (report length: {len(final_report)} chars)")
                
                # Extract findings from report
                findings = extract_findings_from_report(final_report, angle)
                
                # Extract company info from report
                ticker = None
                if "ticker:" in final_report.lower() or "symbol:" in final_report.lower():
                    # Simple ticker extraction
                    import re
                    ticker_match = re.search(r'\b([A-Z]{1,5})\b(?:\s+(?:on|listed|trades))', final_report)
                    if ticker_match:
                        ticker = ticker_match.group(1)
                
                # Create summary (first paragraph or first 500 chars)
                summary_end = min(final_report.find('\n\n') if '\n\n' in final_report else 500, 500)
                summary = final_report[:summary_end].strip()
                
                research = MAResearch(
                    company_name=company,
                    ticker=ticker,
                    research_angle=angle,
                    summary=summary,
                    findings=findings,
                    risk_matrix=None,  # Would need special parsing for risk matrix
                    data_points={
                        "research_mode": mode,
                        "report_length": len(final_report),
                        "notes_collected": len(research_notes)
                    },
                    sources_consulted=[],  # Would need to parse from report
                    research_timestamp=datetime.now().isoformat(),
                    research_quality="Comprehensive" if len(final_report) > 2000 else "Good" if len(final_report) > 1000 else "Limited",
                    raw_research=final_report
                )
                
                return research
                
    except asyncio.TimeoutError:
        print(f"    ERROR: Research timed out after {timeout} seconds")
        return MAResearch(
            company_name=company,
            research_angle=angle,
            summary=f"Research timed out after {timeout} seconds",
            findings=[],
            data_points={"error": "timeout", "timeout_seconds": timeout},
            sources_consulted=[],
            research_timestamp=datetime.now().isoformat(),
            research_quality="Limited"
        )
    except aiohttp.ClientError as e:
        print(f"    ERROR: Network/Client error: {type(e).__name__}: {str(e)}")
        print(f"    Full traceback:\n{traceback.format_exc()}")
        return MAResearch(
            company_name=company,
            research_angle=angle,
            summary=f"Network error: {type(e).__name__}: {str(e)}",
            findings=[],
            data_points={"error": str(e), "error_type": type(e).__name__},
            sources_consulted=[],
            research_timestamp=datetime.now().isoformat(),
            research_quality="Limited"
        )
    except Exception as e:
        print(f"    ERROR: {type(e).__name__}: {str(e)}")
        print(f"    Full traceback:\n{traceback.format_exc()}")
        
        # Try to extract more specific error info
        error_details = {
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }
        
        # Check if it's a specific error we can handle better
        error_msg = str(e).lower()
        if "chunk too big" in error_msg:
            print(f"    CHUNK TOO BIG ERROR DETECTED - this likely means the response exceeded size limits")
            error_details["chunk_error"] = True
        
        return MAResearch(
            company_name=company,
            research_angle=angle,
            summary=f"Research failed: {type(e).__name__}: {str(e)}",
            findings=[],
            data_points=error_details,
            sources_consulted=[],
            research_timestamp=datetime.now().isoformat(),
            research_quality="Limited"
        )

def save_research_results(output_dir: Path, company: str, ticker: Optional[str], research_results: List[MAResearch], create_integration: bool):
    """Save M&A research results"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    company_slug = company.lower().replace(" ", "_").replace(".", "")
    
    # Create company-specific directory
    company_dir = output_dir / company_slug
    company_dir.mkdir(parents=True, exist_ok=True)
    
    # Save individual angle results
    for research in research_results:
        angle_file = company_dir / f"{research.research_angle}_{timestamp}.json"
        with open(angle_file, 'w') as f:
            json.dump(research.model_dump(exclude={'raw_research'}), f, indent=2)
        
        # Save raw research separately
        if research.raw_research:
            raw_file = company_dir / f"{research.research_angle}_{timestamp}_raw.md"
            with open(raw_file, 'w') as f:
                f.write(research.raw_research)
    
    # Create consolidated report
    total_findings = sum(len(r.findings) for r in research_results)
    critical_risks = sum(1 for r in research_results for f in r.findings 
                        if f.category == "Risk" and f.severity == "Critical")
    high_risks = sum(1 for r in research_results for f in r.findings 
                    if f.category == "Risk" and f.severity == "High")
    opportunities = sum(1 for r in research_results for f in r.findings 
                       if f.category == "Opportunity")
    
    # Create markdown summary
    summary_file = company_dir / f"ma_research_summary_{timestamp}.md"
    with open(summary_file, 'w') as f:
        f.write(f"# M&A Deep Research: {company}")
        if ticker:
            f.write(f" ({ticker})")
        f.write("\n\n")
        f.write(f"**Research Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"**Research API:** Local Open Deep Research\n")
        f.write(f"**Research Angles:** {', '.join([r.research_angle.replace('_', ' ').title() for r in research_results])}\n\n")
        
        f.write("## Executive Summary\n\n")
        f.write(f"- **Total Findings:** {total_findings}\n")
        f.write(f"- **Critical Risks:** {critical_risks}\n")
        f.write(f"- **High Risks:** {high_risks}\n")
        f.write(f"- **Opportunities:** {opportunities}\n\n")
        
        # Add research summaries by angle
        for research in research_results:
            f.write(f"## {research.research_angle.replace('_', ' ').title()}\n\n")
            
            if research.summary:
                f.write(f"**Summary:** {research.summary}\n\n")
            
            f.write(f"**Research Quality:** {research.research_quality}\n\n")
            
            # Add raw research if available
            if research.raw_research:
                f.write("### Full Research Report\n\n")
                f.write(research.raw_research)
                f.write("\n\n")
            
            f.write("---\n\n")
    
    # Create integration file if requested
    if create_integration:
        integration_file = company_dir / f"system_context_{timestamp}.md"
        with open(integration_file, 'w') as f:
            f.write(f"# System Context for {company} VDR Analysis\n\n")
            f.write("You are an AI assistant helping a user review documents for ")
            f.write(f"{company}'s Virtual Data Room (VDR). The following external context has been ")
            f.write("compiled from public sources and should inform your interpretation ")
            f.write("of document risk. Keep this context in mind for all questions:\n\n")
            
            # Add all research reports
            for research in research_results:
                if research.raw_research and research.research_quality != "Limited":
                    f.write(f"## {research.research_angle.replace('_', ' ').title()}\n\n")
                    f.write(research.raw_research)
                    f.write("\n\n---\n\n")
            
            f.write(f"*Context compiled: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")
    
    print(f"\nM&A Research results saved to: {company_dir}")
    print(f"  - Individual angles: {len(research_results)} JSON + MD files")
    print(f"  - Summary: {summary_file.name}")
    if create_integration:
        print(f"  - Integration context: {integration_file.name}")
    
    return summary_file

async def main():
    args = parse_args()
    
    # Load sample companies
    sample_companies = load_sample_companies()
    
    # Handle --list-samples
    if args.list_samples:
        print("Sample companies available:")
        for i, company in enumerate(sample_companies, 1):
            print(f"  {i}. {company}")
        sys.exit(0)
    
    # Determine which company to research
    if args.sample:
        if args.sample < 1 or args.sample > len(sample_companies):
            sys.exit(f"Sample index must be between 1 and {len(sample_companies)}")
        company = sample_companies[args.sample - 1]
        print(f"Using sample company #{args.sample}: {company}")
    elif args.company:
        company = args.company
    else:
        sys.exit("Please specify --company or --sample N (use --list-samples to see available companies)")
    
    # Check API availability - skip auth check, just verify base URL
    try:
        # Just check if the server is responding (will get 401 due to auth, but that's OK)
        response = requests.get(f"{args.api_url}/docs", timeout=5)
        # If we can connect, we'll get some response (even if it's 401)
    except Exception as e:
        sys.exit(f"Cannot connect to API at {args.api_url}: {e}\nMake sure to run: uvx --refresh --from 'langgraph-cli[inmem]' --with-editable . --python 3.11 langgraph dev --allow-blocking")
    
    # Set up directories
    output_dir = Path(args.output_dir)
    cache_dir = Path(args.cache_dir)
    
    # Determine which angles to research
    angles_to_research = MA_RESEARCH_ANGLES if "all" in args.angles else args.angles
    
    print(f"\nResearching company: {company}")
    print(f"Research angles: {', '.join(angles_to_research)}")
    print(f"Research mode: {args.mode}")
    print(f"API URL: {args.api_url}")
    
    # Conduct research for each angle
    research_results = []
    ticker = None
    
    for angle in tqdm(angles_to_research, desc="Research angles"):
        # Check cache
        cache_key = get_cache_key(company, angle, args.mode)
        
        if not args.force_refresh:
            cached = load_from_cache(cache_dir, cache_key)
            if cached:
                print(f"\n  Using cached results for {angle}")
                research = MAResearch(**cached)
                research_results.append(research)
                if research.ticker and not ticker:
                    ticker = research.ticker
                continue
        
        print(f"\n  Researching {angle}...")
        research = await conduct_ma_research(args.api_url, company, angle, args.mode, args.timeout)
        research_results.append(research)
        
        # Update ticker if found
        if research.ticker and not ticker:
            ticker = research.ticker
        
        # Save to cache (exclude raw_research to save space)
        cache_data = research.model_dump()
        cache_data.pop('raw_research', None)
        save_to_cache(cache_dir, cache_key, cache_data)
        
        # Brief pause between requests
        if angle != angles_to_research[-1]:
            await asyncio.sleep(2)
    
    # Save all results
    save_research_results(output_dir, company, ticker, research_results, args.create_integration)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"M&A Research Complete: {company}")
    if ticker:
        print(f"Ticker: {ticker}")
    print(f"{'='*60}")
    
    total_findings = sum(len(r.findings) for r in research_results)
    successful_researches = sum(1 for r in research_results if r.research_quality != "Limited")
    
    print(f"Successful researches: {successful_researches}/{len(research_results)}")
    print(f"Total findings extracted: {total_findings}")
    
    # Show research quality breakdown
    quality_counts = {}
    for r in research_results:
        quality_counts[r.research_quality] = quality_counts.get(r.research_quality, 0) + 1
    
    print("\nResearch Quality:")
    for quality, count in quality_counts.items():
        print(f"  - {quality}: {count}")

if __name__ == "__main__":
    asyncio.run(main())