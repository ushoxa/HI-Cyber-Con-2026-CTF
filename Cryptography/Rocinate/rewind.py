import json
from recover import untemper,temper,twist,MASK,A,B,N,Z,C,T
D=json.load(open('work/mt.json'));positions={int(k):v for k,v in D['positions'].items()};U=D['U']
known={}

def put(i,value,mask=MASK):
 old,oldmask=known.get(i,(0,0))
 assert ((old^value)&oldmask&mask)==0, ('conflict',i)
 if mask&~oldmask:
  known[i]=((old&oldmask)|(value&mask),oldmask|mask)
  return 1
 return 0
for j,p in positions.items():
 for k in range(63):put(p*64+k,U[j][k])

def invtwist(v):
 low=v>>31
 return (((v^(low*0x9908b0df))<<1)|low)&MASK

lo=-3000;hi=max(known)
for cycle in range(100):
 changed=0
 for i in range(lo,hi-623):
  x,xm=known.get(i,(0,0));y,ym=known.get(i+1,(0,0));z,zm=known.get(i+397,(0,0));w,wm=known.get(i+624,(0,0))
  if zm==wm==MASK:
   v=invtwist(z^w)
   changed+=put(i,v,0x80000000);changed+=put(i+1,v,0x7fffffff)
  if xm&0x80000000 and ym&0x7fffffff==0x7fffffff:
   v=twist(x,y)
   if zm==MASK:changed+=put(i+624,z^v)
   if wm==MASK:changed+=put(i+397,w^v)
 print('cycle',cycle,'updates',changed,'full',sum(m==MASK for _,m in known.values()))
 if not changed:break
json.dump({str(k):v for k,v in known.items()},open('work/state.json','w'))
print('backwards blocks:')
for p in range(-20,1):
 vals=[known.get(p*64+k,(0,0)) for k in range(64)]
 if not all(m==MASK for _,m in vals):
  print(p,'missing bits:',sum(32-m.bit_count() for _,m in vals));continue
 words=[temper(v) for v,_ in vals]
 v=sum(w<<(32*k) for k,w in enumerate(words[:63]))+((words[63]>>1)<<(32*63))+1
 label=next((label for label,target in [('a',A),('b',B),('C0',C[0]),('C1',C[1])] if v==target),'accepted' if v<=N else 'rejected')
 print(p,label,str(v)[:35])
