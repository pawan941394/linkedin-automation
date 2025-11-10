#!/usr/bin/env python3
"""
Custom LinkedIn Post Scheduler
Allows scheduling posts at specific custom times
"""

import time
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler  # Change from BlockingScheduler
from apscheduler.triggers.date import DateTrigger
import signal
import os
import json
from content_generator import ContentGenerator
from linkedin_poster import LinkedInPoster

class CustomPostScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()  # Use BackgroundScheduler instead
        self.content_generator = ContentGenerator()
        self.linkedin_poster = LinkedInPoster()
        self.scheduled_posts = []
        self.posts_file = 'scheduled_posts.json'
        self.running = False
        
        # Load existing scheduled posts
        self._load_scheduled_posts()
    
    def _load_scheduled_posts(self):
        """Load scheduled posts from file"""
        try:
            if os.path.exists(self.posts_file):
                with open(self.posts_file, 'r', encoding='utf-8') as f:
                    saved_posts = json.load(f)
                
                # Load ALL posts (scheduled, completed, failed) for history
                current_time = datetime.now()
                active_jobs = 0
                
                for post in saved_posts:
                    if post['status'] == 'scheduled':
                        post_time = datetime.fromisoformat(post['schedule_time'])
                        
                        # Only add future scheduled posts to scheduler
                        if post_time > current_time:
                            self.scheduler.add_job(
                                func=self.execute_scheduled_post,
                                trigger=DateTrigger(run_date=post_time),
                                args=[post['topic'], post['content']],
                                id=post['id'],
                                replace_existing=True
                            )
                            active_jobs += 1
                            print(f"[INFO] Loaded scheduled post: {post['topic']} at {post['schedule_time']}")
                        else:
                            # Mark past scheduled posts as expired
                            post['status'] = 'expired'
                
                # Keep ALL posts in memory (including completed/failed for history)
                self.scheduled_posts = saved_posts
                print(f"[SUCCESS] Loaded {active_jobs} active scheduled posts")
                print(f"[INFO] Total posts in history: {len(saved_posts)}")
                
                # Save any status updates (like expired posts)
                self._save_scheduled_posts()
                
        except Exception as e:
            print(f"[WARNING] Could not load scheduled posts: {e}")
            self.scheduled_posts = []
    
    def _save_scheduled_posts(self):
        """Save scheduled posts to file"""
        try:
            with open(self.posts_file, 'w', encoding='utf-8') as f:
                json.dump(self.scheduled_posts, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[WARNING] Could not save scheduled posts: {e}")

    def add_post(self, topic, schedule_time, content=None):
        """
        Add a post to be scheduled at specific time
        
        Args:
            topic (str): Topic for content generation
            schedule_time (str): Time in format "YYYY-MM-DD HH:MM" or "HH:MM" (today)
            content (str, optional): Pre-written content, if None will generate
        """
        try:
            # Parse the schedule time
            post_datetime = self._parse_schedule_time(schedule_time)
            
            if post_datetime <= datetime.now():
                print(f"[WARNING] Schedule time {schedule_time} is in the past!")
                return False
            
            # Create unique job ID
            job_id = f"custom_post_{len(self.scheduled_posts)}_{int(time.time())}"
            
            # Add job to scheduler
            self.scheduler.add_job(
                func=self.execute_scheduled_post,
                trigger=DateTrigger(run_date=post_datetime),
                args=[topic, content],
                id=job_id,
                replace_existing=True
            )
            
            # Store post info
            post_info = {
                'id': job_id,
                'topic': topic,
                'schedule_time': post_datetime.isoformat(),  # Use isoformat for better serialization
                'content': content,
                'status': 'scheduled'
            }
            
            self.scheduled_posts.append(post_info)
            
            # Save to file
            self._save_scheduled_posts()
            
            print(f"[SUCCESS] Post scheduled successfully!")
            print(f"   Topic: {topic}")
            print(f"   Time: {post_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Job ID: {job_id}")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Error scheduling post: {e}")
            return False
    
    def _parse_schedule_time(self, schedule_time):
        """Parse schedule time string to datetime object"""
        try:
            # If only time provided (HH:MM), use today's date
            if ':' in schedule_time and len(schedule_time) <= 5:
                today = datetime.now().date()
                time_part = datetime.strptime(schedule_time, '%H:%M').time()
                return datetime.combine(today, time_part)
            
            # Full datetime (YYYY-MM-DD HH:MM)
            elif len(schedule_time) > 10:
                return datetime.strptime(schedule_time, '%Y-%m-%d %H:%M')
            
            # Date only (YYYY-MM-DD), use 09:00 as default
            else:
                date_part = datetime.strptime(schedule_time, '%Y-%m-%d').date()
                default_time = datetime.strptime('09:00', '%H:%M').time()
                return datetime.combine(date_part, default_time)
                
        except ValueError as e:
            raise ValueError(f"Invalid time format. Use 'HH:MM', 'YYYY-MM-DD', or 'YYYY-MM-DD HH:MM'")
    
    def execute_scheduled_post(self, topic, content=None):
        """Execute a scheduled post"""
        print(f"\n[EXEC] Starting scheduled post creation...")
        print(f"Topic: {topic}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # Generate content if not provided
            if not content:
                print("[INFO] Generating content...")
                content_data = self.content_generator.generate_post(topic)
                if not content_data:
                    print("[ERROR] Failed to generate content")
                    return False
            else:
                # Use provided content
                content_data = {
                    'content': content,
                    'topic': topic,
                    'hashtags': []
                }
                print("[INFO] Using provided content...")
            
            print("[SUCCESS] Content ready!")
            
            # Post to LinkedIn
            print("[INFO] Posting to LinkedIn...")
            success = self.linkedin_poster.post_content(content_data)
            
            if success:
                print("[SUCCESS] Scheduled post published successfully!")
                self._log_post_success(topic, content_data)
                
                # Update post status to completed
                self._update_post_status(topic, 'completed')
                
                return True
            else:
                print("[ERROR] Failed to publish scheduled post")
                self._log_post_failure(topic, "Posting failed")
                self._update_post_status(topic, 'failed')
                return False
                
        except Exception as e:
            print(f"[ERROR] Error executing scheduled post: {e}")
            self._log_post_failure(topic, str(e))
            self._update_post_status(topic, 'error')
            return False
    
    def _update_post_status(self, topic, status):
        """Update post status and save to file"""
        for post in self.scheduled_posts:
            if post['topic'] == topic and post['status'] == 'scheduled':
                post['status'] = status
                post['completed_at'] = datetime.now().isoformat()  # Add completion timestamp
                break
        self._save_scheduled_posts()

    def list_scheduled_posts(self):
        """List all scheduled posts"""
        print("\n[INFO] Scheduled Posts:")
        print("=" * 60)
        
        if not self.scheduled_posts:
            print("No posts found.")
            return
        
        # Separate posts by status
        scheduled_posts = [p for p in self.scheduled_posts if p['status'] == 'scheduled']
        completed_posts = [p for p in self.scheduled_posts if p['status'] == 'completed']
        failed_posts = [p for p in self.scheduled_posts if p['status'] in ['failed', 'error']]
        expired_posts = [p for p in self.scheduled_posts if p['status'] == 'expired']
        
        if scheduled_posts:
            print("UPCOMING POSTS:")
            for i, post in enumerate(scheduled_posts, 1):
                schedule_time = datetime.fromisoformat(post['schedule_time'])
                time_remaining = schedule_time - datetime.now()
                
                if time_remaining.total_seconds() > 0:
                    print(f"{i}. Topic: {post['topic']}")
                    print(f"   Time: {schedule_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"   In: {self._format_time_remaining(time_remaining)}")
                    print(f"   ID: {post['id']}")
                    print("-" * 40)
        
        if completed_posts:
            print(f"\nCOMPLETED POSTS ({len(completed_posts)}):")
            for i, post in enumerate(completed_posts, 1):
                schedule_time = datetime.fromisoformat(post['schedule_time'])
                completed_time = post.get('completed_at', 'Unknown')
                print(f"{i}. Topic: {post['topic']}")
                print(f"   Scheduled: {schedule_time.strftime('%Y-%m-%d %H:%M:%S')}")
                if completed_time != 'Unknown':
                    completed_dt = datetime.fromisoformat(completed_time)
                    print(f"   Completed: {completed_dt.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"   Status: {post['status']}")
                print("-" * 20)
        
        if failed_posts:
            print(f"\nFAILED POSTS ({len(failed_posts)}):")
            for i, post in enumerate(failed_posts, 1):
                schedule_time = datetime.fromisoformat(post['schedule_time'])
                print(f"{i}. Topic: {post['topic']}")
                print(f"   Time: {schedule_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"   Status: {post['status']}")
                print("-" * 20)
    
    def _format_time_remaining(self, time_delta):
        """Format time remaining in a readable way"""
        if time_delta.days > 0:
            return f"{time_delta.days} days, {time_delta.seconds // 3600} hours"
        elif time_delta.seconds > 3600:
            return f"{time_delta.seconds // 3600} hours, {(time_delta.seconds % 3600) // 60} minutes"
        elif time_delta.seconds > 60:
            return f"{time_delta.seconds // 60} minutes"
        else:
            return "less than 1 minute"

    def cancel_post(self, job_id):
        """Cancel a scheduled post"""
        try:
            self.scheduler.remove_job(job_id)
            
            # Update post status
            for post in self.scheduled_posts:
                if post['id'] == job_id:
                    post['status'] = 'cancelled'
                    break
            
            # Save changes
            self._save_scheduled_posts()
            
            print(f"[SUCCESS] Post {job_id} cancelled successfully")
            return True
            
        except Exception as e:
            print(f"[ERROR] Error cancelling post: {e}")
            return False

    def _reload_posts_if_changed(self):
        """Check if posts file has been modified and reload if necessary"""
        try:
            if not os.path.exists(self.posts_file):
                return
            
            # Check file modification time
            current_mtime = os.path.getmtime(self.posts_file)
            
            if not hasattr(self, '_last_mtime'):
                self._last_mtime = current_mtime
                return
            
            if current_mtime > self._last_mtime:
                print("[INFO] Detected new posts, reloading...")
                self._last_mtime = current_mtime
                
                # Load new posts
                with open(self.posts_file, 'r', encoding='utf-8') as f:
                    saved_posts = json.load(f)
                
                # Find new posts that aren't in scheduler yet
                current_job_ids = {job.id for job in self.scheduler.get_jobs()}
                current_time = datetime.now()
                
                new_posts_added = 0
                for post in saved_posts:
                    if (post['id'] not in current_job_ids and 
                        post['status'] == 'scheduled'):
                        
                        post_time = datetime.fromisoformat(post['schedule_time'])
                        
                        if post_time > current_time:
                            # Add new job to scheduler
                            self.scheduler.add_job(
                                func=self.execute_scheduled_post,
                                trigger=DateTrigger(run_date=post_time),
                                args=[post['topic'], post['content']],
                                id=post['id'],
                                replace_existing=True
                            )
                            new_posts_added += 1
                
                if new_posts_added > 0:
                    print(f"[SUCCESS] Added {new_posts_added} new posts to scheduler")
                    self.scheduled_posts = saved_posts
                    self._print_active_jobs()
                
        except Exception as e:
            print(f"[WARNING] Error reloading posts: {e}")
    
    def _print_active_jobs(self):
        """Print currently active jobs"""
        jobs = self.scheduler.get_jobs()
        if jobs:
            print(f"[INFO] Active scheduled posts: {len(jobs)}")
            for job in jobs:
                print(f"   - {job.id}: {job.next_run_time}")
        else:
            print("[INFO] No active posts in scheduler")
    
    def start_scheduler(self):
        """Start the custom scheduler with monitoring loop"""
        print("[START] Custom LinkedIn Scheduler Starting...")
        print("=" * 50)
        
        # Start the background scheduler
        if not self.scheduler.running:
            self.scheduler.start()
        
        self.running = True
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        print("[SUCCESS] Background scheduler started")
        self._print_active_jobs()
        
        print("\n[INFO] Scheduler Features:")
        print("- Auto-reloads new posts every 30 seconds")
        print("- Add posts from another terminal anytime")
        print("- Press Ctrl+C to stop gracefully")
        print("\n" + "=" * 50)
        
        try:
            # Monitoring loop
            while self.running:
                # Check for new posts every 30 seconds
                self._reload_posts_if_changed()
                
                # Show status every 5 minutes
                if not hasattr(self, '_last_status_time'):
                    self._last_status_time = datetime.now()
                
                if (datetime.now() - self._last_status_time).seconds > 300:  # 5 minutes
                    self._show_status()
                    self._last_status_time = datetime.now()
                
                time.sleep(30)  # Check every 30 seconds
                
        except KeyboardInterrupt:
            self._shutdown_gracefully()
        except Exception as e:
            print(f"[ERROR] Scheduler error: {e}")
            self._shutdown_gracefully()
    
    def _show_status(self):
        """Show current scheduler status"""
        jobs = self.scheduler.get_jobs()
        current_time = datetime.now()
        
        print(f"\n[STATUS] Status Update - {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"[INFO] Active posts: {len(jobs)}")
        
        if jobs:
            # Show next upcoming post
            next_job = min(jobs, key=lambda j: j.next_run_time)
            time_until = next_job.next_run_time - current_time
            print(f"[INFO] Next post: {self._format_time_remaining(time_until)}")
        
        print("[INFO] Monitoring for new posts...")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n[INFO] Received signal {signum}, shutting down...")
        self._shutdown_gracefully()
    
    def _shutdown_gracefully(self):
        """Shutdown the scheduler gracefully"""
        print("[INFO] Shutting down scheduler...")
        self.running = False
        
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
        
        print("[SUCCESS] Scheduler stopped gracefully")
        print("[INFO] All scheduled posts have been saved")
    
    def _log_post_success(self, topic, content_data):
        """Log successful post"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'status': 'success',
            'topic': topic,
            'content_preview': content_data['content'][:100] + '...'
        }
        self._write_log('posts', log_entry)
    
    def _log_post_failure(self, topic, error):
        """Log failed post"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'status': 'failed',
            'topic': topic,
            'error': error
        }
        self._write_log('errors', log_entry)
    
    def _write_log(self, log_type, entry):
        """Write log entry to file"""
        try:
            import os
            log_dir = f"logs/{log_type}"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            
            log_file = f"{log_dir}/{datetime.now().strftime('%Y-%m-%d')}.log"
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry) + '\n')
        except Exception as e:
            print(f"[WARNING] Could not write log: {e}")

