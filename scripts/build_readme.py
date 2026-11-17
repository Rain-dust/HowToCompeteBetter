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

def load_chapters():
    chapters=json.loads((ROOT/'data/chapters.json').read_text('utf8'))
    assert [c['id'] for c in chapters]==[f'{i:02d}' for i in range(1,11)]
    for chapter in chapters:
        assert all(chapter.get(key) for key in ['title','file','question','summary','sections']),chapter
    return chapters

def generate_readme(rows,ranked):
    chapters=load_chapters()
    section_count=sum(len(c['sections']) for c in chapters)
    def chapter_link(index):
        c=chapters[index-1]
        return '['+str(index)+'. '+c['title']+']('+c['file']+')'
    lines=[
        '<div align="center">','',
        '<a href="guide.pdf"><img src="assets/cover.png" alt="高性价比大学生竞赛指南：选比赛、找工具、跑实战、交作品；点击预览PDF" width="820"></a>','',
        '# 高性价比大学生竞赛指南','',
        '哪些比赛值得打，用什么 Agent，拿到赛题后怎样开始？<br>',
        '把选赛、工具、数模实战和作品交付，写成可以按问题查的十章指南。','',
        '**27项连续参考排名 · '+str(len(rows))+'条赛事参考 · 完整数模教程与复现案例**','',
        '### [从目录开始](#目录) · [直接做数模]('+chapters[3]['file']+') · [预览 PDF](guide.pdf)','',
        '<table>',
        '<tr><td width="64" align="right"><b>下载</b></td><td align="left">','',
        '[PDF 预览](guide.pdf) · [PDF 下载]('+REPO+'/raw/refs/heads/main/guide.pdf) · [离线筛选 HTML]('+REPO+'/releases/latest/download/explorer.html) · [开赛模板 ZIP](templates/contest-starter.zip)','',
        '</td></tr>',
        '<tr><td width="64" align="right"><b>查阅</b></td><td align="left">','',
        '[全书目录](book/README.md) · [1–27 排名]('+chapters[1]['file']+'#ranking) · [全部赛事卡](docs/competition-catalog.md) · [资料与核查](docs/research/README.md)','',
        '</td></tr>',
        '<tr><td width="64" align="right"><b>实战</b></td><td align="left">','',
        '[Modex 官方教程](docs/modex.md) · [Codex 安装开跑](docs/coding-agent.md) · [国赛 B 题成果](examples/cumcm2024b/README.md) · [零依赖小样例](templates/contest-starter-example/README.md)','',
        '</td></tr>',
        '<tr><td width="64" align="right"><b>反馈</b></td><td align="left">','',
        '[参赛者怎么说](docs/field-feedback.md) · [提交参赛经历]('+REPO+'/issues/new?template=experience.yml) · [纠错补充]('+REPO+'/issues/new?template=correction.yml)','',
        '</td></tr></table>','',
        '<sub>离线筛选页下载后用浏览器打开。赛事参考含赛项和平台；报名时以具体届次、组别和学校认定为准。</sub>','',
        '</div>','',
        '---','',
        '## 这本指南回答什么','',
        '| 你的问题 | 去哪看 |','| --- | --- |',
    ]
    for c in chapters:
        lines.append('| '+safe(c['question'])+' | ['+str(int(c['id']))+'. '+c['title']+']('+c['file']+') |')
    lines += ['','## 怎么读','',
        '- **还没选比赛**：从'+chapter_link(1)+'开始，挑出两三项，再读'+chapter_link(2)+'核资格、奖项和学校认定。',
        '- **现在就想跑数模**：现成软件看'+chapter_link(3)+'；已有 Codex 看'+chapter_link(4)+'。运行结果和复现材料在'+chapter_link(5)+'。',
        '- **已有想法或项目**：软件作品看'+chapter_link(6)+'，仿真项目看'+chapter_link(7)+'，最后按第8、9章补数据、材料和演示。','',
        '排名反映 Agent 制作适配，正式参赛建议另列。计设的外部 Codex 许可待核，统计建模的正式赛核心生成受限；具体结论和原文在对应赛事卡。','',
        '## 目录','',
    ]
    featured={'01':['s01','s03'],'02':['ranking','s04'],'03':['s02','s05','s08'],
              '04':['s02','s04','s07'],'05':['s02','s03','s05'],'06':['s02','s03'],
              '07':['s01','s02','s03'],'08':['practice','s01','paper'],
              '09':['s01','s03','s04'],'10':['s01','s03','s04']}
    for c in chapters:
        selected=[s for s in c['sections'] if s['id'] in featured[c['id']]]
        lines += ['**['+str(int(c['id']))+'. '+c['title']+']('+c['file']+')**','',
                  ' · '.join('['+s['title']+']('+c['file']+'#'+s['id']+')' for s in selected),'']
    lines += ['[展开'+str(section_count)+'节完整目录](book/README.md) · [按条件找比赛](docs/competition-catalog.md) · [查看27项连续排名]('+chapters[1]['file']+'#ranking)','',
        '## 前五：工具与开打指令','',
        '先看当届建议，再复制对应指令。每项的 GitHub、安装和启动写在一起。','',
        '这些任务默认你已在 Agent 中打开本仓库。第一次使用，先按[第4章创建工作区](book/04-用Codex完成数模.md#s02)，再把题面、规则和附件放进 `inputs/`。','',
        '| 参考序号 / 比赛 | GitHub 与当届建议 |','| --- | --- |',
    ]
    for r in ranked[:5]:
        repos=(r.get('top5_view') or {}).get('github') or []
        primary=repos[:2] if r['rank']==1 else repos[:1]
        labels=[]
        for label,url in primary:
            slug='/'.join(url.rstrip('/').split('/')[3:5])
            labels.append('['+slug+']('+url+')')
        lines.append('| **'+str(r['rank'])+'. ['+safe(r['name'])+']('+r['card_path']+')** | '+' · '.join(labels)+'<br>'+safe(r['decision_label'])+' |')
    lines += ['']
    for r in ranked[:5]:
        view=r.get('top5_view') or {}
        lines += ['<details>','<summary><strong>'+str(r['rank'])+'. '+safe(r['name'])+'：展开安装与开打</strong></summary>','',
                  '**'+safe(r['decision_label'])+'。** [赛事详情]('+r['card_path']+')','']
        lines.append(' · '.join('['+label+']('+url+')' for label,url in view.get('github',[])))
        lines += ['']
        if r['rank']==1:
            lines += ['[Codex 完整安装步骤](docs/coding-agent.md) · [Modex 官方配置教程](docs/modex.md)','']
        lines += ['**复制给 Agent：安装**','','~~~text',view.get('install','先按赛事卡确认平台和依赖，再配置项目环境。'),'~~~','',
                  '**复制给 Agent：开打**','','~~~text',view.get('start',r.get('getting_started','先读取题面、当届规则和评分表，跑通最小基线。')),'~~~','',
                  '</details>','']
    lines += ['<details>','<summary>展开完整的 1–27 连续参考排名</summary>','',
              '| 序号 | 比赛 | 当届建议 |','| :--: | --- | --- |']
    for r in ranked:
        lines.append('| '+str(r['rank'])+' | ['+safe(r['name'])+']('+r['card_path']+') | '+safe(r['decision_label'])+' |')
    lines += ['','</details>','',
        '## PDF 预览','',
        '[预览完整 PDF](guide.pdf) · [直接下载]('+REPO+'/raw/refs/heads/main/guide.pdf)','',
        '<a href="guide.pdf"><img src="assets/ranking-preview.png" alt="指南PDF首页预览，点击打开完整文档" width="310"></a>','',
        'PDF 带可点击目录和章节书签；想在 GitHub 按章阅读，直接打开[全书目录](book/README.md)。','',
        '## 内容从哪里来','',
        '赛事规则、作者经历、学生复盘和工具实测分别记载。反馈库保留75篇原帖、22份外部材料，二手知识整理另列，不能据此计算获奖率。','',
        '数模实测完成了历史国赛B题的代码、图表和17页论文，经中断恢复与修正；Modex提供官方教程，Claude未做本轮端到端运行。具体过程见[案例记录](examples/cumcm2024b/README.md)。','',
        '[资料与核查](docs/research/README.md) · [排序怎么定](docs/how-to-read-ranking.md) · [更新记录](CHANGELOG.md) · [如何贡献](CONTRIBUTING.md)','',
        '## 致谢','',
        '本项目参考了 **[高性价比人生指南 · HowToLiveBetter](https://github.com/eternity4719/HowToLiveBetter)** 的书式首页、问题导航和编号章节结构。竞赛资料、工具指令、视觉资产与实战记录由本项目独立整理。','',
        '页面更新：**'+DATE+'**。规则核查日期逐项写在赛事卡，页面更新不表示全部当届规则已重新核查。','',
        '<!-- Generated by scripts/build_readme.py from data/competitions.json and data/chapters.json. -->',''
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
    chapters=load_chapters()
    cover='''<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="450" viewBox="0 0 1280 450">
<rect width="1280" height="450" rx="16" fill="#f6f5f0"/>
<path d="M62 53h54" stroke="#277166" stroke-width="4"/>
<g font-family="Microsoft YaHei,SimHei,sans-serif">
<text x="134" y="60" fill="#277166" font-size="21" letter-spacing="2">HOW TO COMPETE BETTER</text>
<text x="62" y="173" fill="#203c35" font-size="60" font-weight="700">高性价比大学生竞赛指南</text>
<text x="65" y="236" fill="#65726b" font-size="29">从选比赛到交作品，按问题查，照步骤做。</text>
<path d="M64 282h1152" stroke="#d9ded7" stroke-width="1"/>
<text x="65" y="344" fill="#277166" font-size="22" font-weight="700">01　选比赛</text>
<text x="65" y="388" fill="#65726b" font-size="22">先看排名，再看资格与投入</text>
<text x="472" y="344" fill="#277166" font-size="22" font-weight="700">02　跑实战</text>
<text x="472" y="388" fill="#65726b" font-size="22">找到工具，完成一套真题</text>
<text x="876" y="344" fill="#277166" font-size="22" font-weight="700">03　交作品</text>
<text x="876" y="388" fill="#65726b" font-size="22">补齐数据、材料与演示</text>
</g></svg>'''
    emit(ROOT/'assets/cover.svg',cover)
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
    social=f'''<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="640" viewBox="0 0 1280 640"><rect width="1280" height="640" fill="#f6f5f0"/><g font-family="Microsoft YaHei,SimHei,sans-serif"><path d="M68 77h55" stroke="#277166" stroke-width="4"/><text x="145" y="85" fill="#277166" font-size="22" letter-spacing="2">HOW TO COMPETE BETTER</text><text x="68" y="189" fill="#203c35" font-size="58" font-weight="700">高性价比大学生竞赛指南</text><text x="70" y="254" fill="#65726b" font-size="29">从选比赛到交作品，按问题查，照步骤做。</text><path d="M68 303h1144" stroke="#d9ded7" stroke-width="1"/><text x="70" y="375" fill="#277166" font-size="32" font-weight="700">{len(chapters)}章指南　·　27项参考排名　·　{len(rows)}张赛事卡</text><text x="70" y="430" fill="#65726b" font-size="27">Modex官方教程 / Codex实跑 / 真题复现 / 作品交付</text><text x="70" y="532" fill="#203c35" font-size="27">选比赛　→　找工具　→　跑实战　→　交作品</text><text x="70" y="591" fill="#277166" font-size="21">{REPO.replace("https://","")}</text></g></svg>'''
    emit(ROOT/'assets/social-preview.svg',social)

def main():
    global CHECK_ONLY
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args();CHECK_ONLY=args.check
    rows,ranked=load()
    generate_readme(rows,ranked);generate_share(ranked);generate_ranking_svg(ranked);generate_entry_assets(rows)
    if STALE:raise SystemExit('Stale reader views: '+', '.join(STALE))
    print(json.dumps({'homepage':'README.md','reference_ranks':len(ranked),'catalog':len(rows),'source':'data/competitions.json'},ensure_ascii=False))

if __name__=='__main__':main()
