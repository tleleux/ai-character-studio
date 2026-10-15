#!/usr/bin/env python3
"""update-reel.py — swap the demo reel on the AI Character Studio site WITHOUT touching anything else.
Run on the VPS (python3 + ffmpeg):
  python3 update-reel.py --site /root/.openclaw/workspace/knowledge/playbooks/ai-character-studio/guide-site \
     --reel-dir /root/.openclaw/workspace/outputs/ai-characters/nadia-marin/reel-003 \
     --name "Reel 003 · Read the COA (podcast studio)" --duration "2 clips" \
     --route "designed voice measured before render → podcast start frame → wan2_7 → captions → gate" \
     [--char-id nadia-marin-podcast | nadia-marin-apartment | ty-leleux-twin] [--page2 /path/to/new/page2.png] [--sheet /path/to/sheet.png]
Then publish:  bash PUBLISH-TO-GITHUB-PAGES.sh
It: copies <reel-dir>/final-discord.mp4 (or final.mp4) → assets/<reel-id>.mp4, reads score.md (overall + dimensions) and script.md (clip lines),
moves the current outputs.reel into outputs.history[], writes outputs.reel, regenerates characters/index.js from every characters/*.json.
"""
import argparse, json, os, re, shutil, subprocess, sys
ap=argparse.ArgumentParser(); ap.add_argument("--site",required=True); ap.add_argument("--reel-dir",required=True); ap.add_argument("--name",required=True)
ap.add_argument("--duration",default=""); ap.add_argument("--route",default=""); ap.add_argument("--page2"); ap.add_argument("--sheet"); ap.add_argument("--note",default=""); ap.add_argument("--char-id",default="nadia-marin-podcast",help="which characters/<id>.json to update")
a=ap.parse_args()
site=a.site; rd=a.reel_dir; rid=os.path.basename(rd.rstrip("/"))
src=next((os.path.join(rd,f) for f in ("final-discord.mp4","final.mp4") if os.path.exists(os.path.join(rd,f))),None)
if not src: sys.exit("no final-discord.mp4 / final.mp4 in "+rd)
os.makedirs(os.path.join(site,"assets"),exist_ok=True); dst=os.path.join(site,"assets",rid+".mp4"); shutil.copyfile(src,dst)
score=None; sm=os.path.join(rd,"score.md")
if os.path.exists(sm):
    t=open(sm).read(); m=re.search(r"Overall:\s*\**\s*([\d.]+)",t); ov=round(float(m.group(1))) if m else None
    dims={}
    for k,v in re.findall(r"^\|\s*(motion|face|voice_prosody|voice_quality|edit_rhythm|script)\s*\|\s*([\d.]+)\s*\|",t,re.M): dims[k.replace("_"," ")]=round(float(v))
    if ov is not None: score={"overall":ov,"pass":ov>=70 and all(x>=55 for x in dims.values()),"dims":dims}
script=""; sc=os.path.join(rd,"script.md")
if os.path.exists(sc):
    lines=re.findall(r"^\|\s*C(\d)-\d\s*\|\s*(.+?)\s*\|",open(sc).read(),re.M)
    clips={}
    for c,l in lines: clips.setdefault(c,[]).append(l)
    script="  ".join(f"Clip {c}: {' '.join(v)}" for c,v in sorted(clips.items()))
measured=""
for f in ("REEL-%s-NOTES.md"%rid.split('-')[-1].zfill(3),"notes.md","score.log"):
    pth=os.path.join(rd,f)
    if os.path.exists(pth):
        m=re.search(r"Measured:\s*(.+)",open(pth).read())
        if m: measured=m.group(1).strip(); break
jp=os.path.join(site,"characters",a.char_id+".json"); d=json.load(open(jp))
out=d.setdefault("outputs",{}); prev=out.get("reel")
if prev and prev.get("file")!="assets/"+rid+".mp4":
    prev=dict(prev); prev["note"]=prev.get("note") or "earlier render, kept as history"; out.setdefault("history",[]).insert(0,prev)
out["reel"]={"name":a.name,"file":"assets/"+rid+".mp4","duration":a.duration,"route":a.route,"score":score,"measured":measured,"script":script,"openFixes":""}
if a.note: out["reel"]["note"]=a.note
if a.page2 and os.path.exists(a.page2):
    subprocess.run(["ffmpeg","-y","-v","error","-i",a.page2,"-vf","scale=1800:-1","-q:v","3",os.path.join(site,"assets","page2.jpg")],check=True)
    subprocess.run(["ffmpeg","-y","-v","error","-i",a.page2,"-vf","crop=640:800:2040:700,scale=520:-1","-q:v","4",os.path.join(site,"assets","perf.jpg")],check=True)
if a.sheet and os.path.exists(a.sheet):
    subprocess.run(["ffmpeg","-y","-v","error","-i",a.sheet,"-vf","scale=1800:-1","-q:v","4",os.path.join(site,"assets","sheet.jpg")],check=True)
d["updated"]=__import__("datetime").date.today().isoformat()
json.dump(d,open(jp,"w"),indent=1,ensure_ascii=False)
order=["nadia-marin-podcast","nadia-marin-apartment","ty-leleux-twin"]
files=[f for f in order if os.path.exists(os.path.join(site,"characters",f+".json"))]+sorted(f[:-5] for f in os.listdir(os.path.join(site,"characters")) if f.endswith(".json") and f[:-5] not in order)
open(os.path.join(site,"characters","index.js"),"w").write("window.ACS_BUNDLED=["+",".join(json.dumps(json.load(open(os.path.join(site,"characters",f+".json"))),ensure_ascii=False) for f in files)+"];")
print("reel swapped:",out["reel"]["file"],"score",score,"| history:",len(out.get("history",[])),"| now run PUBLISH-TO-GITHUB-PAGES.sh")
