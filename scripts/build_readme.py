"""Generate the reader homepage and share assets from the canonical contest data."""
from pathlib import Path
import argparse,html,json

ROOT=Path(__file__).resolve().parents[1]
REPO='https://github.com/Rain-dust/HowToCompeteBetter'
DATE='2026-11-17'
CHECK_ONLY=False
STALE=[]

def emit(path,text):
    if CHECK_ONLY:
        if not path.is_file() or path.read_text('utf8')!=text:STALE.append(path.relative_to(ROOT).as_posix())
    else:path.write_text(text,encoding='utf8',newline='\n')

def safe(value):
    return str(value or '待核').replace('|','／').replace('\n',' ')

def short(value,n=48):
    value=safe(value)
    return value if len(value)<=n else value[:n-1]+'…'

def load():
    rows=json.loads((ROOT/'data/competitions.json').read_text('utf8'))
    ranked=sorted((r for r in rows if isinstance(r.get('rank'),int)),key=lambda r:r['rank'])
    assert [r['rank'] for r in ranked]==list(range(1,28))
    assert len({r['id'] for r in rows})==len(rows)
    for r in rows:
        assert (ROOT/r['card_path']).is_file(),r['id']
    return rows,ranked

def generate_readme(rows,ranked):
    lines=[
        '# 高性价比大学生竞赛指南','',
        '**找到适合自己的比赛，用 Agent 做出完整作品。**','',
        '| 你现在想做什么 | 从这里开始 |',
        '| --- | --- |',
        '| **还没选比赛** | [按学历、设备和目标找比赛](docs/competition-catalog.md) |',
        '| **已有 Codex，想做数模** | [准备检查 → 安装 → 启动](docs/coding-agent.md) |',
        '| **已有项目，准备参赛** | [核评分、补证据、做演示与答辩](docs/project-delivery.md) |','',
        '[PDF预览](guide.pdf) · [下载PDF]('+REPO+'/raw/refs/heads/main/guide.pdf) · [先看真实数模成果](examples/cumcm2024b/README.md) · [零依赖小样例](templates/contest-starter-example/README.md)','',
        '## 先看这五项','',
        '**序号是制作参考顺序；当届建议单独看。** 计设的Codex许可待核，统计建模核心生成受限，不能仅凭排在前面决定报名。[排序怎么读](docs/how-to-read-ranking.md)','',
        '| 参考序号 / 赛事详情 | 当届怎么选 | 工具与开打 |',
        '| --- | --- | --- |',
    ]
    for r in ranked[:5]:
        tool='[教程]('+r['tool_tutorial']+')' if r.get('tool_tutorial') else '[做法]('+r['card_path']+'#怎么开始)'
        if r.get('tool_url'):tool+=' · [GitHub]('+r['tool_url']+')'
        elif (r.get('top5_view') or {}).get('github'):
            tool+=' · [可选技能GitHub]('+r['top5_view']['github'][0][1]+')'
        lines.append('| **'+str(r['rank'])+'. ['+safe(r['name'])+']('+r['card_path']+')** | **'+safe(r['decision_label'])+'**<br>'+short(r.get('decision_note'),43)+' | '+tool+' |')
    lines += ['', '<details>', '<summary><strong>前五：展开复制安装和启动指令</strong></summary>','',
              '先按上表选择练习或正式赛范围。数模只有一条默认安装主线；其他项目按具体赛项和环境配置。','']
    for r in ranked[:5]:
        view=r.get('top5_view') or {}
        lines += ['### '+str(r['rank'])+'. '+safe(r['name']),'',
                  '**'+safe(r['decision_label'])+'。** [完整赛事卡]('+r['card_path']+')','']
        if r['rank']==1:
            lines += ['[Codex完整安装与开跑](docs/coding-agent.md) · [Modex官方步骤](docs/modex.md)','']
        else:
            lines += ['安装：','','~~~text',view.get('install','先按赛事卡确认具体平台和依赖，再配置项目环境。'),'~~~','']
        lines += ['启动：','','~~~text',view.get('start',r.get('getting_started','先读取完整题面、当届规则和评分表，跑通最小基线。')),'~~~','']
    lines += ['</details>','',
        '<details>','<summary><strong>完整连续参考顺序 1–27：点名字直接看赛事卡</strong></summary>','',
        '| 参考序号 | 比赛 | 当届建议 |','| :--: | --- | --- |']
    for r in ranked:
        lines.append('| '+str(r['rank'])+' | ['+safe(r['name'])+']('+r['card_path']+') | '+safe(r['decision_label'])+' |')
    lines += ['','</details>','',
        '## 选好以后，完成第一步','',
        '| 卡在哪里 | 直接拿走 |',
        '| --- | --- |',
        '| 不知道自己能报什么、学校认不认 | [三关选赛卡与校内资源](docs/competition-playbook.md) |',
        '| 没有数据或不知道怎么引用 | [原始数据入口与来源台账](docs/data-sources.md) |',
        '| 第一次让Agent做完整项目 | [已填小样例](templates/contest-starter-example/README.md) → [空白模板](templates/contest-starter/README.md) |',
        '| 想看代码、论文和实际运行结果 | [2024国赛B：17页论文与复现包](examples/cumcm2024b/README.md) |','',
        '## 下载与查阅','',
        '- [指南PDF](guide.pdf)：有章节书签、可点击导航和返回导航入口。',
        '- [全部'+str(len(rows))+'条参考](docs/competition-catalog.md)：统一赛事卡，分别写资格、奖项路径、成本、人工任务与依据。',
        '- [下载离线筛选页]('+REPO+'/releases/latest/download/explorer.html)：保存HTML后用浏览器打开；筛选无需联网，打开详情需要联网。',
        '- [开赛模板ZIP](templates/contest-starter.zip) · [版本下载](https://github.com/Rain-dust/HowToCompeteBetter/releases/latest)','',
        '<details>','<summary>PDF首页预览</summary>','',
        '<a href="guide.pdf"><img src="assets/ranking-preview.png" alt="指南首页，点击查看有导航的完整PDF" width="380"></a>','',
        '</details>','',
        '## 依据与更新','',
        '数模记录：Codex实际完成历史国赛B题，经中断恢复与修正；Modex整理官方教程，Claude未做本轮端到端运行。历史练习与获奖验证分开。','',
        '[真实参赛反馈](docs/field-feedback.md) · [证据与来源](docs/research/README.md) · [更新记录](CHANGELOG.md) · [贡献方式](CONTRIBUTING.md)','',
        '反馈库保留75篇原帖、22份外部材料；二手知识整理单列，不能推出获奖率。各赛事卡显示资料核查日期，页面更新不表示所有当届规则已重查。','',
        '[提交参赛经历]('+REPO+'/issues/new?template=experience.yml) · [纠错与补规则]('+REPO+'/issues/new?template=correction.yml)','',
        '页面更新：**'+DATE+'**。结构灵感来自[高性价比人生指南](https://github.com/eternity4719/HowToLiveBetter)，竞赛资料独立整理。','',
        '<!-- Generated by scripts/build_readme.py from data/competitions.json. -->',''
    ]
    emit(ROOT/'README.md','\n'.join(lines))

