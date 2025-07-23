"""Cost tracking for LLM API calls in Open Deep Research"""

import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
import tiktoken
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage


@dataclass
class TokenUsage:
    """Track token usage for a single call"""
    model: str
    input_tokens: int
    output_tokens: int
    timestamp: float
    duration: float
    task: str = ""
    

@dataclass 
class CostTracker:
    """Track costs across all LLM calls"""
    usage_records: List[TokenUsage] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    
    def estimate_tokens(self, text: str, model: str) -> int:
        """Estimate token count for text using tiktoken"""
        try:
            # Map model names to tiktoken encoding
            encoding_map = {
                "gpt-4": "cl100k_base",
                "gpt-3.5": "cl100k_base",
                "claude": "cl100k_base",  # Approximate
                "gemini": "cl100k_base",  # Approximate
            }
            
            # Find the right encoding
            encoding_name = "cl100k_base"  # default
            for key, enc in encoding_map.items():
                if key in model.lower():
                    encoding_name = enc
                    break
            
            encoding = tiktoken.get_encoding(encoding_name)
            return len(encoding.encode(text))
        except Exception:
            # Fallback: estimate ~4 chars per token
            return len(text) // 4
    
    def estimate_messages_tokens(self, messages: List[BaseMessage], model: str) -> int:
        """Estimate tokens for a list of messages"""
        total = 0
        for msg in messages:
            # Add message content
            total += self.estimate_tokens(str(msg.content), model)
            # Add overhead for message structure (role, etc)
            total += 4  # Approximate overhead
        return total
    
    def add_call(self, model: str, input_tokens: int, output_tokens: int, 
                 duration: float, task: str = ""):
        """Add a single API call to tracking"""
        self.usage_records.append(TokenUsage(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            timestamp=time.time(),
            duration=duration,
            task=task
        ))
    
    def reset(self):
        """Reset the tracker for a new session"""
        self.usage_records = []
        self.start_time = time.time()
    
    def get_cost_summary(self, model_pricing: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """Calculate total costs based on pricing configuration"""
        summary = {
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost": 0.0,
            "total_duration": 0.0,
            "by_model": {},
            "by_task": {}
        }
        
        for record in self.usage_records:
            # Get pricing for this model
            pricing = model_pricing.get(record.model, model_pricing.get("default", {"input": 1.0, "output": 2.0}))
            
            # Calculate cost for this record
            input_cost = (record.input_tokens / 1_000_000) * pricing["input"]
            output_cost = (record.output_tokens / 1_000_000) * pricing["output"]
            total_cost = input_cost + output_cost
            
            # Update totals
            summary["total_input_tokens"] += record.input_tokens
            summary["total_output_tokens"] += record.output_tokens
            summary["total_cost"] += total_cost
            summary["total_duration"] += record.duration
            
            # Track by model
            if record.model not in summary["by_model"]:
                summary["by_model"][record.model] = {
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cost": 0.0,
                    "calls": 0,
                    "duration": 0.0
                }
            summary["by_model"][record.model]["input_tokens"] += record.input_tokens
            summary["by_model"][record.model]["output_tokens"] += record.output_tokens
            summary["by_model"][record.model]["cost"] += total_cost
            summary["by_model"][record.model]["calls"] += 1
            summary["by_model"][record.model]["duration"] += record.duration
            
            # Track by task
            task = record.task or "unknown"
            if task not in summary["by_task"]:
                summary["by_task"][task] = {
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cost": 0.0,
                    "calls": 0,
                    "duration": 0.0
                }
            summary["by_task"][task]["input_tokens"] += record.input_tokens
            summary["by_task"][task]["output_tokens"] += record.output_tokens
            summary["by_task"][task]["cost"] += total_cost
            summary["by_task"][task]["calls"] += 1
            summary["by_task"][task]["duration"] += record.duration
        
        # Add timing info
        summary["total_time"] = time.time() - self.start_time
        summary["timestamp"] = datetime.now().isoformat()
        
        return summary
    
    def print_summary(self, model_pricing: Dict[str, Dict[str, float]]):
        """Print a formatted cost summary"""
        summary = self.get_cost_summary(model_pricing)
        
        print("\n" + "="*60)
        print("COST & PERFORMANCE SUMMARY")
        print("="*60)
        
        # Overall stats
        print(f"\nTotal Time: {summary['total_time']:.1f}s")
        print(f"Total API Time: {summary['total_duration']:.1f}s")
        print(f"Total Cost: ${summary['total_cost']:.3f}")
        print(f"Total Tokens: {summary['total_input_tokens']:,} input, {summary['total_output_tokens']:,} output")
        
        # By model breakdown
        if summary["by_model"]:
            print("\nBy Model:")
            for model, stats in summary["by_model"].items():
                print(f"  {model}:")
                print(f"    Calls: {stats['calls']}")
                print(f"    Tokens: {stats['input_tokens']:,} in / {stats['output_tokens']:,} out")
                print(f"    Cost: ${stats['cost']:.3f}")
                print(f"    Time: {stats['duration']:.1f}s")
        
        # By task breakdown
        if summary["by_task"] and len(summary["by_task"]) > 1:
            print("\nBy Task:")
            for task, stats in summary["by_task"].items():
                if task != "unknown":
                    print(f"  {task}:")
                    print(f"    Calls: {stats['calls']}")
                    print(f"    Cost: ${stats['cost']:.3f}")
                    print(f"    Time: {stats['duration']:.1f}s")
        
        print("="*60)