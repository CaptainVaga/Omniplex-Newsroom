#!/usr/bin/env python3
"""
WE333 VIDEO GENERATOR - Using Runway ML
Generate AI videos for news content
"""

import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Runway ML
try:
    from runwayml import RunwayML
    RUNWAY_OK = True
except ImportError:
    RUNWAY_OK = False

# Gemini for script/prompt generation
try:
    import google.generativeai as genai
    GEMINI_OK = True
except ImportError:
    GEMINI_OK = False


class RunwayVideoGenerator:
    """Generate videos using Runway ML Gen-3"""

    def __init__(self):
        api_key = os.getenv('RUNWAY_API_KEY')

        if api_key and RUNWAY_OK:
            self.client = RunwayML(api_key=api_key)
            print("✓ Runway ML: Connected")
        else:
            self.client = None
            print("✗ Runway ML: Not available")

    def generate_video_from_text(self, prompt: str, duration: int = 5) -> dict:
        """Generate video from text prompt using Gen-3 Alpha Turbo"""
        if not self.client:
            return {"error": "Runway not configured"}

        print(f"\n🎬 Generating video...")
        print(f"   Prompt: {prompt[:100]}...")
        print(f"   Duration: {duration}s")

        try:
            # Create video generation task
            task = self.client.image_to_video.create(
                model='gen3a_turbo',
                prompt_text=prompt,
                duration=duration
            )

            task_id = task.id
            print(f"   Task ID: {task_id}")

            # Poll for completion
            print("   Waiting for generation...")
            while True:
                task_status = self.client.tasks.retrieve(task_id)
                status = task_status.status
                print(f"   Status: {status}")

                if status == 'SUCCEEDED':
                    video_url = task_status.output[0]
                    print(f"   ✓ Video ready!")
                    return {
                        "status": "success",
                        "video_url": video_url,
                        "task_id": task_id,
                        "prompt": prompt
                    }
                elif status == 'FAILED':
                    return {
                        "status": "failed",
                        "error": task_status.failure or "Unknown error",
                        "task_id": task_id
                    }

                time.sleep(10)  # Wait 10 seconds before checking again

        except Exception as e:
            print(f"   ✗ Error: {e}")
            return {"error": str(e)}

    def generate_news_intro(self, headline: str) -> dict:
        """Generate a news intro video"""
        prompt = f"""Professional news broadcast studio, modern sleek design,
        blue and white color scheme, "WE333 NEWS" logo visible,
        dramatic lighting, news anchor desk, cinematic quality,
        headline text: "{headline[:50]}" """

        return self.generate_video_from_text(prompt, duration=5)

    def generate_parliament_scene(self) -> dict:
        """Generate UK Parliament scene"""
        prompt = """Exterior of UK Houses of Parliament, Westminster, Big Ben visible,
        dramatic sky, golden hour lighting, professional news footage style,
        slight camera movement, cinematic quality, 4K"""

        return self.generate_video_from_text(prompt, duration=5)


class NewsVideoProducer:
    """Produce complete news videos"""

    def __init__(self):
        print("\n" + "="*60)
        print("🎬 WE333 NEWS VIDEO PRODUCER")
        print("="*60)

        self.runway = RunwayVideoGenerator()

        # Setup Gemini for prompts
        api_key = os.getenv('GOOGLE_API_KEY')
        if api_key and GEMINI_OK:
            genai.configure(api_key=api_key)
            self.gemini = genai.GenerativeModel('gemini-2.0-flash')
            print("✓ Gemini: Ready for prompts")
        else:
            self.gemini = None

    def generate_video_prompt(self, news_topic: str) -> str:
        """Use Gemini to create optimal video prompt"""
        if not self.gemini:
            return f"Professional news footage of {news_topic}, cinematic quality"

        try:
            prompt = f"""Create a Runway ML video generation prompt for this news topic:
            "{news_topic}"

            Requirements:
            - Professional news broadcast style
            - Cinematic quality
            - 5-10 seconds of content
            - Appropriate visuals for news
            - No text overlays (we add those later)

            Return ONLY the video prompt, nothing else."""

            response = self.gemini.generate_content(prompt)
            return response.text.strip()
        except:
            return f"Professional news footage of {news_topic}, cinematic quality"

    def load_data(self) -> dict:
        """Load latest Parliament data"""
        data_path = os.path.join(os.path.dirname(__file__), 'data.json')
        try:
            with open(data_path, 'r') as f:
                return json.load(f)
        except:
            return {}

    def produce_news_video(self, custom_topic: str = None) -> dict:
        """Produce a news video from current data"""
        print("\n📰 Producing news video...")

        # Get topic
        if custom_topic:
            topic = custom_topic
        else:
            data = self.load_data()
            bills = data.get('parliament', {}).get('bills', [])
            if bills:
                topic = bills[0].get('shortTitle', 'UK Parliament Update')
            else:
                topic = 'UK Parliament Update'

        print(f"   Topic: {topic}")

        # Generate optimized prompt
        print("\n🤖 Generating video prompt with Gemini...")
        video_prompt = self.generate_video_prompt(topic)
        print(f"   Prompt: {video_prompt[:100]}...")

        # Generate video
        result = self.runway.generate_video_from_text(video_prompt)

        # Save result
        if result.get('status') == 'success':
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            meta_path = os.path.join(os.path.dirname(__file__), f"video_{timestamp}.json")
            with open(meta_path, 'w') as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "topic": topic,
                    "prompt": video_prompt,
                    "result": result
                }, f, indent=2)
            print(f"\n✅ Video metadata saved: video_{timestamp}.json")

        return result


def main():
    print("\n🎬 WE333 RUNWAY VIDEO GENERATOR")
    print("AI-powered news video production\n")

    producer = NewsVideoProducer()

    # Generate a Parliament intro video
    print("\nGenerating UK Parliament intro video...")
    result = producer.runway.generate_parliament_scene()

    if result.get('status') == 'success':
        print(f"\n🎉 SUCCESS!")
        print(f"Video URL: {result['video_url']}")
    else:
        print(f"\n❌ Error: {result.get('error', 'Unknown')}")


if __name__ == "__main__":
    main()
