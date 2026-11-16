"""Independent event-driven physical simulation, never calls cost formulas."""
import numpy as np

def simulate(root,bits,loss,orders=20000,seed=20241116):
    rng=np.random.default_rng(seed)
    costs=np.zeros((orders,5));stats=np.zeros((orders,3))
    for order in range(orders):
        v=costs[order];st=stats[order]
        def supply(n,existing=None,isroot=False):
            recycled=None
            for loop in range(100000):
                if existing is not None:
                    item=existing;existing=None
                elif not n.children:
                    v[0]+=n.c
                    item=(bool(rng.random()>=n.p),())
                else:
                    children=tuple(supply(ch,recycled[j] if recycled else None) for j,ch in enumerate(n.children))
                    v[1]+=n.a;st[0]+=1
                    intrinsic_good=bool(rng.random()>=n.p)
                    item=(all(x[0] for x in children) and intrinsic_good,children)
                    recycled=None
                y=bool(bits[n.inspect])
                if y:v[2]+=n.t
                if isroot and not y and not item[0]:v[4]+=loss;st[1]+=1
                if item[0] or (not isroot and not y):return item
                st[2]+=1
                if n.children and bits[n.dismantle]:
                    v[3]+=n.d
                    recycled=item[1]
                else:
                    recycled=None
            raise RuntimeError('Simulation failed to terminate: improper policy?')
        supply(root,isroot=True)
    total=costs.sum(axis=1)
    return {'orders':orders,'seed':seed,'mean_cost':float(total.mean()),
            'standard_error':float(total.std(ddof=1)/np.sqrt(orders)),
            'ci95':[float(total.mean()-1.96*total.std(ddof=1)/np.sqrt(orders)),float(total.mean()+1.96*total.std(ddof=1)/np.sqrt(orders))],
            'mean_components':costs.mean(axis=0).tolist(),'mean_assembly_attempts':float(stats[:,0].mean()),
            'mean_market_returns':float(stats[:,1].mean()),'mean_detected_failures':float(stats[:,2].mean())}
