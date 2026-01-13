"""
Enhanced text preprocessing with stemming and lemmatization
"""
import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer, WordNetLemmatizer
from nltk.tokenize import word_tokenize
import logging

# Download required NLTK data (run once)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet', quiet=True)

try:
    nltk.data.find('corpora/omw-1.4')
except LookupError:
    nltk.download('omw-1.4', quiet=True)

logger = logging.getLogger(__name__)


class TextPreprocessor:
    """Enhanced text preprocessor with stemming and lemmatization"""
    
    def __init__(self, use_stemming=True, use_lemmatization=True):
        """
        Initialize preprocessor
        
        Args:
            use_stemming: Whether to use stemming
            use_lemmatization: Whether to use lemmatization
        """
        self.use_stemming = use_stemming
        self.use_lemmatization = use_lemmatization
        
        # Initialize NLTK tools
        self.stemmer = PorterStemmer() if use_stemming else None
        self.lemmatizer = WordNetLemmatizer() if use_lemmatization else None
        
        # Load stopwords
        try:
            self.stop_words = set(stopwords.words('english'))
        except:
            # Fallback to basic stopwords
            from config import STOP_WORDS
            self.stop_words = STOP_WORDS
        
        logger.info(f"TextPreprocessor initialized (stemming={use_stemming}, lemmatization={use_lemmatization})")
    
    def preprocess(self, text):
        """
        Convert to lowercase and remove special characters
        
        Args:
            text: Input text string
            
        Returns:
            Cleaned text string
        """
        if not text:
            return ""
        
        text = str(text).lower()
        # Remove special characters but keep spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def tokenize(self, text):
        """
        Split text into tokens using NLTK
        
        Args:
            text: Input text string
            
        Returns:
            List of tokens
        """
        try:
            tokens = word_tokenize(text)
        except:
            # Fallback to simple split
            tokens = text.split()
        
        return tokens
    
    def remove_stopwords(self, tokens):
        """
        Remove stop words from token list
        
        Args:
            tokens: List of tokens
            
        Returns:
            List of tokens without stopwords
        """
        return [t for t in tokens if t not in self.stop_words and len(t) > 2]
    
    def stem(self, tokens):
        """
        Apply stemming to tokens
        
        Args:
            tokens: List of tokens
            
        Returns:
            List of stemmed tokens
        """
        if not self.use_stemming or not self.stemmer:
            return tokens
        
        return [self.stemmer.stem(token) for token in tokens]
    
    def lemmatize(self, tokens):
        """
        Apply lemmatization to tokens
        
        Args:
            tokens: List of tokens
            
        Returns:
            List of lemmatized tokens
        """
        if not self.use_lemmatization or not self.lemmatizer:
            return tokens
        
        return [self.lemmatizer.lemmatize(token) for token in tokens]
    
    def process_text(self, text):
        """
        Complete text processing pipeline
        
        Args:
            text: Input text string
            
        Returns:
            List of processed tokens
        """
        # Clean and lowercase
        text = self.preprocess(text)
        
        # Tokenize
        tokens = self.tokenize(text)
        
        # Remove stopwords
        tokens = self.remove_stopwords(tokens)
        
        # Apply stemming
        if self.use_stemming:
            tokens = self.stem(tokens)
        
        # Apply lemmatization
        if self.use_lemmatization:
            tokens = self.lemmatize(tokens)
        
        return tokens
    
    def process_document(self, doc_data):
        """
        Process entire document with multiple fields
        
        Args:
            doc_data: Dictionary containing document fields
            
        Returns:
            Dictionary of field -> processed tokens
        """
        processed_fields = {}
        
        searchable_fields = {
            'title': doc_data.get('title', ''),
            'authors': ' '.join(doc_data.get('authors', [])) if isinstance(doc_data.get('authors', []), list) else str(doc_data.get('authors', '')),
            'year': str(doc_data.get('year', '')),
            'abstract': doc_data.get('abstract', ''),
            'keywords': ' '.join(doc_data.get('keywords', [])) if isinstance(doc_data.get('keywords', []), list) else str(doc_data.get('keywords', ''))
        }
        
        for field, text in searchable_fields.items():
            if text:
                processed_fields[field] = self.process_text(text)
        
        return processed_fields