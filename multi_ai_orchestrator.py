#!/usr/bin/env python3
"""
WE333 MULTI-AI ORCHESTRATOR
Coordinates: GPT (Ecosystem) + Gemini (Research) + Claude (Code)
Output: Runway (Video) + ElevenLabs (Voice)
"""

import os
import json
from datetime import datetime
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()

# === AI PROVIDERS ===

class GPTClient:
    """OpenAI GPT - Ecosystem Creator & Strategy"""

    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        self.client = None

        if api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=api_key)
                print("✓ GPT: Ready (Ecosystem Creator)")
            except Exception as e:
                print(f"✗ GPT: {e}")
        else:
            print("✗ GPT: No API key")

    def generate(self, prompt: str, role: str = "ecosystem") -> str:
        """Generate with GPT-4"""
        if not self.client:
            return None

        system_prompts = {
            "ecosystem": "You are GPT, the Ecosystem Creator for WE333 Omniplex. You design systems, plan architecture, and create comprehensive strategies.",
            "content": "You are a professional content writer creating engaging, factual content.",
            "strategy": "You are a strategic planner analyzing data and recommending actions."
        }

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompts.get(role, system_prompts["ecosystem"])},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"GPT error: {e}")
            return None


class GeminiClient:
    """Google Gemini - Research & Analysis"""

    def __init__(self):
        api_key = os.getenv('GOOGLE_API_KEY')
        self.model = None

        if api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-2.0-flash')
                print("✓ Gemini: Ready (Research & Analysis)")
            except Exception as e:
                print(f"✗ Gemini: {e}")
        else:
            print("✗ Gemini: No API key")

    def generate(self, prompt: str) -> str:
        """Generate with Gemini"""
        if not self.model:
            return None

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Gemini error: {e}")
            return None


class ElevenLabsClient:
    """ElevenLabs - Voice Generation"""

    def __init__(self):
        api_key = os.getenv('ELEVENLABS_API_KEY')
        self.client = None

        if api_key:
            try:
                from elevenlabs import ElevenLabs
                self.client = ElevenLabs(api_key=api_key)
                print("✓ ElevenLabs: Ready (Voice)")
            except Exception as e:
                print(f"✗ ElevenLabs: {e}")
        else:
            print("✗ ElevenLabs: No API key")

    def generate_voice(self, text: str, output_file: str = "output.mp3") -> str:
        """Generate voice audio"""
        if not self.client:
            return None

        try:
            audio = self.client.text_to_speech.convert(
                text=text,
                voice_id="Rachel",
                model_id="eleven_multilingual_v2"
            )

            output_path = os.path.join(os.path.dirname(__file__), output_file)
            with open(output_path, 'wb') as f:
                for chunk in audio:
                    f.write(chunk)
            return output_path
        except Exception as e:
            print(f"ElevenLabs error: {e}")
            return None


class RunwayClient:
    """Runway ML - Video Generation"""

    def __init__(self):
        api_key = os.getenv('RUNWAY_API_KEY')
        self.client = None

        if api_key:
            try:
                from runwayml import RunwayML
                self.client = RunwayML(api_key=api_key)
                print("✓ Runway: Ready (Video)")
            except Exception as e:
                print(f"✗ Runway: {e}")
        else:
            print("✗ Runway: No API key")


# === ORCHESTRATOR ===

