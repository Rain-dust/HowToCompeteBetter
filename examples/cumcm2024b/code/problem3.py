from utils import init,save,csv
from production import problem3_tree,policy_table
def main():
    init();tree,b,price,loss=problem3_tree()
    result,rows=policy_table(tree,b,price,loss)
    result['baseline_cost']=rows[0]['cost']
    result['top10']=sorted((r for r in rows if r['proper']),key=lambda x:(x['cost'],x['policy_id']))[:10]
    save('results/q3.json',result);csv('results/q3_policies.csv',rows)
    print('Q3',result)
if __name__=='__main__':main()
