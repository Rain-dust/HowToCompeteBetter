"""Build a self-contained, offline competition finder from the canonical catalog.

The generated HTML is a downloadable file, not a deployed website. Filtering
works without a network; detail and tutorial links open the public repository.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = 'https://github.com/Rain-dust/HowToCompeteBetter'
DATE = '2026-11-17'


def public_url(value):
    if not value:
        return None
    if value.startswith(('https://', 'http://')):
        return value
    return REPO + '/blob/main/' + value.lstrip('./')


def normalize(item):
    required = ['rank', 'decision_code', 'decision_label', 'decision_note', 'cost_summary',
                'evidence_label', 'reader_filters', 'card_path', 'tool_name',
                'tool_url', 'tool_tutorial', 'getting_started']
    missing = [key for key in required if key not in item]
    if missing:
        raise ValueError(f"{item['id']} lacks canonical reader fields: {missing}")
    cost = item['cost_summary']
    needed_cost = ['team', 'time', 'registration_fee', 'model_fee', 'hardware', 'human', 'basis']
    if not isinstance(cost, dict) or any(key not in cost for key in needed_cost):
        raise ValueError('Incomplete canonical costs: ' + item['id'])
    facets = item['reader_filters']
    education = facets.get('education') or ['unknown']
    equipment = facets.get('software_hardware') or ['unknown']
    if not set(education) <= {'undergraduate', 'vocational', 'graduate', 'unknown'}:
        raise ValueError('Unknown education facet: ' + item['id'])
    if not set(equipment) <= {'software', 'hardware', 'mixed', 'unknown'}:
        raise ValueError('Unknown equipment facet: ' + item['id'])
    aliases = item.get('aliases', [])
    if isinstance(aliases, str):
        aliases = [aliases]
    return {
        'id': item['id'], 'rank': item['rank'], 'name': item['name'],
        'short': item.get('short', ''), 'aliases': aliases,
        'scope': item.get('scope', '具体学籍资格待核'),
        'track': (item.get('ranking_view') or {}).get('track', ''),
        'decision': item['decision_label'], 'decision_code': item['decision_code'], 'decision_note': item['decision_note'],
        'cost': cost, 'evidence': item['evidence_label'],
        'education': education, 'equipment': equipment,
        'card': public_url(item['card_path']),
        'tool_name': item['tool_name'] or '工具路线待核',
        'tool_url': public_url(item['tool_url']),
        'tutorial': public_url(item['tool_tutorial']),
        'getting_started': item['getting_started'],
        'cycle': item.get('cycle', '具体报名状态待核'),
        'award': item.get('award', '具体奖级路径待核'),
        'checked': item.get('checked_at') or (item.get('ranking_view') or {}).get('rules_checked_through') or '见详情各原文日期',
    }


HTML = r'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<title>按条件找比赛 · 高性价比大学生竞赛指南</title>
<style>
:root{--ink:#163442;--muted:#526770;--teal:#007b7f;--line:#d7e3e6;--pale:#edf6f5;--paper:#fff;--bg:#f5f8f8}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:"Microsoft YaHei","PingFang SC",system-ui,sans-serif;line-height:1.65}
a{color:var(--teal);text-underline-offset:3px}a:hover{text-decoration-thickness:2px}button,input,select{font:inherit}
button,a,input,select,summary{-webkit-tap-highlight-color:transparent}:focus-visible{outline:3px solid #a75e16;outline-offset:3px}
.skip{position:absolute;left:15px;top:-90px;background:white;padding:10px;z-index:5}.skip:focus{top:10px}
main{max-width:1180px;margin:0 auto;padding:28px 26px 60px}.eyebrow{color:var(--teal);font-weight:750;font-size:13px;letter-spacing:.07em;margin:0 0 7px}
h1{font-size:clamp(28px,4vw,42px);line-height:1.3;letter-spacing:-.03em;margin:0 0 10px}.lead{font-size:17px;margin:0;max-width:820px}.top-links{display:flex;flex-wrap:wrap;gap:9px 21px;margin-top:15px;font-size:14px}
.offline{background:var(--pale);border:1px solid var(--line);border-radius:12px;padding:13px 17px;margin:24px 0 20px;font-size:14px}.offline p{margin:0}.offline p+p{margin-top:5px}.offline strong{font-weight:750}
.filters{padding:20px;background:var(--paper);border:1px solid var(--line);border-radius:15px;box-shadow:0 7px 22px #203f4710}.search-line{display:flex;gap:12px;align-items:end}.field{display:flex;flex-direction:column;gap:6px;min-width:0}.search-field{flex:1}.field label{font-weight:700;font-size:14px}input,select{width:100%;min-height:44px;border:1px solid #b4c7cd;border-radius:8px;background:#fff;color:var(--ink);padding:9px 11px}input::placeholder{color:#697c82}
.filter-grid{display:grid;grid-template-columns:1fr 1fr 1fr 1.1fr;gap:13px;margin-top:15px}.reset{min-height:44px;border:1px solid #a7bec5;background:white;color:var(--ink);padding:9px 15px;border-radius:8px;cursor:pointer;white-space:nowrap}.reset:hover{background:var(--pale)}.filter-help{font-size:12px;color:var(--muted);margin-top:13px}.filter-help summary{cursor:pointer}.hint{font-size:12px;color:var(--muted);margin:7px 0 0;max-width:1020px}.scope-note{margin-top:5px}.scope-note summary{cursor:pointer;color:var(--teal)}
.result-head{display:flex;justify-content:space-between;gap:12px;align-items:baseline;margin:24px 1px 13px}#result-count{font-size:17px;font-weight:750;margin:0}.order-note{color:var(--muted);font-size:12px;margin:0}
.cards{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}.card{background:var(--paper);border:1px solid var(--line);border-radius:13px;padding:20px;display:flex;flex-direction:column;min-width:0}.card-top{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:8px}.reference{font-size:12px;color:var(--muted)}.decision{font-size:12px;font-weight:750;padding:3px 9px;border-radius:6px;background:#e8f2f1;color:#136266;max-width:75%;overflow-wrap:anywhere}.card h2{font-size:19px;line-height:1.55;margin:0 0 8px}.card h2 a{color:var(--ink);text-decoration:none}.card h2 a:hover{color:var(--teal);text-decoration:underline}.summary{margin:0 0 10px;font-size:14px;color:var(--muted)}.condition{margin:0 0 13px;font-size:14px}
.facts{margin:0;display:grid;grid-template-columns:45px minmax(0,1fr);gap:7px 11px;font-size:13px}.facts dt{color:var(--muted)}.facts dd{margin:0;overflow-wrap:anywhere}.detail-toggle{margin-top:12px;border-top:1px solid #e5ecee;padding-top:10px;font-size:13px}.detail-toggle summary{cursor:pointer;color:var(--teal);font-weight:650}.more{margin-top:10px}.facts.more{grid-template-columns:67px minmax(0,1fr);font-size:12px}.evidence{font-size:12px;color:var(--muted);margin:12px 0 13px}.actions{margin-top:auto;padding-top:6px;display:flex;gap:10px;flex-wrap:wrap;align-items:center}.primary,.secondary{display:inline-flex;align-items:center;justify-content:center;min-height:40px;border-radius:7px;padding:7px 12px;font-size:13px;text-decoration:none}.primary{background:var(--teal);color:white;font-weight:700}.primary:hover{background:#006568}.secondary{border:1px solid #a9c5c9;color:var(--teal)}.source-link{font-size:12px}
.empty{background:white;border:1px dashed #a6bec6;border-radius:12px;padding:36px 20px;text-align:center}.empty h2{font-size:20px;margin:0 0 9px}.empty p{margin:0 0 16px;color:var(--muted);font-size:14px}.empty[hidden]{display:none}.footer{margin-top:30px;border-top:1px solid var(--line);padding-top:17px;color:var(--muted);font-size:12px}.footer p{margin:5px 0}.noscript{background:#fff2d8;padding:15px;border-radius:8px}
@media(max-width:760px){main{padding:22px 16px 40px}.filter-grid{grid-template-columns:1fr 1fr}.cards{grid-template-columns:1fr}.card{padding:17px}.result-head{align-items:start;flex-direction:column;gap:3px}.lead{font-size:15px}.offline{font-size:13px}.top-links{font-size:13px}}
@media(max-width:420px){.search-line{gap:8px}.reset{padding:9px 11px}.filters{padding:15px}.filter-grid{gap:11px}.field label{font-size:13px}.field select{font-size:13px;padding:9px 6px}.card h2{font-size:18px}.decision{max-width:72%}.facts{grid-template-columns:39px minmax(0,1fr);gap:7px 8px}}
@media print{.filters,.top-links,.offline,.actions,.detail-toggle,.footer{display:none}.cards{display:block}.card{break-inside:avoid;margin-bottom:12px}.result-head{margin-top:15px}main{max-width:none;padding:0}a{color:inherit;text-decoration:none}}
</style>
</head>
<body>
<a class="skip" href="#results">跳到筛选结果</a>
<main>
<header>
<p class="eyebrow">HOW TO COMPETE BETTER · 离线筛选工具</p>
<h1>按条件找比赛</h1>
<p class="lead">先按学历、设备和当届建议筛选，再点开完整赛事卡。参考序号不代表当届推荐或获奖概率。</p>
<nav class="top-links" aria-label="阅读入口">
<a href="https://github.com/Rain-dust/HowToCompeteBetter#readme" target="_blank" rel="noopener noreferrer">回项目首页</a>
<a href="https://github.com/Rain-dust/HowToCompeteBetter/blob/main/docs/competition-catalog.md" target="_blank" rel="noopener noreferrer">Markdown赛事索引</a>
<a href="https://github.com/Rain-dust/HowToCompeteBetter/blob/main/docs/math-modeling.md" target="_blank" rel="noopener noreferrer">数模完整教程</a>
</nav>
</header>
<aside class="offline" aria-label="使用说明">
<p><strong>下载后，用浏览器打开。</strong>筛选离线可用；完整赛事卡和教程联网打开GitHub。</p>
<details class="scope-note"><summary>收录范围与日期说明</summary><p>共 __TOTAL__ 条参考入口，含母赛分支、平台和省级入口；其中 __RANKED__ 项保留参考序号。资料核对日期逐项见详情，2026通知不代表仍在报名。本工具是下载文件，没有上线为独立网站。</p></details>
</aside>
<noscript><p class="noscript">本地筛选需要浏览器启用JavaScript。也可以联网打开上方的Markdown赛事索引。</p></noscript>
<form class="filters" id="filter-form" aria-label="筛选比赛" role="search">
<div class="search-line">
<div class="field search-field"><label for="query">搜比赛、简称或关键词</label><input id="query" type="search" autocomplete="off" placeholder="例如：数模、RST、软件杯、高职" aria-describedby="filter-hint"></div>
<button class="reset" type="reset">清空筛选</button>
</div>
<div class="filter-grid">
<div class="field"><label for="view">查看范围</label><select id="view"><option value="ranked">参考榜 __RANKED__ 项</option><option value="all">全部 __TOTAL__ 条入口</option></select></div>
<div class="field"><label for="education">资料涉及的学历</label><select id="education"><option value="all">不限</option><option value="undergraduate">本科</option><option value="vocational">高职高专</option><option value="graduate">研究生</option><option value="unknown">尚未明确</option></select></div>
<div class="field"><label for="equipment">软件 / 设备条件</label><select id="equipment"><option value="all">不限</option><option value="software">软件方向</option><option value="hardware">硬件方向</option><option value="mixed">含软件与硬件方向</option><option value="unknown">尚未明确</option></select></div>
<div class="field"><label for="decision">当届建议</label><select id="decision"><option value="all">全部建议状态</option></select></div>
</div>
<details class="filter-help"><summary>筛选标签与未知项说明</summary><p class="hint" id="filter-hint">学历和设备筛选只使用资料中的明确标签，不能替代资格审核；“软件方向”也不保证无需特定平台或设备。人时为编辑估算，不能直接换算成完成天数。报名费、模型费和人工投入分别记录，未核实的保留未知。</p></details>
</form>
<section id="results" aria-label="比赛筛选结果" tabindex="-1">
<div class="result-head"><p id="result-count" role="status" aria-live="polite"></p><p class="order-note">按参考序号升序；无序号条目接续原目录顺序</p></div>
<div class="cards" id="cards"></div>
<div class="empty" id="empty" hidden><h2>没有匹配的入口</h2><p>试试更短的简称、减少一个筛选条件，或切换“全部入口”。没有结果不代表不存在可参加的比赛。</p><button type="button" class="reset" id="empty-reset">清空筛选，回到参考榜</button></div>
</section>
<footer class="footer"><p>文件更新：__DATE__。逐项依据和核查日期见赛事卡；下载的文件不会自动更新。</p><p>筛选不自动联网，筛选内容留在本机。正式参赛以当届赛项规则、本校认定与实际报名审核为准。</p></footer>
</main>
<script id="catalog-data" type="application/json">__DATA__</script>
<script>
'use strict';
const contests=JSON.parse(document.getElementById('catalog-data').textContent);
const form=document.getElementById('filter-form');
const query=document.getElementById('query');
const view=document.getElementById('view');
const education=document.getElementById('education');
const equipment=document.getElementById('equipment');
const decision=document.getElementById('decision');
const cardGrid=document.getElementById('cards');
const resultCount=document.getElementById('result-count');
const empty=document.getElementById('empty');
const normalizeText=s=>String(s||'').toLocaleLowerCase('zh-CN').normalize('NFKC').replace(/[\s·—–“”‘’「」《》（）()\-_/]/g,'');
const text=(tag,value,className)=>{const e=document.createElement(tag);e.textContent=value||'待核';if(className)e.className=className;return e;};
const sourceLink=(label,url,className)=>{const a=text('a',label,className);a.href=url;a.target='_blank';a.rel='noopener noreferrer';return a;};
const addFact=(dl,label,value)=>{dl.append(text('dt',label),text('dd',value));};
const sorted=contests.map((item,index)=>({...item,index,search:normalizeText([item.name,...item.aliases,item.short,item.track,item.scope,item.tool_name,item.id].join(' '))})).sort((a,b)=>(a.rank===null?Infinity:a.rank)-(b.rank===null?Infinity:b.rank)||a.index-b.index);
const decisionGroups={conditional:'按具体条件研究',rule_check:'先核当届规则',existing_project:'已有真实项目再看',auxiliary:'正式赛仅在辅助范围',restricted:'核心或作品生成受限',allowlist:'工具名单有明确限制',platform:'先练平台或现场操作'};
for(const code of new Set(sorted.map(item=>item.decision_code))){const option=document.createElement('option');option.value=code;option.textContent=decisionGroups[code]||code;decision.append(option);}
function createCard(item){
 const card=text('article','','card');card.removeAttribute('title');card.dataset.id=item.id;card.dataset.rank=item.rank===null?'':item.rank;
 const top=text('div','','card-top');top.replaceChildren();
 top.append(text('span',item.rank===null?'补充入口 · '+item.id:'参考序号 '+String(item.rank).padStart(2,'0'),'reference'),text('span',item.decision,'decision'));
 const heading=document.createElement('h2');heading.append(sourceLink(item.name,item.card));
 card.replaceChildren(top,heading,text('p',item.short,'summary'),text('p',item.decision_note,'condition'));
 const facts=document.createElement('dl');facts.className='facts';
 const timeText=/人时/.test(item.cost.time)&&!item.cost.time.includes('估算')?item.cost.time+'（编辑估算）':item.cost.time;
 addFact(facts,'时间',timeText);addFact(facts,'人工',item.cost.human);addFact(facts,'工具',item.tool_name);
 card.append(facts);
 const more=document.createElement('details');more.className='detail-toggle';
 more.append(text('summary','展开资格、成本与奖项路径'));
 const inner=document.createElement('dl');inner.className='facts more';
 for(const [label,value] of [['学籍范围',item.scope],['组队',item.cost.team],['报名费',item.cost.registration_fee],['模型费',item.cost.model_fee],['设备',item.cost.hardware],['成本依据',item.cost.basis],['奖项路径',item.award],['当届状态',item.cycle]])addFact(inner,label,value);
 more.append(inner);card.append(more);
 card.append(text('p','证据：'+item.evidence,'evidence'));
 const actions=document.createElement('div');actions.className='actions';
 actions.append(sourceLink('看完整赛事卡 →',item.card,'primary'));
 if(item.tutorial)actions.append(sourceLink('打开实践教程',item.tutorial,'secondary'));
 if(item.tool_url)actions.append(sourceLink('工具出处',item.tool_url,'source-link'));
 card.append(actions);return card;
}
function render(){
 const words=normalizeText(query.value).split(/[,，;；]/).filter(Boolean);
 const matches=sorted.filter(item=>(view.value==='all'||item.rank!==null)&&words.every(word=>item.search.includes(word))&&(education.value==='all'||item.education.includes(education.value))&&(equipment.value==='all'||(equipment.value==='mixed'?item.equipment.includes('mixed')||(item.equipment.includes('software')&&item.equipment.includes('hardware')):item.equipment.includes(equipment.value)))&&(decision.value==='all'||item.decision_code===decision.value));
 const fragment=document.createDocumentFragment();for(const item of matches)fragment.append(createCard(item));cardGrid.replaceChildren(fragment);empty.hidden=matches.length>0;
 resultCount.textContent='找到 '+matches.length+' 条入口';
}
form.addEventListener('input',render);form.addEventListener('change',render);
form.addEventListener('submit',event=>{event.preventDefault();render();});
form.addEventListener('reset',()=>{requestAnimationFrame(render);});
document.getElementById('empty-reset').addEventListener('click',()=>{form.reset();query.focus();});
render();
</script>
</body>
</html>
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'docs/explorer.html')
    parser.add_argument('--check',action='store_true',help='Check the generated HTML without rewriting it')
    args = parser.parse_args()
    raw = json.loads((ROOT/'data/competitions.json').read_text('utf8'))
    items = [normalize(item) for item in raw]
    ranked = [item for item in items if item['rank'] is not None]
    if sorted(item['rank'] for item in ranked) != list(range(1,28)):
        raise ValueError('The reference order must contain each rank 1–27 exactly once.')
    if len({item['id'] for item in items}) != len(items):
        raise ValueError('Duplicate catalog IDs.')
    data = json.dumps(items, ensure_ascii=False, separators=(',',':')).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    output = HTML.replace('__TOTAL__',str(len(items))).replace('__RANKED__',str(len(ranked))).replace('__DATE__',DATE).replace('__DATA__',data)
    if args.check:
        if not args.output.exists() or args.output.read_text('utf8')!=output:raise SystemExit('Stale generated HTML: '+str(args.output))
    else:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(output,encoding='utf8',newline='\n')
    print(json.dumps({'output':str(args.output),'entries':len(items),'ranked':len(ranked),'bytes':args.output.stat().st_size,'external_runtime_dependencies':0},ensure_ascii=False))


if __name__=='__main__':
    main()
