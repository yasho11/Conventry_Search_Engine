"""
Enhanced web crawler with abstract extraction from publication pages
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
    """Enhanced web crawler with two-level crawling for full abstracts"""
    
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
            clean_msg = msg
        logger.info(clean_msg)
        if self.callback:
            self.callback(msg)
    
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
    
    def crawl_department(self, base_url, max_publications=None):
        """
        Crawl department publications with full abstract extraction
        
        Args:
            base_url: Starting URL for crawling
            max_publications: Maximum publications to crawl (None = unlimited)
            
        Returns:
            List of publication dictionaries with full abstracts
        """
        if max_publications is None:
            max_publications = config.MAX_AUTHORS_TO_CRAWL * 10  # Estimate
        
        self.log("="*80)
        self.log("Enhanced Crawler - Full Abstract Extraction")
        self.log("="*80)
        
        # Check robots.txt
        if not self.robots_checker.can_fetch(base_url):
            self.log("[WARNING] Robots.txt check failed - proceeding anyway")
        else:
            self.log("[OK] Robots.txt allows crawling")
        
        crawl_delay = self.robots_checker.get_effective_delay(base_url)
        self.log(f"Using crawl delay: {crawl_delay} seconds")
        
        self.init_driver()
        
        try:
            # Try multiple approaches to get publications
            publications_found = False
            
            # Approach 1: Get publications from organization publications page
            pub_list_url = base_url.rstrip('/') + '/publications/'
            self.log(f"\n[Method 1] Trying publications list: {pub_list_url}")
            
            if self.robots_checker.can_fetch(pub_list_url):
                pubs = self.crawl_publications_list(pub_list_url, crawl_delay, max_publications)
                if pubs:
                    self.publications.extend(pubs)
                    publications_found = True
                    self.log(f"[OK] Found {len(pubs)} publications from list page")
            
            # Approach 2: If no publications, crawl author profiles
            if not publications_found:
                self.log(f"\n[Method 2] Trying author profiles from: {base_url}")
                pubs = self.crawl_via_authors(base_url, crawl_delay, max_publications)
                if pubs:
                    self.publications.extend(pubs)
            
            self.log(f"\n{'='*80}")
            self.log(f"[COMPLETE] Crawling completed!")
            self.log(f"[TOTAL] {len(self.publications)} publications with abstracts")
            self.log(f"{'='*80}\n")
            
            return self.publications
        
        finally:
            self.close_driver()
    
    def crawl_publications_list(self, pub_list_url, crawl_delay, max_pubs):
        """
        Crawl publications from organization's publications list page
        
        Args:
            pub_list_url: URL of publications list
            crawl_delay: Delay between requests
            max_pubs: Maximum publications to crawl
            
        Returns:
            List of publication dictionaries
        """
        publications = []
        
        try:
            self.log(f"Fetching publications list...")
            self.driver.get(pub_list_url)
            time.sleep(crawl_delay)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Find all publication items
            pub_items = soup.find_all('li', class_=re.compile('list-result-item'))
            
            if not pub_items:
                self.log("[WARNING] No publication items found on list page")
                return publications
            
            self.log(f"[OK] Found {len(pub_items)} publication entries")
            
            # Extract publication links
            pub_links = []
            for item in pub_items[:max_pubs]:
                # Find the title link
                title_link = item.find('h3', class_='title')
                if title_link:
                    link = title_link.find('a', href=True)
                    if link:
                        full_url = urljoin(pub_list_url, link['href'])
                        if full_url not in self.visited_urls:
                            pub_links.append(full_url)
                            self.visited_urls.add(full_url)
            
            self.log(f"[OK] Extracted {len(pub_links)} unique publication links")
            self.log(f"[INFO] Will crawl {min(len(pub_links), max_pubs)} publications for abstracts")
            
            # Crawl each publication for full details
            for idx, pub_link in enumerate(pub_links[:max_pubs], 1):
                self.log(f"\n[{idx}/{len(pub_links[:max_pubs])}] Crawling: {pub_link}")
                
                try:
                    time.sleep(crawl_delay)
                    
                    pub_data = self.extract_publication_details(pub_link)
                    
                    if pub_data and pub_data.get('abstract'):
                        publications.append(pub_data)
                        abstract_preview = pub_data['abstract'][:100] + "..." if len(pub_data['abstract']) > 100 else pub_data['abstract']
                        self.log(f"  [OK] Title: {pub_data['title'][:60]}...")
                        self.log(f"  [OK] Abstract: {abstract_preview}")
                    elif pub_data:
                        publications.append(pub_data)
                        self.log(f"  [WARNING] No abstract found, but saved publication")
                    else:
                        self.log(f"  [ERROR] Failed to extract publication data")
                    
                except Exception as e:
                    self.log(f"  [ERROR] {str(e)}")
                    logger.error(f"Error crawling {pub_link}: {e}", exc_info=True)
                    continue
            
        except Exception as e:
            self.log(f"[ERROR] Failed to crawl publications list: {str(e)}")
            logger.error(f"Publications list crawl error: {e}", exc_info=True)
        
        return publications
    
    def extract_publication_details(self, pub_url):
        """
        Extract full publication details including abstract from publication page
        
        Args:
            pub_url: URL of publication page
            
        Returns:
            Publication dictionary with full details
        """
        try:
            self.driver.get(pub_url)
            time.sleep(2)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            pub_data = {
                'title': '',
                'authors': [],
                'year': 'N/A',
                'abstract': '',
                'keywords': [],
                'publication_link': pub_url,
                'profile_link': '',
                'author_profile_name': '',
                'crawled_at': datetime.now().isoformat()
            }
            
            # Extract title from h1
            title_elem = soup.find('h1')
            if title_elem:
                pub_data['title'] = title_elem.get_text(strip=True)
            
            # Extract authors
            authors_elem = soup.find('p', class_='relations persons')
            if authors_elem:
                # Get all text and author links
                author_links = authors_elem.find_all('a', class_='person')
                if author_links:
                    pub_data['authors'] = [a.get_text(strip=True) for a in author_links]
                    # Get first author's profile link
                    pub_data['profile_link'] = urljoin(pub_url, author_links[0]['href'])
                    pub_data['author_profile_name'] = author_links[0].get_text(strip=True)
                else:
                    # Fallback: parse text
                    authors_text = authors_elem.get_text(strip=True)
                    pub_data['authors'] = [a.strip() for a in authors_text.split(',')]
            
            # Extract year from publication date
            date_elem = soup.find('span', class_='date')
            if date_elem:
                date_text = date_elem.get_text(strip=True)
                year_match = re.search(r'(19|20)\d{2}', date_text)
                if year_match:
                    pub_data['year'] = year_match.group()
            
            # Extract abstract - THIS IS THE KEY PART!
            abstract_section = soup.find('h2', string=re.compile('Abstract', re.I))
            if abstract_section:
                # Find the next div with class 'textblock'
                abstract_div = abstract_section.find_next('div', class_='textblock')
                if abstract_div:
                    # Get text and clean up
                    abstract_text = abstract_div.get_text(separator=' ', strip=True)
                    # Remove extra whitespace and line breaks
                    abstract_text = re.sub(r'\s+', ' ', abstract_text)
                    pub_data['abstract'] = abstract_text.strip()
            
            # Fallback: look for any div with rendering_abstractportal class
            if not pub_data['abstract']:
                abstract_div = soup.find('div', class_=re.compile('abstractportal'))
                if abstract_div:
                    textblock = abstract_div.find('div', class_='textblock')
                    if textblock:
                        abstract_text = textblock.get_text(separator=' ', strip=True)
                        abstract_text = re.sub(r'\s+', ' ', abstract_text)
                        pub_data['abstract'] = abstract_text.strip()
            
            # Extract keywords
            keywords_section = soup.find('h2', string=re.compile('Keywords', re.I))
            if keywords_section:
                keywords_list = keywords_section.find_next('ul', class_='keywords')
                if keywords_list:
                    keyword_items = keywords_list.find_all('li')
                    pub_data['keywords'] = [k.get_text(strip=True) for k in keyword_items]
            
            return pub_data
            
        except Exception as e:
            logger.error(f"Error extracting publication details from {pub_url}: {e}", exc_info=True)
            return None
    
    def crawl_via_authors(self, base_url, crawl_delay, max_pubs):
        """
        Fallback: Crawl publications via author profiles
        
        Args:
            base_url: Base organization URL
            crawl_delay: Delay between requests
            max_pubs: Maximum publications to crawl
            
        Returns:
            List of publications
        """
        publications = []
        
        try:
            self.log(f"Fetching author list from: {base_url}")
            self.driver.get(base_url)
            time.sleep(crawl_delay)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Extract author links
            author_links = self.extract_author_links(soup, base_url)
            self.log(f"[OK] Found {len(author_links)} author profiles")
            
            # Limit authors
            max_authors = min(len(author_links), config.MAX_AUTHORS_TO_CRAWL)
            self.log(f"[INFO] Will crawl {max_authors} authors")
            
            # Track total publications
            total_found = 0
            
            # Crawl each author
            for idx, author_link in enumerate(author_links[:max_authors], 1):
                if total_found >= max_pubs:
                    self.log(f"[LIMIT] Reached maximum publications ({max_pubs})")
                    break
                
                self.log(f"\n[{idx}/{max_authors}] Author: {author_link}")
                
                try:
                    time.sleep(crawl_delay)
                    
                    self.driver.get(author_link)
                    time.sleep(2)
                    
                    soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                    author_name = self.extract_author_name(soup)
                    
                    # Get publication links from author page
                    pub_links = self.extract_publication_links_from_author(soup, author_link)
                    
                    if pub_links:
                        self.log(f"  [OK] Found {len(pub_links)} publications")
                        
                        # Crawl each publication
                        for pub_link in pub_links[:max(1, max_pubs - total_found)]:
                            try:
                                time.sleep(crawl_delay)
                                pub_data = self.extract_publication_details(pub_link)
                                
                                if pub_data:
                                    # Set author info if not already set
                                    if not pub_data['author_profile_name']:
                                        pub_data['author_profile_name'] = author_name
                                        pub_data['profile_link'] = author_link
                                    
                                    publications.append(pub_data)
                                    total_found += 1
                                    self.log(f"    [OK] Added: {pub_data['title'][:50]}...")
                                    
                            except Exception as e:
                                self.log(f"    [ERROR] {str(e)}")
                                continue
                    else:
                        self.log(f"  [WARNING] No publications found")
                    
                except Exception as e:
                    self.log(f"  [ERROR] {str(e)}")
                    continue
            
        except Exception as e:
            self.log(f"[ERROR] Author crawling failed: {str(e)}")
            logger.error(f"Author crawl error: {e}", exc_info=True)
        
        return publications
    
    def extract_author_links(self, soup, base_url):
        """Extract author profile links"""
        author_links = set()
        
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
        
        return list(author_links)
    
    def extract_author_name(self, soup):
        """Extract author name from profile page"""
        name_elem = (
            soup.find('h1') or 
            soup.find('h2') or 
            soup.find('span', class_=re.compile('name', re.I))
        )
        
        if name_elem:
            return name_elem.get_text(strip=True)
        
        return 'Unknown Author'
    
    def extract_publication_links_from_author(self, soup, author_url):
        """Extract publication links from author profile"""
        pub_links = []
        
        # Find publication containers
        pub_containers = (
            soup.find_all('h3', class_='title') or
            soup.find_all('a', href=re.compile(r'/en/publications/'))
        )
        
        for container in pub_containers:
            if container.name == 'h3':
                link = container.find('a', href=True)
            else:
                link = container
            
            if link and link.get('href'):
                href = link['href']
                if '/publications/' in href:
                    full_url = urljoin(author_url, href)
                    if full_url not in self.visited_urls:
                        pub_links.append(full_url)
                        self.visited_urls.add(full_url)
        
        return pub_links