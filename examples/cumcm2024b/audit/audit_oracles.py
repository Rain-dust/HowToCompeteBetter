"""Independent finite diagnostic oracles, not a review or solution of the running model.
Reads no solver code/results. Synthetic boundaries are labelled as such.
"""
import json, math
from pathlib import Path
from itertools import product
from scipy.stats import binom, beta

OUT = Path(__file__).parent

def clean(x):
    if isinstance(x, float) and not math.isfinite(x):
        return 'infinite_or_infeasible'
    if isinstance(x, dict): return {k: clean(v) for k,v in x.items()}
    if isinstance(x, (list,tuple)): return [clean(v) for v in x]
    return x

def cp_bounds(x,n,alpha):
    assert isinstance(x,int) and isinstance(n,int) and 0 <= x <= n and n > 0
    lo = 0.0 if x==0 else float(beta.ppf(alpha,x,n-x+1))
    hi = 1.0 if x==n else float(beta.ppf(1-alpha,x+1,n-x))
    return lo,hi

def thresholds(n,p0=.1):
    accept = [x for x in range(n+1) if binom.cdf(x,n,p0) <= .1 + 1e-14]
    reject = [x for x in range(n+1) if binom.sf(x-1,n,p0) <= .05 + 1e-14]
    a = max(accept) if accept else None
    r = min(reject) if reject else None
    return {'n':n,'accept_if_x_le':a,'reject_if_x_ge':r,
            'accept_boundary_tail_at_p0':float(binom.cdf(a,n,p0)) if a is not None else None,
            'reject_boundary_tail_at_p0':float(binom.sf(r-1,n,p0)) if r is not None else None,
            'reject_power_at_p_0_2':float(binom.sf(r-1,n,.2)) if r is not None else 0.0}

def no_dismantle(p1,p2,pf,c1=4,c2=18,t1=2,t2=3,a=6,tf=3,R=56,L=6,x1=0,x2=0,z=0):
    # Perfect tests; tested raw parts are repurchased until good. Fresh purchases every failed assembly.
    if (x1 and p1>=1) or (x2 and p2>=1): return {'feasible':False,'cost_per_fulfilled':math.inf}
    g1=1.0 if x1 else 1-p1; g2=1.0 if x2 else 1-p2
    q=g1*g2*(1-pf)
    if q<=0: return {'feasible':False,'q':q,'cost_per_fulfilled':math.inf}
    procurement=(c1+x1*t1)/(1-x1*p1)+(c2+x2*t2)/(1-x2*p2)
    K=procurement+a+z*tf
    cost=(K+(1-z)*(1-q)*L)/q
    return {'feasible':True,'policy':[x1,x2,z,0],'q':q,'base_cost_per_attempt':K,
            'attempts_per_fulfilled':1/q,'failed_customer_deliveries_per_fulfilled':(1-z)*(1-q)/q,
            'cost_per_fulfilled':cost,'profit_per_fulfilled':R-cost}

def posterior_failed_pair(a,b,pf):
    f=1-a*b*(1-pf)
    if f==0: return {'failure_probability':0,'posterior':'undefined_zero_probability_event'}
    joint={'GG':a*b*pf/f,'GB':a*(1-b)/f,'BG':(1-a)*b/f,'BB':(1-a)*(1-b)/f}
    m1=joint['GG']+joint['GB'];m2=joint['GG']+joint['BG']
    assert abs(sum(joint.values())-1)<1e-12
    return {'failure_probability':f,'conditional_joint':joint,
            'P_G1_given_failure':m1,'P_G2_given_failure':m2,
            'covariance_G1_G2_given_failure':joint['GG']-m1*m2,
            'same_pair_next_attempt_success_probability':joint['GG']*(1-pf)}

def fully_tested_recycle(p1,p2,pf,c1=4,c2=18,t1=2,t2=3,a=6,tf=3,R=56,L=6,d=5,z=1,retest_recovered=True):
    # Both raw parts tested. Retained physical parts are good; process failures alone cause rejection.
    if max(p1,p2,pf)>=1: return {'feasible':False,'cost_per_fulfilled':math.inf}
    initial=(c1+t1)/(1-p1)+(c2+t2)/(1-p2)
    reinspection=t1+t2 if retest_recovered else 0.0
    cost=initial+(a+z*tf+pf*(d+reinspection+(1-z)*L))/(1-pf)
    return {'feasible':True,'policy':[1,1,z,1],'retest_recovered':retest_recovered,
            'cost_per_fulfilled':cost,'profit_per_fulfilled':R-cost,
            'new_raw_purchase_cost_increases_after_process_failure':False}

