#!/usr/bin/env python3
"""
Video Creator Using Your Real HelioEarth Visualizations
Creates authentic videos with your actual 3D space weather pics
Developer: Oluwafemi Idiakhoa
"""

import os
import json
import glob
from datetime import datetime
import subprocess

class RealVisualizationVideoCreator:
    def __init__(self):
        self.website_url = "helioearth.com"
        
        # Your actual visualization directories
        self.pic_directories = [
            "screenshots/",
            "3d_visualizations/", 
            "dashboard_pics/",
            "space_weather_images/",
            "aurora_pics/",
            "solar_flare_images/",
            "cme_visualizations/"
        ]
        
        # Common image extensions
        self.image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.webp']
        
    def find_your_real_pics(self):
        """Find all your real space weather visualization images"""
        
        print("Searching for your real space weather visualizations...")
        
        found_images = []
        
        # Search current directory for specific patterns from your generated content
        import glob
        
        # Look for your real app screenshots first, then generated images
        patterns = [
            # Real app screenshots (highest priority)
            'dashboard_snapshot.png',
            '3d_visualization.png',
            'live_data_display.png',
            'aurora_tracker.png',
            'iss_tracker.png',
            'app_screenshot*.png',
            '*snapshot*.png',
            # Generated space weather images
            'activity_*.png',
            'data_*.png', 
            'title_*.png',
            'website_*.png',
            # Other screenshots
            '*screenshot*.png',
            '*visualization*.png',
            '*space*.png',
            '*aurora*.png',
            # Fallback to any images
            '*.png',
            '*.jpg',
            '*.jpeg'
        ]
        
        for pattern in patterns:
            matches = glob.glob(pattern)
            for match in matches:
                if match not in found_images:
                    # Skip thumbnails and cache files
                    if not any(skip in match.lower() for skip in ['thumb', 'cache', 'temp', '.git']):
                        found_images.append(match)
        
        print(f"Found {len(found_images)} potential images: {found_images[:10]}")
        
        # Categorize images by content type, prioritizing real app screenshots
        categorized = {
            'dashboard_screenshots': [],
            '3d_visualizations': [],
            'live_data_displays': [],
            'tracking_systems': [],
            'title_cards': [],
            'data_displays': [],
            'activity_charts': [],
            'website_promo': [],
            'general': []
        }
        
        for img in found_images:
            img_lower = img.lower()
            # Prioritize real app screenshots
            if 'dashboard_snapshot' in img_lower or 'dashboard-screenshot' in img_lower:
                categorized['dashboard_screenshots'].append(img)
            elif '3d_visualization' in img_lower or '3d-advanced' in img_lower:
                categorized['3d_visualizations'].append(img)
            elif 'live_data_display' in img_lower or 'expert-dashboard' in img_lower:
                categorized['live_data_displays'].append(img)
            elif any(term in img_lower for term in ['aurora_tracker', 'iss_tracker', 'tracker']):
                categorized['tracking_systems'].append(img)
            # Generated content images
            elif 'title' in img_lower:
                categorized['title_cards'].append(img)
            elif 'data' in img_lower:
                categorized['data_displays'].append(img)
            elif 'activity' in img_lower:
                categorized['activity_charts'].append(img)
            elif 'website' in img_lower:
                categorized['website_promo'].append(img)
            elif any(term in img_lower for term in ['screenshot', 'snapshot', 'visualization', 'solar', 'aurora']):
                categorized['general'].append(img)
            else:
                categorized['general'].append(img)
        
        return categorized
    
    def create_video_with_your_pics(self, audio_file, space_data, output_file):
        """Create video using your real visualizations"""
        
        print("Creating video with your real HelioEarth visualizations...")
        
        # Find your images
        your_images = self.find_your_real_pics()
        
        # Print what we found
        total_images = sum(len(imgs) for imgs in your_images.values())
        print(f"Found {total_images} of your real images:")
        for category, images in your_images.items():
            if images:
                print(f"  - {category}: {len(images)} images")
                for img in images[:3]:  # Show first 3
                    print(f"    * {img}")
                if len(images) > 3:
                    print(f"    ... and {len(images) - 3} more")
        
        # Select best images for video
        video_images = self.select_best_images_for_video(your_images, space_data)
        
        if not video_images:
            print("No suitable images found. Creating instructions for manual video creation...")
            return self.create_manual_video_instructions(audio_file, space_data, your_images)
        
        # Create video with FFmpeg using your real pics
        return self.create_ffmpeg_video_with_your_pics(audio_file, video_images, space_data, output_file)
    
    def select_best_images_for_video(self, categorized_images, space_data):
        """Select the best of your images for the video sequence"""
        
        summary = space_data.get('summary', {})
        activity_level = summary.get('activity_level', 'MODERATE')
        
        selected = []
        
        # Title card: Prioritize real dashboard screenshots
        if categorized_images['dashboard_screenshots']:
            selected.append(('title', categorized_images['dashboard_screenshots'][0]))
        elif categorized_images['title_cards']:
            selected.append(('title', categorized_images['title_cards'][0]))
        elif categorized_images['general']:
            selected.append(('title', categorized_images['general'][0]))
        
        # Data display: Prioritize real 3D visualizations and live data
        if categorized_images['3d_visualizations']:
            selected.append(('data', categorized_images['3d_visualizations'][0]))
        elif categorized_images['live_data_displays']:
            selected.append(('data', categorized_images['live_data_displays'][0]))
        elif categorized_images['data_displays']:
            selected.append(('data', categorized_images['data_displays'][0]))
        elif categorized_images['general']:
            selected.append(('data', categorized_images['general'][0]))
        
        # Activity showcase: Use tracking systems or activity charts
        if categorized_images['tracking_systems']:
            selected.append(('activity', categorized_images['tracking_systems'][0]))
        elif categorized_images['activity_charts']:
            selected.append(('activity', categorized_images['activity_charts'][0]))
        elif categorized_images['3d_visualizations']:
            selected.append(('activity', categorized_images['3d_visualizations'][0]))
        elif categorized_images['general']:
            selected.append(('activity', categorized_images['general'][0]))
        
        # Website promotion: Use real app screenshots for credibility
        if categorized_images['live_data_displays']:
            selected.append(('website', categorized_images['live_data_displays'][0]))
        elif categorized_images['dashboard_screenshots']:
            selected.append(('website', categorized_images['dashboard_screenshots'][0]))
        elif categorized_images['website_promo']:
            selected.append(('website', categorized_images['website_promo'][0]))
        elif categorized_images['general']:
            selected.append(('website', categorized_images['general'][0]))
        
        print(f"Selected {len(selected)} images for video:")
        for role, image in selected:
            print(f"  {role}: {image}")
        
        return selected
    
    def create_manual_video_instructions(self, audio_file, space_data, your_images):
        """Create detailed instructions using your real images"""
        
        summary = space_data.get('summary', {})
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        instructions = f"""
# CREATE VIDEO WITH YOUR REAL HELIOEARTH VISUALIZATIONS

## Audio File: {audio_file}
Your professional AI voice narration is ready!

## YOUR REAL IMAGES TO USE:

### Dashboard Screenshots (Best for authenticity):
{self.format_image_list(your_images.get('dashboard_screenshots', []))}

### 3D Visualizations (Show your tech):
{self.format_image_list(your_images.get('3d_visualizations', []))}

### Live Data Displays (Prove real-time capability):
{self.format_image_list(your_images.get('live_data_displays', []))}

### Tracking Systems (Aurora/ISS trackers):
{self.format_image_list(your_images.get('tracking_systems', []))}

### Generated Content Images:
- Title Cards: {self.format_image_list(your_images.get('title_cards', []))}
- Data Displays: {self.format_image_list(your_images.get('data_displays', []))}
- Activity Charts: {self.format_image_list(your_images.get('activity_charts', []))}
- Website Promotion: {self.format_image_list(your_images.get('website_promo', []))}

### Other Images:
{self.format_image_list(your_images.get('general', []))}

## VIDEO TIMELINE WITH YOUR REAL PICS:

### 0-8 seconds: Title Card
- Use: Your dashboard screenshot or 3D visualization
- Add text overlay: "HelioEarth Space Weather Alert"
- Add text: "{summary.get('total_events', 0)} Events Detected Today"

### 10-25 seconds: Data Display  
- Use: Your 3D space weather visualization
- Add text: "CMEs: {summary.get('cme_count', 0)} | Solar Flares: {summary.get('solar_flare_count', 0)}"
- Add text: "Activity Level: {summary.get('activity_level', 'MODERATE')}"

### 25-40 seconds: Activity Showcase
- Use: Your solar activity images or aurora pics
- Show your actual space weather data
- Highlight the real-time nature

### 40-60 seconds: Website Promotion
- Use: Your dashboard or interface screenshot
- Add large text: "Get Live 3D Visualizations & Alerts"
- Add prominent: "{self.website_url}"
- Show your actual website interface

## WHY YOUR REAL PICS ARE BETTER:

+ **AUTHENTICITY**: Shows your actual working system
+ **CREDIBILITY**: Proves you have real space weather data
+ **MONETIZATION**: Showcases your actual product
+ **DIFFERENTIATION**: Unique content nobody else has
+ **TRUST**: Viewers see real working technology

## QUICK VIDEO CREATION:

### Using CapCut (Recommended):
1. Import your audio file
2. Add your real images in sequence
3. Sync images with audio narration
4. Add text overlays with data
5. Highlight {self.website_url} prominently
6. Export as MP4 (1280x720, 30fps)

### Using Canva:
1. Create new video project (16:9)
2. Upload your audio and images
3. Add your pics to timeline
4. Insert text elements with space weather data
5. Ensure {self.website_url} is prominent
6. Download as MP4

## MONETIZATION POWER:

Your real visualizations show:
- Working 3D space weather system
- Live NASA data integration  
- Professional interface design
- Real-time monitoring capabilities
- Actual product value

This builds MUCH more trust and credibility than stock footage!

## Twitter Optimization:
- Keep under 60 seconds
- Start with attention-grabbing real visualization
- End with clear {self.website_url} call-to-action
- Use your actual data numbers in text overlays

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        instructions_file = f"use_your_real_pics_instructions_{timestamp}.txt"
        with open(instructions_file, 'w', encoding='utf-8') as f:
            f.write(instructions)
        
        print(f"SUCCESS: Instructions created: {instructions_file}")
        print("SUCCESS: Use your REAL space weather visualizations for maximum authenticity!")
        
        return instructions_file
    
    def format_image_list(self, images):
        """Format image list for instructions"""
        if not images:
            return "  (No images found in this category)"
        
        formatted = []
        for i, img in enumerate(images[:5]):  # Show up to 5
            formatted.append(f"  {i+1}. {img}")
        
        if len(images) > 5:
            formatted.append(f"  ... and {len(images) - 5} more images")
        
        return '\n'.join(formatted)
    
    def create_ffmpeg_video_with_your_pics(self, audio_file, selected_images, space_data, output_file):
        """Create video with FFmpeg using your real images"""
        
        if not selected_images:
            return False
        
        print("Creating video with FFmpeg using your real visualizations...")
        
        # Simple slideshow approach with your images
        try:
            # Get audio duration
            duration = 60  # Default 60 seconds
            
            # Create image list file for FFmpeg
            image_list_file = "your_images_list.txt"
            with open(image_list_file, 'w') as f:
                for _, image_path in selected_images:
                    # Duration per image
                    img_duration = duration / len(selected_images)
                    f.write(f"file '{image_path}'\n")
                    f.write(f"duration {img_duration}\n")
                
                # Repeat last image
                if selected_images:
                    f.write(f"file '{selected_images[-1][1]}'\n")
            
            ffmpeg_command = [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0", 
                "-i", image_list_file,
                "-i", audio_file,
                "-c:v", "libx264",
                "-c:a", "aac",
                "-pix_fmt", "yuv420p",
                "-shortest",
                "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2",
                output_file
            ]
            
            result = subprocess.run(ffmpeg_command, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                print(f"SUCCESS: Video created with your real pics: {output_file}")
                return True
            else:
                print(f"FFmpeg error: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Error creating video: {e}")
            return False
        finally:
            # Clean up
            if os.path.exists(image_list_file):
                os.remove(image_list_file)
    
    def create_complete_real_video_package(self):
        """Create complete video package using your real visualizations"""
        
        print("=" * 60)
        print("CREATING VIDEO WITH YOUR REAL HELIOEARTH VISUALIZATIONS")
        print("=" * 60)
        
        # Find latest content package
        package_files = glob.glob("monetized_package_*.json")
        if not package_files:
            print("No content package found. Generate content first.")
            return False
        
        latest_package = max(package_files, key=os.path.getctime)
        
        with open(latest_package, 'r') as f:
            content_package = json.load(f)
        
        # Get audio file
        audio_file = content_package['files']['audio']
        space_data = content_package['content']['space_data']
        
        # Create output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_video = f"helioearth_real_video_{timestamp}.mp4"
        
        # Create video with your real pics
        success = self.create_video_with_your_pics(audio_file, space_data, output_video)
        
        if success:
            print("=" * 60)
            print("SUCCESS: Video created with your REAL visualizations!")
            print("=" * 60)
            print("AUTHENTICITY FEATURES:")
            print("- Uses your actual space weather visualizations")
            print("- Shows your working HelioEarth system") 
            print("- Proves real-time NASA data integration")
            print("- Demonstrates actual product capabilities")
            print("- Builds maximum credibility and trust")
            print("=" * 60)
        
        return success

def main():
    """Main function"""
    
    print("Video Creator Using Your Real HelioEarth Visualizations")
    print("Developer: Oluwafemi Idiakhoa")
    print("=" * 60)
    
    creator = RealVisualizationVideoCreator()
    
    try:
        success = creator.create_complete_real_video_package()
        
        if success:
            print("\nSUCCESS: Your authentic HelioEarth video is ready!")
            print("\nWHY YOUR REAL PICS ARE POWERFUL:")
            print("+ Shows working technology (not stock footage)")
            print("+ Proves you have real space weather data") 
            print("+ Demonstrates actual product value")
            print("+ Builds trust and credibility")
            print("+ Differentiates from competitors")
            
            print("\nMONETIZATION ADVANTAGE:")
            print("- Viewers see real working system")
            print("- Higher conversion rates")
            print("- Premium positioning")
            print("- Authentic expertise demonstration")
        
        return success
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    main()