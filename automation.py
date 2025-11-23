#!/usr/bin/env python3
"""
WE333 OMNIPLEX - FULL AUTOMATION
Runs every 2.5 minutes: Data → Analysis → Voice → Push → Log
"""

import os
import sys
import json
import time
import hashlib
import subprocess
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Cycle counter
CYCLE = 0
LOG_FILE = "automation_log.json"

def sha256(data: str) -> str:
    """Generate SHA256 hash"""
    return hashlib.sha256(data.encode()).hexdigest()

def log_action(action: str, details: str, sha: str = None):
    """Log action with timestamp and SHA"""
    global CYCLE
    entry = {
        "cycle": CYCLE,
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "details": details,
        "sha": sha[:16] + "..." if sha else None
    }

    # Print to console
    print(f"[{entry['timestamp'][11:19]}] {action}: {details}")

    # Append to log file
    try:
        with open(LOG_FILE, 'r') as f:
            logs = json.load(f)
    except:
        logs = []

    logs.append(entry)
    # Keep last 100 entries
    logs = logs[-100:]

    with open(LOG_FILE, 'w') as f:
        json.dump(logs, f, indent=2)

def run_data_generator():
    """Run full data generator"""
    log_action("DATA_FETCH", "Starting UK data collection...")

    try:
        result = subprocess.run(
            ["python", "full_data_generator.py"],
            capture_output=True,
            text=True,
            timeout=120
        )

        # Get SHA of data.json
        with open("data.json", "r") as f:
            data = f.read()
        data_sha = sha256(data)

        # Parse stats
        data_json = json.loads(data)
        stats = data_json.get('stats', {})

        log_action("DATA_COMPLETE",
            f"Bills:{stats.get('total_bills',0)} Votes:{stats.get('total_votes',0)} News:{stats.get('total_news',0)}",
            data_sha)

        return True, data_sha
    except Exception as e:
        log_action("DATA_ERROR", str(e))
        return False, None

def generate_voice_briefing():
    """Generate quick voice briefing"""
    log_action("VOICE_GEN", "Generating ElevenLabs briefing...")

    try:
        from elevenlabs import ElevenLabs

        client = ElevenLabs(api_key=os.getenv('ELEVENLABS_API_KEY'))

        # Load current stats
        with open("data.json", "r") as f:
            data = json.load(f)
        stats = data.get('stats', {})

        # Create briefing text
        now = datetime.now().strftime("%H:%M")
        text = f"WE333 Update at {now}. {stats.get('total_bills', 0)} bills tracked. {stats.get('total_news', 0)} news stories. System operational."

        # Generate audio
        audio = client.text_to_speech.convert(
            text=text,
            voice_id="EXAVITQu4vr4xnSDxMaL",
            model_id="eleven_multilingual_v2"
        )

        filename = f"auto_briefing_{datetime.now().strftime('%H%M%S')}.mp3"
        with open(filename, 'wb') as f:
            for chunk in audio:
                f.write(chunk)

        log_action("VOICE_COMPLETE", filename)
        return True, filename
    except Exception as e:
        log_action("VOICE_SKIP", f"ElevenLabs: {str(e)[:50]}")
        return False, None

def git_push(data_sha: str):
    """Push to GitHub"""
    log_action("GIT_PUSH", "Pushing to GitHub...")

    try:
        # Add all changes
        subprocess.run(["git", "add", "-A"], capture_output=True)

        # Commit
        global CYCLE
        commit_msg = f"[AUTO #{CYCLE}] Data update SHA:{data_sha[:12]}"
        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            capture_output=True
        )

        # Push
        result = subprocess.run(
            ["git", "push", "origin", "main"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            log_action("GIT_COMPLETE", "Pushed to omniplex.earth")
            return True
        else:
            log_action("GIT_SKIP", "No changes or push failed")
            return False
    except Exception as e:
        log_action("GIT_ERROR", str(e))
        return False

def run_cycle():
    """Run one complete automation cycle"""
    global CYCLE
    CYCLE += 1

    print("\n" + "="*60)
    print(f"🔄 AUTOMATION CYCLE #{CYCLE} - {datetime.now().strftime('%H:%M:%S')}")
    print("="*60)

    # Step 1: Fetch data
    data_ok, data_sha = run_data_generator()

    # Step 2: Generate voice (every 3rd cycle to save credits)
    voice_ok = False
    if CYCLE % 3 == 1:
        voice_ok, voice_file = generate_voice_briefing()
    else:
        log_action("VOICE_SKIP", f"Cycle {CYCLE} - voice every 3rd cycle")

    # Step 3: Push to GitHub
    if data_ok:
        git_push(data_sha)

    # Summary
    print("-"*60)
    print(f"✅ Cycle #{CYCLE} complete")
    print(f"   Data: {'✓' if data_ok else '✗'} | Voice: {'✓' if voice_ok else '○'} | SHA: {data_sha[:12] if data_sha else 'N/A'}")
    print(f"   Next cycle in 2.5 minutes...")
    print("="*60)

def thirty_min_review():
    """30-minute review with full report"""
    global CYCLE

    print("\n" + "🔷"*30)
    print("📊 30-MINUTE REVIEW")
    print("🔷"*30)

    try:
        with open(LOG_FILE, 'r') as f:
            logs = json.load(f)

        # Get last 30 mins of logs
        recent = logs[-12:]  # ~12 cycles in 30 mins

        data_fetches = len([l for l in recent if l['action'] == 'DATA_COMPLETE'])
        voice_gens = len([l for l in recent if l['action'] == 'VOICE_COMPLETE'])
        git_pushes = len([l for l in recent if l['action'] == 'GIT_COMPLETE'])

        print(f"   Cycles completed: {len(recent)}")
        print(f"   Data fetches: {data_fetches}")
        print(f"   Voice generations: {voice_gens}")
        print(f"   Git pushes: {git_pushes}")

        # Unique SHAs
        shas = [l['sha'] for l in recent if l.get('sha')]
        unique_shas = len(set(shas))
        print(f"   Unique data states: {unique_shas}")

    except Exception as e:
        print(f"   Review error: {e}")

    print("🔷"*30 + "\n")

def main():
    """Main automation loop"""
    print("\n" + "🚀"*20)
    print("WE333 OMNIPLEX - FULL AUTOMATION STARTED")
    print("Interval: 2.5 minutes | Voice: every 3rd cycle")
    print("🚀"*20 + "\n")

    log_action("SYSTEM_START", "Automation initialized")

    cycle_interval = 150  # 2.5 minutes in seconds
    review_interval = 1800  # 30 minutes
    last_review = time.time()

    try:
        while True:
            # Run cycle
            run_cycle()

            # 30-minute review
            if time.time() - last_review >= review_interval:
                thirty_min_review()
                last_review = time.time()

            # Wait for next cycle
            print(f"\n⏳ Waiting 2.5 minutes... (Ctrl+C to stop)\n")
            time.sleep(cycle_interval)

    except KeyboardInterrupt:
        print("\n\n🛑 Automation stopped by user")
        log_action("SYSTEM_STOP", "User interrupt")

if __name__ == "__main__":
    main()