cases=[
 {'case':1,'p1':.1,'p2':.1,'pf':.1,'t1':2,'t2':3,'tf':3,'L':6,'d':5},
 {'case':2,'p1':.2,'p2':.2,'pf':.2,'t1':2,'t2':3,'tf':3,'L':6,'d':5},
 {'case':3,'p1':.1,'p2':.1,'pf':.1,'t1':2,'t2':3,'tf':3,'L':30,'d':5},
 {'case':4,'p1':.2,'p2':.2,'pf':.2,'t1':1,'t2':1,'tf':2,'L':30,'d':5},
 {'case':5,'p1':.1,'p2':.2,'pf':.1,'t1':8,'t2':1,'tf':2,'L':10,'d':5},
 {'case':6,'p1':.05,'p2':.05,'pf':.05,'t1':2,'t2':3,'tf':3,'L':10,'d':40}
]
case_oracles=[]
for row in cases:
    args={k:v for k,v in row.items() if k not in ['case','d']}
    policies=[no_dismantle(**args,x1=x1,x2=x2,z=z) for x1,x2,z in product([0,1],repeat=3)]
    best=min(policies,key=lambda x:x['cost_per_fulfilled'])
    # Universal optimistic cost lower bound: raw good-unit supply + process attempts, with free tests/dismantling.
    lb=4/(1-row['p1'])+18/(1-row['p2'])+6/(1-row['pf'])
    case_oracles.append({'case':row['case'],'input':row,'no_dismantle_policies':policies,
                         'best_within_no_dismantle_only':best,'universal_optimistic_cost_lower_bound':lb,
                         'profit_upper_bound_per_fulfilled':56-lb,
                         'all_raw_tested_recycle_retest':fully_tested_recycle(**args,d=row['d'],z=1)})

zero_none=no_dismantle(0,0,0)
zero_all=no_dismantle(0,0,0,x1=1,x2=1,z=1)
assert zero_none['profit_per_fulfilled']==28
assert zero_all['profit_per_fulfilled']==20
assert not no_dismantle(1,0,0)['feasible']
assert not no_dismantle(1,0,0,x1=1)['feasible']
assert not no_dismantle(0,0,1)['feasible']
assert abs(posterior_failed_pair(.9,.9,.1)['failure_probability']-.271)<1e-12
assert abs(cp_bounds(0,22,.1)[1]-(1-.1**(1/22)))<1e-12

# Q3 input tree confirmed visually from original PDF: [1,2,3], [4,5,6], [7,8] -> final.
raw_c=[2,8,12,2,8,12,8,12];raw_t=[1,1,2,1,1,2,1,2];g=.9
semi_groups=[[0,1,2],[3,4,5],[6,7]]
raw_screened=[(c+t)/g for c,t in zip(raw_c,raw_t)]
semi_costs=[(sum(raw_screened[i] for i in group)+8+4)/g for group in semi_groups]
root_cost=(sum(semi_costs)+8+6)/g
lb=sum(c/g for c in raw_c)+4*8/g
q3={'scope':'one fulfilled final unit; perfect tests; no initial/free inventory; independent fresh defect draws',
    'tree_raw_groups_1_based':[[i+1 for i in group] for group in semi_groups],
    'inspection_decisions':12,'dismantling_decisions':4,'static_binary_policies_if_all_independent':2**16,
    'optimistic_cost_lower_bound':lb,'corresponding_profit_upper_bound':200-lb,
    'fresh_no_inspection_success_probability':g**12,
    'no_inspection_no_dismantle_cost_per_fulfilled':(96+(1-g**12)*40)/(g**12),
    'no_inspection_no_dismantle_profit_per_fulfilled':200-(96+(1-g**12)*40)/(g**12),
    'feasible_all_test_no_dismantle_semi_costs':semi_costs,
    'feasible_all_test_no_dismantle_cost_per_fulfilled':root_cost,
    'feasible_profit_lower_bound_for_profit_maximization':200-root_cost,
    'all_defect_rates_zero_no_tests_no_dismantle_cost':sum(raw_c)+4*8,
    'all_defect_rates_zero_all_tests_no_dismantle_cost':sum(raw_c)+4*8+sum(raw_t)+3*4+6}
assert q3['all_defect_rates_zero_no_tests_no_dismantle_cost']==96
assert q3['all_defect_rates_zero_all_tests_no_dismantle_cost']==125
assert lb <= root_cost

result={'status':'independent_oracles_executed_only; running_solution_not_read_or_reviewed',
        'observation_data':'none; boundaries are synthetic diagnostic inputs, not sampled observations',
        'q1':{'p0':.1,'reject_alpha':.05,'accept_alpha':.1,
              'fixed_n_thresholds':[thresholds(n) for n in [1,2,21,22,29,50,100]],
              'smallest_n_zero_defects_90pct_upper_bound_le_p0':22,
              'smallest_n_any_rejection_feasible_at_5pct_typeI':2,
              'n29_probability_detect_at_least_one_at_p_0_1':1-.9**29,
              'n29_is_not_probability_p_exceeds_p0':True},
        'q2':{'table1_no_dismantle_diagnostics':case_oracles,'fresh_pair_failure_posterior_example':posterior_failed_pair(.9,.9,.1),
              'synthetic_zero_defects_no_test':zero_none,'synthetic_zero_defects_all_test':zero_all,
              'same_pair_no_inspection_always_recycle_completion_probability_example':.9*.9,
              'same_pair_no_inspection_always_recycle_expected_cost_example':'infinite with positive probability of persistent defective part'},
        'q3':q3}
(OUT/'oracle-results.json').write_text(json.dumps(clean(result),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'q1_thresholds':result['q1']['fixed_n_thresholds'],'q2_posterior':result['q2']['fresh_pair_failure_posterior_example'],'q3':q3},ensure_ascii=False,indent=2))
