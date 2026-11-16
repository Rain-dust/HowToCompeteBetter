"""Independent scalar / event simulation audit of an already finished numerical run.

No imports from the solution code. Writes only in independent-audit.
"""
import csv
import hashlib
import json
import math
from copy import deepcopy
from pathlib import Path

import numpy as np
from scipy.optimize import brentq
from scipy.stats import binom

HERE = Path(__file__).resolve().parent
RUN = HERE.parent
PARAM = json.loads((RUN/'inputs/parameters.json').read_text(encoding='utf-8-sig'))
CHECKS = []


def check(name, ok, detail=None):
    CHECKS.append({'name': name, 'pass': bool(ok), 'detail': detail})


def load(name):
    return json.loads((RUN/'results'/name).read_text(encoding='utf-8-sig'))


def raw(p, c, t, bit):
    return dict(p=p,c=c,t=t,bit=bit,children=[])


def stage(p, a, t, d, bit, recycle, children):
    return dict(p=p,a=a,t=t,d=d,bit=bit,recycle=recycle,children=children)


def make(case=None):
    if case is not None:
        r=dict(zip(PARAM['table1_columns'],PARAM['table1'][case-1]))
        ch=[raw(r[f'p{i}'],r[f'c{i}'],r[f't{i}'],i-1) for i in (1,2)]
        return stage(r['pf'],r['assembly'],r['tf'],r['dismantle'],2,3,ch),4,r['price'],r['loss']
    ch=[raw(p,c,t,i) for i,(p,c,t) in enumerate(PARAM['table2_parts'])]
    groups=[stage(p,a,t,d,8+j,11+j,[ch[i-1] for i in g])
            for j,(g,(p,a,t,d)) in enumerate(zip(PARAM['table2_groups_1based'],PARAM['table2_semis']))]
    r=PARAM['table2_final']
    return stage(r['p'],r['assembly'],r['test'],r['dismantle'],14,15,groups),16,r['price'],r['loss']


def post(root):
    return [x for c in root['children'] for x in post(c)]+[root]


def scalar(root, policy, loss):
    # (expected delivery-to-parent cost, delivery quality, proper)
    def rec(n, final=False):
        tested=bool(policy & (1 << n['bit']))
        p=n['p']
        if not n['children']:
            if tested:
                return ((n['c']+n['t'])/(1-p),1.0,True) if p<1 else (math.inf,1,False)
            return n['c'],1-p,True
        values=[rec(c) for c in n['children']]
        if not all(v[2] for v in values): return math.inf,0,False
        purchased=sum(v[0] for v in values)
        child_quality=math.prod(v[1] for v in values)
        success=(1-p)*child_quality
        recycle=bool(policy & (1 << n['recycle'])) and (final or tested)
        if recycle:
            if child_quality<1-1e-12 or p>=1: return math.inf,1,False
            reinspection=sum(c['t'] for c in n['children'] if policy & (1 << c['bit']))
            per_failure=n['d']+reinspection+(loss if final and not tested else 0)
            cost=purchased+(n['a']+tested*n['t']+p*per_failure)/(1-p)
        elif final or tested:
            if success<=0: return math.inf,1,False
            customer=(1-success)*loss if final and not tested else 0
            cost=(purchased+n['a']+tested*n['t']+customer)/success
        else:
            cost=purchased+n['a']
        return cost,1.0 if tested or final else success,True
    return rec(root,True)


def enumerate_scalar(root, bits, loss):
    return np.array([scalar(root,p,loss)[0] for p in range(1<<bits)])


