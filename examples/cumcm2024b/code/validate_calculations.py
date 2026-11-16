"""Independent stochastic checks plus boundary and exhaustive search invariants."""
import numpy as np
from scipy.stats import binom
from scipy.optimize import brentq
from utils import init,save,csv,read
from production import problem2_tree,problem3_tree,nodes,set_rates,evaluate,CATEGORIES
from simulate import simulate
from problem4 import intervals

def q1_sim(p,size=30000,seed=916):
    rng=np.random.default_rng(seed);k=np.zeros(size,dtype=int);active=np.ones(size,dtype=bool)
    state=np.zeros(size,dtype=int);times=np.full(size,2000)
    for n in range(1,2001):
        ids=np.flatnonzero(active)
        if not len(ids):break
        k[ids]+=rng.random(len(ids))<p
        # Formula written independently of problem1.boundaries and exact recursion.
        lr=k[ids]*np.log(.2/.1)+(n-k[ids])*np.log(.8/.9)
        la=k[ids]*np.log(.05/.1)+(n-k[ids])*np.log(.95/.9)
        hitr=ids[lr>=np.log(20)];hita=ids[la>=np.log(10)]
        state[hitr]=2;state[hita]=1
        active[hitr]=False;active[hita]=False;times[hitr]=n;times[hita]=n
    return {'p':p,'trials':size,'accept':float((state==1).mean()),'reject':float((state==2).mean()),
            'inconclusive':float((state==0).mean()),'mean_tests':float(times.mean()),
            'se_tests':float(times.std(ddof=1)/np.sqrt(size))}

