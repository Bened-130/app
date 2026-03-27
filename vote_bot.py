#!/usr/bin/env python3
"""
Enhanced Automated Voting Bot
- Votes for a SPECIFIC candidate you provide
- Distributes 5000 votes over 1 hour
- Randomly rotates through multiple API addresses/URLs
- Handles URL failures gracefully with automatic failover

Usage:
    # Single URL mode
    python vote_bot.py --candidate "Alice" --url http://localhost:5500 --votes 5000 --duration 3600
    
    # Multi-URL rotation mode (recommended)
    python vote_bot.py --candidate "Bob" --urls urls.txt --votes 5500 --duration 3600
    
    # Inline multiple URLs
    python vote_bot.py --candidate "Charlie" --url http://server1.com --url http://server2.com --url http://server3.com --votes 5000 --duration 3600
"""

import requests
import time
import random
import argparse
import sys
import json
from datetime import datetime, timedelta
from urllib.parse import urljoin
import itertools


class MultiURLVoteBot:
    def __init__(self, candidate_name, urls, shuffle_urls=True):
        """
        Initialize bot with specific candidate and multiple URLs.
        
        Args:
            candidate_name: The EXACT name to vote for (case-sensitive)
            urls: List of base URLs to rotate through
            shuffle_urls: Whether to randomize URL order
        """
        self.candidate_name = candidate_name.strip()
        self.urls = [url.rstrip('/') for url in urls]
        self.shuffle_urls = shuffle_urls
        
        # URL rotation management
        self.url_cycle = None
        self.current_url_index = 0
        self.failed_urls = set()
        self.url_stats = {url: {'success': 0, 'fail': 0} for url in self.urls}
        
        # Candidate validation
        self.available_candidates = []
        self.validated_candidate = None
        
        # Statistics
        self.total_success = 0
        self.total_fail = 0
        self.start_time = None
        
        # Setup URL rotation
        self._setup_url_rotation()
        
    def _setup_url_rotation(self):
        """Initialize URL cycling strategy."""
        urls_to_use = list(self.urls)
        
        if self.shuffle_urls:
            random.shuffle(urls_to_use)
            print(f"🔀 URLs shuffled for random rotation")
        
        # Create infinite cycle
        self.url_cycle = itertools.cycle(urls_to_use)
        print(f"🌐 Configured {len(urls_to_use)} URL(s) for rotation:")
        for i, url in enumerate(urls_to_use, 1):
            status = " [ACTIVE]" if i == 1 else ""
            print(f"   {i}. {url}{status}")
    
    def get_next_url(self):
        """Get next URL from rotation, skipping failed ones."""
        max_attempts = len(self.urls)
        attempts = 0
        
        while attempts < max_attempts:
            url = next(self.url_cycle)
            if url not in self.failed_urls:
                return url
            attempts += 1
        
        # All URLs failed
        return None
    
    def mark_url_failed(self, url):
        """Mark a URL as failed and remove from rotation."""
        self.failed_urls.add(url)
        remaining = len(self.urls) - len(self.failed_urls)
        print(f"⚠️  Marked {url} as failed. {remaining} URL(s) remaining.")
        
        if remaining == 0:
            raise RuntimeError("All URLs have failed. Stopping bot.")
    
    def fetch_candidates(self, url):
        """Fetch available candidates from specific URL."""
        try:
            endpoint = f"{url}/api/names"
            response = requests.get(endpoint, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            self.available_candidates = [item['name'] for item in data]
            
            # Validate our target candidate exists
            if self.candidate_name not in self.available_candidates:
                print(f"\n❌ ERROR: Candidate '{self.candidate_name}' not found!")
                print(f"Available candidates: {self.available_candidates}")
                return False
            
            self.validated_candidate = self.candidate_name
            print(f"✅ Candidate '{self.candidate_name}' validated on {url}")
            print(f"All candidates: {self.available_candidates}")
            return True
            
        except Exception as e:
            print(f"⚠️  Failed to fetch candidates from {url}: {e}")
            return False
    
    def cast_vote(self, url):
        """Cast a single vote through specific URL."""
        endpoint = f"{url}/vote"
        
        try:
            response = requests.post(
                endpoint,
                json={"name": self.validated_candidate},
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": f"VoteBot/1.0 (Candidate: {self.candidate_name})"
                },
                timeout=10
            )
            response.raise_for_status()
            
            # Update stats
            self.url_stats[url]['success'] += 1
            return True, response.json()
            
        except requests.exceptions.RequestException as e:
            self.url_stats[url]['fail'] += 1
            return False, str(e)
        except Exception as e:
            self.url_stats[url]['fail'] += 1
            return False, str(e)
    
    def run(self, total_votes, duration_seconds):
        """
        Execute voting campaign.
        
        Strategy:
        - Distribute votes evenly over time
        - Rotate URLs randomly
        - Skip failed URLs automatically
        - Report progress every 100 votes
        """
        print(f"\n{'='*60}")
        print(f"🎯 TARGETED VOTE BOT")
        print(f"{'='*60}")
        print(f"Target Candidate: {self.candidate_name}")
        print(f"Total Votes: {total_votes:,}")
        print(f"Duration: {duration_seconds:,} seconds ({duration_seconds/3600:.2f} hours)")
        print(f"Rate: ~{total_votes/(duration_seconds/3600):.0f} votes/hour")
        print(f"URL Rotation: {'Random' if self.shuffle_urls else 'Sequential'}")
        print(f"{'='*60}\n")
        
        # Initial validation - try URLs until one works
        print("🔍 Validating candidate on available URLs...")
        validated = False
        validation_attempts = 0
        
        while not validated and validation_attempts < len(self.urls) * 2:
            url = self.get_next_url()
            if url is None:
                break
            
            if self.fetch_candidates(url):
                validated = True
                break
            else:
                validation_attempts += 1
                time.sleep(1)
        
        if not validated:
            print("❌ Could not validate candidate on any URL")
            return False
        
        # Calculate timing
        delay_between_votes = duration_seconds / total_votes
        print(f"⏱️  Delay between votes: {delay_between_votes:.3f} seconds")
        
        # Main voting loop
        self.start_time = time.time()
        end_time = self.start_time + duration_seconds
        
        print(f"\n🚀 STARTING at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Expected completion: {(datetime.now() + timedelta(seconds=duration_seconds)).strftime('%H:%M:%S')}")
        print(f"Press Ctrl+C to stop\n")
        
        try:
            for vote_num in range(1, total_votes + 1):
                current_time = time.time()
                
                # Check time limit
                if current_time >= end_time:
                    print(f"\n⏰ Time limit reached. Stopping at vote {vote_num-1}/{total_votes}")
                    break
                
                # Get next URL (random rotation)
                url = self.get_next_url()
                if url is None:
                    print("❌ No available URLs remaining!")
                    break
                
                # Cast vote
                success, result = self.cast_vote(url)
                
                if success:
                    self.total_success += 1
                    status = "✅"
                else:
                    self.total_fail += 1
                    status = "❌"
                    # Check if URL should be marked failed
                    if self.url_stats[url]['fail'] > 5 and self.url_stats[url]['success'] == 0:
                        self.mark_url_failed(url)
                
                # Progress report every 100 votes or on failure
                if vote_num % 100 == 0 or (not success and vote_num % 10 == 0):
                    self._print_progress(vote_num, total_votes, url, status, current_time)
                
                # Calculate precise sleep time
                next_vote_time = self.start_time + (vote_num * delay_between_votes)
                sleep_time = next_vote_time - time.time()
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                elif sleep_time < -5:
                    # We're significantly behind
                    if vote_num % 100 == 0:
                        print(f"   ⚠️  Behind schedule by {abs(sleep_time):.1f}s")
        
        except KeyboardInterrupt:
            print(f"\n\n🛑 STOPPED by user at vote {self.total_success + self.total_fail}/{total_votes}")
        
        # Final report
        self._print_final_report()
        return self.total_fail == 0
    
    def _print_progress(self, current, total, url, status, current_time):
        """Print formatted progress update."""
        elapsed = current_time - self.start_time
        progress_pct = (current / total) * 100
        actual_rate = (current / elapsed * 3600) if elapsed > 0 else 0
        
        remaining = total - current
        avg_delay = elapsed / current if current > 0 else 0
        eta_seconds = remaining * avg_delay
        eta = (datetime.now() + timedelta(seconds=eta_seconds)).strftime('%H:%M:%S')
        
        # Shorten URL for display
        display_url = url.replace('http://', '').replace('https://', '')[:25]
        
        print(f"[{current:5d}/{total}] {status} {self.candidate_name:12s} via {display_url:25s} | "
              f"Progress: {progress_pct:5.1f}% | Rate: {actual_rate:6.1f}/hr | ETA: {eta}")
    
    def _print_final_report(self):
        """Print comprehensive final statistics."""
        total_time = time.time() - self.start_time
        
        print(f"\n{'='*60}")
        print(f"📊 CAMPAIGN REPORT")
        print(f"{'='*60}")
        print(f"Candidate: {self.candidate_name}")
        print(f"Duration: {total_time:.1f}s ({total_time/60:.1f}min)")
        print(f"Successful: {self.total_success:,}")
        print(f"Failed: {self.total_fail:,}")
        print(f"Success Rate: {self.total_success/(self.total_success+self.total_fail)*100:.2f}%" 
              if (self.total_success+self.total_fail) > 0 else "N/A")
        print(f"Actual Rate: {self.total_success/total_time*3600:.1f} votes/hour" if total_time > 0 else "N/A")
        
        print(f"\n📡 URL PERFORMANCE:")
        for url, stats in sorted(self.url_stats.items(), key=lambda x: x[1]['success'], reverse=True):
            total = stats['success'] + stats['fail']
            if total > 0:
                success_rate = stats['success'] / total * 100
                status = "🟢" if url not in self.failed_urls else "🔴"
                print(f"  {status} {url[:40]:40s} | Success: {stats['success']:4d} | "
                      f"Fail: {stats['fail']:3d} | Rate: {success_rate:5.1f}%")
        
        print(f"{'='*60}")


