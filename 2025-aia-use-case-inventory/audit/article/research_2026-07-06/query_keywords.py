import json, subprocess, time
API="https://api.usaspending.gov/api/v2/search/spending_by_award/"
TIME=[{"start_date":"2023-10-01","end_date":"2026-07-06"}]
CONTRACTS=["A","B","C","D"]
def post(p):
    r=subprocess.run(["curl","-s","--max-time","60","-X","POST",API,
        "-H","Content-Type: application/json","-d",json.dumps(p)],capture_output=True,text=True)
    try:return json.loads(r.stdout)
    except Exception as e:print("err",e,r.stdout[:200]);return None
def fetch(kw):
    rows=[]
    for page in range(1,6):
        d=post({"filters":{"time_period":TIME,"keywords":[kw],"award_type_codes":CONTRACTS},
            "fields":["Award ID","Recipient Name","Awarding Agency","Award Amount","Description","Start Date"],
            "page":page,"limit":100,"sort":"Award Amount","order":"desc","subawards":False})
        if not d or not d.get("results"):break
        rows.extend(d["results"])
        if not d.get("page_metadata",{}).get("hasNext"):break
        time.sleep(0.4)
    return rows
out={}
for kw in ["ChatGPT","Microsoft Copilot","Gemini for Government","Claude AI","OpenAI"]:
    rows=fetch(kw); out[kw]=rows
    total=sum((r.get("Award Amount") or 0) for r in rows)
    print(f"\n===== keyword '{kw}': {len(rows)} awards, TOTAL ${total:,.0f} =====")
    for r in rows[:8]:
        print(f"  ${(r.get('Award Amount') or 0):>12,.0f} | {r.get('Recipient Name','?'):<26.26} | {r.get('Awarding Agency','?'):<22.22} | {(r.get('Description') or '')[:40]}")
json.dump(out,open("usaspending_keywords_raw.json","w"),indent=2)
print("\nsaved usaspending_keywords_raw.json")
