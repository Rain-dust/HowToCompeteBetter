"""Exact renewal costs for the explicitly defined fixed station policy class.

No quality resampling of recovered materials. A bad untested child that is
reused forever makes the fixed policy improper. Such policies are excluded.
"""
from dataclasses import dataclass
from copy import deepcopy
import numpy as np
from utils import read

CATEGORIES=['purchase','assembly','inspection','dismantling','replacement_loss']
@dataclass
class Node:
    name:str
    p:float
    t:float
    inspect:int
    c:float=0
    a:float=0
    d:float=0
    dismantle:int=-1
    children:tuple=()

def problem2_tree(case):
    raw=read('inputs/parameters.json')
    row=dict(zip(raw['table1_columns'],raw['table1'][case-1]))
    ch=tuple(Node(f'零件{i}',row[f'p{i}'],row[f't{i}'],i-1,c=row[f'c{i}']) for i in [1,2])
    root=Node('成品',row['pf'],row['tf'],2,a=row['assembly'],d=row['dismantle'],dismantle=3,children=ch)
    return root,4,row['price'],row['loss']

def problem3_tree():
    data=read('inputs/parameters.json')
    parts=[Node(f'零件{i+1}',p,t,i,c=c) for i,(p,c,t) in enumerate(data['table2_parts'])]
    semis=[]
    for j,(grp,(p,a,t,d)) in enumerate(zip(data['table2_groups_1based'],data['table2_semis'])):
        semis.append(Node(f'半成品{j+1}',p,t,8+j,a=a,d=d,dismantle=11+j,children=tuple(parts[i-1] for i in grp)))
    r=data['table2_final']
    return Node('成品',r['p'],r['test'],14,a=r['assembly'],d=r['dismantle'],dismantle=15,children=tuple(semis)),16,r['price'],r['loss']

def nodes(root):
    out=[]
    for c in root.children: out+=nodes(c)
    return out+[root]

def set_rates(root,rates):
    root=deepcopy(root)
    for n,p in zip(nodes(root),rates): n.p=float(p)
    return root

def evaluate(root,nbits,loss,ids=None):
    """Vectorized all policies; cost decomposition proves additive accounting."""
    ids=np.arange(1<<nbits,dtype=np.int64) if ids is None else np.asarray(ids,dtype=np.int64)
    bits=((ids[:,None]>>np.arange(nbits))&1).astype(bool)
    size=len(ids)
    def rec(n,isroot=False):
        y=bits[:,n.inspect]
        if not n.children:
            q=np.where(y,1.0,1-n.p)
            vec=np.zeros((size,5))
            vec[:,0]=n.c
            vec[:,2]=y*n.t
            denom=1-y*n.p
            vec/=denom[:,None]
            return vec,q,np.ones(size,dtype=bool)
        ch=[rec(c) for c in n.children]
        B=sum(x[0] for x in ch)
        qprod=np.prod([x[1] for x in ch],axis=0)
        s=(1-n.p)*qprod
        valid=np.logical_and.reduce([x[2] for x in ch])
        z=bits[:,n.dismantle]
        reuse=z if isroot else z&y
        valid &= ~(reuse & (qprod<1-1e-12))
        base=B.copy()
        base[:,1]+=n.a
        base[:,2]+=y*n.t
        if isroot:
            base[:,4]+=(~y)*(1-s)*loss
            with np.errstate(divide='ignore',invalid='ignore'): base/=s[:,None]
            q=np.ones(size)
        else:
            with np.errstate(divide='ignore',invalid='ignore'): base[y]/=s[y,None]
            q=np.where(y,1,s)
        if reuse.any():
            # Only known good direct children are reused. Charge their tests again.
            extra=np.zeros((size,5))
            extra[:,1]=n.a
            extra[:,2]=y*n.t+n.p*sum(bits[:,c.inspect]*c.t for c in n.children)
            extra[:,3]=n.p*n.d
            if isroot: extra[:,4]=n.p*(~y)*loss
            with np.errstate(divide='ignore',invalid='ignore'):
                val=B+extra/(1-n.p)
            base[reuse]=val[reuse]
        valid &= np.isfinite(base).all(axis=1)
        return base,q,valid
    vec,q,valid=rec(root,True)
    costs=vec.sum(axis=1)
    costs[~valid]=np.inf
    return ids,bits,costs,vec,valid

def solution(root,nbits,price,loss):
    ids,bits,costs,vec,valid=evaluate(root,nbits,loss)
    if not valid.any():
        return {'available':False,'reason':'No finite robust fulfillment cost'},(ids,bits,costs,vec,valid)
    i=int(np.argmin(costs))
    ties=ids[np.isclose(costs,costs[i],rtol=0,atol=1e-9)].tolist()
    result={'available':True,'policy_id':int(ids[i]),'bits':bits[i].astype(int).tolist(),
            'cost':float(costs[i]),'profit':float(price-costs[i]),'price':price,
            'cost_components':dict(zip(CATEGORIES,vec[i].tolist())),
            'enumerated':len(ids),'proper_encodings':int(valid.sum()),'tied_encodings':ties}
    return result,(ids,bits,costs,vec,valid)

def policy_table(root,nbits,price,loss):
    best,arr=solution(root,nbits,price,loss)
    ids,bits,cost,vec,valid=arr
    rows=[]
    for j,i in enumerate(ids):
        rows.append({'policy_id':int(i),'bits':''.join(str(int(b)) for b in bits[j]),
                     'proper':bool(valid[j]),'cost':float(cost[j]) if valid[j] else None,
                     'profit':float(price-cost[j]) if valid[j] else None})
    return best,rows