def load_urls_from_file(filepath):
    """Load URLs from text file (one per line)."""
    try:
        with open(filepath, 'r') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        print(f"📁 Loaded {len(urls)} URL(s) from {filepath}")
        return urls
    except FileNotFoundError:
        print(f"❌ File not found: {filepath}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Targeted Multi-URL Voting Bot - Casts votes for specific candidate through rotating URLs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:

  # Vote for "Alice" via single URL
  python vote_bot.py --candidate "Alice" --url http://localhost:5500

  # Vote for "Bob" through multiple URLs (random rotation)
  python vote_bot.py --candidate "Bob" --url http://server1.com --url http://server2.com --url http://server3.com

  # Load URLs from file (one per line)
  python vote_bot.py --candidate "Charlie" --urls urls.txt

  # Full campaign: 5000 votes over 1 hour, random URL rotation
  python vote_bot.py --candidate "Diana" --urls production_urls.txt --votes 5000 --duration 3600

  # Quick test: 100 votes in 30 seconds via multiple URLs
  python vote_bot.py --candidate "Test" --url http://localhost:5500 --url http://127.0.0.1:5500 --votes 100 --duration 30

URL FILE FORMAT (urls.txt):
  http://server1.example.com
  http://server2.example.com
  https://server3.example.com:8080
  # Lines starting with # are ignored
        """
    )
    
    # Required arguments
    parser.add_argument('--candidate', '-c', required=True,
                       help='Name of candidate to vote for (exact match, case-sensitive)')
    
    # URL options (mutually exclusive groups handled manually)
    parser.add_argument('--url', '-u', action='append', dest='urls',
                       help='Base URL (can specify multiple times)')
    parser.add_argument('--urls', '-f', dest='url_file',
                       help='File containing URLs (one per line)')
    
    # Campaign settings
    parser.add_argument('--votes', '-n', type=int, default=5000,
                       help='Total votes to cast (default: 5000)')
    parser.add_argument('--duration', '-d', type=int, default=3600,
                       help='Duration in seconds (default: 3600 = 1 hour)')
    parser.add_argument('--no-shuffle', action='store_true',
                       help='Use URLs in order instead of random rotation')
    
    args = parser.parse_args()
    
    # Collect URLs
    all_urls = []
    
    if args.urls:
        all_urls.extend(args.urls)
    
    if args.url_file:
        file_urls = load_urls_from_file(args.url_file)
        all_urls.extend(file_urls)
    
    if not all_urls:
        parser.error("No URLs provided. Use --url or --urls")
    
    # Remove duplicates while preserving order
    seen = set()
    unique_urls = []
    for url in all_urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)
    
    # Create and run bot
    bot = MultiURLVoteBot(
        candidate_name=args.candidate,
        urls=unique_urls,
        shuffle_urls=not args.no_shuffle
    )
    
    success = bot.run(
        total_votes=args.votes,
        duration_seconds=args.duration
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()