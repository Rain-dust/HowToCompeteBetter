"""Build the numbered reading edition from maintained tutorials and contest data."""
from pathlib import Path
from urllib.parse import unquote
import argparse,json,os,re

ROOT=Path(__file__).resolve().parents[1]
REPO='https://github.com/Rain-dust/HowToCompeteBetter'
CHECK=False
STALE=[]

def emit(path,text):
    if CHECK:
        if not path.is_file() or path.read_text('utf8')!=text:STALE.append(path.relative_to(ROOT).as_posix())
    else:
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(text,encoding='utf8',newline='\n')

def link(path):
    return '../'+path

def rebase(text,source):
    """Retain the original targets when a maintained section is read in book/."""
    def convert(href):
        if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',href) or href.startswith('//'):return href
        pure,sep,fragment=href.partition('#')
        pure,querysep,query=pure.partition('?')
        target=(ROOT/source).parent/unquote(pure) if pure else ROOT/source
        relative=os.path.relpath(target.resolve(),ROOT/'book').replace('\\','/')
        return relative+('?' + query if querysep else '')+('#'+fragment if sep else '')
    text=re.sub(r'(!?\[[^\]]*\]\()([^\s)]+)(\))',lambda m:m[1]+convert(m[2])+m[3],text)
    return re.sub(r'((?:href|src)=\")([^\"]+)(\")',lambda m:m[1]+convert(m[2])+m[3],text)

def source_parts(path):
    text=(ROOT/path).read_text('utf8')
    matches=list(re.finditer(r'^## (.+)$',text,re.M))
    intro=re.sub(r'^# .+\n+','',text[:matches[0].start()],count=1).strip() if matches else ''
    parts={m[1]:text[m.end():matches[i+1].start() if i+1<len(matches) else len(text)].strip() for i,m in enumerate(matches)}
    return intro,parts

def safe(value):return str(value or '待核').replace('|','／').replace('\n',' ')

def contest_section(row):
    view=row.get('top5_view') or {}
    lines=['**'+safe(row['name'])+'：'+safe(row['decision_label'])+'。**',
           '',row['decision_note'],'',
           '[完整赛事卡]('+link(row['card_path'])+') · 规则资料核查至 '+row['rules_checked_through'],'',
           '**对应工具仓库**','']
    for label,url in view.get('github',[]):lines.append('- ['+label+']('+url+')')
    if not view.get('github') and row.get('tool_url'):lines.append('- ['+row['tool_name']+']('+row['tool_url']+')')
    lines += ['','**复制给 Codex：安装与预检**','','~~~text',view.get('install','先读取具体赛题和工具权限，按完整赛事卡配置。'),'~~~','',
              '**复制给 Codex：开打**','','~~~text',view.get('start',row['detail']['prompt']),'~~~','',
              '**需要交出来：** '+view.get('deliver',row['deliver']),'','**你仍需要完成：** '+ '；'.join(row['human_tasks'])+'。']
    return '\n'.join(lines)

