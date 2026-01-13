"""
Main GUI Application for Vertical Search Engine
Part 1: Imports and Setup
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import json
import os
import logging
import webbrowser
from datetime import datetime
from collections import defaultdict

# Import our modules
import config
from crawler import EnhancedCrawler
from inverted_index import AdvancedInvertedIndex
from scheduler import CrawlerScheduler

# Setup logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT,
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class VerticalSearchEngineGUI:
    """Main GUI application for the Vertical Search Engine"""
    
    def __init__(self, root):
        """
        Initialize the GUI application
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title(config.WINDOW_TITLE)
        self.root.geometry(config.WINDOW_SIZE)
        
        # Initialize components
        self.crawler = None
        self.index = AdvancedInvertedIndex()
        self.scheduler = CrawlerScheduler()
        self.current_results = []
        self.current_doc_data = None
        
        # Setup UI
        self.setup_ui()
        
        # Load existing index
        self.load_index()
        
        # Start scheduler
        self.scheduler.start()
        
        # Update statistics
        self.update_statistics()
        
        logger.info("GUI application initialized")
    
    def setup_ui(self):
        """Setup the complete GUI interface"""
        # Header
        self.setup_header()
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.setup_crawler_tab()
        self.setup_search_tab()
        self.setup_statistics_tab()
        self.setup_scheduler_tab()
    
    def setup_header(self):
        """Setup header section"""
        header = ttk.Frame(self.root)
        header.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(
            header, 
            text="Coventry University - Research Search Engine",
            font=('Helvetica', 16, 'bold')
        ).pack(side=tk.LEFT)
        
        # Status indicator
        self.status_label = ttk.Label(
            header,
            text="● Ready",
            font=('Helvetica', 10),
            foreground='green'
        )
        self.status_label.pack(side=tk.RIGHT, padx=10)
    
    def setup_crawler_tab(self):
        """Setup crawler configuration tab"""
        crawler_frame = ttk.Frame(self.notebook)
        self.notebook.add(crawler_frame, text="🕷️ Crawler")
        
        # Settings frame
        settings_frame = ttk.LabelFrame(crawler_frame, text="Crawling Settings", padding=10)
        settings_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Base URL
        ttk.Label(settings_frame, text="Base URL:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.url_entry = ttk.Entry(settings_frame, width=80)
        self.url_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        self.url_entry.insert(0, config.BASE_URL)
        
        # Max authors
        ttk.Label(settings_frame, text="Max Authors to Crawl:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.max_authors = ttk.Spinbox(settings_frame, from_=5, to=500, width=10)
        self.max_authors.set(config.MAX_AUTHORS_TO_CRAWL)
        self.max_authors.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Crawl delay
        ttk.Label(settings_frame, text="Crawl Delay (seconds):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.crawl_delay = ttk.Spinbox(settings_frame, from_=1, to=10, width=10)
        self.crawl_delay.set(config.CRAWL_DELAY)
        self.crawl_delay.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Robots.txt compliance
        self.robots_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            settings_frame,
            text="Respect robots.txt",
            variable=self.robots_var
        ).grid(row=3, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        settings_frame.columnconfigure(1, weight=1)
        
        # Buttons frame
        button_frame = ttk.Frame(settings_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        self.crawl_btn = ttk.Button(
            button_frame,
            text="▶ Start Crawling",
            command=self.start_crawling
        )
        self.crawl_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="📄 Load Sample Data",
            command=self.load_sample_data
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="🔄 Refresh Status",
            command=self.update_crawler_status
        ).pack(side=tk.LEFT, padx=5)
        
        # Status frame
        status_frame = ttk.LabelFrame(crawler_frame, text="Crawler Status", padding=10)
        status_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.crawler_status_text = tk.Text(status_frame, height=4, width=100)
        self.crawler_status_text.pack(fill=tk.X)
        self.update_crawler_status()
        
        # Log output frame
        log_frame = ttk.LabelFrame(crawler_frame, text="Crawler Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=100)
        self.log_text.pack(fill=tk.BOTH, expand=True)
    
    def setup_search_tab(self):
        """Setup search interface tab"""
        search_frame = ttk.Frame(self.notebook)
        self.notebook.add(search_frame, text="🔍 Search")
        
        # Search input frame
        input_frame = ttk.LabelFrame(search_frame, text="Search Publications", padding=10)
        input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(input_frame, text="Query:").pack(side=tk.LEFT, padx=5)
        
        self.search_entry = ttk.Entry(input_frame, width=80)
        self.search_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.search_entry.bind('<Return>', lambda e: self.perform_search())
        
        ttk.Button(
            input_frame,
            text="🔍 Search",
            command=self.perform_search
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            input_frame,
            text="🗑️ Clear",
            command=self.clear_search
        ).pack(side=tk.LEFT, padx=5)
        
        # Results info
        self.results_info = ttk.Label(search_frame, text="", font=('Helvetica', 10))
        self.results_info.pack(fill=tk.X, padx=10)
        
        # Results frame
        results_frame = ttk.LabelFrame(
            search_frame,
            text="Search Results (Ranked by Relevance)",
            padding=10
        )
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create treeview
        columns = ('Title', 'Authors', 'Year', 'Score')
        self.results_tree = ttk.Treeview(results_frame, columns=columns, height=12)
        
        # Configure columns
        self.results_tree.column('#0', width=0, stretch=tk.NO)
        self.results_tree.column('Title', width=500, anchor=tk.W)
        self.results_tree.column('Authors', width=300, anchor=tk.W)
        self.results_tree.column('Year', width=80, anchor=tk.CENTER)
        self.results_tree.column('Score', width=80, anchor=tk.CENTER)
        
        # Configure headings
        self.results_tree.heading('#0', text='', anchor=tk.W)
        self.results_tree.heading('Title', text='Title', anchor=tk.W)
        self.results_tree.heading('Authors', text='Authors', anchor=tk.W)
        self.results_tree.heading('Year', text='Year', anchor=tk.CENTER)
        self.results_tree.heading('Score', text='Relevance', anchor=tk.CENTER)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscroll=scrollbar.set)
        
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind events
        self.results_tree.bind('<Double-1>', self.open_publication)
        self.results_tree.bind('<<TreeviewSelect>>', self.on_result_select)
        
        # Details frame
        self.setup_details_frame(search_frame)

    """
    Main GUI Application - Part 2: Methods and Event Handlers
    Continuation of VerticalSearchEngineGUI class
    """

    def setup_details_frame(self, parent):
            """Setup publication details frame"""
            details_frame = ttk.LabelFrame(parent, text="Publication Details", padding=10)
            details_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Text widget for details
            self.details_text = tk.Text(details_frame, height=10, width=100, wrap=tk.WORD)
            self.details_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
            
            scrollbar = ttk.Scrollbar(details_frame, orient=tk.VERTICAL, command=self.details_text.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self.details_text.config(yscroll=scrollbar.set)
            
            # Configure link tags
            self.details_text.tag_config('link', foreground='blue', underline=True)
            self.details_text.tag_config('bold', font=('Helvetica', 10, 'bold'))
            self.details_text.tag_bind('link', '<Enter>', self.on_link_enter)
            self.details_text.tag_bind('link', '<Leave>', self.on_link_leave)
            self.details_text.tag_bind('link', '<Button-1>', self.on_link_click)
        
    def setup_statistics_tab(self):
            """Setup statistics display tab"""
            stats_frame = ttk.Frame(self.notebook)
            self.notebook.add(stats_frame, text="📊 Statistics")
            
            # Stats text
            self.stats_text = scrolledtext.ScrolledText(stats_frame, height=25, width=100)
            self.stats_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Buttons
            button_frame = ttk.Frame(stats_frame)
            button_frame.pack(fill=tk.X, padx=10, pady=10)
            
            ttk.Button(
                button_frame,
                text="🔄 Refresh Statistics",
                command=self.update_statistics
            ).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(
                button_frame,
                text="💾 Export Data",
                command=self.export_data
            ).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(
                button_frame,
                text="📋 Export Results",
                command=self.export_search_results
            ).pack(side=tk.LEFT, padx=5)
        
    def setup_scheduler_tab(self):
            """Setup scheduler configuration tab"""
            scheduler_frame = ttk.Frame(self.notebook)
            self.notebook.add(scheduler_frame, text="⏰ Scheduler")
            
            # Settings frame
            settings_frame = ttk.LabelFrame(scheduler_frame, text="Scheduling Settings", padding=10)
            settings_frame.pack(fill=tk.X, padx=10, pady=10)
            
            ttk.Label(settings_frame, text="Schedule Day:").grid(row=0, column=0, sticky=tk.W, pady=5)
            self.schedule_day = ttk.Combobox(
                settings_frame,
                values=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
                width=15
            )
            self.schedule_day.set(config.CRAWL_SCHEDULE_DAY.title())
            self.schedule_day.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
            
            ttk.Label(settings_frame, text="Schedule Time (HH:MM):").grid(row=1, column=0, sticky=tk.W, pady=5)
            self.schedule_time = ttk.Entry(settings_frame, width=15)
            self.schedule_time.insert(0, config.CRAWL_SCHEDULE_TIME)
            self.schedule_time.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
            
            # Buttons
            button_frame = ttk.Frame(settings_frame)
            button_frame.grid(row=2, column=0, columnspan=2, pady=10)
            
            ttk.Button(
                button_frame,
                text="💾 Save Schedule",
                command=self.save_schedule
            ).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(
                button_frame,
                text="▶ Run Now",
                command=self.run_scheduler_now
            ).pack(side=tk.LEFT, padx=5)
            
            # Status frame
            status_frame = ttk.LabelFrame(scheduler_frame, text="Scheduler Status", padding=10)
            status_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            self.scheduler_status_text = scrolledtext.ScrolledText(status_frame, height=20, width=100)
            self.scheduler_status_text.pack(fill=tk.BOTH, expand=True)
            
            self.update_scheduler_status()
        
        # Event Handlers
        
    def log_message(self, msg):
            """Add message to crawler log"""
            self.log_text.insert(tk.END, msg + '\n')
            self.log_text.see(tk.END)
            self.root.update()
        
    def update_status(self, text, color='green'):
            """Update status indicator"""
            self.status_label.config(text=f"● {text}", foreground=color)
            self.root.update()
        
    def start_crawling(self):
            """Start crawling in separate thread"""
            self.crawl_btn.config(state=tk.DISABLED)
            self.log_text.delete(1.0, tk.END)
            self.update_status("Crawling...", "orange")
            
            url = self.url_entry.get()
            max_authors = int(self.max_authors.get())
            
            def crawl():
                try:
                    self.crawler = EnhancedCrawler(callback=self.log_message)
                    pubs = self.crawler.crawl_department(url, max_authors)
                    
                    if pubs:
                        self.build_index(pubs)
                        self.log_message("✓ Indexing completed!")
                        self.update_statistics()
                        self.update_status("Ready", "green")
                    else:
                        self.log_message("⚠ No publications found")
                        self.update_status("Ready", "green")
                        
                except Exception as e:
                    self.log_message(f"✗ Error: {str(e)}")
                    logger.error(f"Crawling error: {e}", exc_info=True)
                    self.update_status("Error", "red")
                finally:
                    self.crawl_btn.config(state=tk.NORMAL)
            
            thread = threading.Thread(target=crawl, daemon=True)
            thread.start()
        
    def build_index(self, publications):
            """Build inverted index from publications"""
            self.index = AdvancedInvertedIndex()
            
            for i, pub in enumerate(publications):
                self.index.add_document(i, pub)
            
            # Save index
            self.index.save(config.INDEX_FILE)
            
            # Save publications
            with open(config.PUBLICATIONS_FILE, 'w') as f:
                json.dump(publications, f, indent=2, default=str)
            
            self.log_message(f"✓ Indexed {len(publications)} publications")
            logger.info(f"Built index with {len(publications)} publications")
        
    def load_sample_data(self):
            """Load sample publications for demonstration"""
            sample_pubs = [
                {
                    'title': 'Machine Learning Approaches for Mathematics and Data Analysis',
                    'authors': ['Dr. John Smith', 'Dr. Jane Doe', 'Prof. Michael Johnson'],
                    'year': '2023',
                    'abstract': 'This paper presents novel machine learning algorithms for mathematical data analysis and computational modeling.',
                    'keywords': ['mathematics', 'machine learning', 'data analysis'],
                    'publication_link': 'https://pureportal.coventry.ac.uk/publications/ml-mathematics-2023',
                    'profile_link': 'https://pureportal.coventry.ac.uk/person/john-smith',
                    'author_profile_name': 'Dr. John Smith',
                    'crawled_at': datetime.now().isoformat()
                },
                {
                    'title': 'Advanced Neural Networks and Deep Learning in Applied Mathematics',
                    'authors': ['Prof. Michael Johnson', 'Dr. Sarah Williams'],
                    'year': '2023',
                    'abstract': 'Deep learning methods for solving differential equations and complex mathematical problems using neural networks.',
                    'keywords': ['mathematics', 'neural networks', 'deep learning'],
                    'publication_link': 'https://pureportal.coventry.ac.uk/publications/neural-networks-2023',
                    'profile_link': 'https://pureportal.coventry.ac.uk/person/michael-johnson',
                    'author_profile_name': 'Prof. Michael Johnson',
                    'crawled_at': datetime.now().isoformat()
                },
                {
                    'title': 'Computational Mathematics: Algorithms and Scientific Applications',
                    'authors': ['Dr. Robert Brown', 'Dr. Emily Davis'],
                    'year': '2022',
                    'abstract': 'Computational methods for solving complex mathematical and scientific problems using advanced algorithms.',
                    'keywords': ['mathematics', 'computational', 'algorithms'],
                    'publication_link': 'https://pureportal.coventry.ac.uk/publications/computational-math-2022',
                    'profile_link': 'https://pureportal.coventry.ac.uk/person/robert-brown',
                    'author_profile_name': 'Dr. Robert Brown',
                    'crawled_at': datetime.now().isoformat()
                },
            ]
            
            self.build_index(sample_pubs)
            self.log_message("✓ Sample data loaded successfully!")
            self.log_message(f"✓ Loaded {len(sample_pubs)} sample publications")
            self.log_message("✓ Try searching: 'Mathematics', 'neural networks', '2023', etc.")
            self.update_statistics()
            self.update_status("Ready", "green")
        
    def load_index(self):
        """Load existing index if available"""
        if config.INDEX_FILE.exists():
            try:
                if self.index.load(config.INDEX_FILE):
                    self.log_message("✓ Index loaded from file")
                    logger.info("Existing index loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load index: {e}")

    """
    Main GUI Application - Part 3: Search and Display Methods
    Continuation of VerticalSearchEngineGUI class
    """

    def perform_search(self):
            """Execute search query"""
            query = self.search_entry.get().strip()
            
            if not query:
                messagebox.showwarning("Input Error", "Please enter a search query")
                return
            
            self.update_status("Searching...", "orange")
            
            # Perform search
            results = self.index.search(query)
            
            # Clear previous results
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
            
            self.details_text.delete(1.0, tk.END)
            
            if not results:
                self.results_info.config(text=f"No results found for '{query}'")
                messagebox.showinfo("Search Results", f"No publications found matching '{query}'")
                self.log_message(f"Search: '{query}' - No results found")
                self.update_status("Ready", "green")
                return
            
            # Store results
            self.current_results = results
            
            # Update results info
            self.results_info.config(
                text=f"Found {len(results)} results for '{query}' (showing top {min(len(results), config.MAX_RESULTS_DISPLAY)})"
            )
            
            # Add results to treeview
            for i, (doc_id, doc_data, score) in enumerate(results[:config.MAX_RESULTS_DISPLAY]):
                authors = ', '.join(doc_data['authors']) if isinstance(doc_data['authors'], list) else str(doc_data['authors'])
                relevance = f"{score:.2f}"
                
                self.results_tree.insert(
                    '', tk.END, iid=i,
                    values=(
                        doc_data['title'][:80],
                        authors[:60],
                        doc_data['year'],
                        relevance
                    )
                )
            
            # Log search
            self.log_message(f"\n{'='*80}")
            self.log_message(f"SEARCH QUERY: '{query}'")
            self.log_message(f"{'='*80}")
            self.log_message(f"✓ Found {len(results)} publications\n")
            
            # Show first result details
            if results:
                first_doc_id, first_doc_data, first_score = results[0]
                self.display_publication_details(first_doc_data)
            
            self.update_status("Ready", "green")
        
    def clear_search(self):
            """Clear search results"""
            self.search_entry.delete(0, tk.END)
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
            self.details_text.delete(1.0, tk.END)
            self.results_info.config(text="")
            self.current_results = []
        
    def on_result_select(self, event):
            """Handle result selection"""
            selection = self.results_tree.selection()
            if not selection:
                return
            
            item_id = int(selection[0])
            
            if hasattr(self, 'current_results') and item_id < len(self.current_results):
                doc_id, doc_data, score = self.current_results[item_id]
                self.display_publication_details(doc_data)
        
    def open_publication(self, event):
            """Open publication link on double-click"""
            selection = self.results_tree.selection()
            if not selection:
                return
            
            item_id = int(selection[0])
            
            if hasattr(self, 'current_results') and item_id < len(self.current_results):
                doc_id, doc_data, score = self.current_results[item_id]
                
                # Open publication link in browser
                if doc_data.get('publication_link'):
                    webbrowser.open(doc_data['publication_link'])
                    self.log_message(f"✓ Opened: {doc_data['publication_link']}")
        
    def display_publication_details(self, doc_data):
            """Display full publication details with clickable links"""
            authors = ', '.join(doc_data['authors']) if isinstance(doc_data['authors'], list) else str(doc_data['authors'])
            
            self.details_text.delete(1.0, tk.END)
            self.details_text.config(state=tk.NORMAL)
            
            # Store current doc data
            self.current_doc_data = doc_data
            
            # Insert formatted text
            self.details_text.insert(tk.END, "PUBLICATION DETAILS\n", 'bold')
            self.details_text.insert(tk.END, "="*80 + "\n\n")
            
            self.details_text.insert(tk.END, "Title: ", 'bold')
            self.details_text.insert(tk.END, doc_data['title'] + "\n\n")
            
            self.details_text.insert(tk.END, "Authors: ", 'bold')
            self.details_text.insert(tk.END, authors + "\n\n")
            
            self.details_text.insert(tk.END, "Year: ", 'bold')
            self.details_text.insert(tk.END, doc_data['year'] + "\n\n")
            
            self.details_text.insert(tk.END, "Author Profile: ", 'bold')
            self.details_text.insert(tk.END, doc_data['author_profile_name'] + "\n\n")
            
            # Publication link
            self.details_text.insert(tk.END, "Publication Link: ", 'bold')
            link_start = self.details_text.index(tk.END + "-1c")
            self.details_text.insert(tk.END, doc_data.get('publication_link', 'N/A'))
            link_end = self.details_text.index(tk.END + "-1c")
            if doc_data.get('publication_link'):
                self.details_text.tag_add('link', link_start, link_end)
            self.details_text.insert(tk.END, "\n\n")
            
            # Profile link
            self.details_text.insert(tk.END, "Profile Link: ", 'bold')
            link_start = self.details_text.index(tk.END + "-1c")
            self.details_text.insert(tk.END, doc_data.get('profile_link', 'N/A'))
            link_end = self.details_text.index(tk.END + "-1c")
            if doc_data.get('profile_link'):
                self.details_text.tag_add('link', link_start, link_end)
            self.details_text.insert(tk.END, "\n\n")
            
            self.details_text.insert(tk.END, "Abstract: ", 'bold')
            self.details_text.insert(tk.END, doc_data.get('abstract', 'N/A') + "\n\n")
            
            keywords = ', '.join(doc_data.get('keywords', [])) if isinstance(doc_data.get('keywords', []), list) else doc_data.get('keywords', 'N/A')
            self.details_text.insert(tk.END, "Keywords: ", 'bold')
            self.details_text.insert(tk.END, keywords + "\n\n")
            
            self.details_text.insert(tk.END, "="*80)
            
            self.details_text.config(state=tk.DISABLED)
        
    def on_link_enter(self, event):
            """Change cursor on link hover"""
            self.details_text.config(cursor='hand2')
        
    def on_link_leave(self, event):
            """Restore cursor when leaving link"""
            self.details_text.config(cursor='')
        
    def on_link_click(self, event):
            """Open link in browser when clicked"""
            try:
                index = self.details_text.index(f"@{event.x},{event.y}")
                
                if 'link' in self.details_text.tag_names(index):
                    line_start = self.details_text.index(f"{index} linestart")
                    line_end = self.details_text.index(f"{index} lineend")
                    line_text = self.details_text.get(line_start, line_end)
                    
                    # Extract URL
                    if 'http' in line_text:
                        url = line_text.split('http')[1]
                        url = 'http' + url.strip()
                        url = url.split()[0]
                        
                        webbrowser.open(url)
                        self.log_message(f"✓ Opened link: {url}")
                        
            except Exception as e:
                logger.error(f"Error opening link: {e}")
                messagebox.showerror("Error", f"Could not open link: {str(e)}")
        
    def update_statistics(self):
            """Update statistics display"""
            stats = self.index.get_statistics()
            
            output = f"""
    {'='*80}
    SEARCH ENGINE STATISTICS
    {'='*80}

    Index Information:
    • Total Publications: {stats.get('total_documents', 0)}
    • Unique Terms (Tokens): {stats.get('unique_terms', 0)}
    • Total Index Entries: {stats.get('total_postings', 0)}
    • Status: {'Ready for Search' if stats.get('total_documents', 0) > 0 else 'Empty - Load or Crawl Data'}

    Searchable Fields & Weights:
    • Title (Weight: {config.FIELD_WEIGHTS['title']}x)
    • Authors (Weight: {config.FIELD_WEIGHTS['authors']}x)
    • Keywords (Weight: {config.FIELD_WEIGHTS['keywords']}x)
    • Year (Weight: {config.FIELD_WEIGHTS['year']}x)
    • Abstract (Weight: {config.FIELD_WEIGHTS['abstract']}x)

    Ranking Algorithm:
    • TF-IDF with field weighting
    • Title matches boost relevance by 1.5x
    • Multi-field matching adds bonus points
    • Query term coverage bonus

    NLP Features:
    • Text preprocessing (lowercase, special char removal)
    • Tokenization using NLTK
    • Stop word removal
    • Porter Stemming
    • WordNet Lemmatization

    Recent Activity:
    • Last Updated: {self.get_last_crawl_time()}
    • Data File: {config.PUBLICATIONS_FILE}
    • Index File: {config.INDEX_FILE}

    """
            
            if stats.get('total_authors'):
                output += f"\nPublication Statistics:\n"
                output += f"  • Total Authors: {stats['total_authors']}\n"
                
                if stats.get('publications_by_year'):
                    output += f"\n  Publications by Year:\n"
                    for year, count in stats['publications_by_year'].items():
                        output += f"    {year}: {count} publications\n"
            
            output += f"\n{'='*80}\n"
            
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(tk.END, output)
        
    def get_last_crawl_time(self):
        """Get last crawl timestamp"""
        if config.PUBLICATIONS_FILE.exists():
            try:
                with open(config.PUBLICATIONS_FILE, 'r') as f:
                    data = json.load(f)
                    if data:
                        return data[0].get('crawled_at', 'Unknown')
            except:
                pass
        return "Never"

    """
    Main GUI Application - Part 4: Scheduler, Export, and Main Entry
    Final part of VerticalSearchEngineGUI class
    """

    def update_crawler_status(self):
            """Update crawler status display"""
            self.crawler_status_text.delete(1.0, tk.END)
            
            status = f"""
    Crawler Status: {'Active' if self.crawler else 'Idle'}
    Base URL: {config.BASE_URL}
    Base Domain: {config.BASE_DOMAIN}
    Robots.txt Compliance: Enabled
    User Agent: {config.USER_AGENT}
    Crawl Delay: {config.CRAWL_DELAY} seconds
    Max Authors: {config.MAX_AUTHORS_TO_CRAWL}
    """
            self.crawler_status_text.insert(tk.END, status)
        
    def update_scheduler_status(self):
            """Update scheduler status display"""
            status = self.scheduler.get_status()
            
            output = f"""
    {'='*80}
    SCHEDULER STATUS
    {'='*80}

    Status: {'Running' if status['running'] else 'Stopped'}

    Schedule Configuration:
    • Day: {config.CRAWL_SCHEDULE_DAY.title()}
    • Time: {config.CRAWL_SCHEDULE_TIME}

    Activity:
    • Last Run: {status['last_run'] if status['last_run'] else 'Never'}
    • Next Run: {status['next_run'] if status['next_run'] else 'Not scheduled'}

    Notes:
    • The crawler will automatically run weekly on the scheduled day/time
    • You can manually trigger a crawl using the "Run Now" button
    • Crawled data will automatically update the search index
    • Check the Crawler Log for detailed crawl information

    {'='*80}
    """
            
            self.scheduler_status_text.delete(1.0, tk.END)
            self.scheduler_status_text.insert(tk.END, output)
        
    def save_schedule(self):
            """Save scheduler configuration"""
            try:
                # Update config (note: this doesn't persist to file)
                config.CRAWL_SCHEDULE_DAY = self.schedule_day.get().lower()
                config.CRAWL_SCHEDULE_TIME = self.schedule_time.get()
                
                # Restart scheduler with new settings
                self.scheduler.stop()
                self.scheduler = CrawlerScheduler()
                self.scheduler.start()
                
                messagebox.showinfo("Success", "Schedule updated successfully!")
                self.update_scheduler_status()
                logger.info(f"Schedule updated: {config.CRAWL_SCHEDULE_DAY} at {config.CRAWL_SCHEDULE_TIME}")
                
            except Exception as e:
                logger.error(f"Failed to save schedule: {e}")
                messagebox.showerror("Error", f"Failed to save schedule: {str(e)}")
        
    def run_scheduler_now(self):
            """Trigger manual crawl through scheduler"""
            if messagebox.askyesno("Confirm", "Run crawler now? This may take several minutes."):
                self.scheduler.run_now()
                self.log_message("✓ Manual crawl triggered via scheduler")
                self.update_status("Crawling...", "orange")
                
                # Monitor completion
                def check_completion():
                    time.sleep(5)
                    self.update_statistics()
                    self.update_status("Ready", "green")
                
                threading.Thread(target=check_completion, daemon=True).start()
        
    def export_data(self):
            """Export all indexed publications"""
            if not self.index.documents:
                messagebox.showwarning("No Data", "No data to export")
                return
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                try:
                    data = [self.index.documents[i] for i in sorted(self.index.documents.keys())]
                    
                    with open(filename, 'w') as f:
                        json.dump(data, f, indent=2, default=str)
                    
                    messagebox.showinfo("Success", f"Data exported to {filename}")
                    self.log_message(f"✓ Exported {len(data)} publications to {filename}")
                    logger.info(f"Data exported to {filename}")
                    
                except Exception as e:
                    logger.error(f"Export failed: {e}")
                    messagebox.showerror("Error", f"Export failed: {str(e)}")
        
    def export_search_results(self):
            """Export current search results"""
            if not self.current_results:
                messagebox.showwarning("No Results", "No search results to export")
                return
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("CSV files", "*.csv"), ("All files", "*.*")]
            )
            
            if filename:
                try:
                    if filename.endswith('.csv'):
                        # Export as CSV
                        import csv
                        with open(filename, 'w', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            writer.writerow(['Title', 'Authors', 'Year', 'Relevance Score', 'Link'])
                            
                            for doc_id, doc_data, score in self.current_results:
                                authors = ', '.join(doc_data['authors']) if isinstance(doc_data['authors'], list) else str(doc_data['authors'])
                                writer.writerow([
                                    doc_data['title'],
                                    authors,
                                    doc_data['year'],
                                    f"{score:.2f}",
                                    doc_data.get('publication_link', '')
                                ])
                    else:
                        # Export as JSON
                        results = [{
                            'title': doc_data['title'],
                            'authors': doc_data['authors'],
                            'year': doc_data['year'],
                            'relevance_score': score,
                            'abstract': doc_data.get('abstract', ''),
                            'keywords': doc_data.get('keywords', []),
                            'publication_link': doc_data.get('publication_link', ''),
                            'profile_link': doc_data.get('profile_link', '')
                        } for doc_id, doc_data, score in self.current_results]
                        
                        with open(filename, 'w') as f:
                            json.dump(results, f, indent=2, default=str)
                    
                    messagebox.showinfo("Success", f"Search results exported to {filename}")
                    self.log_message(f"✓ Exported {len(self.current_results)} search results to {filename}")
                    logger.info(f"Search results exported to {filename}")
                    
                except Exception as e:
                    logger.error(f"Export failed: {e}")
                    messagebox.showerror("Error", f"Export failed: {str(e)}")
        
    def on_closing(self):
            """Handle window closing"""
            if messagebox.askokcancel("Quit", "Do you want to quit?"):
                # Stop scheduler
                self.scheduler.stop()
                
                # Close any open driver
                if self.crawler:
                    self.crawler.close_driver()
                
                logger.info("Application closing")
                self.root.destroy()

def main():
    """Main entry point"""
    # Create root window
    root = tk.Tk()
    
    # Create application
    app = VerticalSearchEngineGUI(root)
    
    # Handle window closing
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Start main loop
    logger.info("Starting application main loop")
    root.mainloop()


if __name__ == "__main__":
    main()