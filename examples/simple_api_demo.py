#!/usr/bin/env python3
"""
Simple demonstration of the Open Deep Research local API.
Shows basic usage and cost tracking functionality.
No user input required - runs with hardcoded example.
"""

import asyncio
import json
import time
from datetime import datetime
import aiohttp

# API Configuration
API_BASE_URL = "http://127.0.0.1:2024"
ASSISTANT_ID = "Deep Researcher"

# Hardcoded research topic (no user input needed)
RESEARCH_TOPIC = "The impact of artificial intelligence on software development productivity"

async def run_research():
    """Run a simple research query and display results with cost tracking"""
    
    print("🔬 Open Deep Research - Simple API Demo")
    print("=" * 60)
    print(f"Topic: {RESEARCH_TOPIC}")
    print("=" * 60)
    
    # Prepare the API request
    url = f"{API_BASE_URL}/runs/stream"
    payload = {
        "assistant_id": ASSISTANT_ID,
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": f"Research the following topic and provide a comprehensive report: {RESEARCH_TOPIC}"
                }
            ]
        },
        "config": {
            "configurable": {
                "search_api": "tavily",  # or "openai" for OpenAI search
                "allow_clarification": False,
                "research_model": "openai:gpt-4o-mini",
                "final_report_model": "openai:gpt-4o-mini",
                "max_researcher_iterations": 2,
                "max_concurrent_research_units": 3
            }
        },
        "stream_mode": ["values"]
    }
    
    print("\n🚀 Starting research...")
    start_time = time.time()
    
    try:
        # Make the API request
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=300)) as response:
                if response.status != 200:
                    error_text = await response.text()
                    print(f"❌ API Error {response.status}: {error_text}")
                    return
                
                # Process the streaming response
                final_report = None
                research_notes = []
                cost_tracking = None
                
                async for line in response.content:
                    if not line:
                        continue
                    
                    line_str = line.decode('utf-8').strip()
                    if line_str.startswith('data:'):
                        data_str = line_str.split(':', 1)[1].strip()
                        try:
                            data = json.loads(data_str)
                            
                            # Collect research notes
                            if "notes" in data and data["notes"]:
                                research_notes.extend(data["notes"])
                                print(f"📝 Collected {len(data['notes'])} research notes")
                            
                            # Get final report
                            if "final_report" in data:
                                final_report = data["final_report"]
                                print(f"✅ Final report received ({len(final_report)} characters)")
                            
                            # Extract cost tracking data
                            if "cost_tracking" in data and data["cost_tracking"]:
                                cost_tracking = data["cost_tracking"]
                                
                        except json.JSONDecodeError:
                            continue
                
                # Calculate total time
                end_time = time.time()
                duration = end_time - start_time
                
                # Display results
                print("\n" + "=" * 60)
                print("📊 RESEARCH RESULTS")
                print("=" * 60)
                
                if final_report:
                    print("\n📄 Final Report Preview (first 1000 characters):")
                    print("-" * 40)
                    print(final_report[:1000])
                    if len(final_report) > 1000:
                        print(f"\n... (truncated, full report is {len(final_report)} characters)")
                    print("-" * 40)
                
                # Display timing information
                print(f"\n⏱️  Total Time: {duration:.1f} seconds")
                print(f"📝 Research Notes Collected: {len(research_notes)}")
                
                # Display cost tracking if available
                if cost_tracking:
                    print("\n💰 COST TRACKING")
                    print("-" * 40)
                    print(f"Total Cost: ${cost_tracking.get('total_cost', 0):.4f}")
                    
                    if "by_model" in cost_tracking:
                        print("\nCost by Model:")
                        for model, stats in cost_tracking["by_model"].items():
                            print(f"  {model}:")
                            print(f"    - Calls: {stats.get('calls', 0)}")
                            print(f"    - Cost: ${stats.get('cost', 0):.4f}")
                    
                    if "total_input_tokens" in cost_tracking:
                        print(f"\nToken Usage:")
                        print(f"  - Input Tokens: {cost_tracking['total_input_tokens']:,}")
                        print(f"  - Output Tokens: {cost_tracking['total_output_tokens']:,}")
                        print(f"  - Total Tokens: {cost_tracking['total_input_tokens'] + cost_tracking['total_output_tokens']:,}")
                    
                    print("-" * 40)
                else:
                    print("\n💰 Cost tracking data not available")
                
                # Save full report to file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"research_output_{timestamp}.md"
                with open(output_file, 'w') as f:
                    f.write(f"# Research Report: {RESEARCH_TOPIC}\n\n")
                    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Duration: {duration:.1f} seconds\n")
                    if cost_tracking:
                        f.write(f"Total Cost: ${cost_tracking.get('total_cost', 0):.4f}\n")
                    f.write("\n---\n\n")
                    f.write(final_report or "No report generated")
                
                print(f"\n💾 Full report saved to: {output_file}")
                
    except asyncio.TimeoutError:
        print("❌ Request timed out after 5 minutes")
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)}")

def main():
    """Main entry point"""
    print("🔍 Open Deep Research - Local API Demo")
    print("This demo shows how to use the local API with cost tracking")
    print()
    
    # Check if API is running
    print("Checking API availability...")
    try:
        import requests
        response = requests.get(f"{API_BASE_URL}/docs", timeout=2)
        print("✅ API is running")
    except Exception:
        print("❌ API is not running!")
        print("\nPlease start the API server with:")
        print("uvx --refresh --from 'langgraph-cli[inmem]' --with-editable . --python 3.11 langgraph dev --allow-blocking")
        return
    
    # Run the research
    asyncio.run(run_research())

if __name__ == "__main__":
    main()