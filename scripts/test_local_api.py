#!/usr/bin/env python3
"""
test_local_api.py - Test script for local deep research API
Tests the request/response format before using it in production scripts
"""

import json
import requests
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, Any, Optional

# Local API endpoint
API_BASE_URL = "http://127.0.0.1:2024"
ASSISTANT_ID = "deep_researcher"  # From langgraph.json

async def test_sync_invoke():
    """Test synchronous invocation endpoint"""
    print("Testing Synchronous Invoke Endpoint...")
    
    url = f"{API_BASE_URL}/runs/stream"
    
    # Test payload based on the configuration
    payload = {
        "assistant_id": ASSISTANT_ID,
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": "What are the latest developments in quantum computing hardware in 2024?"
                }
            ]
        },
        "config": {
            "configurable": {
                # Based on configuration.py defaults
                "search_api": "openai",
                "max_researcher_iterations": 2,
                "max_concurrent_research_units": 3,
                "research_model": "openai:gpt-4.1",
                "allow_clarification": False  # Skip clarification for testing
            }
        },
        "stream_mode": ["values"]
    }
    
    try:
        print(f"Sending request to: {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            stream=True,
            timeout=300
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            print("\nStreaming response:")
            events = []
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('event:'):
                        event_type = line_str.split(':', 1)[1].strip()
                        print(f"  Event type: {event_type}")
                    elif line_str.startswith('data:'):
                        data_str = line_str.split(':', 1)[1].strip()
                        try:
                            data = json.loads(data_str)
                            events.append(data)
                            
                            # Print key information
                            if "final_report" in data:
                                print(f"  Final report received (length: {len(data['final_report'])} chars)")
                            if "notes" in data and data["notes"]:
                                print(f"  Notes collected: {len(data['notes'])} items")
                            if "research_brief" in data:
                                print(f"  Research brief: {data['research_brief'][:100]}...")
                                
                        except json.JSONDecodeError:
                            print(f"  Raw data: {data_str[:100]}...")
            
            return events
        else:
            print(f"Error response: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error testing sync invoke: {e}")
        return None

async def test_async_invoke():
    """Test asynchronous invocation with aiohttp"""
    print("\n\nTesting Asynchronous Invoke...")
    
    url = f"{API_BASE_URL}/runs/stream"
    
    payload = {
        "assistant_id": ASSISTANT_ID,
        "input": {
            "messages": [
                {
                    "role": "user", 
                    "content": "What are the key risks facing Tesla in 2024?"
                }
            ]
        },
        "config": {
            "configurable": {
                "search_api": "openai",
                "max_researcher_iterations": 1,
                "max_concurrent_research_units": 2,
                "allow_clarification": False,
                "research_model": "openai:gpt-4.1-mini"  # Faster model for testing
            }
        },
        "stream_mode": ["values"]
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            print(f"Sending async request...")
            
            async with session.post(url, json=payload) as response:
                print(f"Response status: {response.status}")
                
                if response.status == 200:
                    final_result = None
                    
                    async for line in response.content:
                        line_str = line.decode('utf-8').strip()
                        if line_str.startswith('data:'):
                            data_str = line_str.split(':', 1)[1].strip()
                            try:
                                data = json.loads(data_str)
                                if "final_report" in data:
                                    final_result = data
                                    print("Final report received!")
                            except:
                                pass
                    
                    return final_result
                else:
                    error_text = await response.text()
                    print(f"Error: {error_text}")
                    return None
                    
        except Exception as e:
            print(f"Error in async test: {e}")
            return None

def test_api_info():
    """Test API info endpoints"""
    print("Testing API Info Endpoints...\n")
    
    # Test assistants endpoint
    try:
        response = requests.get(f"{API_BASE_URL}/assistants")
        if response.status_code == 200:
            assistants = response.json()
            print(f"Available assistants: {json.dumps(assistants, indent=2)}")
        else:
            print(f"Failed to get assistants: {response.status_code}")
    except Exception as e:
        print(f"Error getting assistants: {e}")
    
    # Test specific assistant info
    try:
        response = requests.get(f"{API_BASE_URL}/assistants/{ASSISTANT_ID}")
        if response.status_code == 200:
            assistant_info = response.json()
            print(f"\nAssistant '{ASSISTANT_ID}' info:")
            print(f"  - Config schema available: {'config_schema' in assistant_info}")
            if 'config_schema' in assistant_info:
                schema = assistant_info['config_schema']
                if 'properties' in schema:
                    print("  - Configurable properties:")
                    for prop, details in schema['properties'].items():
                        default = details.get('default', 'N/A')
                        print(f"    - {prop}: {default}")
        else:
            print(f"Failed to get assistant info: {response.status_code}")
    except Exception as e:
        print(f"Error getting assistant info: {e}")

def analyze_response_format(events: list) -> Dict[str, Any]:
    """Analyze the response format from the API"""
    analysis = {
        "total_events": len(events),
        "event_types": set(),
        "final_report_found": False,
        "notes_found": False,
        "research_brief_found": False,
        "message_structure": None
    }
    
    for event in events:
        if isinstance(event, dict):
            analysis["event_types"].update(event.keys())
            
            if "final_report" in event:
                analysis["final_report_found"] = True
                analysis["final_report_length"] = len(event["final_report"])
                
            if "notes" in event and event["notes"]:
                analysis["notes_found"] = True
                analysis["notes_count"] = len(event["notes"])
                
            if "research_brief" in event:
                analysis["research_brief_found"] = True
                
            if "messages" in event and event["messages"]:
                # Analyze message structure
                msg = event["messages"][0] if isinstance(event["messages"], list) else event["messages"]
                if hasattr(msg, "__dict__"):
                    analysis["message_structure"] = type(msg).__name__
    
    return analysis

async def main():
    """Run all tests"""
    print("="*60)
    print("Testing Open Deep Research Local API")
    print("="*60)
    print(f"API URL: {API_BASE_URL}")
    print(f"Timestamp: {datetime.now()}")
    print("="*60)
    
    # Test API info first
    test_api_info()
    
    print("\n" + "="*60 + "\n")
    
    # Test synchronous invoke
    sync_events = await test_sync_invoke()
    
    if sync_events:
        print("\nAnalyzing sync response format:")
        analysis = analyze_response_format(sync_events)
        print(json.dumps(analysis, indent=2))
    
    # Test async invoke
    async_result = await test_async_invoke()
    
    if async_result:
        print("\nAsync result keys:", list(async_result.keys()))
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    if sync_events and any("final_report" in e for e in sync_events):
        print("✓ API is working correctly")
        print("✓ Streaming responses received")
        print("✓ Final report generated")
        
        # Extract final report for inspection
        for event in sync_events:
            if "final_report" in event:
                report = event["final_report"]
                print(f"\nFinal Report Preview (first 500 chars):")
                print(report[:500])
                print("...")
                break
    else:
        print("✗ API test failed - no final report received")
    
    print("\nResponse Format:")
    print("- Stream mode returns server-sent events (SSE)")
    print("- Each event has 'event:' and 'data:' lines")
    print("- Final event contains 'final_report' key")
    print("- Intermediate events may contain 'notes', 'research_brief', etc.")

if __name__ == "__main__":
    asyncio.run(main())