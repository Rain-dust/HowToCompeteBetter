"""Fixed-n conditional inference. The default counts are HYPOTHETICAL.

Pass --counts path.json for actual prespecified fixed-n counts. Format:
{"target":"q3" or "q2:1", "counts":[{"n":100,"k":10}, ...]}
in postorder: parts then each semi with its children, then root (see metadata).
"""
import argparse
import numpy as np
from scipy.stats import beta
from utils import init,read,save,csv
from production import problem2_tree,problem3_tree,nodes,set_rates,solution,evaluate

def intervals(counts,alpha=.05):
    d=len(counts);delta=alpha/d
    rows=[]
    for v in counts:
        n,k=int(v['n']),int(v['k'])
        if n<1 or not 0<=k<=n:raise ValueError('Counts must satisfy n >= 1 and 0 <= k <= n')
        l=0. if k==0 else float(beta.ppf(delta/2,k,n-k+1))
        u=1. if k==n else float(beta.ppf(1-delta/2,k+1,n-k))
        rows.append({'n':n,'k':k,'estimate':k/n,'lower':l,'upper':u})
    return rows

def conditional(tree,b,price,loss,counts):
    if len(counts)!=len(nodes(tree)):raise ValueError('One count pair per tree node is required')
    ci=intervals(counts)
    for r,n in zip(ci,nodes(tree)):r['node']=n.name
    center=set_rates(tree,[r['estimate'] for r in ci]);upper=set_rates(tree,[r['upper'] for r in ci])
    nominal,_=solution(center,b,price,loss);robust,_=solution(upper,b,price,loss)
    out={'intervals':ci,'nominal':nominal,'robust':robust,'coverage_per_case':.95,
         'node_order':[n.name for n in nodes(tree)]}
    if nominal['available'] and robust['available']:
        out['nominal_worst_profit']=float(price-evaluate(upper,b,loss,[nominal['policy_id']])[2][0])
        out['robust_center_profit']=float(price-evaluate(center,b,loss,[robust['policy_id']])[2][0])
    return out

def main():
    init();p=argparse.ArgumentParser();p.add_argument('--counts');args=p.parse_args()
    if args.counts:
        spec=read(args.counts);target=spec['target']
        tree,b,price,loss=problem3_tree() if target=='q3' else problem2_tree(int(target.split(':')[1]))
        out=conditional(tree,b,price,loss,spec['counts']);out['count_status']='user_supplied_fixed_n'
        save('results/q4_supplied_counts.json',out);return
    out=[];summary=[];all_ci=[]
    for N in read('inputs/parameters.json')['hypothetical_q4_fixed_n']:
        for target in [f'q2:{i}' for i in range(1,7)]+['q3']:
            tree,b,price,loss=problem3_tree() if target=='q3' else problem2_tree(int(target.split(':')[1]))
            counts=[{'n':N,'k':round(N*n.p)} for n in nodes(tree)]
            rec=conditional(tree,b,price,loss,counts)
            rec.update({'target':target,'N_per_node':N,'count_status':'HYPOTHETICAL_not_observed'})
            out.append(rec)
            for x in rec['intervals']:all_ci.append({'target':target,'N':N,**x,'count_status':'HYPOTHETICAL'})
            summary.append({'target':target,'N':N,'nominal_policy':rec['nominal']['policy_id'],
               'robust_policy':rec['robust']['policy_id'],'robust_bits':rec['robust']['bits'],
               'nominal_worst_profit':rec['nominal_worst_profit'],'robust_worst_profit':rec['robust']['profit'],
               'robust_center_profit':rec['robust_center_profit']})
            print('Q4',target,N,'robust',rec['robust']['bits'],'worst profit',rec['robust']['profit'])
    save('results/q4.json',out);csv('results/q4_summary.csv',summary);csv('results/q4_intervals.csv',all_ci)
if __name__=='__main__':main()
