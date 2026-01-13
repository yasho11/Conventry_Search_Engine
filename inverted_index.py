"""
Advanced inverted index with TF-IDF ranking
"""
import pickle
import math
import logging
from collections import defaultdict
from text_preprocessor import TextPreprocessor
import config

logger = logging.getLogger(__name__)


class AdvancedInvertedIndex:
    """Inverted index with field-weighted TF-IDF ranking"""
    
    def __init__(self):
        """Initialize empty index"""
        self.index = defaultdict(list)  # token -> [(doc_id, freq, field)]
        self.documents = {}  # doc_id -> full document data
        self.doc_count = 0
        self.preprocessor = TextPreprocessor(use_stemming=True, use_lemmatization=True)
        
        logger.info("AdvancedInvertedIndex initialized")
    
    def add_document(self, doc_id, doc_data):
        """
        Add document to index with all fields searchable
        
        Args:
            doc_id: Unique document identifier
            doc_data: Dictionary containing document fields
        """
        self.documents[doc_id] = doc_data
        
        # Process document fields
        processed_fields = self.preprocessor.process_document(doc_data)
        
        # Index each field with different weights
        for field, tokens in processed_fields.items():
            if tokens:
                weight = config.FIELD_WEIGHTS.get(field, 1.0)
                
                for token in set(tokens):
                    freq = tokens.count(token)
                    
                    # Check if doc_id already indexed for this token
                    existing = [x for x in self.index[token] if x[0] == doc_id]
                    if existing:
                        idx = self.index[token].index(existing[0])
                        doc_id_prev, freq_prev, field_prev = self.index[token][idx]
                        self.index[token][idx] = (doc_id, freq_prev + (freq * weight), field)
                    else:
                        self.index[token].append((doc_id, freq * weight, field))
        
        self.doc_count = len(self.documents)
    
    def search(self, query):
        """
        Advanced search with relevance ranking
        
        Args:
            query: Search query string
            
        Returns:
            List of (doc_id, doc_data, score) tuples sorted by relevance
        """
        # Process query
        tokens = self.preprocessor.process_text(query)
        
        if not tokens:
            logger.warning(f"Query produced no valid tokens: {query}")
            return []
        
        logger.info(f"Search query: '{query}' -> tokens: {tokens}")
        
        results = defaultdict(float)
        term_matches = defaultdict(int)
        matched_fields = defaultdict(set)
        
        # Calculate scores
        for token in tokens:
            if token in self.index:
                # IDF: log(total_docs / docs_containing_term)
                doc_freq = len(set(x[0] for x in self.index[token]))
                idf = math.log(self.doc_count / doc_freq + 1)
                
                for doc_id, freq, field in self.index[token]:
                    # TF-IDF score
                    results[doc_id] += freq * idf
                    term_matches[doc_id] += 1
                    matched_fields[doc_id].add(field)
        
        # Apply ranking boosts
        for doc_id in results:
            # Bonus if title matches
            if 'title' in matched_fields[doc_id]:
                results[doc_id] *= 1.5
            
            # Bonus for multiple field matches
            results[doc_id] += len(matched_fields[doc_id]) * 5
            
            # Bonus for matching more query terms
            term_coverage = term_matches[doc_id] / len(tokens)
            results[doc_id] *= (1 + term_coverage)
        
        # Sort by score
        sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)
        
        logger.info(f"Found {len(sorted_results)} results for query: {query}")
        
        return [(doc_id, self.documents[doc_id], score) 
                for doc_id, score in sorted_results 
                if doc_id in self.documents]
    
    def save(self, filepath):
        """
        Save index to file
        
        Args:
            filepath: Path to save file
        """
        try:
            with open(filepath, 'wb') as f:
                pickle.dump({
                    'index': dict(self.index),
                    'documents': self.documents,
                    'doc_count': self.doc_count
                }, f)
            logger.info(f"Index saved to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save index: {e}")
            return False
    
    def load(self, filepath):
        """
        Load index from file
        
        Args:
            filepath: Path to load file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
                self.index = defaultdict(list, data['index'])
                self.documents = data['documents']
                self.doc_count = data.get('doc_count', len(self.documents))
            
            logger.info(f"Index loaded from {filepath} ({self.doc_count} documents)")
            return True
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            return False
    
    def get_statistics(self):
        """
        Get index statistics
        
        Returns:
            Dictionary of statistics
        """
        stats = {
            'total_documents': self.doc_count,
            'unique_terms': len(self.index),
            'total_postings': sum(len(postings) for postings in self.index.values())
        }
        
        if self.documents:
            years = defaultdict(int)
            authors = set()
            
            for doc_id, doc_data in self.documents.items():
                year = doc_data.get('year', 'N/A')
                years[year] += 1
                
                if isinstance(doc_data.get('authors', []), list):
                    authors.update(doc_data['authors'])
            
            stats['total_authors'] = len(authors)
            stats['publications_by_year'] = dict(sorted(years.items(), reverse=True))
        
        return stats