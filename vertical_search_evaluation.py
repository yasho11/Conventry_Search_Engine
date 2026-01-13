# vertical_search_evaluation.py - FIXED VERSION
"""
Evaluation metrics for Vertical Search Engine
"""

import json
import time
import pickle
import logging
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import statistics

import config
from inverted_index import AdvancedInvertedIndex
from crawler import EnhancedCrawler

class VerticalSearchEvaluator:
    """
    Comprehensive evaluator for Vertical Search Engine
    """
    
    def __init__(self, index_path=None, publications_path=None):
        """
        Initialize evaluator
        
        Args:
            index_path: Path to index file (default: config.INDEX_FILE)
            publications_path: Path to publications file (default: config.PUBLICATIONS_FILE)
        """
        self.index_path = index_path or config.INDEX_FILE
        self.publications_path = publications_path or config.PUBLICATIONS_FILE
        
        self.index = None
        self.publications = []
        
        # Load data if available
        self.load_data()
        
        print("=" * 70)
        print("VERTICAL SEARCH ENGINE EVALUATION")
        print("=" * 70)
    
    def load_data(self):
        """Load index and publications data"""
        try:
            # Load inverted index
            if self.index_path.exists():
                self.index = AdvancedInvertedIndex()
                if self.index.load(self.index_path):
                    print(f"✓ Loaded index with {self.index.doc_count} documents")
                else:
                    print(f"✗ Failed to load index from {self.index_path}")
            
            # Load publications
            if self.publications_path.exists():
                with open(self.publications_path, 'r') as f:
                    self.publications = json.load(f)
                print(f"✓ Loaded {len(self.publications)} publications")
            else:
                print(f"✗ Publications file not found: {self.publications_path}")
                
        except Exception as e:
            print(f"✗ Error loading data: {e}")
    
    def evaluate_crawler_performance(self):
        """
        Evaluate crawler performance from stored publications
        """
        print("\n" + "=" * 70)
        print("CRAWLER PERFORMANCE EVALUATION")
        print("=" * 70)
        
        if not self.publications:
            print("No publications data available for evaluation")
            return {}
        
        metrics = {
            'total_publications': len(self.publications),
            'unique_authors': set(),
            'years_covered': set(),
            'crawl_timestamps': []
        }
        
        # Analyze publication data
        complete_metadata_count = 0
        author_publication_count = defaultdict(int)
        
        for pub in self.publications:
            # Check metadata completeness
            required_fields = ['title', 'authors', 'year', 'abstract']
            has_all_fields = all(field in pub and pub[field] for field in required_fields)
            if has_all_fields:
                complete_metadata_count += 1
            
            # Track authors
            if 'authors' in pub and pub['authors']:
                if isinstance(pub['authors'], list):
                    for author in pub['authors']:
                        metrics['unique_authors'].add(author.strip())
                        author_publication_count[author.strip()] += 1
                else:
                    metrics['unique_authors'].add(str(pub['authors']))
                    author_publication_count[str(pub['authors'])] += 1
            
            # Track years
            if 'year' in pub and pub['year']:
                metrics['years_covered'].add(str(pub['year']))
            
            # Track crawl timestamps
            if 'crawled_at' in pub:
                metrics['crawl_timestamps'].append(pub['crawled_at'])
        
        # Convert sets to counts
        metrics['unique_authors'] = len(metrics['unique_authors'])
        metrics['years_covered'] = len(metrics['years_covered'])
        metrics['complete_metadata_pct'] = (complete_metadata_count / len(self.publications)) * 100
        
        # Author productivity statistics
        if author_publication_count:
            pubs_per_author = list(author_publication_count.values())
            metrics['avg_publications_per_author'] = statistics.mean(pubs_per_author)
            metrics['max_publications_per_author'] = max(pubs_per_author)
            metrics['min_publications_per_author'] = min(pubs_per_author)
        
        # Print results
        print(f"\n📊 CRAWLER PERFORMANCE METRICS:")
        print(f"   • Total Publications Crawled: {metrics['total_publications']}")
        print(f"   • Unique Authors: {metrics['unique_authors']}")
        print(f"   • Years Covered: {metrics['years_covered']}")
        print(f"   • Metadata Completeness: {metrics['complete_metadata_pct']:.1f}%")
        
        if 'avg_publications_per_author' in metrics:
            print(f"\n📈 AUTHOR PRODUCTIVITY:")
            print(f"   • Avg Publications per Author: {metrics['avg_publications_per_author']:.1f}")
            print(f"   • Most Productive Author: {metrics['max_publications_per_author']} publications")
            print(f"   • Least Productive Author: {metrics['min_publications_per_author']} publications")
        
        # Top 10 most productive authors
        if author_publication_count:
            print(f"\n🏆 TOP 10 MOST PRODUCTIVE AUTHORS:")
            sorted_authors = sorted(author_publication_count.items(), key=lambda x: x[1], reverse=True)[:10]
            for i, (author, count) in enumerate(sorted_authors, 1):
                # Truncate long author names
                display_author = author[:40] if len(author) > 40 else author
                print(f"   {i:2d}. {display_author:40} - {count:2d} publications")
        
        return metrics
    
    def evaluate_index_performance(self):
        """
        Evaluate search index performance
        """
        print("\n" + "=" * 70)
        print("SEARCH INDEX EVALUATION")
        print("=" * 70)
        
        if not self.index:
            print("No index data available for evaluation")
            return {}
        
        stats = self.index.get_statistics()
        
        metrics = {
            'total_documents': stats.get('total_documents', 0),
            'unique_terms': stats.get('unique_terms', 0),
            'total_postings': stats.get('total_postings', 0),
            'avg_document_length': 0,
            'avg_term_frequency': 0
        }
        
        # Calculate average document length (in tokens)
        if self.index.documents and self.index.index:
            total_tokens = 0
            for doc_id in self.index.documents:
                doc_tokens = 0
                for term, postings in self.index.index.items():
                    for posting in postings:
                        if posting[0] == doc_id:
                            doc_tokens += posting[1]  # Add term frequency
                total_tokens += doc_tokens
            
            if self.index.doc_count > 0:
                metrics['avg_document_length'] = total_tokens / self.index.doc_count
        
        # Calculate average term frequency
        if metrics['total_postings'] > 0 and metrics['unique_terms'] > 0:
            metrics['avg_term_frequency'] = metrics['total_postings'] / metrics['unique_terms']
        
        # Print results
        print(f"\n📊 INDEX PERFORMANCE METRICS:")
        print(f"   • Documents Indexed: {metrics['total_documents']}")
        print(f"   • Vocabulary Size: {metrics['unique_terms']} unique terms")
        print(f"   • Total Postings: {metrics['total_postings']}")
        print(f"   • Avg Document Length: {metrics['avg_document_length']:.1f} tokens")
        print(f"   • Avg Term Frequency: {metrics['avg_term_frequency']:.2f}")
        
        # Field weight effectiveness
        print(f"\n⚖️ FIELD WEIGHTS (for ranking):")
        for field, weight in config.FIELD_WEIGHTS.items():
            print(f"   • {field.capitalize()}: {weight}x")
        
        # Most frequent terms (FIXED: handle float frequencies)
        if self.index.index:
            print(f"\n🔤 TOP 20 MOST FREQUENT TERMS:")
            term_freqs = []
            for term, postings in self.index.index.items():
                total_freq = sum(posting[1] for posting in postings)
                term_freqs.append((term, total_freq))
            
            # Sort by frequency
            term_freqs.sort(key=lambda x: x[1], reverse=True)
            
            for i, (term, freq) in enumerate(term_freqs[:20], 1):
                # Format freq based on whether it's float or int
                if isinstance(freq, float):
                    if freq.is_integer():
                        freq_str = f"{int(freq):4d}"
                    else:
                        freq_str = f"{freq:6.1f}"
                else:
                    freq_str = f"{int(freq):4d}"
                
                print(f"   {i:2d}. {term:20} - {freq_str} occurrences")
        
        return metrics
    
    def evaluate_search_performance(self, test_queries=None):
        """
        Evaluate search engine performance with test queries
        
        Args:
            test_queries: List of test queries (default: sample queries)
        """
        print("\n" + "=" * 70)
        print("SEARCH ENGINE EVALUATION")
        print("=" * 70)
        
        if not self.index or self.index.doc_count == 0:
            print("No index available for search evaluation")
            return {}
        
        # Default test queries
        if test_queries is None:
            test_queries = [
                "machine learning",
                "mathematics",
                "artificial intelligence",
                "data analysis",
                "computational",
                "neural networks",
                "deep learning",
                "algorithm",
                "2023",
                "research"
            ]
        
        metrics = {
            'total_queries': len(test_queries),
            'queries_with_results': 0,
            'avg_results_per_query': 0,
            'avg_response_time': 0,
            'query_success_rate': 0,
            'query_performance': []
        }
        
        total_results = 0
        total_response_time = 0
        
        print(f"\n🔍 SEARCH PERFORMANCE TEST ({len(test_queries)} queries):")
        print("-" * 70)
        
        for query in test_queries:
            start_time = time.time()
            results = self.index.search(query)
            end_time = time.time()
            
            response_time = end_time - start_time
            total_response_time += response_time
            
            num_results = len(results)
            total_results += num_results
            
            if num_results > 0:
                metrics['queries_with_results'] += 1
            
            metrics['query_performance'].append({
                'query': query,
                'results': num_results,
                'response_time': response_time
            })
            
            # Print query result
            result_status = "✓" if num_results > 0 else "✗"
            print(f"   {result_status} '{query}' → {num_results:3d} results ({response_time:.4f}s)")
        
        # Calculate averages
        if metrics['total_queries'] > 0:
            metrics['avg_results_per_query'] = total_results / metrics['total_queries']
            metrics['avg_response_time'] = total_response_time / metrics['total_queries']
            metrics['query_success_rate'] = (metrics['queries_with_results'] / metrics['total_queries']) * 100
        
        # Print summary
        print(f"\n📊 SEARCH PERFORMANCE SUMMARY:")
        print(f"   • Query Success Rate: {metrics['query_success_rate']:.1f}%")
        print(f"   • Avg Results per Query: {metrics['avg_results_per_query']:.1f}")
        print(f"   • Avg Response Time: {metrics['avg_response_time']:.4f} seconds")
        
        # Top performing queries
        print(f"\n🚀 FASTEST QUERIES (response time):")
        fast_queries = sorted(metrics['query_performance'], key=lambda x: x['response_time'])[:5]
        for i, query_data in enumerate(fast_queries, 1):
            print(f"   {i}. '{query_data['query']}' - {query_data['response_time']:.4f}s")
        
        # Most productive queries
        print(f"\n🎯 MOST PRODUCTIVE QUERIES (most results):")
        productive_queries = sorted(metrics['query_performance'], key=lambda x: x['results'], reverse=True)[:5]
        for i, query_data in enumerate(productive_queries, 1):
            print(f"   {i}. '{query_data['query']}' - {query_data['results']} results")
        
        return metrics
    
    def evaluate_system_health(self):
        """
        Evaluate overall system health and configuration
        """
        print("\n" + "=" * 70)
        print("SYSTEM HEALTH CHECK")
        print("=" * 70)
        
        metrics = {
            'config_valid': True,
            'files_exist': {},
            'file_sizes': {},
            'directories_exist': {},
            'scheduler_status': 'Unknown'
        }
        
        # Check configuration
        print(f"\n🔧 CONFIGURATION CHECK:")
        print(f"   • Base URL: {config.BASE_URL}")
        print(f"   • Base Domain: {config.BASE_DOMAIN}")
        print(f"   • Max Authors: {config.MAX_AUTHORS_TO_CRAWL}")
        print(f"   • Crawl Delay: {config.CRAWL_DELAY}s")
        print(f"   • User Agent: {config.USER_AGENT}")
        
        # Check required files
        required_files = [
            (config.INDEX_FILE, "Index File"),
            (config.PUBLICATIONS_FILE, "Publications File"),
            (config.LOG_FILE, "Log File"),
            (config.ROBOTS_CACHE_FILE, "Robots Cache")
        ]
        
        print(f"\n📁 FILE SYSTEM CHECK:")
        for filepath, description in required_files:
            exists = filepath.exists()
            metrics['files_exist'][description] = exists
            
            if exists:
                size_kb = filepath.stat().st_size / 1024
                metrics['file_sizes'][description] = size_kb
                print(f"   ✓ {description}: {size_kb:.1f} KB")
            else:
                print(f"   ✗ {description}: NOT FOUND")
        
        # Check required directories
        required_dirs = [
            (config.DATA_DIR, "Data Directory"),
            (config.LOGS_DIR, "Logs Directory")
        ]
        
        for dirpath, description in required_dirs:
            exists = dirpath.exists()
            metrics['directories_exist'][description] = exists
            
            if exists:
                print(f"   ✓ {description}: OK")
            else:
                print(f"   ✗ {description}: NOT FOUND")
        
        # Check scheduler configuration
        print(f"\n⏰ SCHEDULER CONFIGURATION:")
        print(f"   • Schedule Day: {config.CRAWL_SCHEDULE_DAY}")
        print(f"   • Schedule Time: {config.CRAWL_SCHEDULE_TIME}")
        
        # Check if scheduler status file exists
        scheduler_status_file = config.DATA_DIR / "scheduler_status.json"
        if scheduler_status_file.exists():
            try:
                with open(scheduler_status_file, 'r') as f:
                    status = json.load(f)
                    last_run = status.get('last_run', 'Never')
                    print(f"   • Last Run: {last_run}")
                    metrics['scheduler_status'] = last_run
            except:
                print(f"   • Last Run: Error reading status")
        else:
            print(f"   • Last Run: Never (no status file)")
        
        return metrics
    
    def run_comprehensive_evaluation(self, test_queries=None):
        """
        Run all evaluation metrics and generate summary report
        """
        print("\n" + "=" * 70)
        print("COMPREHENSIVE EVALUATION SUMMARY")
        print("=" * 70)
        
        all_metrics = {
            'timestamp': datetime.now().isoformat(),
            'crawler': {},
            'index': {},
            'search': {},
            'system': {}
        }
        
        # Run all evaluations
        all_metrics['crawler'] = self.evaluate_crawler_performance()
        all_metrics['index'] = self.evaluate_index_performance()
        all_metrics['search'] = self.evaluate_search_performance(test_queries)
        all_metrics['system'] = self.evaluate_system_health()
        
        # Generate summary score
        score = self.calculate_overall_score(all_metrics)
        all_metrics['overall_score'] = score
        
        # Save results
        self.save_evaluation_results(all_metrics)
        
        return all_metrics
    
    def calculate_overall_score(self, metrics):
        """
        Calculate an overall performance score (0-100)
        """
        score = 0
        max_score = 100
        
        # Crawler score (30 points)
        crawler = metrics.get('crawler', {})
        if crawler.get('total_publications', 0) > 0:
            score += 10  # Has data
            if crawler.get('complete_metadata_pct', 0) > 80:
                score += 10  # Good metadata
            if crawler.get('unique_authors', 0) > 5:
                score += 10  # Good author coverage
        
        # Index score (30 points)
        index = metrics.get('index', {})
        if index.get('total_documents', 0) > 0:
            score += 10  # Has index
            if index.get('unique_terms', 0) > 100:
                score += 10  # Good vocabulary
            if index.get('total_postings', 0) > 1000:
                score += 10  # Good index size
        
        # Search score (30 points)
        search = metrics.get('search', {})
        if search.get('query_success_rate', 0) > 50:
            score += 10  # Good success rate
        if search.get('avg_results_per_query', 0) > 0:
            score += 10  # Returns results
        if search.get('avg_response_time', 0) < 0.1:
            score += 10  # Fast response
        
        # System health score (10 points)
        system = metrics.get('system', {})
        if all(system.get('files_exist', {}).values()):
            score += 10  # All files exist
        
        return min(score, max_score)
    
    def save_evaluation_results(self, metrics, filename="evaluation_results.json"):
        """
        Save evaluation results to JSON file
        """
        output_file = config.DATA_DIR / filename
        
        try:
            # Convert any non-serializable objects
            serializable_metrics = json.loads(
                json.dumps(metrics, default=str, indent=2)
            )
            
            with open(output_file, 'w') as f:
                json.dump(serializable_metrics, f, indent=2)
            
            print(f"\n💾 Evaluation results saved to: {output_file}")
            print(f"📊 Overall Performance Score: {metrics['overall_score']}/100")
            
            # Print final summary
            print("\n" + "=" * 70)
            print("EVALUATION COMPLETE")
            print("=" * 70)
            
            if metrics['overall_score'] >= 80:
                print("🎉 EXCELLENT - System is performing well!")
            elif metrics['overall_score'] >= 60:
                print("👍 GOOD - System is functional but could be improved")
            elif metrics['overall_score'] >= 40:
                print("⚠️ FAIR - System needs attention")
            else:
                print("🔴 POOR - System needs significant improvements")
                
        except Exception as e:
            print(f"\n⚠️ Could not save results: {e}")
            print(f"Overall Performance Score: {metrics['overall_score']}/100")

