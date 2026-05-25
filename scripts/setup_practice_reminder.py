#!/usr/bin/env python3
"""
Instrument Practice Coach — Setup Helper
Run this to generate a cron job for daily instrument practice reminders.

Usage:
  python3 setup_practice_reminder.py

Or import and call:
  from setup_practice_reminder import create_reminder
  create_reminder(instrument='guitar', plan_file='/home/user/...', start_date='2026-06-01', schedule='0 19 * * *')
"""

import os
import re
from datetime import datetime

# Instrument-specific daily templates
TEMPLATES = {
    "guitar": {
        "warmup": "Tune: 2–3 min",
        "posture": "Posture/strap check: 1 min",
        "technique": "Right-hand picking or strumming: 5 min",
        "repertoire": "Scale or chord drill + song: 10–20 min",
        "review": "Record/review: 1–2 min once or twice weekly",
    },
    "mandolin": {
        "warmup": "Tune: 2–3 min",
        "posture": "Stabilization/posture check: 1 min",
        "technique": "Right hand: 5 min",
        "repertoire": "Scale/chords + tune: 10–20 min",
        "review": "Record/review: 1–2 min once or twice weekly",
    },
    "ukulele": {
        "warmup": "Tune: 2 min",
        "posture": "Posture/strap check: 1 min",
        "technique": "Strumming or fingerpicking: 5 min",
        "repertoire": "Chord progressions + song: 10–20 min",
        "review": "Record/review: 1–2 min once or twice weekly",
    },
    "banjo": {
        "warmup": "Tune: 2–3 min",
        "posture": "Strap/posture check: 1 min",
        "technique": "Rolls or clawhammer pattern: 5 min",
        "repertoire": "Chord changes + tune: 10–20 min",
        "review": "Record/review: 1–2 min once or twice weekly",
    },
    "piano": {
        "warmup": "Finger warm-up / scales: 5 min",
        "posture": "Bench height / wrist posture check: 1 min",
        "technique": "Technical exercise: 5–10 min",
        "repertoire": "Piece / sight-reading: 15–25 min",
        "review": "Record/review: 1–2 min once or twice weekly",
    },
    "keyboard": {
        "warmup": "Finger warm-up / scales: 5 min",
        "posture": "Bench height / wrist posture check: 1 min",
        "technique": "Technical exercise: 5–10 min",
        "repertoire": "Piece / sight-reading: 15–25 min",
        "review": "Record/review: 1–2 min once or twice weekly",
    },
    "violin": {
        "warmup": "Open strings / bow control: 3–5 min",
        "posture": "Posture / shoulder rest check: 1 min",
        "technique": "Scale / etude: 5–10 min",
        "repertoire": "Repertoire / intonation drill: 10–20 min",
        "review": "Record/review: 1–2 min once or twice weekly",
    },
    "viola": {
        "warmup": "Open strings / bow control: 3–5 min",
        "posture": "Posture / shoulder rest check: 1 min",
        "technique": "Scale / etude: 5–10 min",
        "repertoire": "Repertoire / intonation drill: 10–20 min",
        "review": "Record/review: 1–2 min once or twice weekly",
    },
    "cello": {
        "warmup": "Open strings / bow control: 3–5 min",
        "posture": "Posture / endpin height check: 1 min",
        "technique": "Scale / etude: 5–10 min",
        "repertoire": "Repertoire / intonation drill: 10–20 min",
        "review": "Record/review: 1–2 min once or twice weekly",
    },
    "saxophone": {
        "warmup": "Long tones / embouchure: 3–5 min",
        "posture": "Reed / posture check: 1 min",
        "technique": "Technical exercise / scales: 5–10 min",
        "repertoire": "Piece / improvisation: 10–20 min",
        "review": "Record/review: 1–2 min once or twice weekly",
    },
    "clarinet": {
        "warmup": "Long tones / embouchure: 3–5 min",
        "posture": "Reed / posture check: 1 min",
        "technique": "Technical exercise / scales: 5–10 min",
        "repertoire": "Piece / improvisation: 10–20 min",
        "review": "Record/review: 1–2 min once or twice weekly",
    },
    "flute": {
        "warmup": "Long tones / breath control: 3–5 min",
        "posture": "Posture / headjoint alignment check: 1 min",
        "technique": "Technical exercise / scales: 5–10 min",
        "repertoire": "Piece / tone exercise: 10–20 min",
        "review": "Record/review: 1–2 min once or twice weekly",
    },
    "trumpet": {
        "warmup": "Long tones / lip slurs: 3–5 min",
        "posture": "Posture / mouthpiece check: 1 min",
        "technique": "Technical exercise / scales: 5–10 min",
        "repertoire": "Piece / improvisation: 10–20 min",
        "review": "Record/review: 1–2 min once or twice weekly",
    },
    "drums": {
        "warmup": "Stick control / rudiments: 5 min",
        "posture": "Throne height / posture check: 1 min",
        "technique": "Groove / fill exercise: 5–10 min",
        "repertoire": "Song / independence drill: 10–20 min",
        "review": "Record/review: 1–2 min once or twice weekly",
    },
}


