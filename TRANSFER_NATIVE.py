#!/usr/bin/env python3
import os, sys, json, urllib.request, urllib.error, subprocess, time
from datetime import datetime

SOURCE, TARGET = "CryptoTaxi247", "247TaxiDriver"

TOKEN = None
for m in [lambda: os.getenv("GITHUB_TOKEN"), lambda: subprocess.getoutput("git config --global github.token").strip()]:
    try:
        t = m()
        if t and (t.startswith("ghp_") or t.startswith("gho_")):
            TOKEN = t
            print(f"✅ Token: {t[:15]}...")
            break
    except: pass

if not TOKEN:
    TOKEN = input("Paste GitHub token: ").strip()
    if not TOKEN: sys.exit(1)

def api(url, method="GET", data=None):
    req = urllib.request.Request(url, headers={"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github.v3+json"}, method=method)
    if data: req.data = json.dumps(data).encode()
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, str(e)
    except Exception as e:
        return 0, str(e)

print("🔑 Testing token...")
s, d = api("https://api.github.com/user")
if s != 200:
    print(f"❌ Token failed: {s}")
    sys.exit(1)
print(f"✅ Authenticated: {d['login']}")

print(f"🔍 Scanning {SOURCE}...")
repos, page = [], 1
while page < 10:
    s, d = api(f"https://api.github.com/users/{SOURCE}/repos?per_page=100&page={page}")
    if s != 200 or not d: break
    repos.extend(d)
    page += 1
    if len(d) < 100: break

print(f"✅ Found {len(repos)} repos")

if not repos:
    print("❌ No repos!")
    sys.exit(1)

for i, r in enumerate(repos[:20], 1):
    print(f"  {{i}}. {{r['name']}}")
if len(repos) > 20: print(f"  ... +{{len(repos)-20}} more")

if input(f"\nTransfer {{len(repos)}} repos to {{TARGET}}? (YES): ").strip() != "YES":
    sys.exit(0)

ok, fail = [], []
for i, r in enumerate(repos, 1):
    n = r['name']
    print(f"\n[{{i}}/{{len(repos)}}] {{n}}")
    s, _ = api(f"https://api.github.com/repos/{{SOURCE}}/{{n}}/transfer", "POST", {"new_owner": TARGET})
    if s == 202:
        print(f"✅ Success")
        ok.append(n)
    else:
        print(f"❌ Failed ({{s}})")
        fail.append(n)
    time.sleep(3)

print(f"\n🎉 Done! ✅ {{len(ok)}} | ❌ {{len(fail)}}")
with open("manifest.json", "w") as f:
    json.dump({"transferred": ok, "failed": fail}, f, indent=2)
print("📄 manifest.json saved")