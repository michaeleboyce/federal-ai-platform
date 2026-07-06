import json, subprocess, time

API = "https://api.usaspending.gov/api/v2/search/spending_by_award/"
TIME = [{"start_date": "2023-10-01", "end_date": "2026-07-06"}]
CONTRACTS = ["A", "B", "C", "D"]

def post(payload):
    p = subprocess.run(["curl","-s","--max-time","60","-X","POST",API,
        "-H","Content-Type: application/json","-d",json.dumps(payload)],
        capture_output=True, text=True)
    try: return json.loads(p.stdout)
    except Exception as e: print("parse err", e, p.stdout[:200]); return None

def fetch(filters, label):
    rows=[]
    for page in range(1,6):
        payload={"filters":filters,
            "fields":["Award ID","Recipient Name","Awarding Agency",
                "Awarding Sub Agency","Award Amount","Description",
                "Start Date","End Date","Award Type"],
            "page":page,"limit":100,"sort":"Award Amount","order":"desc","subawards":False}
        d=post(payload)
        if not d or not d.get("results"): break
        rows.extend(d["results"])
        if not d.get("page_metadata",{}).get("hasNext"): break
        time.sleep(0.4)
    return rows

def report(label, rows, show=8):
    total=sum((r.get("Award Amount") or 0) for r in rows)
    byag={}
    for r in rows:
        a=r.get("Awarding Agency","?"); byag[a]=byag.get(a,0)+(r.get("Award Amount") or 0)
    print(f"\n===== {label}: {len(rows)} contract awards, TOTAL = ${total:,.0f} =====")
    for a,amt in sorted(byag.items(),key=lambda x:-x[1])[:8]:
        print(f"    ${amt:>15,.0f} | {a}")
    print("  -- top awards --")
    for r in rows[:show]:
        print(f"    ${(r.get('Award Amount') or 0):>13,.0f} | {r.get('Awarding Agency','?'):<30.30} | {(r.get('Description') or '')[:48]}")
    return total, byag

out={}
# AI-pure vendors: recipient name is meaningful
for v in ["OpenAI","Anthropic","Palantir"]:
    rows=fetch({"time_period":TIME,"recipient_search_text":[v],"award_type_codes":CONTRACTS}, v)
    out[v]=rows; report(v, rows)

# Microsoft / Google: recipient totals dominated by non-AI. Narrow with keywords.
for v,kw in [("Microsoft",["Copilot"]),("Google",["Gemini"])]:
    rows=fetch({"time_period":TIME,"recipient_search_text":[v],"keywords":kw,"award_type_codes":CONTRACTS}, f"{v}+kw{kw}")
    out[f"{v}_kw"]=rows; report(f"{v} (recipient={v}, keyword={kw})", rows, show=6)

json.dump(out, open("usaspending_ai_vendors_raw.json","w"), indent=2)
print("\nsaved usaspending_ai_vendors_raw.json")