def generate_share(ranked):
    lines=['《大学生用Agent做竞赛作品：27项制作参考顺序》','',
        '序号看制作适配，当届资格和AI使用范围另看赛事卡。计设Codex许可待核，统计建模核心生成受限；历史经历不能证明下一届许可。','']
    lines += [str(r['rank'])+'. '+r['name'] for r in ranked]
    lines += ['','项目收录逐赛详情、工具与启动教程、PDF、真实反馈和复现案例：',REPO,'']
    emit(ROOT/'social/x-post.txt','\n'.join(lines))

def generate_ranking_svg(ranked):
    width=840;row_h=143;height=242+len(ranked)*row_h
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
         '<rect width="100%" height="100%" fill="#f3f7f8"/><g font-family="Microsoft YaHei,SimHei,sans-serif">',
         '<text x="38" y="53" fill="#007e87" font-size="17">HOW TO COMPETE BETTER</text>',
         '<text x="38" y="104" fill="#162c3b" font-size="32" font-weight="700">大学生竞赛 · 27项制作参考顺序</text>',
         '<text x="38" y="146" fill="#526673" font-size="19">当届怎么选，单独看每项标签；点卡片进入赛事详情。</text>',
         '<text x="38" y="181" fill="#526673" font-size="18">未知费用和权限明示待核，不把名次当作获奖率。</text>']
    def wrap(text,size=31):return [text[i:i+size] for i in range(0,len(text),size)]
    for i,r in enumerate(ranked):
        y=211+i*row_h
        out += [f'<a href="{REPO}/blob/main/{r["card_path"]}"><rect x="28" y="{y}" width="784" height="130" rx="13" fill="white" stroke="#dbe5e8"/>',
                f'<text x="46" y="{y+34}" fill="#007e87" font-size="21" font-weight="700">{r["rank"]:02d}</text>']
        titles=wrap(r['name'],29)
        for j,t in enumerate(titles):out.append(f'<text x="96" y="{y+32+j*26}" fill="#162c3b" font-size="22" font-weight="700">{html.escape(t)}</text>')
        out.append(f'<text x="96" y="{y+91}" fill="#007e87" font-size="19">{html.escape(short(r["decision_label"],30))}</text>')
        out.append(f'<text x="96" y="{y+117}" fill="#526673" font-size="16">{html.escape(short(r.get("evidence_label"),40))}</text></a>')
    out.append('</g></svg>')
    emit(ROOT/'assets/ranking.svg',''.join(out))

