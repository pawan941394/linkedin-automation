import openai
import json
import random
from typing import List, Dict, Optional
import os
import requests
from dotenv import load_dotenv

load_dotenv()

class ContentGenerator:
    def __init__(self):
        openai.api_key = os.getenv('OPENAI_API_KEY')
        with open('config.json', 'r') as f:
            self.config = json.load(f)
    
    def generate_post(self, topic: str = None, with_image: bool = None) -> Dict[str, str]:
        """Generate a LinkedIn post based on topic with optional image"""
        if not topic:
            topic = random.choice(self.config['content_topics'])
        
        if with_image is None:
            with_image = self.config.get('include_images', False)
        
        prompt = self._create_prompt(topic)
        
        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional LinkedIn content creator."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            content = response.choices[0].message.content.strip()
            hashtags = self._generate_hashtags(topic, content) if self.config['include_hashtags'] else []
            
            result = {
                "content": content,
                "hashtags": hashtags,
                "topic": topic
            }
            
            # Generate image if requested
            if with_image:
                image_data = self._generate_image(topic, content)
                if image_data:
                    result["image_url"] = image_data["url"]
                    result["image_path"] = image_data["local_path"]
                    result["image_description"] = image_data["description"]
            
            return result
            
        except Exception as e:
            print(f"Error generating content: {e}")
            return self._fallback_content(topic)
    
    def _generate_image(self, topic: str, content: str) -> Optional[Dict[str, str]]:
        """Generate an image using DALL-E based on the post topic and content"""
        try:
            # Create image prompt based on topic and content
            image_prompt = self._create_image_prompt(topic, content)
            
            print(f"🎨 Generating image with prompt: {image_prompt[:100]}...")
            
            response = openai.images.generate(
                model="dall-e-3",
                prompt=image_prompt,
                size=self.config.get('image_size', "1024x1024"),
                quality=self.config.get('image_quality', "standard"),
                n=1
            )
            
            image_url = response.data[0].url
            
            # Download and save the image locally
            local_path = self._download_image(image_url, topic)
            
            return {
                "url": image_url,
                "local_path": local_path,
                "description": f"Generated image for: {topic}"
            }
            
        except Exception as e:
            print(f"❌ Error generating image: {e}")
            return None
    
    def _create_image_prompt(self, topic: str, content: str) -> str:
        """Create a DALL-E prompt based on the post topic and content"""
        # Extract key themes from content (first 200 chars for context)
        content_preview = content[:200]
        
        base_prompts = {
            "AI and Machine Learning": "Professional tech illustration showing AI, neural networks, data visualization, modern office setting",
            "Software Development": "Clean tech workspace with coding, programming elements, modern developer setup",
            "Career Growth": "Professional development concept, upward growth arrows, business success visualization",
            "Industry Insights": "Business analytics, charts, professional meeting, corporate environment",
            "Tech News": "Technology news, digital innovation, futuristic tech concepts"
        }
        
        # Get base prompt or create generic one
        base_prompt = None
        for key in base_prompts:
            if key.lower() in topic.lower():
                base_prompt = base_prompts[key]
                break
        
        if not base_prompt:
            base_prompt = f"Professional illustration representing {topic}, modern business context"
        
        # Enhanced prompt for LinkedIn professional content
        enhanced_prompt = f"""
        {base_prompt}, professional LinkedIn post style, clean modern design, 
        corporate colors (blue, white, gray), no text overlay, high quality, 
        professional photography style, suitable for business social media
        """
        
        return enhanced_prompt.strip()
    
    def _download_image(self, image_url: str, topic: str) -> str:
        """Download image from URL and save locally"""
        try:
            # Create images directory if it doesn't exist
            images_dir = "generated_images"
            os.makedirs(images_dir, exist_ok=True)
            
            # Generate filename
            import time
            timestamp = int(time.time())
            safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_topic = safe_topic.replace(' ', '_')[:30]
            filename = f"{safe_topic}_{timestamp}.png"
            filepath = os.path.join(images_dir, filename)
            
            # Download image
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            print(f"✅ Image saved: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ Error downloading image: {e}")
            return None

    def _create_prompt(self, topic: str) -> str:
        """Create prompt for content generation"""
        length_map = {
            "short": "100-150 words",
            "medium": "200-300 words",
            "long": "300-500 words"
        }
        
        length = length_map.get(self.config['post_length'], "200-300 words")
        
        return f"""
        Create a professional and engaging LinkedIn post about {topic}.
        The post should be {length} long.
        Make it informative, professional, and engaging.
        Include a call-to-action or question to encourage engagement.
        Do not include hashtags in the main content.
        """
    
    def _generate_hashtags(self, topic: str, content: str = "") -> List[str]:
        """Generate relevant hashtags using AI"""
        try:
            hashtag_prompt = f"""
            Generate {self.config['max_hashtags']} relevant and popular LinkedIn hashtags for a post about "{topic}".
            {f"Post content: {content[:200]}..." if content else ""}
            
            Requirements:
            - Return only hashtags, one per line
            - Include the # symbol
            - Make them relevant to LinkedIn professional audience
            - Mix of broad and specific hashtags
            - No explanations, just the hashtags
            """
            
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a LinkedIn hashtag expert. Generate relevant professional hashtags."},
                    {"role": "user", "content": hashtag_prompt}
                ],
                max_tokens=100,
                temperature=0.5
            )
            
            hashtags_text = response.choices[0].message.content.strip()
            hashtags = [tag.strip() for tag in hashtags_text.split('\n') if tag.strip().startswith('#')]
            
            # Ensure we have the right number of hashtags
            hashtags = hashtags[:self.config['max_hashtags']]
            
            # Fallback to static if not enough hashtags generated
            if len(hashtags) < 3:
                return self._get_static_hashtags(topic)
            
            return hashtags
            
        except Exception as e:
            print(f"Error generating hashtags with AI: {e}")
            return self._get_static_hashtags(topic)
    
    def _get_static_hashtags(self, topic: str) -> List[str]:
        """Fallback static hashtags when AI generation fails"""
        hashtag_map = {
            "AI and Machine Learning": ["#AI", "#MachineLearning", "#TechTrends", "#Innovation", "#DataScience"],
            "Software Development": ["#SoftwareDevelopment", "#Programming", "#Coding", "#TechCommunity", "#DevLife"],
            "Career Growth": ["#CareerGrowth", "#ProfessionalDevelopment", "#Leadership", "#Success", "#Networking"],
            "Industry Insights": ["#Industry", "#Business", "#Trends", "#Innovation", "#Strategy"],
            "Tech News": ["#TechNews", "#Technology", "#Innovation", "#DigitalTransformation", "#Future"]
        }
        
        hashtags = hashtag_map.get(topic, ["#Professional", "#Growth", "#Innovation", "#Success", "#LinkedIn"])
        return hashtags[:self.config['max_hashtags']]
    
    def _fallback_content(self, topic: str) -> Dict[str, str]:
        """Fallback content when API fails"""
        fallback_posts = {
            "technology trends": "Exploring the latest technology trends that are shaping our industry. What innovations are you most excited about?",
            "professional development": "Continuous learning is key to professional growth. What skills are you developing this year?",
            "default": "Reflecting on the importance of staying current in our ever-evolving professional landscape. What's your take?"
        }
        
        content = fallback_posts.get(topic, fallback_posts['default'])
        hashtags = self._get_static_hashtags(topic) if self.config['include_hashtags'] else []
        
        return {
            "content": content,
            "hashtags": hashtags,
            "topic": topic
        }