def physical_mc(root, policy, loss, count, seed):
    """Stores physical quality; assembly draws only process quality anew."""
    rng=np.random.default_rng(seed)
    totals=np.empty(count)
    for j in range(count):
        account=[0.0]
        def provide(n, held=None, final=False):
            while True:
                if held is None:
                    if not n['children']:
                        account[0]+=n['c']
                        item=(rng.random()>n['p'],())
                    else:
                        kids=tuple(provide(c) for c in n['children'])
                        account[0]+=n['a']
                        good_process=rng.random()>n['p']
                        item=(all(k[0] for k in kids) and good_process,kids)
                else:
                    item=held;held=None
                tested=bool(policy & (1 << n['bit']))
                if tested: account[0]+=n['t']
                if item[0] or (not final and not tested): return item
                if final and not tested: account[0]+=loss
                if n['children'] and policy & (1 << n['recycle']):
                    account[0]+=n['d']
                    kids=tuple(provide(c,k) for c,k in zip(n['children'],item[1]))
                    account[0]+=n['a']
                    good_process=rng.random()>n['p']
                    held=(all(k[0] for k in kids) and good_process,kids)
        provide(root,final=True)
        totals[j]=account[0]
    mean=float(totals.mean());se=float(totals.std(ddof=1)/math.sqrt(count))
    exact=scalar(root,policy,loss)[0]
    z=abs(mean-exact)/se if se else (0 if abs(mean-exact)<1e-10 else math.inf)
    return dict(policy=policy,trials=count,seed=seed,exact=exact,mean=mean,standard_error=se,z=z)


def q1audit():
    result=load('q1.json')
    # Integer count barriers derived from two log likelihood ratio inequalities.
    cap=2000
    reject=[None];accept=[None]
    for n in range(1,cap+1):
        rr=math.ceil((math.log(20)-n*math.log(8/9))/math.log(2/(8/9))-1e-12)
        aa=math.floor((n*math.log(19/18)-math.log(10))/math.log((19/18)/.5)+1e-12)
        reject.append(rr if rr<=n else None)
        accept.append(aa if aa>=0 else None)
    with (RUN/'results/q1_boundaries.csv').open(encoding='utf-8-sig',newline='') as f:
        rows=list(csv.DictReader(f))
    check('Q1 all 2000 sequential count barriers',all(
        (int(r['reject_k_min']) if r['reject_k_min'] else None)==reject[int(r['n'])] and
        (int(r['accept_k_max']) if r['accept_k_max'] else None)==accept[int(r['n'])] for r in rows))
    maxdiff=0
    for row in result['oc']:
        p=row['p'];mass=np.array([1.]);a=r=en=0.
        for n in range(1,cap+1):
            en+=float(mass.sum())
            mass=np.convolve(mass,[1-p,p])
            if reject[n] is not None:
                r+=float(mass[reject[n]:].sum());mass[reject[n]:]=0
            if accept[n] is not None:
                a+=float(mass[:accept[n]+1].sum());mass[:accept[n]+1]=0
        diff=max(abs(a-row['accept']),abs(r-row['reject']),abs(mass.sum()-row['inconclusive']),abs(en-row['expected_tests_capped']))
        maxdiff=max(maxdiff,float(diff))
    check('Q1 31 exact OC rows recomputed via integer barriers',maxdiff<1e-9,{'max_abs_difference':maxdiff})
    check('Q1 fixed sample exact tests',result['fixed_single_look']['earliest_all_defective_reject_n']==2 and result['fixed_single_look']['earliest_zero_defect_accept_n']==22 and result['fixed_single_look']['n22_reject_at_least']==6)
    check('Q1 anytime risk at boundary',result['risk_at_p0']['reject']<.05 and result['risk_at_p0']['accept']<.1,result['risk_at_p0'])
    mc_rows=[]
    for seed,p in enumerate([.05,.1,.2],198721):
        rng=np.random.default_rng(seed);count=25000
        k=np.zeros(count,dtype=int);active=np.ones(count,dtype=bool)
        stopped=np.zeros(count,dtype=int);time=np.full(count,cap)
        for n in range(1,cap+1):
            idx=np.flatnonzero(active)
            if not len(idx): break
            k[idx]+=rng.binomial(1,p,len(idx))
            if reject[n] is not None:
                chosen=idx[k[idx]>=reject[n]]
                stopped[chosen]=2;time[chosen]=n;active[chosen]=False
            if accept[n] is not None:
                chosen=idx[k[idx]<=accept[n]]
                stopped[chosen]=1;time[chosen]=n;active[chosen]=False
        exact=min(result['oc'],key=lambda x:abs(x['p']-p))
        row={'p':p,'trials':count,'seed':seed}
        for status,name in [(0,'inconclusive'),(1,'accept'),(2,'reject')]:
            freq=float(np.mean(stopped==status));row[name]=freq
            se=math.sqrt(max(exact[name]*(1-exact[name]),1e-8)/count)
            check(f'Q1 independent MC p={p} {name}',abs(freq-exact[name])<5*se+1/count,{'simulation':freq,'exact':exact[name]})
        row['mean_tests']=float(time.mean());se=float(time.std(ddof=1)/math.sqrt(count))
        check(f'Q1 independent MC p={p} stopping mean',abs(row['mean_tests']-exact['expected_tests_capped'])<5*se,{'simulation':row['mean_tests'],'exact':exact['expected_tests_capped'],'standard_error':se})
        mc_rows.append(row)
    return {'at_p0':result['risk_at_p0'],'max_exact_OC_difference':maxdiff,
        'independent_simulations':mc_rows,
        'risk_proof':'For p<=.1, E[2^X(8/9)^(1-X)]<=1. For p>=.1, E[(1/2)^X(19/18)^(1-X)]<=1. Ville bounds are .05 and .1; intersecting stopping rules cannot increase either error.',
        'limits':['p_reject_alternative=.2 and p_accept_alternative=.05 are design choices, not data.','No uniformly minimum sample-size claim is justified.','At n=2000 the procedure retains an inconclusive outcome; near p=.1 most batches remain inconclusive.']}


