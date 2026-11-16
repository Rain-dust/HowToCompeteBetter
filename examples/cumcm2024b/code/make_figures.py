"""All data-driven figures; PDFs and source metadata are deterministic."""
from datetime import datetime,timezone
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from utils import init,read,save,ROOT

plt.rcParams.update({'font.family':'SimSun','font.size':10.5,'axes.unicode_minus':False,
 'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.alpha':.18,
 'pdf.fonttype':42,'savefig.bbox':'tight','figure.dpi':160})
BLUE='#285980';ORANGE='#c56d27';GREEN='#36705b';GRAY='#73777e'
provenance=[]
def finish(fig,name,sources,purpose):
    fig.savefig(ROOT/f'figures/{name}.pdf',metadata={'Creator':'Matplotlib','CreationDate':datetime(2026,11,16,tzinfo=timezone.utc)})
    fig.savefig(ROOT/f'figures/{name}.png',dpi=180)
    plt.close(fig)
    provenance.append({'figure':f'{name}.pdf','sources':sources,'purpose':purpose})

def main():
    init()
    q1=read('results/q1.json');q2=read('results/q2.json');q3=read('results/q3.json');q4=read('results/q4.json')
    oc=pd.read_csv(ROOT/'results/q1_oc.csv');bd=pd.read_csv(ROOT/'results/q1_boundaries.csv')
    fig,ax=plt.subplots(figsize=(6.5,3.2),layout='constrained')
    a=bd[bd.n<=200]
    ax.plot(a.n,a.reject_k_min,color=ORANGE,label='拒收：次品数不小于边界')
    ax.plot(a.n,a.accept_k_max,color=BLUE,label='接收：次品数不大于边界')
    ax.fill_between(a.n,0,a.accept_k_max,color=BLUE,alpha=.1)
    ax.set(xlabel='累计检测数 n',ylabel='累计次品数 k',ylim=(0,65),xlim=(0,200))
    ax.legend(loc='upper left',frameon=False,fontsize=9)
    finish(fig,'fig_q1_boundaries',['results/q1_boundaries.csv'],'给出随时有效的停止边界，空缺表示该样本量尚无接收路径')
    fig,axs=plt.subplots(1,2,figsize=(7,3.1),layout='constrained')
    for key,label,color,ls in [('accept','接收',BLUE,'-'),('reject','拒收',ORANGE,'--'),('inconclusive','未决',GRAY,':')]:
        axs[0].plot(oc.p,oc[key],label=label,color=color,ls=ls)
    axs[0].set(xlabel='真实次品率 p',ylabel='结论概率',ylim=(-.02,1.04));axs[0].legend(frameon=False)
    axs[1].plot(oc.p,oc.expected_tests_capped,color=GREEN,marker='.',ms=3)
    axs[1].set(xlabel='真实次品率 p',ylabel='截断平均检测数')
    for ax in axs:ax.axvline(.1,c=GRAY,ls=':',lw=1)
    finish(fig,'fig_q1_oc',['results/q1_oc.csv'],'比较判断概率和检测代价，2000次上限保留未决')
    fig,axs=plt.subplots(1,2,figsize=(7,3.2),layout='constrained',gridspec_kw={'width_ratios':[1.2,1]})
    x=np.arange(6);w=.35
    axs[0].bar(x-w/2,[r['baseline_cost'] for r in q2],w,label='不检测、不拆解',color='#b9bfc5',hatch='//')
    axs[0].bar(x+w/2,[r['cost'] for r in q2],w,label='固定策略类最优',color=BLUE)
    axs[0].set(xticks=x,xticklabels=range(1,7),xlabel='表1情况',ylabel='履约成本（元/单）',ylim=(0,115));axs[0].legend(frameon=False,fontsize=9)
    bits=np.array([r['bits'] for r in q2])
    axs[1].imshow(bits,cmap=ListedColormap(['#eef0f3',BLUE]),vmin=0,vmax=1,aspect='auto')
    for i in range(6):
        for j in range(4):axs[1].text(j,i,str(bits[i,j]),ha='center',va='center',color='white' if bits[i,j] else 'black')
    axs[1].set(xticks=range(4),xticklabels=['零件1检','零件2检','成品检','拆解'],yticks=range(6),yticklabels=range(1,7),ylabel='表1情况')
    axs[1].tick_params(axis='x',labelsize=9);axs[1].grid(False)
    finish(fig,'fig_q2_decisions',['results/q2.json'],'统一履约口径下的成本比较和四位策略')
    fig,axs=plt.subplots(1,2,figsize=(7,3.3),layout='constrained',gridspec_kw={'width_ratios':[1,1.4]})
    labels=['采购','装配','检测','拆解','调换损失'];colors=[BLUE,'#6293ad',GREEN,ORANGE,GRAY]
    bottom=0
    for label,val,color in zip(labels,q3['cost_components'].values(),colors):
        axs[0].bar(['最优固定策略'],[val],bottom=bottom,label=label,color=color)
        if val>10:axs[0].text(0,bottom+val/2,f'{val:.2f}',color='white',ha='center',va='center')
        bottom+=val
    axs[0].set(ylabel='履约成本（元/单）',ylim=(0,190));axs[0].legend(frameon=False,fontsize=8,ncol=2,loc='upper left')
    top=q3['top10'][:6]
    axs[1].barh(range(6),[r['profit'] for r in top],color=[BLUE]+['#adb8c2']*5)
    axs[1].set(yticks=range(6),yticklabels=[str(r['policy_id']) for r in top],xlabel='期望利润（元/单）',ylabel='策略编码',xlim=(0,65));axs[1].invert_yaxis()
    for i,r in enumerate(top):axs[1].text(r['profit']+.4,i,f'{r["profit"]:.2f}',va='center',fontsize=9)
    finish(fig,'fig_q3_results',['results/q3.json'],'解释多工序最优策略成本构成及候选差距')
    fig,axs=plt.subplots(1,2,figsize=(7,3.2),layout='constrained')
    for j,N in enumerate([100,400]):
        rows=[r for r in q4 if r['N_per_node']==N and r['target']!='q3']
        axs[0].plot(range(1,7),[r['robust']['profit'] for r in rows],color=[ORANGE,BLUE][j],marker=['s','o'][j],ls=['--','-'][j],label=f'假想每节点 n={N}')
    axs[0].set(xlabel='表1情况',ylabel='区间最坏利润（元/单）');axs[0].legend(frameon=False,fontsize=9)
    rows=[r for r in q4 if r['target']=='q3'];xx=np.arange(2);w=.34
    axs[1].bar(xx-w/2,[r['nominal_worst_profit'] for r in rows],w,color=GRAY,label='名义策略在区间最坏点')
    axs[1].bar(xx+w/2,[r['robust']['profit'] for r in rows],w,color=BLUE,label='区间鲁棒策略')
    axs[1].set(xticks=xx,xticklabels=['100','400'],xlabel='假想每节点固定样本量',ylabel='表2最坏利润（元/单）',ylim=(0,60));axs[1].legend(frameon=False,fontsize=8)
    finish(fig,'fig_q4_robust',['results/q4.json'],'明确假想抽样条件下的鲁棒利润与名义决策风险')
    fig,ax=plt.subplots(figsize=(6.5,2.7),layout='constrained')
    selected=[r for r in q4 if r['target']=='q3']
    for j,r in enumerate(selected):
        ci=r['intervals'][0]
        ax.errorbar(.1,j,xerr=[[.1-ci['lower']],[ci['upper']-.1]],fmt='o',capsize=5,color=[ORANGE,BLUE][j],label=f'n={r["N_per_node"]}')
    ax.set(yticks=[0,1],yticklabels=['假想 n=100，k=10','假想 n=400，k=40'],xlabel='节点次品率的同时区间',ylim=(-.6,1.6),xlim=(0,.27))
    ax.axvline(.1,c=GRAY,ls=':');ax.grid(axis='y',visible=False)
    finish(fig,'fig_q4_intervals',['results/q4_intervals.csv'],'表2共12个率分配错误概率后的单节点区间')
    sens=pd.read_csv(ROOT/'results/sensitivity.csv');fig,axs=plt.subplots(1,2,figsize=(7,3.3),layout='constrained')
    for ax,target in zip(axs,['q2:1','q3']):
        for param,label,color,marker in zip(['loss','dismantle','inspection','defect'],['调换损失','拆解费','检测费','次品率'],[GRAY,ORANGE,BLUE,GREEN],['s','^','o','d']):
            sub=sens[(sens.target==target)&(sens.parameter==param)]
            ax.plot(sub.factor,sub.profit,label=label,color=color,marker=marker,ms=4)
        ax.set(xlabel='参数倍率',ylabel=('表1情况1' if target=='q2:1' else '表2')+'利润（元/单）')
        ax.legend(frameon=False,fontsize=8,ncol=2)
    finish(fig,'fig_sensitivity',['results/sensitivity.csv'],'每个扰动点重新枚举后的策略类最优利润')
    save('figures/DATA_FIGURE_SOURCES.json',provenance)
    print('Generated',len(provenance),'data figures')
if __name__=='__main__':main()