def custom(section,ranked):
    kind=section['kind']
    if kind=='ranking':
        lines=['**序号保持 1–27 连续排列，按名字进入完整赛事卡。** 正式参赛先看当届建议；资格、工具范围和奖项认定另核。','',
               '| 序号 | 比赛完整名字 / 具体赛项 | 当届建议 |','| :--: | --- | --- |']
        lines += ['| '+str(r['rank'])+' | ['+safe(r['name'])+']('+link(r['card_path'])+') | '+safe(r['decision_label'])+' |' for r in ranked]
        lines += ['','[全部 73 条参考入口](../docs/competition-catalog.md) · [下载离线筛选页]('+REPO+'/releases/latest/download/explorer.html)（保存后用浏览器打开）。',
                  '','73 条包含母赛分支、平台、境外与省级入口，不代表 73 项独立竞赛。']
        return '\n'.join(lines)
    if kind=='contest':return contest_section(next(r for r in ranked if r['rank']==section['rank']))
    bodies={
      'software_selection':'''先拿到当届赛题、评分表和提交清单。别先让 Agent 做一个大而全的产品：先确认输入数据、接口、平台与演示环境可用，再把一个评分动作从头跑通。

| 先问什么 | 你需要拿到什么 |
| --- | --- |
| 评委按什么打分？ | 评分点 → 验收动作 → 对应文件或演示位置 |
| 数据、SDK、接口从哪来？ | 可实际读取的数据、可运行的官方示例或接口响应 |
| 最小作品交什么？ | 一个真实输入、一条完整业务链、一个可以检查的输出 |
| 工具范围是什么？ | 当届允许的开发方式、模型/平台要求和声明位置 |

计设与软件杯都适合用编码 Agent 推进开发，但本项目没有核到覆盖所有赛项的外部 Codex 许可；按下面的具体赛事卡确认范围再开工。''',
      'software_acceptance':'''先让 Agent 交出：能启动的程序、固定输入样本、对应输出、启动命令与一条可重复的验收过程。一个评分动作跑通后再加第二个，每次保留之前已通过的结果。

~~~text
先只完成评分表中最关键的一条业务链。把输入、操作、期望输出和实际结果写进验收记录；保存可运行版本。
通过后再扩展功能。完成前请在干净环境按 README 启动，核对异常输入、演示路径和失败提示。
最后把评分表逐条映射到测试、截图或演示时间点；未完成的项明确列出来。
~~~

有了可运行产品后，继续看[第 9 章：演示、答辩与提交](09-演示、答辩与提交.md)。想找同类赛事，打开[全部赛事目录](../docs/competition-catalog.md)，逐项读数据、设备和人工门槛。''',
      'rst_selection':'''RST 不是一种统一的交付方式。同一母赛下先确认届次、赛道和组别，再决定如何使用编码 Agent。

| 具体类型 | 第一件事 | 用什么证明做到了 |
| --- | --- | --- |
| 创新创业作品 | 对评分表做一个可运行的小产品 | 功能演示、真实输入输出与说明 |
| 仿真竞技 | 安装对应官方平台，运行原始基线 | 原始策略、环境版本、原始成绩与日志 |
| 硬件竞技 | 确认器材、维护、场地和现场要求 | 同设备实测与可复现的现场操作 |

本项目作者的省奖经历是**第 18 届创新创业赛道—前沿技术挑战组**；外部 Gemini 机器鱼国一自述来自第 19 届另一赛项。两者不能合成所有 RST 赛项都已跑通的证明。''',
      'rst_evidence':'''先保存官方基线版本和原始成绩，再做可单独撤回的小改动。对照时保持平台、输入和评测条件一致，保留多次运行结果与失败回放，不只挑最好的一次。

~~~text
先复现官方基线，不修改策略。记录平台和 SDK 版本、启动命令、输入、成绩及完整日志。
基线跑通后，每轮只改一项策略；在相同条件下与基线重复比较，汇总每次成绩与失败原因。
保留能够回退的代码、失败回放和环境说明。未实际运行的结果不能填成成绩。
~~~

这里没有提供经核验的 RST 专用保奖 skill。创新作品需要 Web 界面时才选界面技能；仿真策略应让 Codex 读取实际平台和 SDK，不能用网页模板代替。''',
      'practice':'''还没做过完整项目，先跑这个小样例。它使用仓库内的**合成工单数据**，不调用模型、不联网取数，也不需要密钥。

在仓库根目录执行：

~~~text
python templates/contest-starter-example/run.py
~~~

你会得到汇总表、清洗拒绝记录、图表、报告与验收记录：输入 15 行、保留 10 行、拒绝 5 行，总时长 450 分钟。这个数字来自固定练习数据，不是学校业务数据或参赛成绩。

先打开[已填样例说明](../templates/contest-starter-example/README.md)核对输出，再复制[空白项目模板](../templates/contest-starter/README.md)放自己的题目与数据。[下载两个模板 ZIP](../templates/contest-starter.zip)。''',
      'paper':'''把“来源 → 清洗 → 计算 → 图表 → 正文”连成一条能复查的链。正文中的每个关键数字能指回结果文件；图表能指回生成脚本；外部事实能指回原始来源。

~~~text
先读取完整题面、评分表和来源台账。保留原始文件，只在工作副本上清洗；输出缺失、重复和拒绝记录。
每张图记录输入文件和生成脚本，每个关键数字记录结果文件与计算口径。没有数据时明确缺口，不能补写成调查、访谈或实测。
先完成真实计算和复核，再组织论文或项目材料；逐项检查正文数字、图表、代码输出是否一致。
~~~

数模的实际例子见[第 5 章](05-从真题看完整成果.md)。项目书、商业计划书、论文各有不同提交要求，进入[第 9 章](09-演示、答辩与提交.md)再按评分表整理。''',
      'feedback_scope':'''本批实读资料截至 **2026-11-12**：45 篇小红书原帖详情、30 篇贴吧原帖详情，其中 74 篇有非空文字正文；取得 270 条去重小红书评论、121 条贴吧楼层记录。另有 22 份外部材料，分开记录。

这些是能找到并读到的经验材料，不是随机抽样；没有完整参赛人数和未获奖人数，不能计算获奖率。知识库整理、官方通知与外部经验也不是同一种证据，不能为了增加数量混在一起。

[查看原帖反馈与反例](../docs/field-feedback.md) · [查看证据资料总入口](../docs/research/README.md)''',
      'feedback_evidence':'''| 资料类型 | 可以回答什么 | 不能由此推出什么 |
| --- | --- | --- |
| 作者历史经历 | 作者在哪类作品、哪一赛项用过 Agent | 未给出的届次、每个杯赛的具体奖项或下一届许可 |
| 外部参赛自述 | 过程、卡点、工具和奖项的原作者说法 | 独立身份核真或总体获奖率 |
| 本仓库真实运行 | 固定环境、固定输入下产物和复算结果 | 正式竞赛成绩、任意题目都能完成 |
| 官方规则与通知 | 对应年份、赛项的资格、流程与限制 | 未写明的工具许可或当前正在报名 |
| 官方教程整理 | 已读手册描述的安装与操作步骤 | 已在本机安装、付费或实际出论文 |

本项目跑通的是 **Codex + MathModelAgent 历史题路线**；Modex 是官方教程路线，Claude 只有兼容安装说明。它们的验证状态分别标注。''',
      'feedback_update':'''真正报名之前，重新查当前届次、具体赛项、AI 条款、报名时间与本校认定。赛事卡保留各自的资料核查日期；页面更新不等于所有规则都重查了一遍。

想补一段参赛经历，尽量提供：**比赛完整名字、届次、具体赛项、使用的 Agent/模型、人工做了什么、实际结果、可公开的原始链接或材料**。不方便公开身份可以说明，缺失信息不替你补写。

- [提交亲历反馈]('''+REPO+'''/issues/new?template=experience.yml)
- [提交纠错与规则更新]('''+REPO+'''/issues/new?template=correction.yml)
- [看贡献说明](../CONTRIBUTING.md) · [看更新记录](../CHANGELOG.md)

阅读框架参考[高性价比人生指南 HowToLiveBetter](https://github.com/eternity4719/HowToLiveBetter)：借鉴其问题目录、编号章节和分层查阅方式；竞赛内容、数据和工具实测独立整理。'''
    }
    if kind=='feedback_conclusions':
        _,parts=source_parts('docs/field-feedback.md')
        return rebase(parts['直接影响排名的结论'],'docs/field-feedback.md')+'\n\n[逐条阅读原帖与核验边界](../docs/field-feedback.md)。'
    if kind=='data_entry_points':
        intro,_=source_parts('docs/data-sources.md')
        table=[line for line in intro.splitlines() if line.startswith('|')][2:]
        lines=['以下入口沿用 2026-11-16 的资料核查。先定位具体原始表，再核下载条件与使用范围；入口可见不表示已经拿到数据。','']
        for i,line in enumerate(table,1):
            cells=[c.strip() for c in line.strip('|').split('|')]
            assert len(cells)==4,cells
            title,entry,task,checks=cells
            lines += ['### '+str(i)+'. '+title,'','**入口：** '+entry,'','**交给 Agent：** '+task,'','**读数前检查：** '+checks,'']
        lines += ['行业报告和搜索指数可以帮助找关键词，但引用时要追到原始发布者、年份、样本与方法。搜索热度不是销量，第三方估算也不是自己的经营数据。']
        return '\n'.join(lines)
    if kind not in bodies:raise ValueError('Unknown book section: '+kind)
    return bodies[kind]