def audit_tables():
    details=[]
    all_mc=[]
    for target,case,file in [(f'q2:{i}',i,f'q2_case{i}_policies.csv') for i in range(1,7)]+[('q3',None,'q3_policies.csv')]:
        root,bits,price,loss=make(case)
        exact=enumerate_scalar(root,bits,loss)
        with (RUN/'results'/file).open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
        diffs=[];proper_ok=True;bit_ok=True
        for row in rows:
            i=int(row['policy_id']);isproper=math.isfinite(exact[i])
            proper_ok &= isproper==(row['proper'].lower()=='true')
            bit_ok &= row['bits']==''.join(str((i>>k)&1) for k in range(bits))
            if isproper: diffs.append(abs(float(row['cost'])-exact[i]))
        maximum=max(diffs)
        best_id=int(np.argmin(exact));best=float(exact[best_id])
        official=load('q2.json')[case-1] if case else load('q3.json')
        check(target+' all policy cost rows',len(rows)==1<<bits and maximum<1e-9 and proper_ok and bit_ok,
              {'encodings':len(rows),'proper':int(np.isfinite(exact).sum()),'max_abs_error':maximum})
        check(target+' minimizer and tie set',best_id==official['policy_id'] and abs(best-official['cost'])<1e-9 and
              np.flatnonzero(np.isclose(exact,best,rtol=0,atol=1e-9)).tolist()==official['tied_encodings'])
        record=dict(target=target,best_policy=best_id,best_cost=best,best_profit=price-best,proper=int(np.isfinite(exact).sum()),max_error=maximum)
        details.append(record)
        chosen=np.flatnonzero(np.isfinite(exact)).tolist() if case else [0,best_id,65535,18431,40959]
        for i in chosen:
            mc=physical_mc(root,i,loss,4000 if case else 8000,16781+(case or 10)*100000+i)
            mc['target']=target;all_mc.append(mc)
            check(target+f' independent physical MC policy {i}',mc['z']<5,mc)
    return details,all_mc


def cp_by_inversion(k,n,tail):
    lo=0.0 if k==0 else brentq(lambda p:binom.sf(k-1,n,p)-tail,1e-14,1-1e-14,xtol=1e-13)
    hi=1.0 if k==n else brentq(lambda p:binom.cdf(k,n,p)-tail,1e-14,1-1e-14,xtol=1e-13)
    return lo,hi


