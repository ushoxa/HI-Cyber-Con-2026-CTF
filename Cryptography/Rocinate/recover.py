import json
from collections import defaultdict, deque
A,B,N,Z,C,T=json.load(open('work/data.json'))
MASK=(1<<32)-1

def undo_right(y,shift):
 x=y
 for _ in range(32//shift): x=y^(x>>shift)
 return x

def undo_left(y,shift,mask):
 x=y
 for _ in range(32//shift): x=y^((x<<shift)&mask)
 return x

def untemper(y):
 y=undo_right(y,18)
 y=undo_left(y,15,0xefc60000)
 y=undo_left(y,7,0x9d2c5680)
 return undo_right(y,11)

def temper(y):
 y^=y>>11;y^=(y<<7)&0x9d2c5680;y^=(y<<15)&0xefc60000;y^=y>>18
 return y
assert all(temper(untemper(x))==x for x in [0,1,0xffffffff,123456789])

def twist(x,y): return (((x&0x80000000)|(y&0x7fffffff))>>1)^((y&1)*0x9908b0df)

U=[[untemper(((c-1)>>(32*i))&MASK) for i in range(63)] for c in C]
graph=defaultdict(list)
for i in range(len(C)):
 for offset,jumpj,jumpk in [(0,6,9),(20,6,10),(51,7,10)]:
  uj=(offset+397)%64;uk=(offset+624)%64
  y=twist(U[i][offset],U[i][offset+1])
  lookup={U[k][uk]:k for k in range(i+2,min(len(C),i+jumpk+1))}
  for j in range(i+1,min(len(C),i+jumpj+1)):
   k=lookup.get(y^U[j][uj])
   if k is not None and k>j:
    graph[i].append((j,jumpj));graph[j].append((i,-jumpj))
    graph[i].append((k,jumpk));graph[k].append((i,-jumpk))
positions={1:0};queue=deque([1])
while queue:
 i=queue.popleft()
 for j,diff in graph[i]:
  p=positions[i]+diff
  if j in positions: assert positions[j]==p
  else: positions[j]=p;queue.append(j)
print('connected blocks:',len(positions),'of',len(C))
print('missing blocks:',[i for i in range(len(C)) if i not in positions])
print('positions:',sorted(positions.items()))
json.dump({'positions':positions,'U':U},open('work/mt.json','w'))
print('graph nodes, edges:',len(graph),sum(map(len,graph.values())))
for node in graph:
 if graph[node]: print('example:',node,graph[node][:6]);break
# Check reconstruction on locally generated samples.
import random
r=random.Random(123); xs=[r.getrandbits(32) for _ in range(1300)]
us=list(map(untemper,xs))
assert all(us[i+624]==us[i+397]^twist(us[i],us[i+1]) for i in range(676))
