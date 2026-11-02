import json,urllib.request,statistics,time
BASE="https://blind-index-1d830d29ece3.chall.hiddeninvestigations.net"
R=json.load(open("solve_result.json"))
S=dict(R["log"]); est=R["est"]
records=["517dd591a03c02a8ded1893b","a2c16097501047437c0a8375","5eada38cd20b5073965f0d53","9c51bb7dd67efc8ce08e8a90","2f4395416b295fb7d3ebb2a9","6cf7093681cbecf33b2ede1a","fe773709d5accbbfa8d304fd","58a3df67b3bc0af7c385f9ff","727618b716ce44ac2a173d58","71853b150a7c793b07ecbf9e"]
recset=set(records)
def sub(t,p,c): return t[:p]+c+t[p+1:]
def alt0(r,p):
    for c in "0123456789abcdef":
        if c!=r[p] and sub(r,p,c) not in recset: return c
def altf(r,p):  # different scheme: toward 'f'
    for c in "fedcba9876543210":
        if c!=r[p] and sub(r,p,c) not in recset: return c
PAIRS0=[(i,i+12) for i in range(12)]
PAIRSNEW=[(0,12),(2,14),(4,16),(6,18),(8,20),(10,22),(1,13),(3,15),(5,17),(7,19),(9,21),(11,23)]
def lookup(texts):
    texts=[t for t in texts if t not in S]
    rem=None
    for i in range(0,len(texts),32):
        chunk=texts[i:i+32]
        data=json.dumps({"texts":chunk}).encode()
        for attempt in range(8):
            try:
                req=urllib.request.Request(BASE+"/lookup",data=data,headers={"Content-Type":"application/json"})
                r=json.load(urllib.request.urlopen(req))
                break
            except urllib.error.HTTPError as e:
                if e.code==429:
                    time.sleep(3+2*attempt); continue
                raise
        for res in r["results"]: S[res["text"]]=res["score"]
        rem=r.get("lookups_remaining")
        time.sleep(1.5)
    return rem
def estimates(r,pairs,altfn):
    out=[]
    for (i,j) in pairs:
        ai=altfn(r,i); aj=altfn(r,j)
        si=sub(r,i,ai); sj=sub(r,j,aj); dij=sub(sub(r,i,ai),j,aj)
        out.append((si,sj,dij))
    return out

# which records to sharpen: the near-tie cluster
sharpen=["2f4395416b295fb7d3ebb2a9","71853b150a7c793b07ecbf9e","a2c16097501047437c0a8375"]
need=set()
plan={}
for r in sharpen:
    e=estimates(r,PAIRSNEW[:8],altf)  # 8 fresh far pairs, alt toward f
    plan[r]=e
    for si,sj,dij in e: need.update([si,sj,dij])
rem=lookup(sorted(need))
print("remaining after tiebreak queries:",rem)

# recompute full estimate set per record: original 12 (alt0) + new (altf, for sharpened)
allest={}
for r in records:
    vals=[]
    for (i,j) in PAIRS0:
        ai=alt0(r,i);aj=alt0(r,j)
        si=sub(r,i,ai);sj=sub(r,j,aj);dij=sub(sub(r,i,ai),j,aj)
        if si in S and sj in S and dij in S:
            vals.append(S[si]+S[sj]-S[dij])
    if r in plan:
        for si,sj,dij in plan[r]:
            vals.append(S[si]+S[sj]-S[dij])
    allest[r]=(statistics.median(vals),len(vals),statistics.pstdev(vals))

print("\nRefined estimates:")
for r in records:
    m,n,sd=allest[r]
    print(f"  {r} score={m:+.6f} n={n} std={sd:.5f} sem={sd/(n**0.5):.5f}")
order=sorted(records,key=lambda r:allest[r][0])
rankpos={r:idx for idx,r in enumerate(order)}
print("\nSorted low->high:")
for idx,r in enumerate(order): print(f"  pos{idx} {r} {allest[r][0]:+.6f}")
digits="".join(str(rankpos[r]) for r in records)
print("\nDigits:",digits,"\nFLAG: hiCTF{%s}"%digits)
sc=sorted(allest[r][0] for r in records)
print("min adjacent gap:",min(sc[k+1]-sc[k] for k in range(9)))
