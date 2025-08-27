#!/usr/bin/env python3
"""
Performance monitoring script for the Salesforce RAG Bot.
Helps track and optimize performance with large Pinecone databases.
"""

import sys
import os
import time
import json
from typing import Dict, Any

# Add the src/chatbot directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'chatbot'))

from rag_service import RAGService
from config import config

class PerformanceMonitor:
    """Monitor and optimize RAG bot performance"""
    
    def __init__(self):
        self.rag_service = RAGService()
        self.test_queries = [
            "What security permissions do we have for the Account object?",
            "What fields does the Contact object have?",
            "What validation rules exist on the Lead object?",
            "Which users can delete Opportunity records?",
            "What are the relationships for the Case object?",
            "Show me all field-level security for the User object",
            "What custom objects do we have?",
            "What are the picklist values for Lead Status?",
            "What automation rules exist for the Account object?",
            "What are the data retention policies in our org?"
        ]
    
    def run_performance_test(self, num_iterations: int = 3) -> Dict[str, Any]:
        """Run comprehensive performance tests"""
        print("🚀 Starting Performance Test...")
        print(f"📊 Testing {len(self.test_queries)} queries with {num_iterations} iterations each")
        print("=" * 60)
        
        results = {
            "test_queries": len(self.test_queries),
            "iterations_per_query": num_iterations,
            "total_tests": len(self.test_queries) * num_iterations,
            "query_results": [],
            "cache_stats": [],
            "performance_summary": {}
        }
        
        # Clear cache before testing
        self.rag_service.clear_cache()
        
        for i, query in enumerate(self.test_queries, 1):
            print(f"\n🔍 Testing Query {i}/{len(self.test_queries)}: {query[:50]}...")
            
            query_results = {
                "query": query,
                "iterations": []
            }
            
            for j in range(num_iterations):
                print(f"  Iteration {j+1}/{num_iterations}...")
                
                start_time = time.time()
                
                try:
                    # Perform the search
                    documents = self.rag_service.search_context(query, top_k=10)
                    
                    # Get cache stats
                    cache_stats = self.rag_service.get_cache_stats()
                    
                    end_time = time.time()
                    duration = end_time - start_time
                    
                    iteration_result = {
                        "iteration": j + 1,
                        "duration_seconds": round(duration, 3),
                        "documents_found": len(documents),
                        "cache_stats": cache_stats
                    }
                    
                    query_results["iterations"].append(iteration_result)
                    
                    print(f"    ✅ Completed in {duration:.3f}s, found {len(documents)} documents")
                    
                except Exception as e:
                    print(f"    ❌ Error: {e}")
                    iteration_result = {
                        "iteration": j + 1,
                        "error": str(e),
                        "duration_seconds": 0,
                        "documents_found": 0
                    }
                    query_results["iterations"].append(iteration_result)
            
            results["query_results"].append(query_results)
            
            # Calculate average performance for this query
            successful_iterations = [r for r in query_results["iterations"] if "error" not in r]
            if successful_iterations:
                avg_duration = sum(r["duration_seconds"] for r in successful_iterations) / len(successful_iterations)
                avg_documents = sum(r["documents_found"] for r in successful_iterations) / len(successful_iterations)
                print(f"  📈 Average: {avg_duration:.3f}s, {avg_documents:.1f} documents")
        
        # Calculate overall performance summary
        all_durations = []
        all_document_counts = []
        
        for query_result in results["query_results"]:
            for iteration in query_result["iterations"]:
                if "error" not in iteration:
                    all_durations.append(iteration["duration_seconds"])
                    all_document_counts.append(iteration["documents_found"])
        
        if all_durations:
            results["performance_summary"] = {
                "total_queries_tested": len(self.test_queries),
                "total_iterations": len(all_durations),
                "average_search_time": round(sum(all_durations) / len(all_durations), 3),
                "min_search_time": round(min(all_durations), 3),
                "max_search_time": round(max(all_durations), 3),
                "average_documents_found": round(sum(all_document_counts) / len(all_document_counts), 1),
                "cache_enabled": config.ENABLE_SEARCH_CACHING,
                "search_batch_size": config.SEARCH_BATCH_SIZE,
                "max_search_results": config.MAX_SEARCH_RESULTS
            }
        
        return results
    
    def print_performance_report(self, results: Dict[str, Any]):
        """Print a formatted performance report"""
        print("\n" + "=" * 60)
        print("📊 PERFORMANCE TEST RESULTS")
        print("=" * 60)
        
        summary = results["performance_summary"]
        print(f"🔍 Total Queries Tested: {summary['total_queries_tested']}")
        print(f"🔄 Total Iterations: {summary['total_iterations']}")
        print(f"⏱️  Average Search Time: {summary['average_search_time']}s")
        print(f"⚡ Fastest Search: {summary['min_search_time']}s")
        print(f"🐌 Slowest Search: {summary['max_search_time']}s")
        print(f"📄 Average Documents Found: {summary['average_documents_found']}")
        print(f"💾 Cache Enabled: {summary['cache_enabled']}")
        print(f"📦 Search Batch Size: {summary['search_batch_size']}")
        print(f"🔢 Max Search Results: {summary['max_search_results']}")
        
        print("\n📈 QUERY-BY-QUERY BREAKDOWN:")
        print("-" * 40)
        
        for i, query_result in enumerate(results["query_results"], 1):
            query = query_result["query"]
            successful_iterations = [r for r in query_result["iterations"] if "error" not in r]
            
            if successful_iterations:
                avg_duration = sum(r["duration_seconds"] for r in successful_iterations) / len(successful_iterations)
                avg_documents = sum(r["documents_found"] for r in successful_iterations) / len(successful_iterations)
                print(f"{i:2d}. {query[:40]:<40} | {avg_duration:>6.3f}s | {avg_documents:>3.0f} docs")
            else:
                print(f"{i:2d}. {query[:40]:<40} | {'ERROR':>6} | {'N/A':>3}")
        
        # Performance recommendations
        print("\n💡 PERFORMANCE RECOMMENDATIONS:")
        print("-" * 40)
        
        avg_time = summary["average_search_time"]
        if avg_time > 2.0:
            print("⚠️  Search times are slow (>2s). Consider:")
            print("   - Increasing SEARCH_BATCH_SIZE")
            print("   - Enabling caching (ENABLE_SEARCH_CACHING=true)")
            print("   - Reducing MAX_SEARCH_RESULTS")
        elif avg_time > 1.0:
            print("⚠️  Search times are moderate (>1s). Consider:")
            print("   - Enabling caching for repeated queries")
            print("   - Optimizing search queries")
        else:
            print("✅ Search performance is excellent!")
        
        if not summary["cache_enabled"]:
            print("💡 Enable caching for better performance:")
            print("   Set ENABLE_SEARCH_CACHING=true in your environment")
        
        if summary["search_batch_size"] < 100:
            print("💡 Consider increasing SEARCH_BATCH_SIZE for better coverage")
    
    def save_results(self, results: Dict[str, Any], filename: str = "performance_test_results.json"):
        """Save performance test results to a JSON file"""
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Results saved to {filename}")
    
    def optimize_config(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest configuration optimizations based on performance results"""
        summary = results["performance_summary"]
        recommendations = {}
        
        avg_time = summary["average_search_time"]
        
        if avg_time > 2.0:
            recommendations["SEARCH_BATCH_SIZE"] = min(200, summary["search_batch_size"] * 2)
            recommendations["MAX_SEARCH_RESULTS"] = min(2000, summary["max_search_results"] * 2)
            recommendations["ENABLE_SEARCH_CACHING"] = True
        elif avg_time > 1.0:
            recommendations["SEARCH_BATCH_SIZE"] = min(150, summary["search_batch_size"] + 50)
            recommendations["ENABLE_SEARCH_CACHING"] = True
        
        if not summary["cache_enabled"]:
            recommendations["ENABLE_SEARCH_CACHING"] = True
        
        return recommendations

def main():
    """Main function to run performance monitoring"""
    print("🔧 Salesforce RAG Bot Performance Monitor")
    print("=" * 50)
    
    monitor = PerformanceMonitor()
    
    # Check if RAG service is properly initialized
    try:
        status = monitor.rag_service.get_status()
        print(f"✅ RAG Service Status: {status['pinecone_connected']}")
        print(f"🤖 LLM Provider: {status['llm_provider']}")
        print(f"📊 Index Name: {status['index_name']}")
    except Exception as e:
        print(f"❌ Failed to initialize RAG service: {e}")
        return
    
    # Run performance test
    try:
        results = monitor.run_performance_test(num_iterations=2)
        monitor.print_performance_report(results)
        
        # Save results
        monitor.save_results(results)
        
        # Get optimization recommendations
        recommendations = monitor.optimize_config(results)
        if recommendations:
            print("\n🔧 CONFIGURATION RECOMMENDATIONS:")
            print("-" * 40)
            for key, value in recommendations.items():
                print(f"   {key}={value}")
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")

if __name__ == "__main__":
    main()
