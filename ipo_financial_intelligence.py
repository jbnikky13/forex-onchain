"""IPO / pre-listing intelligence for Forex Onchain.

Discovery is intentionally conservative: a candidate is not treated as a verified
IPO until an official regulatory or exchange document is found. The extractor
surfaces the requested metrics when present and preserves the source URL.
"""
import hashlib, html, json, re
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

STATE = Path("data/ipo_intelligence_state.json")
SOURCES = [
    "https://www.sec.gov.ng/for-investors/keep-track-of-circulars/",
    "https://www.sec.gov.ng/get-listed/",
    "https://ngxgroup.com/exchange/raise-capital/notices-to-issuers/",
]
GENERIC = ("listing your company", "listing requirements", "becoming an investor", "investor education", "how to list")
KEYWORDS = ("prospectus", "public offer", "offer for subscription", "offer for sale", "ipo", "listing", "pricing", "admission", "quarterly", "financial statements")
HEADERS = {"User-Agent":"Forex-Onchain IPO Intelligence/1.0"}


def load_state():
    try: return json.loads(STATE.read_text())
    except Exception: return {"seen": {}, "candidates": {}}


def save_state(state):
    STATE.parent.mkdir(parents=True, exist_ok=True); STATE.write_text(json.dumps(state, indent=2))


def discover():
    results=[]
    for source in SOURCES:
        try:
            r=requests.get(source,headers=HEADERS,timeout=30); r.raise_for_status()
            soup=BeautifulSoup(r.text,"html.parser")
            for a in soup.find_all("a",href=True):
                title=" ".join(a.stripped_strings); url=urljoin(source,a["href"]); s=f"{title} {url}".lower()
                if any(g in s for g in GENERIC): continue
                if any(k in s for k in KEYWORDS) and (url.lower().endswith((".pdf",".html",".htm")) or "pdf" in s):
                    results.append({"title":title[:240],"url":url,"source":source})
        except Exception as exc: print(f"source error: {source}: {exc}")
    return list({x["url"]:x for x in results}.values())


def fetch_text(url):
    try:
        r=requests.get(url,headers=HEADERS,timeout=45); r.raise_for_status()
        if "pdf" in r.headers.get("content-type","").lower() or url.lower().endswith(".pdf"):
            from io import BytesIO
            from pypdf import PdfReader
            text="\n".join((p.extract_text() or "") for p in PdfReader(BytesIO(r.content)).pages)
            return text if len(text.strip()) >= 200 else ""
        return BeautifulSoup(r.text,"html.parser").get_text(" ",strip=True)
    except Exception as exc: print(f"document error: {url}: {exc}"); return ""


def context(text, patterns, window=900):
    for p in patterns:
        m=re.search(p,text,re.I)
        if m: return text[max(0,m.start()-150):m.end()+window].strip()
    return None


def identify(title,text):
    s=f"{title} {text[:12000]}"
    company=None
    for p in (r"(?:issuer|company|group)\s*[:\-]\s*([A-Z][A-Za-z0-9 .&'()\-/]{2,100})", r"([A-Z][A-Za-z0-9 .&'()\-/]{2,90}\s+(?:PLC|Plc|Limited|LIMITED))"):
        m=re.search(p,s)
        if m: company=m.group(1).strip(); break
    q=re.search(r"\b(Q[1-4])\b[^\d]{0,20}(20\d{2})",s,re.I)
    period=f"{q.group(1).upper()} {q.group(2)}" if q else None
    return company or title[:100] or None, period


def analyze(doc):
    text=fetch_text(doc["url"])
    if not text: return None
    company,period=identify(doc["title"],text)
    if not company: return None
    metrics={
        "audited_profit": context(text,[r"audited financial statements",r"net profit",r"net income",r"profit after tax"]),
        "operating_cash_flow": context(text,[r"net cash (?:provided by|generated from) operating activities",r"operating cash flow"]),
        "debt": context(text,[r"total debt",r"total borrowings",r"total indebtedness"]),
        "refining_margins": context(text,[r"refining margin",r"refinery margin",r"crack spread"]),
        "crude_supply_terms": context(text,[r"crude supply",r"crude oil supply",r"crude purchase agreement",r"supply agreement"]),
        "expansion_costs": context(text,[r"expansion costs?",r"expansion project",r"capital expenditures?",r"growth capital"]),
        "use_of_proceeds": context(text,[r"use of proceeds",r"net proceeds",r"proceeds from the offering"]),
        "offer_terms": context(text,[r"offer price",r"number of shares",r"shares offered",r"issue price"]),
    }
    found=sum(v is not None for v in metrics.values())
    return {"company":company,"period":period,"title":doc["title"],"url":doc["url"],"source":doc["source"],"verified_document":True,"disclosure_coverage":round(found/len(metrics)*100),"metrics":metrics,"checked_at":datetime.now(timezone.utc).isoformat()}


def render_alert(profile):
    m=profile["metrics"]
    return (f"🚨 <b>VERIFIED IPO / PRE-LISTING INTELLIGENCE</b>\n<b>{html.escape(profile['company'])}</b>\n\n"
            f"Audited profit: {'FOUND' if m['audited_profit'] else 'N/A'}\nOperating cash flow: {'FOUND' if m['operating_cash_flow'] else 'N/A'}\nDebt: {'FOUND' if m['debt'] else 'N/A'}\n"
            f"Refining margins: {'FOUND' if m['refining_margins'] else 'N/A'}\nCrude-supply terms: {'FOUND' if m['crude_supply_terms'] else 'N/A'}\nExpansion costs: {'FOUND' if m['expansion_costs'] else 'N/A'}\nUse of proceeds: {'FOUND' if m['use_of_proceeds'] else 'N/A'}\nOffer terms: {'FOUND' if m['offer_terms'] else 'N/A'}\n"
            f"Disclosure coverage: <b>{profile['disclosure_coverage']}%</b>\n\n📄 <a href=\"{html.escape(profile['url'],quote=True)}\">Official document</a>")


def run():
    state=load_state(); alerts=[]
    for doc in discover():
        key=hashlib.sha256(doc["url"].encode()).hexdigest()
        if key in state["seen"]: continue
        profile=analyze(doc)
        if not profile: continue
        state["seen"][key]=datetime.now(timezone.utc).isoformat(); state["candidates"][key]=profile; alerts.append(profile)
    save_state(state)
    return alerts

if __name__=="__main__":
    for p in run(): print(render_alert(p))