class MultiAIOrchestrator:
    """
    WE333 Multi-AI Orchestrator

    Roles:
    - Claude (via terminal): Code, Deploy, Coordinate
    - GPT: Ecosystem Creation, Strategy, Planning
    - Gemini: Research, Analysis, Data Processing
    - ElevenLabs: Voice Output
    - Runway: Video Output
    """

    def __init__(self):
        print("\n" + "="*60)
        print("🤖 WE333 MULTI-AI ORCHESTRATOR")
        print("="*60)

        self.gpt = GPTClient()
        self.gemini = GeminiClient()
        self.elevenlabs = ElevenLabsClient()
        self.runway = RunwayClient()

        print("="*60)

    def load_data(self) -> Dict:
        """Load latest UK data"""
        data_path = os.path.join(os.path.dirname(__file__), 'data.json')
        try:
            with open(data_path, 'r') as f:
                return json.load(f)
        except:
            return {}

    def research_with_gemini(self, topic: str) -> str:
        """Use Gemini for research and analysis"""
        print(f"\n🔬 Gemini researching: {topic[:50]}...")

        prompt = f"""As WE333 Research AI, analyze this topic:
{topic}

Provide factual, objective analysis. Cite data where possible.
End with "Human verification recommended." """

        result = self.gemini.generate(prompt)
        if result:
            print("   ✓ Research complete")
        return result

    def plan_with_gpt(self, objective: str) -> str:
        """Use GPT for ecosystem planning"""
        print(f"\n📋 GPT planning: {objective[:50]}...")

        prompt = f"""As WE333 Ecosystem Creator, create a plan for:
{objective}

Structure your response as:
1. Overview
2. Components needed
3. Integration points
4. Implementation steps
5. Success metrics"""

        result = self.gpt.generate(prompt, role="ecosystem")
        if result:
            print("   ✓ Plan complete")
        return result

    def create_content_with_gpt(self, data: Dict, content_type: str = "news") -> str:
        """Use GPT to create content"""
        print(f"\n✍️ GPT creating {content_type}...")

        stats = data.get('stats', {})

        prompt = f"""Create a professional {content_type} briefing from this UK data:

Statistics:
- Bills: {stats.get('total_bills', 0)}
- Votes: {stats.get('total_votes', 0)}
- News stories: {stats.get('total_news', 0)}
- Crime reports: {stats.get('total_crimes', 0)}
- Weather warnings: {stats.get('total_weather_warnings', 0)}

Write a 100-word summary suitable for broadcast.
Be factual and objective."""

        result = self.gpt.generate(prompt, role="content")
        if result:
            print("   ✓ Content created")
        return result

    def analyze_with_gemini(self, data: Dict) -> str:
        """Use Gemini to analyze data"""
        print("\n📊 Gemini analyzing data...")

        stats = data.get('stats', {})

        prompt = f"""Analyze this UK democracy data:

Parliament: {stats.get('total_bills', 0)} bills, {stats.get('total_votes', 0)} votes
News: {stats.get('total_news', 0)} stories
Crime: {stats.get('total_crimes', 0)} reports in London
Weather: {stats.get('total_weather_warnings', 0)} warnings

Identify:
1. Key trends
2. Potential concerns
3. Notable patterns

Be objective and factual."""

        result = self.gemini.generate(prompt)
        if result:
            print("   ✓ Analysis complete")
        return result

    def generate_voice(self, text: str, filename: str = "briefing.mp3") -> str:
        """Generate voice with ElevenLabs"""
        print(f"\n🎙️ ElevenLabs generating voice...")

        result = self.elevenlabs.generate_voice(text, filename)
        if result:
            print(f"   ✓ Audio saved: {filename}")
        return result

    def orchestrate_news_briefing(self) -> Dict:
        """Full orchestration: Research → Analyze → Content → Voice"""
        print("\n" + "="*60)
        print("📰 ORCHESTRATING NEWS BRIEFING")
        print("="*60)

        results = {
            "timestamp": datetime.now().isoformat(),
            "steps": {}
        }

        # Step 1: Load data
        data = self.load_data()
        if not data:
            print("❌ No data.json found. Run full_data_generator.py first.")
            return results

        results['data_timestamp'] = data.get('timestamp')

        # Step 2: Gemini analyzes
        analysis = self.analyze_with_gemini(data)
        results['steps']['gemini_analysis'] = analysis

        # Step 3: GPT creates content
        content = self.create_content_with_gpt(data)
        results['steps']['gpt_content'] = content

        # Step 4: Generate voice (optional)
        if content and self.elevenlabs.client:
            audio = self.generate_voice(content, f"briefing_{datetime.now().strftime('%H%M%S')}.mp3")
            results['steps']['audio_file'] = audio

        # Summary
        print("\n" + "="*60)
        print("✅ ORCHESTRATION COMPLETE")
        print("="*60)
        print(f"• Gemini Analysis: {'✓' if analysis else '✗'}")
        print(f"• GPT Content: {'✓' if content else '✗'}")
        print(f"• Audio: {'✓' if results['steps'].get('audio_file') else '✗'}")

        return results

    def compare_ai_responses(self, question: str) -> Dict:
        """Compare GPT vs Gemini on same question"""
        print(f"\n🔄 Comparing AI responses...")
        print(f"   Question: {question[:50]}...")

        gpt_response = self.gpt.generate(question, role="content")
        gemini_response = self.gemini.generate(question)

        return {
            "question": question,
            "gpt": gpt_response,
            "gemini": gemini_response
        }


def main():
    print("\n🤖 WE333 MULTI-AI ORCHESTRATOR")
    print("GPT + Gemini + ElevenLabs + Runway")
    print("Coordinated by Claude\n")

    orchestrator = MultiAIOrchestrator()

    # Run full orchestration
    print("\n" + "-"*60)
    results = orchestrator.orchestrate_news_briefing()

    # Show results
    if results.get('steps', {}).get('gpt_content'):
        print("\n📝 GPT CONTENT:")
        print("-"*40)
        print(results['steps']['gpt_content'])

    if results.get('steps', {}).get('gemini_analysis'):
        print("\n🔬 GEMINI ANALYSIS:")
        print("-"*40)
        print(results['steps']['gemini_analysis'][:500] + "...")


if __name__ == "__main__":
    main()
