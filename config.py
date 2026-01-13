"""
Configuration settings for the Vertical Search Engine
"""
import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# File paths
INDEX_FILE = DATA_DIR / "search_index.pkl"
PUBLICATIONS_FILE = DATA_DIR / "publications.json"
ROBOTS_CACHE_FILE = DATA_DIR / "robots_cache.json"
LOG_FILE = LOGS_DIR / "crawler.log"

# Crawling settings
BASE_URL = "https://pureportal.coventry.ac.uk/en/organisations/ics-research-centre-for-computational-science-and-mathematical-mo"
BASE_DOMAIN = "pureportal.coventry.ac.uk"
MAX_AUTHORS_TO_CRAWL = 30
CRAWL_DELAY = 5  # seconds between requests
PAGE_LOAD_TIMEOUT = 20  # seconds
USER_AGENT = "CU-Research-Bot/1.0 (Educational Project; +mailto:your-email@example.com)"

# Scheduling settings
CRAWL_SCHEDULE_DAY = "monday"  # Day of week to run crawler
CRAWL_SCHEDULE_TIME = "03:00"  # Time to run crawler (24-hour format)

# Search settings
STOP_WORDS = {
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'has',
    'he', 'in', 'is', 'it', 'its', 'of', 'on', 'or', 'that', 'the', 'to',
    'was', 'will', 'with', 'this', 'but', 'they', 'have', 'had',
    'what', 'when', 'where', 'who', 'why', 'how', 'all', 'each', 'every',
    'both', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
    'not', 'only', 'same', 'so', 'than', 'too', 'very', 'can', 'just',
    'should', 'now'
}

# Field weights for search ranking
FIELD_WEIGHTS = {
    'title': 3.0,
    'authors': 2.5,
    'keywords': 2.0,
    'year': 1.5,
    'abstract': 1.0
}

# Selenium settings
CHROME_OPTIONS = [
    '--disable-blink-features=AutomationControlled',
    '--disable-images',
    '--no-sandbox',
    '--disable-dev-shm-usage',
    '--headless'  # Run in background
]

# GUI settings
WINDOW_TITLE = "Coventry University Research Search Engine"
WINDOW_SIZE = "1200x750"
MAX_RESULTS_DISPLAY = 100

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Fix Windows console encoding issues
import sys
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass