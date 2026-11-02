import json,urllib.request,statistics,sys

BASE=sys.argv[1].rstrip("/") if len(sys.argv)>1 else "https://blind-index-<id>.chall.hiddeninvestigations.net"
H="0123456789abcdef"

def get(path):
    return json.load(urllib.request.urlopen(BASE+path))

def lookup(texts):
    out={}
    rem=None
    for i in range(0,len(texts),64):
        chunk=texts[i:i+64]
        data=json.dumps({"texts":chunk}).encode()
        req=urllib.request.Request(BASE+"/lookup",data=data,headers={"Content-Type":"application/json"})
        r=json.load(urllib.request.urlopen(req))
        for res in r["results"]:
            out[res["text"]]=res["score"]
        rem=r.get("lookups_remaining")
    return out,rem

status=get("/status"); print("status",status)
records=get("/records")["records"]; print("records",records)
recset=set(records)

def sub(t,p,c): return t[:p]+c+t[p+1:]
def alt(r,p):
    # choose a nibble != r[p], prefer '0' else '1'
    for c in "0123456789abcdef":
        if c!=r[p]:
            cand=sub(r,p,c)
            if cand not in recset:
                return c
    return None

PAIRS=[(i,i+12) for i in range(12)]   # 12 disjoint far-apart pairs

# build all needed texts
texts=set()
plan={}  # record -> list of (i,j, single_i_text, single_j_text, double_text)
for r in records:
    entries=[]
    for (i,j) in PAIRS:
        ai=alt(r,i); aj=alt(r,j)
        si=sub(r,i,ai); sj=sub(r,j,aj)
        dij=sub(sub(r,i,ai),j,aj)
        assert si not in recset and sj not in recset and dij not in recset
        texts.add(si); texts.add(sj); texts.add(dij)
        entries.append((i,j,si,sj,dij))
    plan[r]=entries

texts=sorted(texts)
print("total unique texts to query:",len(texts))
S,rem=lookup(texts)
print("lookups_remaining after:",rem)

est={}
spread={}
for r in records:
    vals=[]
    for (i,j,si,sj,dij) in plan[r]:
        vals.append(S[si]+S[sj]-S[dij])
    est[r]=statistics.median(vals)
    spread[r]=(min(vals),max(vals),statistics.pstdev(vals))

print("\nPer-record estimated score (median), [min,max,std of pair estimates]:")
for r in records:
    print(f"  {r}  score={est[r]:+.6f}   spread=[{spread[r][0]:+.5f},{spread[r][1]:+.5f}] std={spread[r][2]:.5f}")

# rank low->high, assign 0-indexed scale position
order=sorted(records,key=lambda r:est[r])
rankpos={r:idx for idx,r in enumerate(order)}
print("\nSorted low->high:")
for idx,r in enumerate(order):
    print(f"  pos{idx}  {r}  {est[r]:+.6f}")

digits="".join(str(rankpos[r]) for r in records)  # in original /records order
print("\nDigit string (ranks in /records order):",digits)
print("FLAG: hiCTF{%s}"%digits)

# check near-ties
sc=sorted(est.values())
mindiff=min(sc[k+1]-sc[k] for k in range(len(sc)-1))
print("\nmin adjacent score gap:",mindiff)
json.dump({"est":est,"digits":digits,"log":S,"rem":rem,"order":order},open("solve_result.json","w"))