def q4audit():
    records=[];mc=[];rng=np.random.default_rng(17783)
    for rec in load('q4.json'):
        case=None if rec['target']=='q3' else int(rec['target'].split(':')[1])
        root,bits,price,loss=make(case);nn=post(root);d=len(nn);N=rec['N_per_node']
        label=rec['target']+f' N={N}'
        lo=[];hi=[];maxdiff=0.;marg=[]
        for node,row in zip(nn,rec['intervals']):
            low,high=cp_by_inversion(row['k'],row['n'],.05/(2*d))
            maxdiff=max(maxdiff,abs(low-row['lower']),abs(high-row['upper']))
            lo.append(low);hi.append(high)
            ks=np.arange(N+1)
            # Coverage via equivalent inverted-tail acceptance region, no beta ppf.
            covered=(binom.sf(ks-1,N,node['p'])>=.05/(2*d)-1e-13)&(binom.cdf(ks,N,node['p'])>=.05/(2*d)-1e-13)
            marg.append(float(binom.pmf(ks,N,node['p'])[covered].sum()))
        upper=deepcopy(root)
        for n,p in zip(post(upper),hi):n['p']=p
        values=enumerate_scalar(upper,bits,loss)
        best_id=int(np.argmin(values));worst=float(values[best_id])
        check('Q4 '+label+' inverse binomial CIs',maxdiff<1e-9,{'max_abs_error':maxdiff})
        check('Q4 '+label+' exhaustive upper-corner optimum',best_id==rec['robust']['policy_id'] and abs(worst-rec['robust']['cost'])<1e-8,{'policy':best_id,'cost':worst})
        max_cost=-math.inf
        for _ in range(1000):
            sample=deepcopy(root)
            for n,p in zip(post(sample),rng.uniform(lo,hi)):n['p']=float(p)
            max_cost=max(max_cost,scalar(sample,best_id,loss)[0])
        check('Q4 '+label+' 1000 interior points',max_cost<=worst+1e-9,{'max_sampled_cost':max_cost,'upper_cost':worst})
        cov=math.prod(marg)
        check('Q4 '+label+' joint fixed-n coverage under independent samples',cov>=.95,{'joint_exact':cov,'bonferroni_guarantee':.95})
        check('Q4 '+label+' hypothetical counts labelled',rec['count_status']=='HYPOTHETICAL_not_observed')
        sim=physical_mc(upper,best_id,loss,4000,87811+N+(case or 20));sim['target']=label;mc.append(sim)
        check('Q4 '+label+' independent physical MC',sim['z']<5,sim)
        records.append(dict(target=rec['target'],N=N,best_policy=best_id,worst_cost=worst,worst_profit=price-worst,exact_independent_joint_coverage=cov,max_CI_error=maxdiff))
    return records,mc


def boundaries_and_scope():
    root,b,price,loss=make(1)
    for n in post(root):n['p']=0
    check('Zero quality defects no tests',abs(scalar(root,0,loss)[0]-28)<1e-12)
    check('Zero quality defects all tests',abs(scalar(root,7,loss)[0]-36)<1e-12)
    root,b,price,loss=make(1)
    check('Persistent untested defect is improper',not scalar(root,8,loss)[2])
    zero_children=deepcopy(root)
    for c in zero_children['children']: c['p']=0
    # The raw parts need no tests, although positive-rate assembly can fail.
    # Returning those raw parts must not charge nonexistent test decisions.
    closed=22+(6+.1*(5+6))/.9
    check('Zero-defect untested children recycled without invented tests',abs(scalar(zero_children,8,loss)[0]-closed)<1e-12,{'closed_form_cost':closed})
    sim=physical_mc(zero_children,8,loss,20000,331982)
    check('Zero-defect children process-failure physical MC',sim['z']<5,sim)
    oracle=json.loads((HERE/'oracle-results.json').read_text(encoding='utf-8-sig'))
    for row in oracle['q2']['table1_no_dismantle_diagnostics']:
        root,b,price,loss=make(row['case'])
        for p in row['no_dismantle_policies']:
            pid=sum(int(bit)<<i for i,bit in enumerate(p['policy']))
            check(f"Existing blind oracle Q2 case{row['case']} policy{pid}",abs(scalar(root,pid,loss)[0]-p['cost_per_fulfilled'])<1e-10)
        expected=row['all_raw_tested_recycle_retest']['cost_per_fulfilled']
        check(f"Existing blind oracle Q2 tested recycle case{row['case']}",abs(scalar(root,15,loss)[0]-expected)<1e-10)
    root,b,price,loss=make()
    q3=oracle['q3'];best=load('q3.json')['cost']
    check('Existing blind oracle Q3 baseline',abs(scalar(root,0,loss)[0]-q3['no_inspection_no_dismantle_cost_per_fulfilled'])<1e-9)
    check('Existing blind oracle Q3 all tests no dismantling',abs(scalar(root,18431,loss)[0]-q3['feasible_all_test_no_dismantle_cost_per_fulfilled'])<1e-9)
    check('Existing blind oracle Q3 optimistic bound',q3['optimistic_cost_lower_bound']<=best<=q3['feasible_all_test_no_dismantle_cost_per_fulfilled'])
    # A constructive counterexample to an unrestricted optimum claim: do not pay
    # for retesting physically known-good recovered parts after process failure.
    # This is outside the audited fixed-station reinspection class.
    gains=[]
    formal=load('q2.json')
    for case in [1,2,3,4]:
        root,b,price,loss=make(case)
        pid=formal[case-1]['policy_id']
        saving=root['p']/(1-root['p'])*sum(c['t'] for c in root['children'])
        gains.append({'case':case,'fixed_station_policy':pid,'fixed_station_cost':formal[case-1]['cost'],
                      'known_good_reinspection_omitted_feasible_cost':formal[case-1]['cost']-saving,'saving':saving})
    return gains