def generate_entry_assets(rows):
    entries=[('01','还没选比赛','先按身份、资源和目标缩小范围','docs/competition-catalog.md'),
             ('02','已有Codex，想做数模','从准备检查直接安装和启动','docs/coding-agent.md'),
             ('03','已有项目，准备参赛','核评分、补证据、做演示与答辩','docs/project-delivery.md')]
    out=['<svg xmlns="http://www.w3.org/2000/svg" width="840" height="810" viewBox="0 0 840 810"><rect width="840" height="810" fill="#f3f7f8"/><g font-family="Microsoft YaHei,SimHei,sans-serif">',
         '<text x="42" y="58" fill="#007e87" font-size="18">HOW TO COMPETE BETTER</text>',
         '<text x="42" y="115" fill="#162c3b" font-size="35" font-weight="700">从你的问题开始</text>']
    for i,(num,title,sub,path) in enumerate(entries):
        y=153+i*184
        out += [f'<a href="{REPO}/blob/main/{path}"><rect x="34" y="{y}" width="772" height="162" rx="17" fill="white" stroke="#dbe5e8"/>',
                f'<text x="58" y="{y+37}" fill="#007e87" font-size="20" font-weight="700">{num}</text>',
                f'<text x="58" y="{y+84}" fill="#162c3b" font-size="29" font-weight="700">{title}</text>',
                f'<text x="58" y="{y+124}" fill="#526673" font-size="21">{sub}</text></a>']
    out += [f'<text x="42" y="743" fill="#526673" font-size="19">27项制作参考 · {len(rows)}张赛事卡 · 不用先读完全部资料</text>',
            f'<text x="42" y="778" fill="#007e87" font-size="16">{REPO.replace("https://","")} · {DATE}</text></g></svg>']
    emit(ROOT/'assets/overview.svg',''.join(out))
    social=f'''<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="640" viewBox="0 0 1280 640"><rect width="1280" height="640" fill="#f3f7f8"/><g font-family="Microsoft YaHei,SimHei,sans-serif"><text x="68" y="86" fill="#007e87" font-size="22">HOW TO COMPETE BETTER</text><text x="68" y="182" fill="#162c3b" font-size="58" font-weight="700">高性价比大学生竞赛指南</text><text x="68" y="247" fill="#526673" font-size="29">先找适合自己的比赛，再用Agent做出完整作品。</text><rect x="68" y="301" width="1144" height="158" rx="19" fill="white" stroke="#dbe5e8"/><text x="101" y="361" fill="#007e87" font-size="33" font-weight="700">27项制作参考　·　{len(rows)}张赛事卡　·　数模完整实战</text><text x="101" y="411" fill="#526673" font-size="25">当届建议、成本未知项、人工任务与工具步骤分别写清。</text><text x="68" y="540" fill="#162c3b" font-size="26">按问题导航 → 点比赛看详情 → 跑一个最小成果</text><text x="68" y="596" fill="#007e87" font-size="21">{REPO.replace("https://","")}</text></g></svg>'''
    emit(ROOT/'assets/social-preview.svg',social)

def main():
    global CHECK_ONLY
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args();CHECK_ONLY=args.check
    rows,ranked=load()
    generate_readme(rows,ranked);generate_share(ranked);generate_ranking_svg(ranked);generate_entry_assets(rows)
    if STALE:raise SystemExit('Stale reader views: '+', '.join(STALE))
    print(json.dumps({'homepage':'README.md','reference_ranks':len(ranked),'catalog':len(rows),'source':'data/competitions.json'},ensure_ascii=False))

if __name__=='__main__':main()
