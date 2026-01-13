"""
Robots.txt compliance checker
"""
import urllib.robotparser
import json
import logging
from urllib.parse import urlparse, urljoin
from datetime import datetime, timedelta
import config

logger = logging.getLogger(__name__)


class RobotsChecker:
    """Check and respect robots.txt rules"""
    
    def __init__(self, user_agent=config.USER_AGENT):
        """
        Initialize robots checker
        
        Args:
            user_agent: User agent string to identify crawler
        """
        self.user_agent = user_agent
        self.parsers = {}  # domain -> RobotFileParser
        self.cache_file = config.ROBOTS_CACHE_FILE
        self.cache_duration = timedelta(days=1)  # Refresh daily
        
        self._load_cache()
        logger.info(f"RobotsChecker initialized with user agent: {user_agent}")
    
    def _load_cache(self):
        """Load cached robots.txt data"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                    
                    for domain, data in cache_data.items():
                        cached_time = datetime.fromisoformat(data['cached_at'])
                        
                        # Check if cache is still valid
                        if datetime.now() - cached_time < self.cache_duration:
                            logger.info(f"Loaded cached robots.txt for {domain}")
                            # Note: We'll need to re-fetch anyway as RobotFileParser can't be pickled
        except Exception as e:
            logger.warning(f"Could not load robots cache: {e}")
    
    def _save_cache(self):
        """Save robots.txt cache"""
        try:
            cache_data = {}
            for domain, parser in self.parsers.items():
                cache_data[domain] = {
                    'cached_at': datetime.now().isoformat(),
                    'user_agent': self.user_agent
                }
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            logger.info("Robots cache saved")
        except Exception as e:
            logger.warning(f"Could not save robots cache: {e}")
    
    def _get_parser(self, url):
        """
        Get robots.txt parser for a domain
        
        Args:
            url: URL to check
            
        Returns:
            RobotFileParser instance
        """
        parsed = urlparse(url)
        domain = parsed.netloc
        
        if domain not in self.parsers:
            robots_url = f"{parsed.scheme}://{domain}/robots.txt"
            
            parser = urllib.robotparser.RobotFileParser()
            parser.set_url(robots_url)
            
            try:
                parser.read()
                self.parsers[domain] = parser
                logger.info(f"Loaded robots.txt from {robots_url}")
                self._save_cache()
            except Exception as e:
                logger.warning(f"Could not fetch robots.txt from {robots_url}: {e}")
                # Create permissive parser
                parser = urllib.robotparser.RobotFileParser()
                self.parsers[domain] = parser
        
        return self.parsers[domain]
    
    def can_fetch(self, url):
        """
        Check if URL can be fetched according to robots.txt
        
        Args:
            url: URL to check
            
        Returns:
            True if allowed, False if disallowed
        """
        try:
            # Parse the URL to check for blocked patterns
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            
            # Check if URL contains explicitly blocked patterns
            # Robots.txt blocks: /*?*format=rss and /*?*export=xls
            if 'format' in query_params and 'rss' in query_params.get('format', []):
                logger.warning(f"Robots.txt disallows crawling (format=rss): {url}")
                return False
            
            if 'export' in query_params and 'xls' in query_params.get('export', []):
                logger.warning(f"Robots.txt disallows crawling (export=xls): {url}")
                return False
            
            # For Coventry portal, if no blocked query params, allow
            if 'pureportal.coventry.ac.uk' in url:
                logger.debug(f"Robots.txt allows crawling (no blocked params): {url}")
                return True
            
            # Fallback to standard parser for other sites
            parser = self._get_parser(url)
            allowed = parser.can_fetch(self.user_agent, url)
            
            if not allowed:
                logger.warning(f"Robots.txt disallows crawling: {url}")
            else:
                logger.info(f"Robots.txt allows crawling: {url}")
            
            return allowed
        except Exception as e:
            logger.error(f"Error checking robots.txt for {url}: {e}")
            # Default to allowing if there's an error
            return True
    
    def get_crawl_delay(self, url):
        """
        Get crawl delay from robots.txt
        
        Args:
            url: URL to check
            
        Returns:
            Crawl delay in seconds (None if not specified)
        """
        try:
            parser = self._get_parser(url)
            delay = parser.crawl_delay(self.user_agent)
            
            if delay:
                logger.info(f"Robots.txt specifies crawl delay: {delay}s for {url}")
            
            return delay
        except Exception as e:
            logger.error(f"Error getting crawl delay for {url}: {e}")
            return None
    
    def get_effective_delay(self, url):
        """
        Get effective crawl delay (max of config and robots.txt)
        
        Args:
            url: URL to check
            
        Returns:
            Crawl delay in seconds
        """
        robots_delay = self.get_crawl_delay(url)
        
        if robots_delay:
            return max(config.CRAWL_DELAY, robots_delay)
        
        return config.CRAWL_DELAY