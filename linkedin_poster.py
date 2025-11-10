import requests
import json
import os
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

class LinkedInPoster:
    def __init__(self):
        self.access_token = os.getenv('LINKEDIN_ACCESS_TOKEN')
        self.user_id = os.getenv('LINKEDIN_USER_ID')
        self.person_urn = os.getenv('LINKEDIN_PERSON_URN', f"urn:li:person:{self.user_id}")
        self.base_url = "https://api.linkedin.com"
        
        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'X-Restli-Protocol-Version': '2.0.0',
            'LinkedIn-Version': '202405'  # Use latest API version
        }
    
    def post_content(self, content_data: Dict[str, str]) -> bool:
        """Post content to LinkedIn with optional image using Posts API"""
        try:
            # Check if image is included
            has_image = 'image_path' in content_data and content_data['image_path']
            
            if has_image:
                return self._post_with_image_new_api(content_data)
            else:
                return self._post_text_only_new_api(content_data)
                
        except Exception as e:
            print(f"❌ Error posting to LinkedIn: {e}")
            return False
    
    def _post_with_image_new_api(self, content_data: Dict[str, str]) -> bool:
        """Post content with image using new Posts API"""
        try:
            print("🖼️ Posting with image using new Posts API...")
            
            # Step 1: Upload image and get media URN
            media_urn = self._upload_image_new_api(content_data['image_path'])
            if not media_urn:
                print("❌ Failed to upload image, falling back to text-only post")
                return self._post_text_only_new_api(content_data)
            
            # Step 2: Create post with image using new Posts API
            post_text = content_data['content']
            if content_data.get('hashtags'):
                hashtags_text = '\n\n' + ' '.join(content_data['hashtags'])
                post_text += hashtags_text
            
            # Use new Posts API format
            posts_payload = {
                "author": self.person_urn,
                "commentary": post_text,
                "visibility": "PUBLIC",
                "content": {
                    "media": {
                        "id": media_urn
                    }
                }
            }
            
            # Use REST endpoint
            response = requests.post(
                f"{self.base_url}/rest/posts",
                headers=self.headers,
                data=json.dumps(posts_payload)
            )
            
            if response.status_code in [200, 201]:
                print(f"✅ Successfully posted with image: {content_data['topic']}")
                return True
            else:
                print(f"❌ Failed to post with image. Status: {response.status_code}")
                print(f"📄 Response: {response.text}")
                # Try fallback to UGC API
                return self._post_with_image_ugc_fallback(content_data, media_urn)
                
        except Exception as e:
            print(f"❌ Error posting with image: {e}")
            return self._post_text_only_new_api(content_data)
    
    def _upload_image_new_api(self, image_path: str) -> Optional[str]:
        """Upload image using Images API with correct owner format"""
        try:
            if not os.path.exists(image_path):
                print(f"❌ Image file not found: {image_path}")
                return None
            
            print(f"📤 Uploading image using Images API: {image_path}")
            
            # Step 1: Register upload with correct owner URN
            register_payload = {
                "registerUploadRequest": {
                    "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                    "owner": self.person_urn,
                    "serviceRelationships": [
                        {
                            "relationshipType": "OWNER",
                            "identifier": "urn:li:userGeneratedContent"
                        }
                    ]
                }
            }
            
            register_response = requests.post(
                f"{self.base_url}/v2/assets?action=registerUpload",
                headers=self.headers,
                data=json.dumps(register_payload)
            )
            
            if register_response.status_code != 200:
                print(f"❌ Failed to register upload: {register_response.text}")
                return None
            
            register_data = register_response.json()
            upload_url = register_data['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
            asset_urn = register_data['value']['asset']
            
            # Step 2: Upload the image binary data
            with open(image_path, 'rb') as image_file:
                upload_headers = {
                    'Authorization': f'Bearer {self.access_token}'
                }
                
                upload_response = requests.put(
                    upload_url,
                    headers=upload_headers,
                    data=image_file.read()
                )
                
                if upload_response.status_code not in [200, 201]:
                    print(f"❌ Failed to upload image binary: {upload_response.text}")
                    return None
            
            print(f"✅ Image uploaded successfully: {asset_urn}")
            return asset_urn
            
        except Exception as e:
            print(f"❌ Error uploading image: {e}")
            return None
    
    def _post_with_image_ugc_fallback(self, content_data: Dict[str, str], media_urn: str) -> bool:
        """Fallback to UGC API with uploaded image"""
        try:
            print("🔄 Trying UGC API fallback...")
            
            post_text = content_data['content']
            if content_data.get('hashtags'):
                hashtags_text = '\n\n' + ' '.join(content_data['hashtags'])
                post_text += hashtags_text
            
            ugc_payload = {
                "author": self.person_urn,
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": post_text
                        },
                        "shareMediaCategory": "IMAGE",
                        "media": [
                            {
                                "status": "READY",
                                "description": {
                                    "text": content_data.get('image_description', '')
                                },
                                "media": media_urn,
                                "title": {
                                    "text": content_data['topic']
                                }
                            }
                        ]
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            
            response = requests.post(
                f"{self.base_url}/v2/ugcPosts",
                headers=self.headers,
                data=json.dumps(ugc_payload)
            )
            
            if response.status_code == 201:
                print(f"✅ Successfully posted with UGC fallback: {content_data['topic']}")
                return True
            else:
                print(f"❌ UGC fallback also failed. Status: {response.status_code}")
                print(f"📄 Response: {response.text}")
                return self._post_text_only_new_api(content_data)
                
        except Exception as e:
            print(f"❌ Error with UGC fallback: {e}")
            return self._post_text_only_new_api(content_data)
    
    def _post_text_only_new_api(self, content_data: Dict[str, str]) -> bool:
        """Post text-only content using new Posts API"""
        try:
            print("📝 Posting text-only content using new Posts API...")
            
            # Prepare the post content
            post_text = content_data['content']
            if content_data.get('hashtags'):
                hashtags_text = '\n\n' + ' '.join(content_data['hashtags'])
                post_text += hashtags_text
            
            # Use new Posts API format
            posts_payload = {
                "author": self.person_urn,
                "commentary": post_text,
                "visibility": "PUBLIC"
            }
            
            response = requests.post(
                f"{self.base_url}/rest/posts",
                headers=self.headers,
                data=json.dumps(posts_payload)
            )
            
            if response.status_code in [200, 201]:
                print(f"✅ Successfully posted: {content_data['topic']}")
                return True
            else:
                print(f"❌ Failed to post. Status: {response.status_code}")
                print(f"📄 Response: {response.text}")
                
                # Try fallback to UGC API
                return self._post_text_only_ugc_fallback(content_data)
                
        except Exception as e:
            print(f"❌ Error posting text content: {e}")
            return False
    
    def _post_text_only_ugc_fallback(self, content_data: Dict[str, str]) -> bool:
        """Fallback to UGC API for text-only posts"""
        try:
            print("🔄 Trying UGC API fallback for text-only...")
            
            post_text = content_data['content']
            if content_data.get('hashtags'):
                hashtags_text = '\n\n' + ' '.join(content_data['hashtags'])
                post_text += hashtags_text
            
            ugc_payload = {
                "author": self.person_urn,
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": post_text
                        },
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            
            response = requests.post(
                f"{self.base_url}/v2/ugcPosts",
                headers=self.headers,
                data=json.dumps(ugc_payload)
            )
            
            if response.status_code == 201:
                print(f"✅ Successfully posted with UGC fallback: {content_data['topic']}")
                return True
            else:
                print(f"❌ UGC fallback also failed. Status: {response.status_code}")
                print(f"📄 Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error with UGC fallback: {e}")
            return False

    def test_connection(self) -> bool:
        """Test LinkedIn API connection with multiple endpoints"""
        print("🔍 Testing LinkedIn API connection...")
        
        try:
            # Test 1: OpenID Connect userinfo endpoint
            userinfo_headers = {
                'Authorization': f'Bearer {self.access_token}',
            }
            
            response = requests.get(
                'https://api.linkedin.com/v2/userinfo',
                headers=userinfo_headers,
                timeout=10
            )
            
            if response.status_code == 200:
                user_data = response.json()
                print("✅ LinkedIn API connection successful!")
                print(f"   User: {user_data.get('name', 'Unknown')}")
                print(f"   Email: {user_data.get('email', 'Unknown')}")
                
                # Test posting endpoints
                return self._test_posting_endpoints()
                
            # Test 2: Basic profile endpoint
            elif response.status_code == 403:
                print("🔄 Trying profile endpoint...")
                response = requests.get(
                    f"{self.base_url}/people/(id:{self.user_id})?projection=(id,localizedFirstName,localizedLastName)",
                    headers=self.headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    profile_data = response.json()
                    print("✅ LinkedIn API connection successful!")
                    first_name = profile_data.get('localizedFirstName', '')
                    last_name = profile_data.get('localizedLastName', '')
                    print(f"   Profile: {first_name} {last_name}")
                    return self._test_posting_endpoints()
                else:
                    print(f"❌ Profile endpoint failed: {response.status_code}")
                    print(f"📄 Response: {response.text}")
                    return False
            else:
                print(f"❌ LinkedIn API connection failed: {response.status_code}")
                print(f"📄 Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing LinkedIn connection: {e}")
            return False
    
    def _test_posting_endpoints(self) -> bool:
        """Test access to posting endpoints"""
        try:
            print("🔍 Testing posting endpoints access...")
            
            # Test new Posts API endpoint
            posts_response = requests.get(
                f"{self.base_url}/rest/posts",
                headers=self.headers,
                timeout=10
            )
            
            if posts_response.status_code == 200:
                print("✅ Posts API endpoint accessible - posting should work!")
                return True
            else:
                print(f"⚠️ Posts API endpoint response: {posts_response.status_code}")
                
            # Test UGC endpoint
            ugc_response = requests.get(
                f"{self.base_url}/v2/ugcPosts?q=authors&authors={self.person_urn}&count=1",
                headers=self.headers,
                timeout=10
            )
            
            if ugc_response.status_code == 200:
                print("✅ UGC Posts endpoint accessible - fallback available!")
                return True
            else:
                print(f"⚠️ UGC endpoint response: {ugc_response.status_code}")
                print(f"📄 Response: {ugc_response.text}")
                print("🔍 This may affect posting capabilities")
                return True  # Still return True as connection works
                
        except Exception as e:
            print(f"⚠️ Error testing posting access: {e}")
            return True  # Don't fail connection test for this
    
    def get_user_profile(self) -> dict:
        """Get user profile information"""
        try:
            # Try userinfo endpoint first
            response = requests.get(
                'https://api.linkedin.com/v2/userinfo',
                headers={'Authorization': f'Bearer {self.access_token}'}
            )
            
            if response.status_code == 200:
                return response.json()
            
            # Fallback to people endpoint
            response = requests.get(
                f"{self.base_url}/v2/people/(id:{self.user_id})?projection=(id,localizedFirstName,localizedLastName)",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json()
            
            return {}
            
        except Exception as e:
            print(f"Error getting profile: {e}")
            return {}
