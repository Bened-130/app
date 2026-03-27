#!/usr/bin/env python3
"""
Automated Voting Bot
Casts 5000 votes over 1 hour to test the voting system.

Usage:
    python vote_bot.py --url http://localhost:5500 --target "Candidate Name" --votes 5000 --duration 3600
    python vote_bot.py --url http://localhost:5500 --random --votes 5500 --duration 3600
"""

import requests
import time
import random
import argparse
import sys
from datetime import datetime, timedelta


class VoteBot:
    def __init__(self, base_url, target_name=None, random_mode=False):
        self.base_url = base_url.rstrip('/')
        self.target_name = target_name
        self.random_mode = random_mode
        self.vote_endpoint = f"{self.base_url}/vote"
        self.names_endpoint = f"{self.base_url}/api/names"
        self.candidates = []
        
    def fetch_candidates(self):
        """Get list of available candidates."""
        try:
            response = requests.get(self.names_endpoint, timeout=10)
            response.raise_for_status()
            data = response.json()
            self.candidates = [item['name'] for item in data]
            print(f"Found candidates: {self.candidates}")
            return True
        except Exception as e:
            print(f"Failed to fetch candidates: {e}")
            return False
    
    def cast_vote(self, name):
        """Cast a single vote."""
        try:
            response = requests.post(
                self.vote_endpoint,
                json={"name": name},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Vote failed for '{name}': {e}")
            return False
    
    def get_target_name(self):
        """Determine which candidate to vote for."""
        if self.random_mode and self.candidates:
            return random.choice(self.candidates)
        return self.target_name
    
    def run(self, total_votes, duration_seconds):
        """
        Run the bot to cast votes over specified duration.
        
        Args:
            total_votes: Total number of votes to cast
            duration_seconds: Time period over which to distribute votes
        """
        print(f"\n{'='*50}")
        print(f"🤖 VOTE BOT ACTIVATED")
        print(f"{'='*50}")
        print(f"Target URL: {self.base_url}")
        print(f"Mode: {'Random' if self.random_mode else f'Fixed ({self.target_name})'}")
        print(f"Total votes: {total_votes}")
        print(f"Duration: {duration_seconds} seconds ({duration_seconds/3600:.1f} hours)")
        print(f"{'='*50}\n")
        
        # Fetch candidates first
        if not self.fetch_candidates():
            print("Cannot proceed without candidate list")
            return False
        
        # Validate target if fixed mode
        if not self.random_mode:
            if self.target_name not in self.candidates:
                print(f"ERROR: Target '{self.target_name}' not in candidates: {self.candidates}")
                return False
        
        # Calculate timing
        delay_between_votes = duration_seconds / total_votes
        print(f"Calculated delay: {delay_between_votes:.3f} seconds between votes")
        print(f"Expected rate: {3600/delay_between_votes:.1f} votes/hour\n")
        
        # Statistics
        successful = 0
        failed = 0
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        print(f"Starting at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Expected end: {(datetime.now() + timedelta(seconds=duration_seconds)).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Press Ctrl+C to stop early\n")
        
        try:
            for i in range(total_votes):
                # Check if we should stop
                current_time = time.time()
                if current_time >= end_time:
                    print(f"\nTime limit reached. Stopping early at vote {i}/{total_votes}")
                    break
                
                # Select target
                target = self.get_target_name()
                
                # Cast vote
                if self.cast_vote(target):
                    successful += 1
                    status = "✓"
                else:
                    failed += 1
                    status = "✗"
                
                # Progress report every 100 votes
                if (i + 1) % 100 == 0 or i == 0:
                    elapsed = current_time - start_time
                    progress = (i + 1) / total_votes * 100
                    actual_rate = (i + 1) / elapsed * 3600 if elapsed > 0 else 0
                    remaining = total_votes - (i + 1)
                    eta_seconds = remaining * delay_between_votes
                    eta = (datetime.now() + timedelta(seconds=eta_seconds)).strftime('%H:%M:%S')
                    
                    print(f"[{i+1:5d}/{total_votes}] {status} {target:15s} | "
                          f"Progress: {progress:5.1f}% | Rate: {actual_rate:6.1f}/hr | ETA: {eta}")
                
                # Calculate sleep time (account for request duration)
                next_vote_time = start_time + (i + 1) * delay_between_votes
                sleep_time = next_vote_time - time.time()
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                elif sleep_time < -1:
                    # We're falling behind, warn but continue
                    if (i + 1) % 100 == 0:
                        print(f"  ⚠️ Behind schedule by {abs(sleep_time):.1f}s")
        
        except KeyboardInterrupt:
            print(f"\n\n⚠️ Bot stopped by user at vote {successful + failed}/{total_votes}")
        
        # Final statistics
        total_time = time.time() - start_time
        print(f"\n{'='*50}")
        print(f"📊 FINAL STATISTICS")
        print(f"{'='*50}")
        print(f"Duration: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
        print(f"Successful votes: {successful}")
        print(f"Failed votes: {failed}")
        print(f"Success rate: {successful/(successful+failed)*100:.1f}%" if (successful+failed) > 0 else "N/A")
        print(f"Actual rate: {successful/total_time*3600:.1f} votes/hour" if total_time > 0 else "N/A")
        print(f"{'='*50}")
        
        return failed == 0


def main():
    parser = argparse.ArgumentParser(
        description='Automated Voting Bot - Casts votes over time to test real-time systems',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Vote 5000 times for "Alice" over 1 hour
  python vote_bot.py --url http://localhost:5500 --target "Alice" --votes 5000 --duration 3600
  
  # Random voting across all candidates
  python vote_bot.py --url http://localhost:5500 --random --votes 1000 --duration 600
  
  # Quick test: 100 votes in 10 seconds
  python vote_bot.py --url http://localhost:5500 --random --votes 100 --duration 10
  
  # Production test with live URL
  python vote_bot.py --url https://your-app.herokuapp.com --target "Candidate A" --votes 5000 --duration 3600
        """
    )
    
    parser.add_argument('--url', required=True, help='Base URL of the voting app')
    parser.add_argument('--target', help='Name of candidate to vote for (required unless --random)')
    parser.add_argument('--random', action='store_true', help='Vote randomly among all candidates')
    parser.add_argument('--votes', type=int, default=5500, help='Total number of votes (default: 5000)')
    parser.add_argument('--duration', type=int, default=3600, 
                       help='Duration in seconds (default: 3600 = 1 hour)')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.random and not args.target:
        parser.error("Either --target or --random must be specified")
    
    # Create and run bot
    bot = VoteBot(
        base_url=args.url,
        target_name=args.target,
        random_mode=args.random
    )
    
    success = bot.run(
        total_votes=args.votes,
        duration_seconds=args.duration
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()