def nav(chapters,index):
    links=[]
    if index:links.append('[← '+str(index)+'. '+chapters[index-1]['title']+']('+Path(chapters[index-1]['file']).name+')')
    links.append('[总目录](README.md)')
    if index+1<len(chapters):links.append('['+str(index+2)+'. '+chapters[index+1]['title']+' →]('+Path(chapters[index+1]['file']).name+')')
    return ' · '.join(links)

def adapt_working_directory(chapter,section,body):
    """Make terminal starting directories explicit after moving prose into book/."""
    heading=section.get('source_heading','')
    if chapter['id']=='05':
        if heading=='复现计算':
            body=body.replace('进入本目录，在新的 Python 3.12 环境执行：','从仓库根目录开始，先进入示例目录，再在新的 Python 3.12 环境执行：')
            body=body.replace('~~~text\npython -m venv','~~~text\ncd examples/cumcm2024b\npython -m venv',1)
        elif heading=='编译论文':
            body=body.replace('先安装官方Typst0.15.1，再从本目录执行：','先安装官方 Typst0.15.1。以下命令在 `examples/cumcm2024b/` 执行：已按上一节执行 `cd` 的人保持当前目录；新终端先从仓库根目录执行 `cd examples/cumcm2024b`。')
        body=body.replace('本目录','`examples/cumcm2024b/`')
    elif chapter['id']=='04':
        if heading=='1. 创建工作区':
            body='**命令目录：** 从准备存放项目的父目录开始。下方 `cd HowToCompeteBetter` 之后保持在指南仓库根目录；后续预检与启动脚本也从这里运行。\n\n'+body
        elif heading in ('2. 放题目，先预检','3. 一次启动完整链'):
            body='**命令目录：`HowToCompeteBetter/` 仓库根目录。** 沿用上一节终端；另开终端时先进入该目录。\n\n'+body
        elif heading=='5. 中断后继续':
            body=body.replace('在目录中运行 `codex resume`','在 `my-math-run/` 工作区目录中运行 `codex resume`')
            body=body.replace('使用本仓库启动器可运行','使用本仓库启动器时，先回到 `HowToCompeteBetter/` 仓库根目录，再运行')
    return body

