#!/usr/bin/env python3
"""
Command-line interface for scheduling LinkedIn posts at custom times
"""

import argparse
import sys
import os
from datetime import datetime, timedelta
from custom_scheduler import CustomPostScheduler

def main():
    parser = argparse.ArgumentParser(description='Schedule LinkedIn Posts at Custom Times')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Add post command
    add_parser = subparsers.add_parser('add', help='Add a new scheduled post')
    add_parser.add_argument('--topic', required=True, help='Topic for content generation')
    add_parser.add_argument('--time', required=True, help='Schedule time (HH:MM, YYYY-MM-DD, or YYYY-MM-DD HH:MM)')
    add_parser.add_argument('--content', help='Pre-written content (optional)')
    
    # List posts command
    list_parser = subparsers.add_parser('list', help='List scheduled posts')
    
    # Start scheduler command
    start_parser = subparsers.add_parser('start', help='Start the scheduler')
    
    # Cancel post command
    cancel_parser = subparsers.add_parser('cancel', help='Cancel a scheduled post')
    cancel_parser.add_argument('--id', required=True, help='Job ID to cancel')
    
    # Clear completed posts
    clear_parser = subparsers.add_parser('clear', help='Clear completed/cancelled posts')
    
    # Add status command
    status_parser = subparsers.add_parser('status', help='Check scheduler status')
    
    # Quick schedule commands
    quick_parser = subparsers.add_parser('quick', help='Quick schedule options')
    quick_parser.add_argument('--topic', required=True, help='Topic for content')
    quick_parser.add_argument('--when', choices=['now', 'in-1h', 'in-2h', 'tomorrow', 'next-week'], 
                             required=True, help='When to post')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    scheduler = CustomPostScheduler()
    
    if args.command == 'add':
        print(f"[SCHEDULE] Scheduling post...")
        print(f"   Topic: {args.topic}")
        print(f"   Time: {args.time}")
        if args.content:
            print(f"   Content: {args.content[:50]}...")
        
        success = scheduler.add_post(args.topic, args.time, args.content)
        
        if success:
            print("\n[INFO] Next steps:")
            print("1. Run 'python schedule_post.py list' to see all scheduled posts")
            print("2. Run 'python schedule_post.py start' to start the scheduler")
    
    elif args.command == 'list':
        scheduler.list_scheduled_posts()
        print("\n[INFO] Commands:")
        print("- Add post: python schedule_post.py add --topic 'AI trends' --time '14:30'")
        print("- Start scheduler: python schedule_post.py start")
        print("- Cancel post: python schedule_post.py cancel --id JOB_ID")
        print("- Clear old posts: python schedule_post.py clear")
    
    elif args.command == 'start':
        print("[INFO] Checking for scheduled posts...")
        scheduler.list_scheduled_posts()
        print("\nStarting scheduler...")
        scheduler.start_scheduler()
    
    elif args.command == 'cancel':
        scheduler.cancel_post(args.id)
    
    elif args.command == 'status':
        check_scheduler_status()
    
    elif args.command == 'clear':
        clear_completed_posts()
    
    elif args.command == 'quick':
        quick_time = get_quick_time(args.when)
        if quick_time:
            print(f"[SCHEDULE] Quick scheduling for '{args.when}'...")
            success = scheduler.add_post(args.topic, quick_time)
            
            if success:
                print("\n[SUCCESS] Quick schedule complete!")
                print("Run 'python schedule_post.py start' to activate scheduler")

def clear_completed_posts():
    """Clear completed, failed, and cancelled posts"""
    posts_file = 'scheduled_posts.json'
    
    if not os.path.exists(posts_file):
        print("No posts file found.")
        return
    
    try:
        import json
        with open(posts_file, 'r', encoding='utf-8') as f:
            all_posts = json.load(f)
        
        # Keep only scheduled posts
        scheduled_posts = [p for p in all_posts if p['status'] == 'scheduled']
        
        with open(posts_file, 'w', encoding='utf-8') as f:
            json.dump(scheduled_posts, f, indent=2, ensure_ascii=False)
        
        cleared_count = len(all_posts) - len(scheduled_posts)
        print(f"[SUCCESS] Cleared {cleared_count} completed posts")
        print(f"[INFO] {len(scheduled_posts)} scheduled posts remaining")
        
    except Exception as e:
        print(f"[ERROR] Error clearing posts: {e}")

def check_scheduler_status():
    """Check if scheduler is running and show status"""
    import psutil
    import os
    
    print("[INFO] Checking scheduler status...")
    
    # Check if scheduled_posts.json exists and has content
    posts_file = 'scheduled_posts.json'
    if os.path.exists(posts_file):
        try:
            import json
            with open(posts_file, 'r') as f:
                posts = json.load(f)
            
            scheduled_count = len([p for p in posts if p['status'] == 'scheduled'])
            total_count = len(posts)
            
            print(f"[INFO] Posts in queue: {scheduled_count} scheduled, {total_count} total")
            
            if scheduled_count > 0:
                print("[SUCCESS] Posts are ready for scheduler")
            else:
                print("[WARNING] No scheduled posts found")
                
        except Exception as e:
            print(f"[ERROR] Error reading posts file: {e}")
    else:
        print("[INFO] No posts file found")
    
    # Check for running Python processes
    current_pid = os.getpid()
    scheduler_processes = []
    
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if (proc.info['name'] and 'python' in proc.info['name'].lower() and
                proc.info['cmdline'] and len(proc.info['cmdline']) > 1):
                
                cmdline = ' '.join(proc.info['cmdline'])
                if 'schedule_post.py start' in cmdline and proc.info['pid'] != current_pid:
                    scheduler_processes.append(proc.info)
    
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
    
    if scheduler_processes:
        print(f"[SUCCESS] Scheduler is running (PIDs: {[p['pid'] for p in scheduler_processes]})")
    else:
        print("[INFO] Scheduler is not running")
        print("[INFO] Start with: python schedule_post.py start")

def get_quick_time(when_option):
    """Convert quick time options to actual times"""
    now = datetime.now()
    
    quick_times = {
        'now': (now + timedelta(minutes=1)).strftime('%H:%M'),
        'in-1h': (now + timedelta(hours=1)).strftime('%H:%M'),
        'in-2h': (now + timedelta(hours=2)).strftime('%H:%M'),
        'tomorrow': (now + timedelta(days=1)).strftime('%Y-%m-%d 09:00'),
        'next-week': (now + timedelta(days=7)).strftime('%Y-%m-%d 09:00')
    }
    
    return quick_times.get(when_option)

def show_examples():
    """Show usage examples"""
    print("[INFO] LinkedIn Post Scheduler - Usage Examples")
    print("=" * 50)
    print()
    print("1. Schedule for specific time today:")
    print("   python schedule_post.py add --topic 'AI trends' --time '14:30'")
    print()
    print("2. Schedule for specific date and time:")
    print("   python schedule_post.py add --topic 'Career tips' --time '2024-01-15 09:00'")
    print()
    print("3. Schedule with pre-written content:")
    print("   python schedule_post.py add --topic 'Tech' --time '16:00' --content 'My custom post content'")
    print()
    print("4. Quick schedule options:")
    print("   python schedule_post.py quick --topic 'AI news' --when in-2h")
    print("   python schedule_post.py quick --topic 'Monday motivation' --when tomorrow")
    print()
    print("5. List all scheduled posts:")
    print("   python schedule_post.py list")
    print()
    print("6. Start the scheduler:")
    print("   python schedule_post.py start")
    print()

if __name__ == "__main__":
    if len(sys.argv) == 1:
        show_examples()
    else:
        main()