def guess_template(instrument: str):
    """Return the best matching template for an instrument name."""
    key = instrument.lower().strip()
    if key in TEMPLATES:
        return TEMPLATES[key]
    # Fuzzy match
    for k, v in TEMPLATES.items():
        if k in key or key in k:
            return v
    # Generic fallback
    return {
        "warmup": "Warm-up / tuning: 3–5 min",
        "posture": "Posture / setup check: 1 min",
        "technique": "Technical exercise: 5–10 min",
        "repertoire": "Repertoire / song: 10–20 min",
        "review": "Record/review: 1–2 min once or twice weekly",
    }


def build_prompt(instrument: str, plan_file: str, start_date: str, n_weeks: int = 12) -> str:
    """Build the cron prompt for a given instrument and plan."""
    template = guess_template(instrument)
    total_days = n_weeks * 7

    prompt = f"""You are a {instrument} practice coach. Today is {{date}}.

Reference the {n_weeks}-week {instrument} learning plan at `{plan_file}` to give a targeted daily reminder.

Calculate which week/day of the plan the user is on based on when they started ({start_date}).

Rules for calculation:
- Day 1 = {start_date}
- Count every calendar day as one plan day (practice days and rest days both advance the counter)
- If the plan has {total_days} total days, loop or cap at the final day

Then produce exactly this format:
1. **Week N, Day X** (X days into your {n_weeks}-week plan)
2. **Today's tasks:** (read from the plan file for this day)
   - Task 1
   - Task 2
3. **Session template:**
   - {template['warmup']}
   - {template['posture']}
   - {template['technique']}
   - {template['repertoire']}
   - {template['review']}
4. **Focus tip:** One encouragement or form cue specific to today's task.

Keep the total message under 300 words. Do not guess tasks — read them from the plan file."""
    return prompt


def validate_plan_file(plan_file: str) -> bool:
    """Check if the plan file exists and has the minimum required structure."""
    if not os.path.isfile(plan_file):
        print(f"⚠️  Plan file not found: {plan_file}")
        return False

    with open(plan_file, 'r', encoding='utf-8') as f:
        content = f.read()

    checks = []
    if '## Week 1:' in content or '## Week 1' in content:
        checks.append("✅ Has Week 1 section")
    else:
        checks.append("❌ Missing Week 1 section")

    if '**Day 1:**' in content:
        checks.append("✅ Has Day 1 entry")
    else:
        checks.append("❌ Missing Day 1 entry")

    if '## Daily template' in content:
        checks.append("✅ Has Daily template section")
    else:
        checks.append("❌ Missing Daily template section")

    for c in checks:
        print(f"  {c}")

    return all('✅' in c for c in checks)


def create_reminder(
    instrument: str,
    plan_file: str,
    start_date: str,
    schedule: str = "0 19 * * *",
    deliver: str = "origin",
    n_weeks: int = 12,
    validate: bool = True,
):
    """
    Generate the cron prompt and print instructions for creating the job.
    This is designed to be copy-paste friendly for Hermes cronjob creation.
    """
    instrument = instrument.lower().strip()
    plan_file = os.path.abspath(os.path.expanduser(plan_file))

    print(f"\n{'='*60}")
    print(f"  Instrument Practice Coach — Setup")
    print(f"{'='*60}")
    print(f"  Instrument:    {instrument.title()}")
    print(f"  Plan file:     {plan_file}")
    print(f"  Start date:    {start_date}")
    print(f"  Schedule:      {schedule}")
    print(f"  Deliver to:    {deliver}")
    print(f"  Plan weeks:    {n_weeks}")
    print(f"{'='*60}\n")

    if validate:
        print("Validating plan file...")
        if not validate_plan_file(plan_file):
            print("\n⚠️  Plan file validation failed. See templates/plan-template.md for the expected format.")
            return None
        print("✅ Plan file looks good.\n")

    prompt = build_prompt(instrument, plan_file, start_date, n_weeks)

    job_name = f"{instrument}-practice-reminder"

    print("Generated cron prompt (ready to paste into cronjob create):\n")
    print("-" * 60)
    print(prompt)
    print("-" * 60)

    print(f"\nTo create the cron job, run:\n")
    print(f"```python")
    print(f"cronjob(action='create',")
    print(f"    name='{job_name}',")
    print(f"    prompt='''{prompt}''',")
    print(f"    schedule='{schedule}',")
    print(f"    deliver='{deliver}',")
    print(f")")
    print(f"```")

    return {
        "instrument": instrument,
        "job_name": job_name,
        "prompt": prompt,
        "schedule": schedule,
        "deliver": deliver,
        "plan_file": plan_file,
        "start_date": start_date,
        "n_weeks": n_weeks,
    }


def interactive_setup():
    """Ask the user for inputs interactively."""
    print("\n🎵 Instrument Practice Coach Setup\n")

    instrument = input("Instrument (e.g., guitar, piano, violin): ").strip().lower()
    plan_file = input("Plan file path (e.g., ~/Documents/guitar-plan/12-week-plan.md): ").strip()
    start_date = input("Start date (YYYY-MM-DD, e.g., 2026-06-01): ").strip()
    schedule = input("Reminder time (cron, e.g., '0 19 * * *' for 7pm daily): ").strip() or "0 19 * * *"
    deliver = input("Deliver target (origin/telegram/local): ").strip() or "origin"
    n_weeks_input = input("Number of weeks in plan (default 12): ").strip()
    n_weeks = int(n_weeks_input) if n_weeks_input else 12

    create_reminder(instrument, plan_file, start_date, schedule, deliver, n_weeks)


if __name__ == "__main__":
    interactive_setup()