def build_chapter(chapter,index,chapters,ranked):
    lines=['# '+str(index+1)+'. '+chapter['title'],'','**'+chapter['summary']+'**','',
           '**这一章拿到什么：** '+chapter['takeaway'],'',nav(chapters,index),'',
           '**本章目录**','']
    for i,section in enumerate(chapter['sections'],1):lines.append('- ['+str(index+1)+'.'+str(i)+' '+section['title']+'](#'+section['id']+')')
    sources=[]
    for i,section in enumerate(chapter['sections'],1):
        lines += ['','---','', '<a id="'+section['id']+'"></a>','', '## '+str(index+1)+'.'+str(i)+' '+section['title'],'']
        if section.get('source'):
            source=section['source'];intro,parts=source_parts(source)
            body=parts[section['source_heading']]
            if source not in sources:
                sources.append(source)
                if intro and chapter['id'] in ('04','05'):body=intro+'\n\n'+body
            body=rebase(body,source)
            body=re.sub(r'^(#{3,6})\s+\d+(?:\.\d+)*\.?\s+',r'\1 ',body,flags=re.M)
        else:body=custom(section,ranked)
        body=adapt_working_directory(chapter,section,body)
        lines += [body.strip()]
    lines += ['','---','',nav(chapters,index),'','[回项目首页](../README.md) · [术语表](../docs/glossary.md) · [PDF](../guide.pdf)','']
    if chapter['id']=='01':lines += ['先过本章三关，再去[第 2 章看连续排名](02-看懂排名与奖项.md#ranking)。','']
    if sources:lines += ['<sub>本章资料：'+' · '.join('['+Path(p).stem+']('+link(p)+')' for p in sources)+'。资料日期以原记录为准。</sub>','']
    lines += ['<!-- Generated by scripts/build_book.py. Edit chapter metadata or maintained source tutorials. -->','']
    emit(ROOT/chapter['file'],'\n'.join(lines))