def main():
    init();checks=[];simrows=[]
    def check(name,ok,detail):
        checks.append({'name':name,'pass':bool(ok),'detail':detail})
        if not ok: print('FAILED',name,detail)
    q1=read('results/q1.json');q2=read('results/q2.json');q3=read('results/q3.json');q4=read('results/q4.json')
    for j,p in enumerate([.05,.1,.2]):
        sim=q1_sim(p,seed=916+j);oc=min(q1['oc'],key=lambda x:abs(x['p']-p))
        for key in ['accept','reject','inconclusive']:
            se=np.sqrt(max(oc[key]*(1-oc[key]),1e-8)/sim['trials'])
            check(f'Q1 p={p} {key}',abs(sim[key]-oc[key])<5*se+1/sim['trials'],{'exact':oc[key],'simulation':sim[key]})
        check(f'Q1 p={p} stopping mean',abs(sim['mean_tests']-oc['expected_tests_capped'])<5*sim['se_tests'],sim)
        simrows.append({'question':'q1',**sim})
    for oc in q1['oc']:
        check(f'Q1 mass p={oc["p"]}',abs(oc['accept']+oc['reject']+oc['inconclusive']-1)<1e-11,'Forward absorption mass conservation')
        if oc['p']<=.1:check(f'Q1 rejection risk p={oc["p"]}',oc['reject']<=.05+1e-12,oc['reject'])
        if oc['p']>=.1:check(f'Q1 acceptance risk p={oc["p"]}',oc['accept']<=.1+1e-12,oc['accept'])
    check('Q1 minimum fixed acceptance',.9**21>.1 and .9**22<=.1,'21 cannot accept even at k=0; 22 can')
    check('Q1 minimum fixed rejection',.1>.05 and .1**2<=.05,'1 cannot reject even at k=n; 2 can')
    for case,ans in enumerate(q2,1):
        root,b,price,loss=problem2_tree(case)
        ids,bits,costs,vec,valid=evaluate(root,b,loss)
        check(f'Q2 case{case} exhaustive',ans['enumerated']==16 and ans['proper_encodings']==10 and abs(costs.min()-ans['cost'])<1e-10,ans)
        # Independently derive the no-detection/no-disassembly geometric fulfillment cost.
        p1,p2,pf=[n.p for n in nodes(root)]
        s=(1-p1)*(1-p2)*(1-pf)
        closed=(sum(c.c for c in root.children)+root.a+(1-s)*loss)/s
        check(f'Q2 case{case} closed baseline',abs(closed-costs[0])<1e-10,closed)
        for label,policy in [('best',ans['policy_id']),('baseline',0)]:
            sim=simulate(root,bits[policy].astype(int).tolist(),loss,orders=20000,seed=1200+case*10+policy)
            exact=float(costs[policy]);z=abs(sim['mean_cost']-exact)/sim['standard_error']
            check(f'Q2 case{case} {label} physical MC',z<5,{'exact':exact,'simulation':sim,'z':z})
            simrows.append({'question':f'q2:{case}','label':label,'exact':exact,'z':z,**sim})
    root,b,price,loss=problem3_tree();ids,bits,costs,vec,valid=evaluate(root,b,loss)
    check('Q3 enumeration',len(ids)==65536 and valid.sum()==17060 and np.argmin(costs)==q3['policy_id'],{'proper':int(valid.sum()),'argmin':int(np.argmin(costs))})
    for label,policy in [('best',q3['policy_id']),('baseline',0),('all_tests',65535),('next_best',q3['top10'][1]['policy_id'])]:
        sim=simulate(root,bits[policy].astype(int).tolist(),loss,orders=20000,seed=3300+policy)
        exact=float(costs[policy]);z=abs(sim['mean_cost']-exact)/sim['standard_error']
        check(f'Q3 {label} physical MC',z<5,{'exact':exact,'simulation':sim,'z':z})
        simrows.append({'question':'q3','label':label,'exact':exact,'z':z,**sim})
    check('Q3 component sum',abs(sum(q3['cost_components'].values())-q3['cost'])<1e-10,q3['cost_components'])
    rng=np.random.default_rng(444)
    coverage=[]
    for rec in q4:
        target,N=rec['target'],rec['N_per_node']
        root,b,price,loss=problem3_tree() if target=='q3' else problem2_tree(int(target.split(':')[1]))
        ns=nodes(root);lo=np.array([r['lower'] for r in rec['intervals']]);hi=np.array([r['upper'] for r in rec['intervals']])
        policy=rec['robust']['policy_id'];upper=set_rates(root,hi)
        worst=float(evaluate(upper,b,loss,[policy])[2][0])
        maxsample=-np.inf
        for _ in range(500):
            rates=rng.uniform(lo,hi);cost=float(evaluate(set_rates(root,rates),b,loss,[policy])[2][0]);maxsample=max(maxsample,cost)
        check(f'Q4 {target} N{N} monotone corners',maxsample<=worst+1e-10,{'max_500_random':maxsample,'upper':worst})
        sim=simulate(upper,rec['robust']['bits'],loss,orders=10000,seed=4000+N+len(simrows))
        z=abs(sim['mean_cost']-worst)/sim['standard_error']
        check(f'Q4 {target} N{N} worst physical MC',z<5,{'exact':worst,'simulation':sim,'z':z})
        simrows.append({'question':f'q4:{target}:{N}','label':'upper_robust','exact':worst,'z':z,**sim})
        # CP table generated for all possible k, then independent binomial sampling.
        d=len(ns);table=intervals([{'n':N,'k':0}]*d) # check implementation boundary too
        alpha=.05/d
        from scipy.stats import beta
        ks=np.arange(N+1)
        ll=np.zeros(N+1);uu=np.ones(N+1)
        ll[1:]=beta.ppf(alpha/2,ks[1:],N-ks[1:]+1)
        uu[:-1]=beta.ppf(1-alpha/2,ks[:-1]+1,N-ks[:-1])
        p=np.array([n.p for n in ns]);draw=rng.binomial(N,p,size=(20000,d))
        hit=((ll[draw]<=p)&(uu[draw]>=p)).all(axis=1)
        exact_joint=float(np.prod([binom.pmf(ks,N,pp)[(ll<=pp)&(uu>=pp)].sum() for pp in p]))
        rate=float(hit.mean());coverage.append({'target':target,'N':N,'trials':20000,'joint_coverage_MC':rate,'joint_coverage_independent_exact':exact_joint})
        check(f'Q4 {target} N{N} coverage',exact_joint>=.95-1e-10 and abs(rate-exact_joint)<5*np.sqrt(exact_joint*(1-exact_joint)/20000)+1/20000,coverage[-1])
        # Invert binomial CDF by root finding instead of beta quantile as a cross-check.
        for row in rec['intervals']:
            n,k=row['n'],row['k']
            if 0<k<n:
                ll2=brentq(lambda p:binom.sf(k-1,n,p)-alpha/2,1e-14,1-1e-14)
                uu2=brentq(lambda p:binom.cdf(k,n,p)-alpha/2,1e-14,1-1e-14)
                check(f'Q4 inverse {target} {N} {row["node"]}',max(abs(ll2-row['lower']),abs(uu2-row['upper']))<1e-9,{'cdf_lower':ll2,'cdf_upper':uu2})
    # Boundary regimes: perfect quality and defective recycled input.
    zero=set_rates(problem2_tree(1)[0],[0,0,0])
    check('zero defects baseline cost',abs(evaluate(zero,4,6,[0])[2][0]-28)<1e-10,'22 purchase + 6 assembly')
    check('untested defective recycling improper',not bool(evaluate(problem2_tree(1)[0],4,6,[8])[4][0]),'Policy 0001 reuses untested bad components forever')
    save('results/validation.json',{'checks':checks,'passed':sum(c['pass'] for c in checks),'total':len(checks),'all_pass':all(c['pass'] for c in checks)})
    save('results/simulations.json',simrows);csv('results/simulations.csv',simrows);csv('results/q4_coverage.csv',coverage)
    print('VALIDATION',sum(c['pass'] for c in checks),'/',len(checks),'max production z',max(r.get('z',0) for r in simrows))
    if not all(c['pass'] for c in checks):raise SystemExit(1)
if __name__=='__main__':main()
