from utils import init,save,csv
from production import problem2_tree,policy_table
def main():
    init(); answers=[]
    for case in range(1,7):
        tree,b,price,loss=problem2_tree(case)
        result,rows=policy_table(tree,b,price,loss)
        result['case']=case
        result['baseline_cost']=rows[0]['cost']
        answers.append(result);csv(f'results/q2_case{case}_policies.csv',rows)
        print('Q2',case,result['bits'],result['cost'],result['profit'])
    save('results/q2.json',answers);csv('results/q2_summary.csv',[{k:v for k,v in a.items() if k not in ['cost_components','tied_encodings']} for a in answers])
if __name__=='__main__':main()