def main():
    """
    Main function to run the evaluation
    """
    print("\n" + "=" * 70)
    print("VERTICAL SEARCH ENGINE EVALUATION TOOL")
    print("=" * 70)
    
    # Optional: Add custom test queries
    custom_queries = [
        "machine learning",
        "data science",
        "artificial intelligence",
        "neural network",
        "deep learning",
        "mathematics",
        "algorithm",
        "research",
        "coventry university",
        "2023 publication"
    ]
    
    # Initialize evaluator
    evaluator = VerticalSearchEvaluator()
    
    # Run comprehensive evaluation
    try:
        results = evaluator.run_comprehensive_evaluation(test_queries=custom_queries)
        
        # Print additional recommendations
        print("\n" + "=" * 70)
        print("RECOMMENDATIONS")
        print("=" * 70)
        
        if results['crawler'].get('total_publications', 0) == 0:
            print("1. ❗ No publications found. Run the crawler to collect data.")
        elif results['crawler'].get('total_publications', 0) < 50:
            print("1. ⚠️ Few publications collected. Consider increasing MAX_AUTHORS_TO_CRAWL.")
        
        if results['index'].get('total_documents', 0) == 0:
            print("2. ❗ No documents indexed. Build index from publications.")
        
        if results['search'].get('query_success_rate', 0) < 50:
            print("3. ⚠️ Low query success rate. Consider adding more data or optimizing queries.")
        
        if results['search'].get('avg_response_time', 0) > 0.5:
            print("4. ⚠️ Slow search response. Consider optimizing index structure.")
        
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"\n❌ ERROR during evaluation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()