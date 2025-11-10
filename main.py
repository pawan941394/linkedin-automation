#!/usr/bin/env python3
"""
LinkedIn Automation Tool
Automatically generates and posts content to LinkedIn based on schedule
"""

import argparse
import sys
import os
from content_generator import ContentGenerator
from linkedin_poster import LinkedInPoster

def main():
    parser = argparse.ArgumentParser(description='LinkedIn Automation Tool')
    parser.add_argument('--mode', choices=['test', 'post-now', 'schedule'], 
                       default='test', help='Operation mode')
    parser.add_argument('--topic', type=str, help='Topic for content generation')
    parser.add_argument('--time', type=str, help='Schedule time (HH:MM or YYYY-MM-DD HH:MM)')
    parser.add_argument('--content', type=str, help='Pre-written content')
    parser.add_argument('--with-image', action='store_true', help='Generate post with AI image')
    parser.add_argument('--no-image', action='store_true', help='Generate post without image')
    
    args = parser.parse_args()
    
    # Check if required files exist
    required_files = ['.env', 'config.json']
    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ Required file '{file}' not found!")
            print("Please create the required configuration files.")
            sys.exit(1)
    
    # Determine image setting
    with_image = None
    if args.with_image:
        with_image = True
    elif args.no_image:
        with_image = False
    
    if args.mode == 'schedule':
        # Use custom scheduler for all scheduling
        if not args.topic or not args.time:
            print("❌ Schedule mode requires --topic and --time arguments")
            print("Example: python main.py --mode schedule --topic 'AI trends' --time '14:30' --with-image")
            print("\nAlternative: Use schedule_post.py for more options")
            return
        
        from custom_scheduler import CustomPostScheduler
        custom_scheduler = CustomPostScheduler()
        
        success = custom_scheduler.add_post(args.topic, args.time, args.content, with_image)
        
        if success:
            print("\n🎯 Post scheduled! Next steps:")
            print("1. Start scheduler: python schedule_post.py start")
            print("2. List posts: python schedule_post.py list")
            print("3. Monitor: python monitor_scheduler.py")
        
        return
    
    elif args.mode == 'test':
        # Test connections and generate sample content
        print("🧪 Running tests...")
        
        # Test LinkedIn connection
        poster = LinkedInPoster()
        if poster.test_connection():
            print("✅ LinkedIn API connection working")
        else:
            print("❌ LinkedIn API connection failed")
            return
        
        # Test content generation
        generator = ContentGenerator()
        print(f"📝 Generating sample content{' with image' if with_image else ''}...")
        content = generator.generate_post(args.topic, with_image)
        
        print("📝 Sample generated content:")
        print("-" * 50)
        print(content['content'])
        if content['hashtags']:
            print(f"\n🏷️ Hashtags: {' '.join(content['hashtags'])}")
        if content.get('image_path'):
            print(f"\n🖼️ Image generated: {content['image_path']}")
            print(f"   Description: {content.get('image_description', 'N/A')}")
        print("-" * 50)
        
    elif args.mode == 'post-now':
        # Post immediately
        print(f"🚀 Testing immediate post{' with image' if with_image else ''}...")
        
        generator = ContentGenerator()
        poster = LinkedInPoster()
        
        print("📝 Generating content...")
        content_data = generator.generate_post(args.topic or "test post", with_image)
        
        if content_data:
            print("✅ Content generated successfully")
            if content_data.get('image_path'):
                print(f"🖼️ Image generated: {content_data['image_path']}")
            
            print("📤 Posting to LinkedIn...")
            success = poster.post_content(content_data)
            
            if success:
                print("🎉 Post published successfully!")
                if content_data.get('image_path'):
                    print("🖼️ Post includes generated image")
            else:
                print("❌ Failed to publish post")
        else:
            print("❌ Failed to generate content")

if __name__ == "__main__":
    main()
