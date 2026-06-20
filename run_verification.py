#!/usr/bin/env python3
"""
run_verification.py - Quick one-click verification script for the Redrob AI Challenge.
Runs unit tests, ranking pipeline, submission validator, and checks for traps/honeypots.
"""

import subprocess
import sys
import json
import csv
from pathlib import Path

def print_banner(msg):
    print("\n" + "=" * 80)
    print(f" {msg}")
    print("=" * 80)

def run_command(cmd, desc):
    print(f"\n[+] Running: {desc}...")
    print(f"Command: {cmd}")
    try:
        res = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        print(res.stdout)
        return True, res.stdout
    except subprocess.CalledProcessError as e:
        print("[-] FAILED!")
        print(e.stdout)
        return False, e.stdout

def main():
    print_banner("AI RECRUITER HACKATHON VERIFICATION SUITE")
    
    # 1. Run Unit Tests
    test_success, _ = run_command("python -m pytest backend/tests", "Unit Tests")
    
    # 2. Run Ranking Pipeline
    rank_success, _ = run_command(
        "python rank.py --candidates ./backend/processed_candidates.jsonl --out ./AI_Recruiter.csv",
        "Candidate Ranking Pipeline"
    )
    
    if not rank_success:
        print_banner("VERIFICATION FAILED: Ranking step failed.")
        sys.exit(1)
        
    # 3. Run Submission Format Validator
    val_success, _ = run_command(
        "python \"[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/validate_submission.py\" AI_Recruiter.csv",
        "Official Submission Validator"
    )
    
    # 4. Check for Traps and Honeypots in the Top 100 Shortlist
    print("\n[+] Scanning shortlist for non-tech traps and honeypots...")
    
    # Load shortlist
    shortlist_ids = []
    with open("AI_Recruiter.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            shortlist_ids.append(row["candidate_id"])
            
    # Load candidate mapping
    candidates_dict = {}
    with open("backend/processed_candidates.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            cand = json.loads(line)
            candidates_dict[cand.get("candidate_id")] = cand

    # Scan
    non_tech_traps = []
    honeypots = []
    
    # Simple trap and honeypot detection rules
    non_tech_keywords = {"marketing", "sales", "operations", "hr", "accountant", "civil", "mechanical", "graphic", "support", "writer", "scrum master", "agile coach", "recruiter", "talent acquisition", "analyst", "project manager", "product manager", "program manager"}
    
    for cid in shortlist_ids:
        cand = candidates_dict.get(cid)
        if not cand:
            continue
        
        # Non-tech check
        title = (cand.get("current_title") or "").lower().strip()
        if not title:
            summary = cand.get("profile_summary", "").lower()
            title = summary.split(" with ")[0].split(" at ")[0].strip()
            
        for kw in non_tech_keywords:
            if kw in title:
                # Check if it's a technical manager
                if "manager" in title:
                    is_tech_mgr = False
                    for tm_kw in ["engineering", "technical", "development", "technology", "software"]:
                        if tm_kw in title:
                            is_tech_mgr = True
                            break
                    if is_tech_mgr:
                        continue
                non_tech_traps.append((cid, title))
                break
                
        # Honeypot check
        yoe = cand.get("total_experience_years", 0)
        curr_role_yrs = cand.get("years_in_current_role", 0)
        if curr_role_yrs > yoe:
            honeypots.append((cid, f"Current role years ({curr_role_yrs}) > total experience ({yoe})"))
            
    print(f"  - Non-technical traps found: {len(non_tech_traps)}")
    for cid, title in non_tech_traps:
        print(f"    * {cid}: {title}")
        
    print(f"  - Honeypots found: {len(honeypots)}")
    for cid, reason in honeypots:
        print(f"    * {cid}: {reason}")
        
    trap_success = len(non_tech_traps) == 0 and len(honeypots) == 0

    # Final Report Summary
    print_banner("VERIFICATION SUMMARY")
    print(f"1. Pytest Unit Tests:       {'[PASSED]' if test_success else '[FAILED]'}")
    print(f"2. Ranking Pipeline Run:    {'[PASSED]' if rank_success else '[FAILED]'}")
    print(f"3. Format Specification:    {'[PASSED]' if val_success else '[FAILED]'}")
    print(f"4. Trap & Honeypot Filters: {'[PASSED]' if trap_success else '[FAILED]'}")
    print("=" * 80)
    
    if test_success and rank_success and val_success and trap_success:
        print(" SUCCESS: The project is fully compliant and ready for the hackathon!")
        sys.exit(0)
    else:
        print(" FAILURE: One or more checks failed. Please inspect the logs above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