def build_contents(chapters):
    lines=['# 目录','','**按你现在遇到的问题读，选一条路线即可开始。**','',
           '[回项目首页](../README.md) · [PDF预览](../guide.pdf) · [术语表](../docs/glossary.md) · [全部赛事卡](../docs/competition-catalog.md)','',
           '## 先找自己的路线','',
           '| 你现在的情况 | 建议顺序 |','| --- | --- |',
           '| 还没选比赛 | 第 1 章选范围 → 第 2 章看连续排名 → 打开具体赛事卡 |',
           '| 想用成品软件做数模 | 第 3 章 Modex 官方步骤 → 第 5 章看真实成果 → 第 8、9 章准备材料 |',
           '| 已有 Codex，想跑完整数模链 | 第 4 章安装与启动 → 第 5 章真题成果 → 第 8、9 章核对交付 |',
           '| 已选软件、设计或仿真作品 | 第 6 或 7 章直接开始 → 第 8 章补数据 → 第 9 章做演示与答辩 |',
           '| 想知道依据够不够 | 第 10 章证据边界 → 原帖与规则来源 |','',
           '## 这份指南想回答的问题','',
           '| 问题 | 去哪看 |','| --- | --- |']
    for c in chapters:lines.append('| '+c['question']+' | ['+str(int(c['id']))+'. '+c['title']+']('+Path(c['file']).name+') |')
    lines += ['','## 完整章节与小节','']
    for c in chapters:
        filename=Path(c['file']).name
        lines += ['### ['+str(int(c['id']))+'. '+c['title']+']('+filename+')','',c['summary'],'']
        lines += ['- ['+str(int(c['id']))+'.'+str(i)+' '+s['title']+']('+filename+'#'+s['id']+')' for i,s in enumerate(c['sections'],1)]
        lines.append('')
    lines += ['## 附录与工具','',
              '- [73 条参考入口与统一赛事卡](../docs/competition-catalog.md)；含母赛分支和平台，不按 73 项独立比赛计数。',
              '- [离线筛选页下载]('+REPO+'/releases/latest/download/explorer.html)：下载后用浏览器打开。',
              '- [术语表](../docs/glossary.md)：全国性、省奖、学校认定、Agent、Skill、基线与复现。',
              '- [真实数模成果包](../examples/cumcm2024b/README.md) · [已填小练习](../templates/contest-starter-example/README.md) · [空白开赛模板](../templates/contest-starter/README.md)。',
              '- [资料与核查记录](../docs/research/README.md) · [历史来源列表](../docs/sources.md) · [更新记录](../CHANGELOG.md)。','',
              '阅读结构参考[高性价比人生指南](https://github.com/eternity4719/HowToLiveBetter)，竞赛资料独立整理。','',
              '<!-- Generated by scripts/build_book.py from data/chapters.json and maintained source tutorials. -->','']
    emit(ROOT/'book/README.md','\n'.join(lines))

