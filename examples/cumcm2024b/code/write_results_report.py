from utils import init,read,save,ROOT
def main():
    init();q1=read('results/q1.json');q2=read('results/q2.json');q3=read('results/q3.json');q4=read('results/q4.json')
    val=read('results/validation.json');sims=read('results/simulations.json');sens=read('results/sensitivity.json')
    env=read('reports/environment.json');risk=q1['risk_at_p0']
    save('results/all_results.json',{'q1':q1,'q2':q2,'q3':q3,'q4':q4,'validation':val})
    s=['# 计算结果','', '## 运行环境',f"Python {env['python'].split()[0]}；{env['typst_version']}；包版本详见 environment.json。shell固定cmd.exe。固定随机种子；不安装新依赖。",'',
       '## 数据读取与预处理','inputs/parameters.json逐项转录原题两张表；原PDF两页已渲染人工核对。表1六行、每行12个数值字段（分析阶段误记13个，已纠正）；表2装配组为(1,2,3)、(4,5,6)、(7,8)。没有实测样本。概率为小数，货币元/件。', '',
       '## 问题一结果',f"单次事先固定方案：2个全坏可拒收，尾概率{q1['fixed_single_look']['reject_tail']:.8f}；22个全好可接收，尾概率{q1['fixed_single_look']['accept_tail']:.8f}。n=22时k≥6可拒收。不可把两个单次最早界限混成反复窥视规则。",'',
       f"双证据过程最早全坏拒收n={q1['sequential_earliest_reject_n']}、全好接收n={q1['sequential_earliest_accept_n']}。p=0.10时2000次截断：接收{risk['accept']:.8f}、拒收{risk['reject']:.8f}、未决{risk['inconclusive']:.8f}、平均检测{risk['expected_tests_capped']:.6f}。在边界处可能长期未决，这是控制两侧错误所需的保留结论。没有观测值，未作任何实际批次判断。",'',
       '完整操作特性及边界：results/q1_oc.csv、q1_boundaries.csv；图：fig_q1_boundaries.pdf、fig_q1_oc.pdf。', '',
       '## 问题二结果','固定策略位顺序：零件1检、零件2检、成品检、拆解（1为是）。售价只收一次；直到交付一件合格品。每情形16编码中10个适定。','',
       '|情况|策略|成本 元/单|利润 元/单|无检无拆成本|','|---|---|---:|---:|---:|']
    for r in q2:s.append(f"|{r['case']}|{''.join(map(str,r['bits']))}|{r['cost']:.8f}|{r['profit']:.8f}|{r['baseline_cost']:.8f}|")
    s+=['','完整16策略表见 results/q2_case1_policies.csv 至 q2_case6_policies.csv；不适定策略成本留空而非虚报有限值。图：fig_q2_decisions.pdf。','',
       '## 问题三结果',f"枚举{q3['enumerated']}编码，{q3['proper_encodings']}个适定编码。最优编码{q3['policy_id']}，策略位{''.join(map(str,q3['bits']))}，成本{q3['cost']:.8f}，利润{q3['profit']:.8f}。检测所有原料与半成品，各层失败均拆解；成品免检。每次重新检测合格回收子件仍收费。固定站点策略类内穷举最优；不宣称更广的自适应策略全局最优。",'',
       f"成本分解：{q3['cost_components']}。无检无拆成本{q3['baseline_cost']:.8f}，其负利润源于企业必须无条件换货。完整表 results/q3_policies.csv，前10候选在q3.json；图fig_q3_results.pdf。",'',
       '## 问题四结果','以下全部为假想固定样本场景：每节点n=100或400，k=n×原表率；这些不是实测样本，不是对真实企业数据的估计。每生产情形内联合覆盖至少95%，不代表所有七情形同时95%。真实固定n计数可用problem4.py --counts相对路径.json。', '',
       '|目标|假想n|鲁棒策略|最坏利润|名义策略最坏利润|鲁棒策略中心利润|','|---|---|---|---:|---:|---:|']
    for r in q4:s.append(f"|{r['target']}|{r['N_per_node']}|{''.join(map(str,r['robust']['bits']))}|{r['robust']['profit']:.8f}|{r['nominal_worst_profit']:.8f}|{r['robust_center_profit']:.8f}|")
    s+=['','区间及计数保存 results/q4_intervals.csv，全部策略汇总 q4_summary.csv。图fig_q4_robust.pdf、fig_q4_intervals.pdf。矩形内最坏成本由单调性确定在各率上端点，500随机内点/场景作数值复核。上限若为1则可能无有限履约保证。顺序停止样本不能直接使用固定n的CP区间。', '',
       '## 灵敏度分析','40次重新枚举保存在 results/sensitivity.csv/json，图fig_sensitivity.pdf。各倍率0.5、0.8、1、1.2、1.5；单独改变调换损失、拆解费用、全部节点检测费、全部节点次品率。','',
       '|目标|参数|倍率0.5的策略/利润|倍率1.5的策略/利润|','|---|---|---|---|']
    for target in ['q2:1','q3']:
        for p in ['loss','dismantle','inspection','defect']:
            rr=[r for r in sens if r['target']==target and r['parameter']==p]
            a,z=rr[0],rr[-1]
            s.append(f"|{target}|{p}|{a['policy_id']} / {a['profit']:.6f}|{z['policy_id']} / {z['profit']:.6f}|")
    s+=['','## 约束与一致性校验',f"独立检验{val['passed']}/{val['total']}通过。生产事件模拟总订单数{sum(r.get('orders',0) for r in sims)}；最大标准化偏差{max(r.get('z',0) for r in sims):.6f}，阈值5个标准误。抽样证据过程在p=0.05/0.10/0.20分别独立模拟30000批次。模拟保留物理质量、不调用解析成本递推；原料失败丢弃，拆解不改变子件质量。",'',
       '详细证据：results/validation.json、simulations.json/csv、q4_coverage.csv。二项CDF独立反演复核Beta区间端点，检查边界、概率质量守恒、穷举最小值与费用分项。Monte Carlo的95%误差条是随机精度描述，5标准误通过阈值用于回归检验，两者不可混同。', '',
       '## 与建模报告的一致性说明','保持固定策略、物理回收质量和每单履约口径。仅修正零次品率边界下“回收子件重新检测费”为实际检测位×检测费；原题所有率正，数值不受此修正影响。未使用启发式或独立重采样回收近似。大批量二项假设、准确检测、独立装配缺陷、无库存耦合、固定策略类仍是模型限制。','',
       '## 可复现运行方式','在项目根目录用cmd.exe执行 `python.exe code/run_all.py`。单问入口problem1.py至problem4.py；独立验证validate_calculations.py；图make_figures.py。图源关系详见figures/DATA_FIGURE_SOURCES.json。最终全量重跑、编译、排版和hash证据见VERIFY_REPORT.md及RUN_MANIFEST.json。']
    (ROOT/'reports/RESULTS_REPORT.md').write_text('\n'.join(s)+'\n',encoding='utf-8')
    print('Wrote RESULTS_REPORT.md')
if __name__=='__main__':main()
