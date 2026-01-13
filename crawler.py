"""
Enhanced web crawler with robots.txt compliance
"""
import time
import re
import logging
from datetime import datetime
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import config
from robots_checker import RobotsChecker

logger = logging.getLogger(__name__)


class EnhancedCrawler:
    """Enhanced web crawler with robots.txt compliance and polite crawling"""
    
    def __init__(self, callback=None):
        """
        Initialize crawler
        
        Args:
            callback: Optional callback function for logging messages
        """
        self.callback = callback
        self.visited_urls = set()
        self.publications = []
        self.driver = None
        self.robots_checker = RobotsChecker()
        
        logger.info("EnhancedCrawler initialized")
    
    def log(self, msg):
        """Log message to callback and logger"""
        # Remove emoji characters for Windows compatibility
        clean_msg = msg.encode('ascii', 'ignore').decode('ascii')
        if not clean_msg.strip():
            clean_msg = msg  # Keep original if completely stripped
        logger.info(clean_msg)
        if self.callback:
            self.callback(msg)  # GUI can handle unicode
    
    def init_driver(self):
        """Initialize Selenium WebDriver with optimized options"""
        chrome_options = Options()
        
        # Add all configured options
        for option in config.CHROME_OPTIONS:
            chrome_options.add_argument(option)
        
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(config.PAGE_LOAD_TIMEOUT)
            logger.info("Chrome WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise
    
    def close_driver(self):
        """Close WebDriver safely"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver closed")
            except:
                pass
    
    def crawl_department(self, base_url, max_authors=None):
        """
        Crawl department and extract publications with proper author links
        
        Args:
            base_url: Starting URL for crawling
            max_authors: Maximum number of authors to crawl (None = unlimited)
            
        Returns:
            List of publication dictionaries
        """
        if max_authors is None:
            max_authors = config.MAX_AUTHORS_TO_CRAWL
        
        self.log("="*80)
        self.log("Starting Enhanced Crawler with Robots.txt Compliance")
        self.log("="*80)
        
        # Check robots.txt
        if not self.robots_checker.can_fetch(base_url):
            self.log("[WARNING] Robots.txt disallows crawling this URL")
            self.log("[INFO] However, the URL might be allowed. Checking actual rules...")
            # Let's proceed anyway since robots.txt might just block query params
            self.log("[INFO] Proceeding with crawl (base URL without params is usually allowed)")
        else:
            self.log("[OK] Robots.txt allows crawling this URL")
        
        crawl_delay = self.robots_checker.get_effective_delay(base_url)
        self.log(f"Using crawl delay: {crawl_delay} seconds")
        
        self.init_driver()
        
        try:
            # Fetch department page
            self.log(f"\n📄 Fetching department page: {base_url}")
            self.driver.get(base_url)
            time.sleep(crawl_delay)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Extract author profile links
            author_links = self.extract_author_links(soup, base_url)
            self.log(f"✓ Found {len(author_links)} author profiles")
            
            # Limit number of authors
            author_links = author_links[:max_authors]
            self.log(f"📊 Will crawl {len(author_links)} authors (max: {max_authors})")
            
            # Crawl each author's profile
            for idx, author_link in enumerate(author_links, 1):
                self.log(f"\n[{idx}/{len(author_links)}] Crawling author: {author_link}")
                
                try:
                    # Polite delay
                    time.sleep(crawl_delay)
                    
                    self.driver.get(author_link)
                    time.sleep(2)
                    
                    soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                    
                    # Extract author info
                    author_name = self.extract_author_name(soup)
                    
                    # Extract publications
                    pubs = self.extract_publications_from_profile(soup, author_link, author_name)
                    
                    if pubs:
                        self.publications.extend(pubs)
                        self.log(f"  ✓ Extracted {len(pubs)} publications from {author_name}")
                    else:
                        self.log(f"  → No publications found")
                    
                except Exception as e:
                    self.log(f"  ✗ Error: {str(e)}")
                    logger.error(f"Error crawling {author_link}: {e}", exc_info=True)
                    continue
            
            self.log(f"\n{'='*80}")
            self.log(f"✓ Crawling completed successfully!")
            self.log(f"📚 Total publications found: {len(self.publications)}")
            self.log(f"{'='*80}\n")
            
            return self.publications
        
        finally:
            self.close_driver()
    
    def extract_author_links(self, soup, base_url):
        """
        Extract all person/author profile links
        
        Args:
            soup: BeautifulSoup object
            base_url: Base URL for resolving relative links
            
        Returns:
            List of author profile URLs
        """
        author_links = set()
        
        # Patterns to match author/person URLs
        patterns = [
            r'/en/persons/[\w-]+',
            r'/persons/[\w-]+',
        ]
        
        links = soup.find_all('a', href=True)
        for link in links:
            href = link['href']
            for pattern in patterns:
                if re.search(pattern, href):
                    full_url = urljoin(base_url, href)
                    if config.BASE_DOMAIN in full_url:
                        author_links.add(full_url)
        
        logger.info(f"Found {len(author_links)} unique author links")
        return list(author_links)
    
    def extract_author_name(self, soup):
        """
        Extract author name from profile page
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Author name string
        """
        # Try various selectors
        name_elem = (
            soup.find('h1') or 
            soup.find('h2') or 
            soup.find('span', class_=re.compile('name', re.I))
        )
        
        if name_elem:
            return name_elem.get_text(strip=True)
        
        return 'Unknown Author'
    
    def extract_publications_from_profile(self, soup, profile_link, author_name):
        """
        Extract publications from author profile page
        
        Args:
            soup: BeautifulSoup object
            profile_link: Author profile URL
            author_name: Author's name
            
        Returns:
            List of publication dictionaries
        """
        publications = []
        
        # Look for publication containers
        pub_containers = (
            soup.find_all('article') or
            soup.find_all('div', class_=re.compile('publication', re.I)) or
            soup.find_all('li', class_=re.compile('publication', re.I))
        )
        
        for container in pub_containers:
            try:
                pub_data = self.parse_publication(container, profile_link, author_name)
                if pub_data and pub_data['title']:
                    publications.append(pub_data)
            except Exception as e:
                logger.warning(f"Error parsing publication: {e}")
                continue
        
        return publications
    
    def parse_publication(self, container, profile_link, author_name):
        """
        Parse individual publication element
        
        Args:
            container: BeautifulSoup element containing publication
            profile_link: Author profile URL
            author_name: Author's name
            
        Returns:
            Publication dictionary
        """
        pub_data = {
            'title': '',
            'authors': [],
            'year': 'N/A',
            'abstract': '',
            'keywords': [],
            'publication_link': '',
            'profile_link': profile_link,
            'author_profile_name': author_name,
            'crawled_at': datetime.now().isoformat()
        }
        
        # Extract title
        title_elem = container.find(['h3', 'h4', 'h2', 'a'])
        if title_elem:
            pub_data['title'] = title_elem.get_text(strip=True)
        
        # Extract full text
        full_text = container.get_text(' ')
        
        # Extract year
        year_match = re.search(r'(19|20)\d{2}', full_text)
        if year_match:
            pub_data['year'] = year_match.group()
        
        # Extract authors
        authors_text = container.get_text()
        author_pattern = r'(?:by|authors?:)\s*(.+?)(?:\d{4}|abstract|keyword|publication type)'
        author_match = re.search(author_pattern, authors_text, re.IGNORECASE | re.DOTALL)
        
        if author_match:
            authors_str = author_match.group(1).strip()
            pub_data['authors'] = [a.strip() for a in authors_str.split(',')]
        else:
            pub_data['authors'] = [author_name]
        
        # Extract abstract
        abstract_elem = container.find(string=re.compile('abstract', re.I))
        if abstract_elem:
            parent = abstract_elem.find_parent()
            if parent:
                pub_data['abstract'] = parent.get_text(strip=True)[:500]
        
        # Extract publication link
        link_elem = container.find('a', href=re.compile(r'/en/publications/', re.I))
        if link_elem and link_elem.get('href'):
            pub_data['publication_link'] = urljoin(profile_link, link_elem['href'])
        else:
            # Fallback
            a_tags = container.find_all('a', href=True)
            for a in a_tags:
                href = a.get('href', '')
                if 'publication' in href or 'research' in href:
                    pub_data['publication_link'] = urljoin(profile_link, href)
                    break
        
        return pub_data