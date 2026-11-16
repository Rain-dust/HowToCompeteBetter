"""Anytime-valid dual likelihood evidence; no observations are asserted."""
import numpy as np
from scipy.stats import binom
from utils import init,save,csv,read

def boundaries(n):
    k=np.arange(n+1)
    reject=k*np.log(2)+(n-k)*np.log(.8/.9)>=np.log(20)-1e-12
    accept=k*np.log(.5)+(n-k)*np.log(.95/.9)>=np.log(10)-1e-12
    assert not (reject&accept).any()
    return reject,accept

def exact_oc(p,cap=2000):
    mass=np.ones(1); A=R=EN=0.
    for n in range(1,cap+1):
        EN+=mass.sum()
        nxt=np.zeros(n+1)
        nxt[:-1]+=mass*(1-p)
        nxt[1:]+=mass*p
        reject,accept=boundaries(n)
        R+=nxt[reject].sum(); A+=nxt[accept].sum()
        nxt[reject|accept]=0; mass=nxt
    return {'p':float(p),'accept':float(A),'reject':float(R),'inconclusive':float(mass.sum()),'expected_tests_capped':float(EN)}

def main():
    init()
    out={'design':read('inputs/parameters.json')['sampling_design'],
         'interpretation':'No observed sample: all paths are conditional design examples.',
         'fixed_single_look':{'earliest_all_defective_reject_n':2,'reject_tail':float(binom.sf(1,2,.1)),
           'earliest_zero_defect_accept_n':22,'accept_tail':float(binom.cdf(0,22,.1)),
           'n22_reject_at_least':next(k for k in range(23) if binom.sf(k-1,22,.1)<=.05)},
         'sequential_earliest_reject_n':next(n for n in range(1,2001) if boundaries(n)[0][-1]),
         'sequential_earliest_accept_n':next(n for n in range(1,2001) if boundaries(n)[1][0])}
    rows=[exact_oc(p) for p in np.linspace(0,.3,31)]
    out['oc']=rows
    out['risk_at_p0']=next(r for r in rows if abs(r['p']-.1)<1e-9)
    save('results/q1.json',out); csv('results/q1_oc.csv',rows)
    brows=[]
    for n in range(1,2001):
        r,a=boundaries(n)
        brows.append({'n':n,'reject_k_min':int(np.flatnonzero(r)[0]) if r.any() else None,
                      'accept_k_max':int(np.flatnonzero(a)[-1]) if a.any() else None})
    csv('results/q1_boundaries.csv',brows)
    print('Q1',out['fixed_single_look'],out['risk_at_p0'])
if __name__=='__main__':main()
