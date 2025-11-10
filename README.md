<div align="center">

<h1>LinkedIn Automation</h1>
<em>Automation • AI • Scheduler • Web Dashboard</em>

<p>
  <a href="https://github.com/pawan941394/linkedin-automation/actions/workflows/ci.yml">
    <img alt="CI" src="https://github.com/pawan941394/linkedin-automation/actions/workflows/ci.yml/badge.svg" />
  </a>
  <img src="https://img.shields.io/badge/Python-3.11+-blue?style=flat-square" />
  <img src="https://img.shields.io/badge/Django-5.x-092E20?style=flat-square" />
  <img src="https://img.shields.io/badge/OpenAI-API-412991?style=flat-square" />
  <img src="https://img.shields.io/badge/LinkedIn-REST_API-0077B5?style=flat-square" />
  <img src="https://img.shields.io/badge/Scheduler-APScheduler-orange?style=flat-square" />
</p>

<!-- Subtle animated typing line (no repo assets required) -->
<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=22&pause=1400&color=7C77C6&center=true&vCenter=true&width=880&lines=Automate+your+LinkedIn+growth;Generate+professional+posts+with+AI;Create+images+via+DALL-E+3;Schedule+from+CLI+or+Web+Dashboard" alt="Typing Animation" />

<p>
  <a href="https://www.linkedin.com/in/pawan941394/">
    <img alt="LinkedIn" src="https://img.shields.io/badge/LinkedIn-Connect-0077B5?logo=linkedin&logoColor=white" />
  </a>
  <a href="https://www.youtube.com/@Pawankumar-py4tk">
    <img alt="YouTube" src="https://img.shields.io/badge/YouTube-Subscribe-FF0000?logo=youtube&logoColor=white" />
  </a>
</p>

</div>


## Demo 

## 1. 
<img width="1142" height="851" alt="1" src="https://github.com/user-attachments/assets/feb82dab-6800-4b1f-8f89-2b4ab643c465" />


## 2.
<img width="1111" height="882" alt="2" src="https://github.com/user-attachments/assets/2854d808-a828-4d03-838e-4fc04a054591" />


# LinkedIn Automation Tool 🤖

An intelligent LinkedIn automation tool that generates and posts professional content automatically using AI and LinkedIn API.

## 📁 Project Structure

```
LinkeDIN aUTOMATION/
├── 📄 main.py                     # Main application entry point
├── 📄 scheduler.py                # Automated posting scheduler
├── 📄 content_generator.py        # AI content generation
├── 📄 linkedin_poster.py          # LinkedIn API integration
├── 📄 test_setup.py              # Setup validation tests
├── 📄 run_test.py                # Comprehensive testing
├── 📄 simple_content_poster.py   # Manual posting helper
├── 📄 get_linkedin_token.py      # OAuth token generator
├── 📄 get_correct_user_id.py     # User ID finder
├── 📄 fix_linkedin_permissions.py # Permission helper
├── 📄 requirements.txt           # Python dependencies
├── 📄 .env                       # Environment variables (secrets)
├── 📄 config.json               # Configuration settings
├── 📄 setup_guide.md            # Setup instructions
└── 📄 README.md                 # This file
```

## ✨ Features

- 🤖 **AI Content Generation** - Creates professional LinkedIn posts
- 🖼️ **AI Image Generation** - Creates relevant images using DALL-E 3
- ⏰ **Automated Scheduling** - Posts at specified times/days
- 🏷️ **Smart Hashtags** - Adds relevant hashtags automatically
- 🔄 **Error Handling** - Robust fallback mechanisms
- 🧪 **Testing Suite** - Comprehensive validation tools
- 📊 **Multiple Topics** - Covers various professional subjects

## 🚀 Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Setup Environment**
   - Configure your `.env` file with API credentials
   - Customize `config.json` with your posting schedule

3. **Test Setup**
   ```bash
   python test_setup.py
   ```

4. **Start Automation**
   ```bash
   python main.py --mode schedule
   ```

## 📋 Usage Commands

```bash
# Post immediately
python main.py --mode post-now --topic "AI trends"

# Post with AI-generated image
python main.py --mode post-now --topic "AI trends" --with-image

# Post without image (text only)
python main.py --mode post-now --topic "AI trends" --no-image

# Start scheduled automation
python main.py --mode schedule

# Test content generation with image
python main.py --mode test --with-image

# Generate batch content
python simple_content_poster.py --batch 5

# Run comprehensive tests
python run_test.py
```

## ⚙️ Configuration

### Environment Variables (.env)
- `LINKEDIN_CLIENT_ID` - Your LinkedIn app client ID
- `LINKEDIN_CLIENT_SECRET` - Your LinkedIn app secret
- `LINKEDIN_ACCESS_TOKEN` - OAuth access token
- `LINKEDIN_USER_ID` - Your LinkedIn user ID
- `OPENAI_API_KEY` - OpenAI API key for content generation

### Schedule Configuration (config.json)
```json
{
    "post_schedule": [
        {
            "time": "09:00",
            "days": ["monday", "wednesday", "friday"],
            "topic": "technology trends"
        }
    ],
    "content_topics": [...],
    "post_length": "medium",
    "include_hashtags": true,
    "max_hashtags": 5
}
```

### Image Generation Settings (config.json)
```json
{
    "include_images": true,
    "image_size": "1024x1024",
    "image_quality": "standard"
}
```

Available image sizes: `256x256`, `512x512`, `1024x1024`, `1792x1024`, `1024x1792`  
Available qualities: `standard`, `hd`

## 🖼️ Image Features

- **AI-Generated Images**: Uses DALL-E 3 for professional business imagery
- **Topic-Relevant**: Images match your post content and topic
- **LinkedIn Optimized**: Professional style suitable for business social media
- **Local Storage**: Images saved to `generated_images/` directory
- **Fallback Support**: Posts as text-only if image generation fails

## 🛠️ Troubleshooting

- **Token Problems**: Use `python get_linkedin_token.py`
- **User ID Issues**: Run `python get_correct_user_id.py`
- **Permission Errors**: Check `python fix_linkedin_permissions.py`

## 📈 Status

✅ **Working Features:**
- Content generation with OpenAI
- AI image generation with DALL-E 3
- LinkedIn API posting with images
- Automated scheduling
- Error handling and fallbacks
- Comprehensive testing suite

## 🔧 Technical Details

- **Python 3.7+** required
- **LinkedIn API v2** integration
- **OpenAI GPT-3.5** for content generation
- **APScheduler** for automated posting
- **Robust error handling** with multiple API fallbacks

## 🎯 Future Enhancements

- Image/media posting support
- Analytics and engagement tracking
- Content performance optimization
- Multiple LinkedIn accounts support
- Web dashboard interface

---

**Status: ✅ Production Ready**  
**Last Updated: 2025**  
**Author: Pawan Kumar**