def build_glossary():
    text='''# 术语表

**这些词不是一回事。** 遇到陌生词时回来查，不必先学完一套工具名词。

[回项目首页](../README.md) · [章节目录](../book/README.md) · [排序怎么读](how-to-read-ranking.md)

| 词 | 通俗解释 | 读本项目时怎么用 |
| --- | --- | --- |
| Agent | 能读文件、调用工具、改代码并继续完成任务的助手 | 看它实际交付什么；最后一句“完成”不能代替验收 |
| Coding Agent | 主要围绕代码、文件和终端工作的 Agent，例如 Codex、Claude Code | 本项目真实跑通的是固定环境下的 Codex 路线；Claude 未做本轮端到端实测 |
| Skill | 给 Agent 的一套任务步骤，常带脚本、模板与参考资料 | 安装完整技能和依赖，不是只复制一个提示词文件；见[数模安装教程](coding-agent.md) |
| 模型 | Agent 背后处理语言和代码的能力来源 | Agent 工具链与模型服务分开理解；安装软件不表示已有模型额度 |
| CLI | 在终端里输入命令使用的程序 | 装桌面应用不等于 CLI 命令能运行；先做教程预检 |
| 端到端 / 全流程 | 从输入题目走到计算、图表、文档与验收的一整条链 | 必须说明起点、终点、中断和人工修正；“全流程”不等于无人检查 |
| 基线 | 修改之前先跑通、留作比较的最小方法或官方样例 | 改策略或换模型之前先保存原成绩与环境 |
| 复现 | 按给定输入、代码和环境说明重新得到结果 | 看是否真能重算，不只看截图；[历史数模案例](../examples/cumcm2024b/README.md)可无模型复算 |
| 独立审计 | 用另一套实现或公式核查原结果 | 原实现自己的测试与独立检查分开记账，均不等于竞赛成绩 |
| 全国性比赛 | 赛事面向全国组织 | 不能据此把省赛证书认定为全国奖，或推定学校一定认可 |
| 国赛 | 可能指一项比赛的简称，也可能指该比赛全国阶段 | 写清比赛完整名字、年份、阶段与赛项，避免只说“国赛获奖” |
| 省奖 / 赛区奖 | 对应省级或赛区评奖的证书 | 各比赛路径和名称不同；看实际证书与本校认定 |
| 学校认定 | 学校对竞赛目录、级别、加分或奖励的具体规则 | 用自己的学校、学院和当年文件核对，不照搬另一所学校的表 |
| A / B / C 类 | 常见于高校或部门自己的分类、认定目录 | 本项目不虚构“教育部统一给所有比赛分 ABC”；具体看本校正式文件 |
| 母赛 / 赛道 / 赛项 | 同一比赛下面可能有多个方向、平台、组别和评审方式 | 母赛有 AI 题目不表示所有赛项都允许外部 Agent；按具体赛项核 |
| 制作参考顺序 | 本项目按现有过程资料与制作适配形成的连续编辑顺序 | 不是统计获奖率或精密性价比分；看[第 2 章](../book/02-看懂排名与奖项.md) |
| 证据状态 | 区分作者经历、外部自述、真实运行与官方教程的标记 | 不把不同队伍的工具过程与奖项拼成同一条“Agent 国奖”证据 |
| 待核 | 尚缺足够依据，当前资料不能确定 | 没确认的报名费、模型费、工具权限、报名状态保持未知 |

[看懂排名与奖项](../book/02-看懂排名与奖项.md) · [真实反馈与资料核查](../book/10-真实反馈与资料核查.md)

<!-- Generated by scripts/build_book.py. -->
'''
    emit(ROOT/'docs/glossary.md',text)

def main():
    global CHECK
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args();CHECK=args.check
    chapters=json.loads((ROOT/'data/chapters.json').read_text('utf8'))
    rows=json.loads((ROOT/'data/competitions.json').read_text('utf8'))
    ranked=sorted((r for r in rows if isinstance(r.get('rank'),int)),key=lambda r:r['rank'])
    assert [r['rank'] for r in ranked]==list(range(1,28))
    assert [c['id'] for c in chapters]==['%02d'%i for i in range(1,11)]
    for i,c in enumerate(chapters):
        assert c['file'].startswith('book/') and len({s['id'] for s in c['sections']})==len(c['sections'])
        build_chapter(c,i,chapters,ranked)
    build_contents(chapters);build_glossary()
    if STALE:raise SystemExit('Stale book views: '+', '.join(STALE))
    print(json.dumps({'book_chapters':len(chapters),'chapter_sections':sum(len(c['sections']) for c in chapters),'outputs':len(chapters)+2,'source':'data/chapters.json + maintained tutorials + data/competitions.json'},ensure_ascii=False))

if __name__=='__main__':main()
