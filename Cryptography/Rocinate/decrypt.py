import json, math
from recover import temper,A,B,N,Z,C,T
state={int(k):v for k,v in json.load(open('work/state.json')).items()}
def draw(p):
 words=[]
 for k in range(64):
  v,m=state[64*p+k];assert m==2**32-1
  words.append(temper(v))
 return sum(w<<(32*k) for k,w in enumerate(words[:63]))+((words[63]>>1)<<(32*63))+1
assert draw(-4)==A and draw(-2)==B and draw(-1)==C[0]
e=draw(-5);r=draw(-6)
assert 1<=e<=N and 1<=r<=N
assert pow(r,e,N)==T[0]
R=[];V=[]
for z,t in zip(Z,T):
 assert z%r==0
 assert pow(r,e,N)==t
 R.append(r);V.append(z//r);r=(A*r+B)%N

def egcd(a,b):
 x0,x1,y0,y1=1,0,0,1
 while b:
  q,a,b=a//b,b,a%b;x0,x1=x1,x0-q*x1;y0,y1=y1,y0-q*y1
 return a,x0,y0

g=C[0];s=V[0]
for ci,vi in zip(C[1:],V[1:]):
 g,x,y=egcd(g,ci);s=pow(s,x,N)*pow(vi,y,N)%N
 if g==1:break
assert g==1
assert all(pow(s,ci,N)==vi for ci,vi in zip(C,V))
flag=s.to_bytes((s.bit_length()+7)//8,'big').decode()
assert flag.startswith('hiCTF{') and flag.endswith('}')
print('FLAG:',flag)
print('Verified all 100 LCG products, ciphertext powers, and T values.')
json.dump({'r':R[0],'e':e,'flag':flag},open('work/solution.json','w'))
