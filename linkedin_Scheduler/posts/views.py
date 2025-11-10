import os
import sys
import subprocess
import json
from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse

# Add the parent directory to sys.path to import our custom scheduler
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


sys.path.append(BASE_DIR)

try:
    from custom_scheduler import CustomPostScheduler
except ImportError:
    CustomPostScheduler = None

def home(request):
    """Display the home page with scheduling form and stats"""
    
    # Get post statistics
    stats = get_post_statistics()
    
    context = {
        'scheduled_count': stats['scheduled'],
        'completed_count': stats['completed'],
        'failed_count': stats['failed'],
    }
    
    return render(request, 'home.html', context)

def schedule_post(request):
    """Handle post scheduling form submission"""
    
    if request.method == 'POST':
        topic = request.POST.get('topic', '').strip()
        content = request.POST.get('content', '').strip()
        schedule_date = request.POST.get('schedule_date')
        schedule_time = request.POST.get('schedule_time')
        
        # Validate required fields
        if not topic or not schedule_date or not schedule_time:
            messages.error(request, 'Please fill in all required fields!')
            return redirect('home')
        
        # Combine date and time
        schedule_datetime = f"{schedule_date} {schedule_time}"
        
        # Validate future time
        try:
            scheduled_dt = datetime.strptime(schedule_datetime, '%Y-%m-%d %H:%M')
            if scheduled_dt <= datetime.now():
                messages.error(request, 'Please schedule the post for a future time!')
                return redirect('home')
        except ValueError:
            messages.error(request, 'Invalid date/time format!')
            return redirect('home')
        
        # Try Method 1: Use CustomPostScheduler directly
        success = False
        
        if CustomPostScheduler:
            try:
                scheduler = CustomPostScheduler()
                success = scheduler.add_post(
                    topic=topic,
                    schedule_time=schedule_datetime,
                    content=content if content else None
                )
                
                if success:
                    messages.success(request, f'✅ Post scheduled successfully for {scheduled_dt.strftime("%Y-%m-%d at %H:%M")}!')
                else:
                    messages.error(request, '❌ Failed to schedule post. Please try again.')
                    
            except Exception as e:
                print(f"Error with CustomPostScheduler: {e}")
                success = False
        
        # Method 2: Fallback to subprocess call
        if not success:
            try:
                # Build command
                cmd = [
                    sys.executable,
                    os.path.join(BASE_DIR, 'schedule_post.py'),
                    'add',
                    '--topic', topic,
                    '--time', schedule_datetime
                ]
                
                if content:
                    cmd.extend(['--content', content])
                
                # Execute command
                result = subprocess.run(
                    cmd,
                    cwd=BASE_DIR,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    messages.success(request, f'✅ Post scheduled successfully for {scheduled_dt.strftime("%Y-%m-%d at %H:%M")}!')
                    success = True
                else:
                    messages.error(request, f'❌ Error scheduling post: {result.stderr}')
                    
            except subprocess.TimeoutExpired:
                messages.error(request, '❌ Scheduling timeout. Please try again.')
            except Exception as e:
                messages.error(request, f'❌ Unexpected error: {str(e)}')
        
        # Method 3: Direct JSON file manipulation as last resort
        if not success:
            try:
                success = add_post_to_json(topic, schedule_datetime, content)
                if success:
                    messages.success(request, f'✅ Post added to schedule for {scheduled_dt.strftime("%Y-%m-%d at %H:%M")}!')
                else:
                    messages.error(request, '❌ Failed to save post to schedule.')
            except Exception as e:
                messages.error(request, f'❌ Final attempt failed: {str(e)}')
    
    return redirect('home')

def add_post_to_json(topic, schedule_time, content=None):
    """Directly add post to scheduled_posts.json file"""
    try:
        posts_file = os.path.join(BASE_DIR, 'scheduled_posts.json')
        
        # Load existing posts
        if os.path.exists(posts_file):
            with open(posts_file, 'r', encoding='utf-8') as f:
                posts = json.load(f)
        else:
            posts = []
        
        # Create new post
        import time as time_module
        post_id = f"web_post_{len(posts)}_{int(time_module.time())}"
        
        # Parse schedule time to ISO format
        dt = datetime.strptime(schedule_time, '%Y-%m-%d %H:%M')
        
        new_post = {
            'id': post_id,
            'topic': topic,
            'schedule_time': dt.isoformat(),
            'content': content,
            'status': 'scheduled'
        }
        
        posts.append(new_post)
        
        # Save back to file
        with open(posts_file, 'w', encoding='utf-8') as f:
            json.dump(posts, f, indent=2, ensure_ascii=False)
        
        return True
        
    except Exception as e:
        print(f"Error adding post to JSON: {e}")
        return False

def api_get_scheduled_posts(request):
    """API endpoint to get scheduled posts for dashboard"""
    try:
        posts_file = os.path.join(BASE_DIR, 'scheduled_posts.json')
        
        if not os.path.exists(posts_file):
            return JsonResponse({'posts': []})
        
        with open(posts_file, 'r', encoding='utf-8') as f:
            posts = json.load(f)
        
        # Filter and format posts
        current_time = datetime.now()
        scheduled_posts = []
        
        for post in posts:
            if post.get('status') == 'scheduled':
                try:
                    post_time = datetime.fromisoformat(post['schedule_time'])
                    if post_time > current_time:
                        scheduled_posts.append({
                            'id': post['id'],
                            'topic': post['topic'],
                            'schedule_time': post_time.strftime('%Y-%m-%d %H:%M'),
                            'time_remaining': str(post_time - current_time).split('.')[0]
                        })
                except:
                    pass
        
        return JsonResponse({'posts': scheduled_posts})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def api_delete_post(request):
    """API endpoint to delete a scheduled post"""
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            post_id = data.get('post_id')
            
            if not post_id:
                return JsonResponse({'success': False, 'error': 'Post ID required'})
            
            posts_file = os.path.join(BASE_DIR, 'scheduled_posts.json')
            
            if not os.path.exists(posts_file):
                return JsonResponse({'success': False, 'error': 'No posts file found'})
            
            # Load posts
            with open(posts_file, 'r', encoding='utf-8') as f:
                posts = json.load(f)
            
            # Find and remove the post
            original_count = len(posts)
            posts = [post for post in posts if post['id'] != post_id]
            
            if len(posts) == original_count:
                return JsonResponse({'success': False, 'error': 'Post not found'})
            
            # Save updated posts
            with open(posts_file, 'w', encoding='utf-8') as f:
                json.dump(posts, f, indent=2, ensure_ascii=False)
            
            # Try to remove from scheduler if it's running
            try:
                if CustomPostScheduler:
                    scheduler = CustomPostScheduler()
                    scheduler.cancel_post(post_id)
            except Exception as e:
                print(f"Warning: Could not remove from scheduler: {e}")
            
            return JsonResponse({'success': True, 'message': 'Post deleted successfully'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def api_update_post(request):
    """API endpoint to update a scheduled post time"""
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            post_id = data.get('post_id')
            new_time = data.get('new_time')
            
            if not post_id or not new_time:
                return JsonResponse({'success': False, 'error': 'Post ID and new time required'})
            
            # Validate time format
            try:
                new_datetime = datetime.strptime(new_time, '%Y-%m-%d %H:%M')
                if new_datetime <= datetime.now():
                    return JsonResponse({'success': False, 'error': 'Time must be in the future'})
            except ValueError:
                return JsonResponse({'success': False, 'error': 'Invalid time format'})
            
            posts_file = os.path.join(BASE_DIR, 'scheduled_posts.json')
            
            if not os.path.exists(posts_file):
                return JsonResponse({'success': False, 'error': 'No posts file found'})
            
            # Load posts
            with open(posts_file, 'r', encoding='utf-8') as f:
                posts = json.load(f)
            
            # Find and update the post
            post_found = False
            for post in posts:
                if post['id'] == post_id:
                    post['schedule_time'] = new_datetime.isoformat()
                    post_found = True
                    break
            
            if not post_found:
                return JsonResponse({'success': False, 'error': 'Post not found'})
            
            # Save updated posts
            with open(posts_file, 'w', encoding='utf-8') as f:
                json.dump(posts, f, indent=2, ensure_ascii=False)
            
            return JsonResponse({'success': True, 'message': 'Post time updated successfully'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def api_reschedule_post(request):
    """API endpoint to reschedule a failed/expired post"""
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            post_id = data.get('post_id')
            new_time = data.get('new_time')
            
            if not post_id or not new_time:
                return JsonResponse({'success': False, 'error': 'Post ID and new time required'})
            
            # Validate time format
            try:
                new_datetime = datetime.strptime(new_time, '%Y-%m-%d %H:%M')
                if new_datetime <= datetime.now():
                    return JsonResponse({'success': False, 'error': 'Time must be in the future'})
            except ValueError:
                return JsonResponse({'success': False, 'error': 'Invalid time format'})
            
            posts_file = os.path.join(BASE_DIR, 'scheduled_posts.json')
            
            if not os.path.exists(posts_file):
                return JsonResponse({'success': False, 'error': 'No posts file found'})
            
            # Load posts
            with open(posts_file, 'r', encoding='utf-8') as f:
                posts = json.load(f)
            
            # Find and update the post
            post_found = False
            for post in posts:
                if post['id'] == post_id:
                    post['schedule_time'] = new_datetime.isoformat()
                    post['status'] = 'scheduled'  # Reset status to scheduled
                    # Remove completion timestamp if it exists
                    if 'completed_at' in post:
                        del post['completed_at']
                    post_found = True
                    break
            
            if not post_found:
                return JsonResponse({'success': False, 'error': 'Post not found'})
            
            # Save updated posts
            with open(posts_file, 'w', encoding='utf-8') as f:
                json.dump(posts, f, indent=2, ensure_ascii=False)
            
            return JsonResponse({'success': True, 'message': 'Post rescheduled successfully'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def get_post_statistics():
    """Get statistics from scheduled_posts.json"""
    try:
        posts_file = os.path.join(BASE_DIR, 'scheduled_posts.json')
        
        if not os.path.exists(posts_file):
            return {'scheduled': 0, 'completed': 0, 'failed': 0}
        
        with open(posts_file, 'r', encoding='utf-8') as f:
            posts = json.load(f)
        
        stats = {'scheduled': 0, 'completed': 0, 'failed': 0}
        
        for post in posts:
            status = post.get('status', 'unknown')
            if status == 'scheduled':
                # Check if still in future
                try:
                    post_time = datetime.fromisoformat(post['schedule_time'])
                    if post_time > datetime.now():
                        stats['scheduled'] += 1
                except:
                    pass
            elif status == 'completed':
                stats['completed'] += 1
            elif status in ['failed', 'error', 'expired']:
                stats['failed'] += 1
        
        return stats
        
    except Exception as e:
        print(f"Error getting statistics: {e}")
        return {'scheduled': 0, 'completed': 0, 'failed': 0}

def api_get_stats(request):
    """API endpoint to get updated statistics"""
    try:
        stats = get_post_statistics()
        return JsonResponse({
            'success': True,
            'scheduled_count': stats['scheduled'],
            'completed_count': stats['completed'],
            'failed_count': stats['failed']
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})