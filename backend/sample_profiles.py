import json

with open(r'C:\AI_Recruiter\backend\processed_candidates.jsonl', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if i >= 5:
            break
        c = json.loads(line)
        print(f"=== {c['id']} ===")
        print(f"Seniority: {c['seniority']}")
        print(f"Experience: {c['total_experience_years']}y")
        print(f"Skills: {list(c['skills'].keys())[:10]}")
        print(f"Summary: {c['profile_summary'][:300]}")
        print()
