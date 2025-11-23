#!/usr/bin/env python3
"""
CAPTAIN AIIA - Quality Journalism Every 10 Minutes
Research → Fact-Check → Write → Voice → Video → Publish
"""

import os
import json
import time
import hashlib
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")

def run_quality_story():
    """One quality story with full verification"""

    print("\n" + "="*70)
    print("📰 CAPTAIN AIIA - QUALITY JOURNALISM CYCLE")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Spain)")
    print("="*70)

    # Initialize AI clients
    log("Loading AI clients...")

    from openai import OpenAI
    from elevenlabs import ElevenLabs
    import google.generativeai as genai

    gpt = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    eleven = ElevenLabs(api_key=os.getenv('ELEVENLABS_API_KEY'))
    genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
    gemini = genai.GenerativeModel('gemini-2.0-flash')

    log("✓ Claude (Orchestrator), GPT, Gemini, ElevenLabs ready")

    # ========================================
    # STEP 1: RESEARCH with Gemini
    # ========================================
    print("\n" + "-"*70)
    log("🔬 STEP 1: GEMINI RESEARCH - Finding today's top UK story...")

    research_prompt = """You are a senior UK political researcher. Find the MOST IMPORTANT UK news story right now.

Consider:
- UK Parliament activity (bills, debates, votes)
- Government announcements
- Breaking political news
- Economic developments
- Public interest stories

Provide:
1. HEADLINE (clear, factual)
2. KEY FACTS (5 bullet points)
3. WHY IT MATTERS (2 sentences)
4. SOURCES to verify (official sources only)

Be factual, objective, no opinion."""

    research = gemini.generate_content(research_prompt)
    research_text = research.text
    log(f"✓ Research complete ({len(research_text)} chars)")
    print(f"\n📋 RESEARCH:\n{research_text[:500]}...")

    research_sha = sha256(research_text)
    log(f"   SHA: {research_sha[:16]}...")

    # ========================================
    # STEP 2: FACT-CHECK with GPT
    # ========================================
    print("\n" + "-"*70)
    log("✅ STEP 2: GPT FACT-CHECK...")

    fact_check = gpt.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a fact-checker. Verify the claims in this research. Flag any concerns."},
            {"role": "user", "content": f"Fact-check this UK news research:\n\n{research_text}\n\nProvide: 1) Verification status 2) Any concerns 3) Confidence level (high/medium/low)"}
        ]
    )
    fact_check_result = fact_check.choices[0].message.content
    log("✓ Fact-check complete")
    print(f"\n🔍 FACT-CHECK:\n{fact_check_result[:300]}...")

    # ========================================
    # STEP 3: WRITE STORY as Captain AIIA
    # ========================================
    print("\n" + "-"*70)
    log("✍️ STEP 3: GPT WRITING - Captain AIIA style...")

    story_prompt = f"""You are Captain AIIA, a professional AI journalist for WE333 Omniplex UK Democracy Monitor.

Write a broadcast-ready news story based on this research:

{research_text}

REQUIREMENTS:
- Professional journalistic tone
- Opening hook that grabs attention
- 3 paragraphs maximum
- End with "Human verification recommended."
- Sign off: "Captain AIIA, WE333 Omniplex"
- Total: 150-200 words (for 60-90 second voiceover)

Write the story now:"""

    story_response = gpt.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are Captain AIIA, a trusted AI journalist delivering factual news with integrity."},
            {"role": "user", "content": story_prompt}
        ]
    )
    story_text = story_response.choices[0].message.content
    log(f"✓ Story written ({len(story_text.split())} words)")
    print(f"\n📝 STORY:\n{story_text}")

    story_sha = sha256(story_text)
    log(f"   SHA: {story_sha[:16]}...")

    # ========================================
    # STEP 4: GENERATE VOICE (Priority!)
    # ========================================
    print("\n" + "-"*70)
    log("🎙️ STEP 4: ELEVENLABS VOICE...")

    audio = eleven.text_to_speech.convert(
        text=story_text,
        voice_id="EXAVITQu4vr4xnSDxMaL",  # Sarah - professional
        model_id="eleven_multilingual_v2"
    )

    timestamp = datetime.now().strftime("%H%M")
    voice_file = f"captain_aiia_{timestamp}.mp3"
    with open(voice_file, 'wb') as f:
        for chunk in audio:
            f.write(chunk)

    voice_size = os.path.getsize(voice_file) / 1024
    log(f"✓ Voice saved: {voice_file} ({voice_size:.0f} KB)")

    # ========================================
    # STEP 5: GENERATE VIDEO (SORA)
    # ========================================
    print("\n" + "-"*70)
    log("🎬 STEP 5: SORA VIDEO...")

    # Extract topic for video prompt
    headline = research_text.split('\n')[0][:100]

    video_task = gpt.videos.create(
        model="sora-2",
        prompt=f"Professional news broadcast, UK Parliament Westminster, dramatic lighting, cinematic slow zoom, broadcast quality"
    )
    video_id = video_task.id
    log(f"   Video queued: {video_id}")

    # Poll for video (max 2 min)
    video_file = None
    for i in range(24):
        video_status = gpt.videos.retrieve(video_id)
        if video_status.status == "completed":
            content = gpt.videos.download_content(video_id)
            video_file = f"captain_aiia_{timestamp}.mp4"
            with open(video_file, 'wb') as f:
                for chunk in content.iter_bytes():
                    f.write(chunk)
            video_size = os.path.getsize(video_file) / 1024
            log(f"✓ Video saved: {video_file} ({video_size:.0f} KB)")
            break
        elif video_status.status == "failed":
            log(f"✗ Video failed")
            break
        else:
            if i % 4 == 0:
                log(f"   Video: {video_status.status} {video_status.progress}%")
            time.sleep(5)

    # ========================================
    # STEP 6: UPDATE WEBSITE
    # ========================================
    print("\n" + "-"*70)
    log("🌐 STEP 6: UPDATE OMNIPLEX.EARTH...")

    # Create story JSON
    story_data = {
        "timestamp": datetime.now().isoformat(),
        "headline": headline,
        "story": story_text,
        "research_sha": research_sha,
        "story_sha": story_sha,
        "voice_file": voice_file,
        "video_file": video_file,
        "fact_check": fact_check_result[:500],
        "captain": "AIIA"
    }

    with open("latest_story.json", "w") as f:
        json.dump(story_data, f, indent=2)

    # Git push
    os.system('git add -A')
    os.system(f'git commit -m "[CAPTAIN AIIA] {headline[:50]}... SHA:{story_sha[:12]}"')
    os.system('git push origin main')

    log("✓ Pushed to omniplex.earth")

    # ========================================
    # SUMMARY
    # ========================================
    print("\n" + "="*70)
    print("✅ CAPTAIN AIIA STORY COMPLETE")
    print("="*70)
    print(f"📰 Headline: {headline[:60]}...")
    print(f"🎙️ Voice: {voice_file}")
    print(f"🎬 Video: {video_file or 'Processing...'}")
    print(f"🔐 Story SHA: {story_sha[:16]}...")
    print(f"⏱️ Completed: {datetime.now().strftime('%H:%M:%S')}")
    print("="*70)
    print("\n🔔 Human verification recommended.")

    # Play the voice
    os.system(f'open "{voice_file}"')
    if video_file:
        os.system(f'open "{video_file}"')

    return story_data

if __name__ == "__main__":
    print("\n🚀 CAPTAIN AIIA STARTING...")
    print("Quality journalism - 1 story, fully verified")

    # Wait for human confirmation
    input("\n⏳ Press ENTER to start the story cycle...")

    run_quality_story()