def main():
    q1=q1audit()
    tables,mc=audit_tables()
    q4,mc4=q4audit()
    counter=boundaries_and_scope()
    formal=load('validation.json')
    check('Formal validation reports internally consistent passing checks',formal['all_pass'] and formal['passed']==formal['total'] and formal['total']>0 and all(c['pass'] for c in formal['checks']),{'passed':formal['passed'],'total':formal['total']})
    result={'status':'passed_with_explicit_model_scope' if all(c['pass'] for c in CHECKS) else 'failed',
            'audit_method':'Independent scalar enumeration, integer-barrier sequential recursion, binomial-tail CI inversion, and new physical event simulations. No solution modules imported.',
            'pass_count':sum(c['pass'] for c in CHECKS),'check_count':len(CHECKS),
            'q1':q1,'policy_tables':tables,'q4':q4,'simulations':mc+mc4,
            'scope_counterexamples':counter,
            'limits':['Only fixed station tests/disassembly with mandatory return through direct-child stations were audited. No claim of optimality over arbitrary history-dependent, pooled-inventory, or known-good-exemption policies.',
                      'Assembly defect rates are conditional on all direct children being good; recovered item qualities persist; process failures redraw at new assembly.',
                      'Price is received once per fulfilled order. L is an extra return/replacement loss; new-production costs are charged separately.',
                      'Q4 has no actual observed n/k. Counts 100/400 per node are hypothetical; the confidence guarantee is per target and assumes prespecified fixed n and representative binomial data for each conditional defect rate.',
                      'Bonferroni simultaneous coverage does not require independent node samples; the product coverage calculation additionally assumes independent samples.',
                      'Upper-corner robustness is conditional on the specified rectangular confidence set and monotone cost within the audited proper-policy class; it is not a probability that a numerical profit will be realized.',
                      'Monte Carlo 5-standard-error comparisons are numerical diagnostics, not theorem proofs or prizes.'],
            'checks':CHECKS}
    snapshot_paths=[RUN/'inputs/parameters.json']+sorted((RUN/'results').glob('*'))+sorted((RUN/'code').glob('*.py'))
    result['source_snapshot_sha256']={str(p.relative_to(RUN)):hashlib.sha256(p.read_bytes()).hexdigest() for p in snapshot_paths if p.is_file()}
    (HERE/'audit-review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],'passed':result['pass_count'],'checks':result['check_count'],'max_mc_z':max(s['z'] for s in mc+mc4),'policy_tables':tables,'failures':[c for c in CHECKS if not c['pass']]},ensure_ascii=False,indent=2))


if __name__=='__main__': main()
