import json, subprocess, time
API="https://api.usaspending.gov/api/v2/search/spending_by_award/"
TIME=[{"start_date":"2023-10-01","end_date":"2026-07-06"}]
CONTRACTS=["A","B","C","D"]
def post(p):
    r=subprocess.run(["curl","-s","--max-time","60","-X","POST",API,
        "-H","Content-Type: application/json","-d",json.dumps(p)],capture_output=True,text=True)
    try:return json.loads(r.stdout)
    except:return None
def fetch(kw,agency_recipient=None):
    f={"time_period":TIME,"keywords":[kw],"award_type_codes":CONTRACTS}
    d=post({"filters":f,"fields":["Award ID","Recipient Name","Awarding Agency","Award Amount","Description","Start Date"],
        "page":1,"limit":30,"sort":"Award Amount","order":"desc","subawards":False})
    return d.get("results",[]) if d else []
for kw in ["Google Workspace","Vertex AI","Azure OpenAI","GitHub Copilot"]:
    rows=fetch(kw)
    total=sum((r.get("Award Amount") or 0) for r in rows)
    print(f"\n=== '{kw}': {len(rows)} awards (top page), TOTAL(page) ${total:,.0f} ===")
    for r in rows[:6]:
        print(f"  ${(r.get('Award Amount') or 0):>13,.0f} | {r.get('Recipient Name','?'):<26.26} | {r.get('Awarding Agency','?'):<24.24} | {(r.get('Description') or '')[:38]}")
