from copy import deepcopy
from utils import init,save,csv
from production import problem2_tree,problem3_tree,nodes,solution
def main():
    init();rows=[]
    for target,factory in [('q2:1',lambda:problem2_tree(1)),('q3',problem3_tree)]:
        for param in ['loss','dismantle','inspection','defect']:
            for factor in [.5,.8,1,1.2,1.5]:
                root,b,price,loss=factory()
                if param=='loss':loss*=factor
                for n in nodes(root):
                    if param=='dismantle':n.d*=factor
                    if param=='inspection':n.t*=factor
                    if param=='defect':n.p*=factor
                ans,_=solution(root,b,price,loss)
                rows.append({'target':target,'parameter':param,'factor':factor,'policy_id':ans['policy_id'],'profit':ans['profit'],'bits':ans['bits']})
    save('results/sensitivity.json',rows);csv('results/sensitivity.csv',rows)
    print('SENSITIVITY',len(rows),'re-optimizations')
if __name__=='__main__':main()
