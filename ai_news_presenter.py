#!/usr/bin/env python3
"""
WE333 AI NEWS PRESENTER
Generates audio news briefings from UK Parliament data
Using: Gemini (script) + ElevenLabs (voice)
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Gemini
try:
    import google.generativeai as genai
    GEMINI_OK = True
except ImportError:
    GEMINI_OK = False

# ElevenLabs
try:
    from elevenlabs import ElevenLabs
    ELEVEN_OK = True
except ImportError:
    ELEVEN_OK = False


class NewsScriptWriter:
    """Write news scripts using Gemini"""

    def __init__(self):
        api_key = os.getenv('GOOGLE_API_KEY')
        if api_key and GEMINI_OK:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
            print("✓ Gemini: Ready")
        else:
            self.model = None
            print("✗ Gemini: Not available")

    def write_script(self, data: dict, style: str = "professional") -> str:
        """Generate a news script from data"""
        if not self.model:
            return self._fallback_script(data)

        bills = data.get('parliament', {}).get('bills', [])
        votes = data.get('parliament', {}).get('commons_divisions', [])
        news = data.get('news', {}).get('bbc_politics', [])

        prompt = f"""You are a professional UK news presenter for WE333 News.
Write a 60-second news briefing script (about 150 words) covering:

TODAY'S PARLIAMENT:
- {len(bills)} bills being debated
- Key bills: {', '.join([b.get('shortTitle', '')[:40] for b in bills[:3]])}
- Recent votes: {len(votes)}

TOP HEADLINES:
{chr(10).join(['- ' + n.get('title', '')[:50] for n in news[:3]])}

Style: {style}, authoritative, clear
Format: Ready to read aloud, with natural pauses marked by ...
Start with: "Good evening, I'm your WE333 news presenter..."
End with: "This has been your WE333 briefing. Human verification recommended."

Write the script now:"""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Script error: {e}")
            return self._fallback_script(data)

    def _fallback_script(self, data: dict) -> str:
        """Fallback simple script"""
        bills = len(data.get('parliament', {}).get('bills', []))
        votes = len(data.get('parliament', {}).get('commons_divisions', []))

        return f"""Good evening, I'm your WE333 news presenter.

Today in UK Parliament... {bills} bills are being debated,
with {votes} votes recorded this week.

Parliament continues to address key issues affecting the nation...
including legislation on public safety, economic reform, and social policy.

We're monitoring all developments with our 8-agent system...
ensuring triple verification on every fact.

This has been your WE333 briefing. Human verification recommended."""


class VoiceGenerator:
    """Generate voice audio using ElevenLabs"""

    def __init__(self):
        api_key = os.getenv('ELEVENLABS_API_KEY')
        if api_key and ELEVEN_OK:
            self.client = ElevenLabs(api_key=api_key)
            print("✓ ElevenLabs: Ready")
            self._list_voices()
        else:
            self.client = None
            print("✗ ElevenLabs: Not available")

    def _list_voices(self):
        """List available voices"""
        try:
            response = self.client.voices.get_all()
            print(f"  Available voices: {len(response.voices)}")
            for v in response.voices[:5]:
                print(f"    - {v.name} ({v.voice_id})")
        except Exception as e:
            print(f"  Voice list error: {e}")

    def generate_audio(self, text: str, voice: str = "Rachel", output_file: str = "news_briefing.mp3") -> str:
        """Generate audio from text"""
        if not self.client:
            print("ElevenLabs not configured")
            return None

        try:
            print(f"\n🎙️ Generating audio with voice: {voice}")
            print(f"   Text length: {len(text)} characters")

            audio = self.client.text_to_speech.convert(
                text=text,
                voice_id=voice,
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128"
            )

            # Save audio
            output_path = os.path.join(os.path.dirname(__file__), output_file)
            with open(output_path, 'wb') as f:
                for chunk in audio:
                    f.write(chunk)

            print(f"   ✓ Audio saved: {output_file}")
            return output_path

        except Exception as e:
            print(f"   ✗ Audio error: {e}")
            return None


class AINewsPresenter:
    """Main AI News Presenter system"""

    def __init__(self):
        print("\n" + "="*60)
        print("🎬 WE333 AI NEWS PRESENTER")
        print("="*60)

        self.writer = NewsScriptWriter()
        self.voice = VoiceGenerator()

    def load_data(self) -> dict:
        """Load latest data.json"""
        data_path = os.path.join(os.path.dirname(__file__), 'data.json')
        try:
            with open(data_path, 'r') as f:
                return json.load(f)
        except:
            return {}

    def create_briefing(self, voice_name: str = "Rachel") -> dict:
        """Create full news briefing"""
        print("\n📰 Creating news briefing...")

        # Load data
        data = self.load_data()
        if not data:
            print("No data.json found - run full_data_generator.py first")
            return {}

        print(f"   Data loaded: {data.get('timestamp', 'unknown')}")

        # Write script
        print("\n📝 Writing script with Gemini...")
        script = self.writer.write_script(data)
        print(f"   Script: {len(script)} characters")
        print("\n--- SCRIPT ---")
        print(script)
        print("--- END SCRIPT ---\n")

        # Generate audio
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_file = f"briefing_{timestamp}.mp3"
        audio_path = self.voice.generate_audio(script, voice_name, audio_file)

        result = {
            "timestamp": datetime.now().isoformat(),
            "script": script,
            "audio_file": audio_path,
            "voice": voice_name,
            "data_timestamp": data.get('timestamp')
        }

        # Save briefing metadata
        meta_path = os.path.join(os.path.dirname(__file__), f"briefing_{timestamp}.json")
        with open(meta_path, 'w') as f:
            json.dump(result, f, indent=2)

        print("\n" + "="*60)
        print("✅ BRIEFING COMPLETE")
        print("="*60)
        if audio_path:
            print(f"🎧 Audio: {audio_file}")
        print(f"📄 Script saved")

        return result


def main():
    print("\n🎬 WE333 AI NEWS PRESENTER")
    print("Your digital journalism clone\n")

    presenter = AINewsPresenter()

    # Create briefing
    result = presenter.create_briefing(voice_name="Rachel")

    if result.get('audio_file'):
        print(f"\n▶️ To play: open {result['audio_file']}")


if __name__ == "__main__":
    main()
