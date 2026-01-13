"""
Automated crawler scheduling
"""
import schedule
import time
import threading
import logging
import json
from datetime import datetime
from pathlib import Path
import config
from crawler import EnhancedCrawler
from inverted_index import AdvancedInvertedIndex

logger = logging.getLogger(__name__)


class CrawlerScheduler:
    """Manages automated crawling on a schedule"""
    
    def __init__(self):
        """Initialize scheduler"""
        self.running = False
        self.thread = None
        self.last_run = None
        self.next_run = None
        self.status_file = config.DATA_DIR / "scheduler_status.json"
        
        self._load_status()
        logger.info("CrawlerScheduler initialized")
    
    def _load_status(self):
        """Load scheduler status from file"""
        try:
            if self.status_file.exists():
                with open(self.status_file, 'r') as f:
                    status = json.load(f)
                    self.last_run = status.get('last_run')
                    logger.info(f"Last crawl run: {self.last_run}")
        except Exception as e:
            logger.warning(f"Could not load scheduler status: {e}")
    
    def _save_status(self):
        """Save scheduler status to file"""
        try:
            status = {
                'last_run': self.last_run,
                'next_run': self.next_run
            }
            
            with open(self.status_file, 'w') as f:
                json.dump(status, f, indent=2)
            
            logger.info("Scheduler status saved")
        except Exception as e:
            logger.warning(f"Could not save scheduler status: {e}")
    
    def crawl_and_index(self):
        """Execute crawling and indexing"""
        logger.info("="*80)
        logger.info("SCHEDULED CRAWL STARTING")
        logger.info("="*80)
        
        try:
            # Initialize crawler
            crawler = EnhancedCrawler()
            
            # Crawl publications
            publications = crawler.crawl_department(
                config.BASE_URL,
                config.MAX_AUTHORS_TO_CRAWL
            )
            
            if publications:
                # Build index
                index = AdvancedInvertedIndex()
                
                for i, pub in enumerate(publications):
                    index.add_document(i, pub)
                
                # Save index
                index.save(config.INDEX_FILE)
                
                # Save publications
                with open(config.PUBLICATIONS_FILE, 'w') as f:
                    json.dump(publications, f, indent=2, default=str)
                
                logger.info(f"✓ Successfully indexed {len(publications)} publications")
                
                # Update status
                self.last_run = datetime.now().isoformat()
                self._save_status()
                
            else:
                logger.warning("No publications found during scheduled crawl")
            
        except Exception as e:
            logger.error(f"Scheduled crawl failed: {e}", exc_info=True)
        
        logger.info("="*80)
        logger.info("SCHEDULED CRAWL COMPLETED")
        logger.info("="*80)
    
    def start(self):
        """Start the scheduler"""
        if self.running:
            logger.warning("Scheduler already running")
            return
        
        # Schedule weekly crawl
        schedule_time = config.CRAWL_SCHEDULE_TIME
        schedule_day = config.CRAWL_SCHEDULE_DAY.lower()
        
        # Map day names to schedule methods
        day_methods = {
            'monday': schedule.every().monday,
            'tuesday': schedule.every().tuesday,
            'wednesday': schedule.every().wednesday,
            'thursday': schedule.every().thursday,
            'friday': schedule.every().friday,
            'saturday': schedule.every().saturday,
            'sunday': schedule.every().sunday
        }
        
        if schedule_day in day_methods:
            day_methods[schedule_day].at(schedule_time).do(self.crawl_and_index)
            logger.info(f"Scheduled weekly crawl: Every {schedule_day.title()} at {schedule_time}")
        else:
            logger.error(f"Invalid schedule day: {schedule_day}")
            return
        
        # Start scheduler thread
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        
        logger.info("Scheduler started successfully")
    
    def _run_scheduler(self):
        """Run scheduler loop"""
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        
        schedule.clear()
        logger.info("Scheduler stopped")
    
    def run_now(self):
        """Run crawl immediately (for manual trigger)"""
        logger.info("Manual crawl triggered")
        thread = threading.Thread(target=self.crawl_and_index, daemon=True)
        thread.start()
    
    def get_next_run_time(self):
        """Get next scheduled run time"""
        jobs = schedule.get_jobs()
        if jobs:
            return jobs[0].next_run
        return None
    
    def get_status(self):
        """Get scheduler status"""
        return {
            'running': self.running,
            'last_run': self.last_run,
            'next_run': str(self.get_next_run_time()) if self.get_next_run_time() else None
        }