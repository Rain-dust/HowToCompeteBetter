"""Build the v6 offline guide from current repository data and the verified run.

This is a deliberately paginated A4 document. Every content box is measured and
checked against the printable area; a missing/unverified run summary is fatal.
Run with --measure-only to check layout without writing a PDF.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import math
import os
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / 'output/pdf/高性价比大学生竞赛指南_v6_2026-11-16.pdf'
DEFAULT_VALIDATION = ROOT / 'research/pdf-v6-validation.json'
REPOSITORY = 'https://github.com/Rain-dust/HowToCompeteBetter'
BLOB = REPOSITORY + '/blob/main/'
COMMIT = '03f4eb388b3862b7bde55b508dceaf3d6b39d5ac'
W, H = A4
LEFT, RIGHT, BOTTOM = 43.0, W - 43.0, 47.0
CONTENT_TOP = H - 69.0
WIDTH = RIGHT - LEFT
INK = colors.HexColor('#162c3b')
MUTED = colors.HexColor('#526673')
TEAL = colors.HexColor('#007e87')
LIGHT = colors.HexColor('#eef6f6')
LINE = colors.HexColor('#dbe5e8')
PALE = colors.HexColor('#f4f7fa')
AMBER = colors.HexColor('#8c5721')


def read_json(relative):
    return json.loads((ROOT / relative).read_text(encoding='utf-8'))


def register_fonts():
    font_dir = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts'
    regular = font_dir / 'Deng.ttf'
    bold = font_dir / 'simhei.ttf'
    if not regular.exists() or not bold.exists():
        raise FileNotFoundError('Expected Deng.ttf and simhei.ttf in ' + str(font_dir))
    pdfmetrics.registerFont(TTFont('GuideBody', str(regular)))
    pdfmetrics.registerFont(TTFont('GuideBold', str(bold)))
    pdfmetrics.registerFontFamily('GuideBody', normal='GuideBody', bold='GuideBold')


def E(value):
    return escape(str(value).translate(str.maketrans({'‐': '-', '‑': '-', '–': '-', '—': '-'})))


def link(label, url):
    return '<link href="%s" color="#007e87">%s</link>' % (escape(str(url), {'"': '&quot;'}), E(label))


def local(label, relative):
    return link(label, BLOB + relative)


def load_inputs():
    ranking = read_json('data/ranking.json')
    top5 = read_json('data/top5.json')
    feedback = read_json('data/feedback-records.json')
    social = read_json('data/social-feedback.json')
    summary_file = ROOT / 'examples/cumcm2024b/run-summary.json'
    if not summary_file.exists():
        raise FileNotFoundError('Verified run-summary.json is required; refusing a placeholder PDF.')
    run = json.loads(summary_file.read_text(encoding='utf-8'))
    if run.get('status') != 'verified':
        raise ValueError('run-summary.status must be verified before producing this guide.')
    if [r['rank'] for r in ranking] != list(range(1, 28)):
        raise ValueError('ranking.json must contain continuous ranks 1 through 27.')
    if len(top5) != 5 or len(feedback['external']) != 22:
        raise ValueError('Unexpected top-five or external-evidence count.')
    if len(social['records']) != 75:
        raise ValueError('Expected the documented 75 social records.')
    if run.get('skill', {}).get('commit') != COMMIT:
        raise ValueError('Unexpected MathModelAgent commit in run summary.')
    if not isinstance(run.get('paper_pages'), int) or run['paper_pages'] < 1:
        raise ValueError('A real paper page count is required.')
    q2 = run.get('q2_summary', [])
    if len(q2) != 6:
        raise ValueError('Six Q2 results are required.')
    policies = ['1101', '1101', '1101', '1111', '0100', '0000']
    profits = [17.55555556, 10.75, 14.88888889, 14.25, 11.98765432, 21.67867036]
    for row, policy, profit in zip(q2, policies, profits):
        if str(row['policy']) != policy or not math.isclose(float(row['profit']), profit, abs_tol=1e-7):
            raise ValueError('Q2 differs from the independently audited fixed result.')
    q3 = run.get('q3', {})
    for key, expected in [('cost', 142.33333333), ('profit', 57.66666667)]:
        if not math.isclose(float(q3[key]), expected, abs_tol=1e-7):
            raise ValueError('Q3 differs from the independently audited fixed result.')
    checks = run.get('checks', {})
    for key in ['agent', 'independent', 'independent_passed', 'production_mc_groups', 'q1_mc_groups', 'boundary_mc_groups']:
        if not isinstance(checks.get(key), int) or checks[key] < 0:
            raise ValueError('Actual nonnegative check count required: ' + key)
    if checks['independent_passed'] != checks['independent']:
        raise ValueError('The guide requires the independently audited run to pass.')
    for relative in ['paper/main.pdf', 'paper/main.typ', 'code/run_all.py', 'inputs/parameters.json', 'requirements.txt']:
        if not (ROOT / 'examples/cumcm2024b' / relative).exists():
            raise FileNotFoundError('Missing public reproduction artifact: ' + relative)
    return ranking, top5, feedback, social, run


class Guide:
    def __init__(self, target):
        self.c = canvas.Canvas(target, pagesize=A4, pageCompression=1)
        self.c.setTitle('高性价比大学生竞赛指南 - v6 / 2026-11-16')
        self.c.setAuthor('Rain-dust / HowToCompeteBetter')
        self.c.setSubject('连续27项制作适配顺序、两条数模路线、历史题实测与复现')
        self.pages = []
        self.current = None
        self.y = CONTENT_TOP

    def style(self, size=12, leading=None, color=INK, bold=False):
        return ParagraphStyle('g', fontName='GuideBold' if bold else 'GuideBody',
                              fontSize=size, leading=leading or size * 1.48,
                              textColor=color, alignment=TA_LEFT, wordWrap='CJK',
                              splitLongWords=True, allowWidows=0, allowOrphans=0,
                              spaceBefore=0, spaceAfter=0)

    def box(self, kind, x, y, width, height, text=''):
        box = {'kind': kind, 'x': round(x, 3), 'y': round(y, 3),
               'width': round(width, 3), 'height': round(height, 3), 'text': text}
        if x < LEFT - .1 or x + width > RIGHT + .1 or y < BOTTOM - .1 or y + height > CONTENT_TOP + .1:
            raise AssertionError('Page %s (%s): %s lies outside content bounds: %r' %
                                 (len(self.pages), self.current['title'], kind, box))
        self.current['boxes'].append(box)

    def page(self, section, title, subtitle=None):
        if self.current is not None:
            self.finish_page()
        num = len(self.pages) + 1
        self.current = {'page': num, 'section': section, 'title': title, 'boxes': []}
        self.pages.append(self.current)
        self.y = CONTENT_TOP
        c = self.c
        c.setFillColor(TEAL)
        c.rect(LEFT, H - 37, 23, 3, fill=1, stroke=0)
        c.setFont('GuideBody', 9)
        c.setFillColor(MUTED)
        c.drawString(LEFT + 33, H - 38, 'HOW TO COMPETE BETTER  /  ' + section)
        c.setStrokeColor(LINE)
        c.setLineWidth(.55)
        c.line(LEFT, 34, RIGHT, 34)
        c.setFont('GuideBody', 8.5)
        c.drawString(LEFT, 21, 'v6 · 2026-11-16   |   历史题练习与正式参赛分别核对')
        c.drawRightString(RIGHT, 21, '%02d' % num)
        self.p(E(title), size=23, leading=31, bold=True, gap=8, kind='page_title')
        if subtitle:
            self.p(subtitle, size=11.5, leading=17, color=MUTED, gap=17, kind='subtitle')

    def p(self, text, size=12, leading=None, color=INK, bold=False, gap=10, kind='paragraph', indent=0):
        para = Paragraph(str(text), self.style(size, leading, color, bold))
        width = WIDTH - indent
        _, height = para.wrap(width, H)
        bottom = self.y - height
        self.box(kind, LEFT + indent, bottom, width, height, text)
        para.drawOn(self.c, LEFT + indent, bottom)
        self.y = bottom - gap
        return height

    def h(self, text):
        self.p(E(text), size=15, leading=21, bold=True, color=TEAL, gap=9, kind='heading')

    def bullet(self, text, number=None):
        prefix = '• ' if number is None else str(number) + '. '
        self.p(E(prefix) + text, gap=8, indent=2, kind='list_item')

    def note(self, text, title=None, fill=LIGHT, size=12, gap=13):
        label = ('<b>' + E(title) + '</b><br/>') if title else ''
        para = Paragraph(label + text, self.style(size, size * 1.48))
        _, ph = para.wrap(WIDTH - 26, H)
        height = ph + 22
        bottom = self.y - height
        self.box('callout', LEFT, bottom, WIDTH, height, label + text)
        self.c.setFillColor(fill)
        self.c.roundRect(LEFT, bottom, WIDTH, height, 7, stroke=0, fill=1)
        para.drawOn(self.c, LEFT + 13, bottom + 11)
        self.y = bottom - gap

    def code(self, lines, title=None, size=11.5):
        if isinstance(lines, str):
            lines = lines.splitlines()
        body = '<br/>'.join(E(s) if s else '&#160;' for s in lines)
        self.note(body, title, fill=PALE, size=size)

    def rule(self):
        self.c.setStrokeColor(LINE)
        self.c.setLineWidth(.6)
        self.c.line(LEFT, self.y - 2, RIGHT, self.y - 2)
        self.y -= 15

    def table(self, headers, rows, widths, size=11.5, leading=16, pad=8):
        if not math.isclose(sum(widths), WIDTH, abs_tol=.1):
            raise ValueError('Table widths must fill content width.')
        all_rows = [headers] + rows
        for ri, row in enumerate(all_rows):
            paras = [Paragraph(str(cell), self.style(size, leading, colors.white if ri == 0 else INK, ri == 0))
                     for cell in row]
            heights = [p.wrap(w - pad * 2, H)[1] for p, w in zip(paras, widths)]
            rh = max(heights) + pad * 2
            bottom = self.y - rh
            self.box('table_header' if ri == 0 else 'table_row', LEFT, bottom, WIDTH, rh, ' | '.join(map(str, row)))
            self.c.setFillColor(TEAL if ri == 0 else (PALE if ri % 2 else colors.white))
            self.c.rect(LEFT, bottom, WIDTH, rh, fill=1, stroke=0)
            x = LEFT
            for p, width, ph in zip(paras, widths, heights):
                p.drawOn(self.c, x + pad, bottom + rh - pad - ph)
                x += width
            self.y = bottom
        self.y -= 14

    def ranking_card(self, row, track, evidence):
        title = '%02d  %s' % (row['rank'], row['name'])
        self.p(E(title), size=12.2, leading=16, bold=True, gap=3, kind='ranking_title')
        self.p(E(track), size=11.5, leading=15.7, color=MUTED, gap=3, kind='ranking_track')
        self.p('<font color="#007e87">' + E(row['ai_status']) + '</font>  |  ' + E(evidence),
               size=11.5, leading=15.7, gap=11, kind='ranking_permission_evidence')

    def finish_page(self):
        bottom = min((b['y'] for b in self.current['boxes']), default=CONTENT_TOP)
        self.current['content_bottom'] = round(bottom, 3)
        self.current['content_used_height'] = round(CONTENT_TOP - bottom, 3)
        self.current['remaining_height'] = round(bottom - BOTTOM, 3)
        self.current['bounds_passed'] = True
        self.c.showPage()
        self.current = None

    def save(self):
        if self.current:
            self.finish_page()
        if len(self.pages) != 26:
            raise AssertionError('Expected exactly 26 designed pages, got %d.' % len(self.pages))
        self.c.save()


def compact(text, limit):
    text = str(text)
    return text if len(text) <= limit else text[:limit - 1] + '…'


def repo_line(g, label, url):
    g.p(link(label, url), bold=True, size=11.5, gap=3)
    g.p(E(url), size=11.5, color=MUTED, gap=11)


def make_pages(g, ranking, top5, feedback, social, run):
    # 01: Lead with a usable conclusion, not the research apparatus.
    g.page('先做选择', '高性价比大学生竞赛指南', '用编程 Agent 做出能运行、能解释、能复现的作品。版本：2026-11-16。')
    g.note('第一次尝试，先用历史数模题跑通完整链。想用 Windows 界面选 <b>Modex</b>；已有 Codex 选 <b>MathModelAgent skills</b>。', '先从一条数模路线开始')
    for row in ranking[:5]:
        g.p('<font color="#007e87"><b>%02d</b></font>  <b>%s</b><br/><font color="#526673">%s</font>' %
            (row['rank'], E(row['name']), E(row['verdict'])), size=12, leading=18, gap=14)
    g.p('前五表示制作适配与已读反馈的编辑顺序。计设工具名单、统计建模核心生成禁令，都会影响正式赛能做什么。', color=MUTED)
    g.rule()
    g.p('<b>直接跳读</b>　Modex 07-09页　|　Codex 10-12页<br/>历史题实测 13-15页　|　其他前五 16-19页<br/>完整顺序 04-06页　|　集中来源 23-26页', size=12, leading=21)

    # 02: Make scope and the two choices clear with little text per block.
    g.page('怎么使用', '先选能交付的题，再核工具权限', '排名回答“适不适合制作”，正式参赛还需要当届规则、资格与本校认定。')
    g.h('三步开始')
    g.bullet('把具体赛项、评分点、题面、附件和真实输入放进独立工作区。只有比赛名字，还不足以开工。', 1)
    g.bullet('先做最小完整成果：从输入到真实结果，再到图表、文稿与演示。第一次练习不要同时装五套技能。', 2)
    g.bullet('让同一版本重跑；每个关键数字都能回到代码、参数和结果文件。', 3)
    g.note('有界面需求：按 Modex 官方手册配置、连接测试与检查点推进。<br/>有 Codex 环境：用固定技能链、启动脚本、事件日志和独立验收。', '数模的两条入口')
    g.h('这份指南的证据来自哪里')
    g.p('75篇原帖详情：小红书45、贴吧30，其中74篇有非空正文；另有22份既有外部材料。16篇亲历或个人经验材料用于路线判断。')
    g.p('270条去重小红书评论与121条贴吧楼层记录，帮助理解体验与卡点；评论数量不等于成功案例数量。', color=MUTED)
    g.note('作者U01自述数模系列、计设和第18届RST前沿技术挑战组的省奖经历，单列保留。未细分的杯赛、等级与届次不补写；历史经历也不能证明2026工具获准。', '亲历与正式规则分别记录', fill=PALE)
    g.p('资料与规则核对日期见末页索引；历史题实测是独立的一组证据，不是获奖验证。', size=11.5, color=MUTED)

    # 03: A concise permissions-first front-five view.
    g.page('前五具体范围', '前五名，具体做哪一种作品', '制作范围、权限与亲历证据一起看。安装和可复制任务在后面的路线页。')
    for row in ranking[:5]:
        g.p('<b>%02d  %s</b>' % (row['rank'], E(row['name'])), size=13, leading=19, gap=5)
        g.p(E(row['track']), size=11.5, leading=17, gap=4, color=MUTED)
        g.p('<font color="#007e87">%s</font><br/>%s' % (E(row['ai_status']), E(row['evidence'])), size=11.5, leading=17, gap=16)
    g.note('计设：历史Codex省奖不覆盖2026限定工具表。<br/>统计建模：2026禁止AI直接生成核心设计与论文正文。<br/>RST：前沿技术挑战与机器鱼仿真属于两个赛项。', '先读这三个边界', size=11.5)

    # 04-06: Continuous ranking, kept legible rather than a dense mega-table.
    tracks = {
        6: 'MCM/ICM具体题；资格、英文稿与AI报告分别核',
        7: '第16届对应学历组；核心建模、求解须队员独立',
        8: '明确届次、杯赛和学历组后再做限时建模',
        9: '电工、电力具体数模题；同校组队规则另核',
        10: '数据已给、评测明确、算力能承担的题',
        11: 'A类纯软件企业题；OPC与创业实践另判',
        12: 'Web交互、游戏、可视化；类名以当届指南为准',
        13: '交互设计、创意编程；AIGC类别分别核',
        14: '第20届指定题；优先学习生产力等软件题',
        15: '2026智能体互联主题；其他主题分别核',
        16: '人工智能创意赛；不与4C、AIGC赛混用',
        17: '华为ICT创新赛；实践赛和编程赛分别判断',
        18: '主题一创意设计/AIGC等无需实物类别',
        19: '优先CAIA设计、应用作品；CAIP现场编程另判',
        20: '常规赛与实战赛分别核；有真实业务再复用',
        21: '高教、红旅、职教、产业对应组；已有项目再投',
        22: '论文、调查、发明对应组；主体与专项分开',
        23: '创业计划对应组；真实创业项目先行',
        24: '团队实践对应学历组；知识赛权限单列',
        25: '论文、调研、创业三类；方法不等于工具许可',
        26: '国内与国际赛分别核；不混同其他同名杯赛',
        27: '研究生数模；本科生先核报名资格',
    }
    evidence_short = {
        6: 'F18：MM-Agent辅助两队Finalist，非Codex',
        7: 'F09获奖方法；缺Agent赛果绑定',
        8: 'F01自述一等奖，带服务赞助',
        9: 'F17国二访谈；X44电工杯无奖',
        10: 'F10/F11约两月实作，未披露Agent',
        11: 'X23/X24流程经验；缺OPC赛果',
        12: '多为教程、专项介绍；缺独立获奖复盘',
        13: 'X42有获奖也有落选；X29未获省三',
        14: '工具适配判断；缺合格Agent获奖复盘',
        15: '题目含Agent，未证明开发Agent获奖',
        16: '缺本轮独立Agent参赛反馈',
        17: 'F14旧案例含硬件、两月与英文答辩',
        18: '有AI作品线索；缺独立制作复盘',
        19: '缺本轮Agent获奖实录',
        20: 'F15强调调研、盈利与路演',
        21: 'F20仅旧校赛感想，不能推断省奖',
        22: '缺同赛项Agent获奖亲历',
        23: '缺Agent与本赛省奖绑定',
        24: 'F16研究生历史访谈；未披露Agent',
        25: 'F19获奖分享，未披露Agent',
        26: 'X44使用AI，未绑定本杯奖项',
        27: '缺Agent奖项绑定；不是华为ICT',
    }
    for lo, hi in [(6, 13), (14, 20), (21, 27)]:
        g.page('连续制作适配顺序', '完整排名 %02d-%02d' % (lo, hi), '接续前五，同一顺序，不分档。蓝色为工具权限标签；来源编号在文末集中列出。')
        for row in ranking[lo - 1:hi]:
            g.ranking_card(row, tracks[row['rank']], evidence_short[row['rank']])

    # 07: Modex official route, explicitly not a local run.
    g.page('Modex 1 / 3', '下载后，先把连接配置好', '<b>官方教程路线，本项目未安装实测。</b> 核读官网、README、官方手册和分享文件信息，日期2026-11-16。')
    repo_line(g, 'Modex官方展示与反馈仓库', 'https://github.com/N-allpass/modex-mh-agent')
    g.p('GitHub没有公开应用源码或安装包；不能靠git clone运行。下载入口在 ' + link('官网 mingheng.xin', 'https://www.mingheng.xin/') + '，配置说明见 ' + link('官方使用手册', 'https://docs.qq.com/doc/DQk1LZWtBaFhRd0VF') + '。', size=12)
    g.note('核查时官方分享文件：Modex-MH-Agent Setup 2.1.2.exe，约1.40 GB，文件修改时间2026-09-26。分享包版本不等于当前应用版本；最低配置和安装后占用未核实。', '下载与安装', size=11.5)
    g.h('按顺序完成六件事')
    for i, text in enumerate([
        '从官网进入Windows下载；记录首次打开的应用版本。路径尽量简短，按实际安装提示处理授权与激活。',
        '打开右上角设置，查看它实际支持的服务与获取Key入口；先读当前价格、计费单位和渠道说明。',
        '按所选服务创建Key，核对渠道分组。聊天订阅、服务账号与模型调用额度分别核对。',
        '在模型预设库添加配套预设，确认模型ID；有服务地址字段时填API地址。',
        '保存连接信息并完成连接测试。认证、余额、分组、模型ID或网络报错，先修到能连接。',
        '在工作流设置底部，为三个角色分配预设；或在新建工作流底部逐步骤指定。保存后再建小任务。',
    ], 1):
        g.bullet(text, i)
    g.p('README与旧手册对接入方式描述有差异；当前界面是否限制自定义URL、现有Key能否使用，均未实测。', size=11.5, color=MUTED)

    # 08
    g.page('Modex 2 / 3', '先读对题，再让工作流求解', '第一次用历史题。先传完整题面与附件，再核对表格、单位、百分数和四问要求。')
    g.table(['界面选择', '第一次练习的做法'], [
        ['全自动 / 协同', '先选协同。全自动仍可能在检查点暂停。'],
        ['严格 / 省额度', '这是另一组执行与用量选项。先用小任务验证。'],
        ['模型预设', '确认每个角色或步骤已分配可连接的预设。'],
    ], [140, WIDTH - 140], size=12, leading=18)
    g.code([
        '请用我上传的2024国赛B题官方PDF建立中文历史题练习。',
        '先完成题意、数据表和四问拆解，等我确认后再求解。',
        '没有附件、样本、引用或运行结果，不得编造。',
        'Q1：分别写清拒收/接收要求、样本量与判定阈值。',
        'Q2：解释采购、检测、拆解回流、损失与收入口径。',
        'Q3：推广到多工序；说明状态、终止和验证办法。',
        'Q4：区分点估计与估计不确定性，报告策略敏感性。',
        '每问都要有模型、真运行代码、结果表与独立复核。',
        '有不同成本解释时列出差异，等我确认。随机法固定种子。',
        '检查点：读题后、建模后、求解后、大纲后、导出前。',
        '每次说清产物在哪、疑点是什么，再等我继续。',
    ], '上传题面后，复制这段任务')
    g.note('软件不附模型额度。旧手册中的“额度”举例缺货币单位，不能换算为每篇费用。先看当前单价、余额、循环轮数与用量，再决定继续范围。', '用量怎样控制', size=11.5)
    g.p('完整启动任务见 ' + local('docs/modex.md', 'docs/modex.md') + '。官方宣传的速度、评分增长与获奖率不作为本项目结论。', size=11.5, color=MUTED)

    # 09
    g.page('Modex 3 / 3', '检查点要验收，完成后要复算', '下面是按官方能力整理的操作顺序；当前按钮、恢复范围和导出位置未做应用实测。')
    for title, text in [
        ('读题后', '四问、表格、单位都能回到原PDF。缺一问就要求重新拆题，先不写论文。'),
        ('建模后', '目标函数、约束与成本口径明确。让它用小例子解释拆解回流，排除重复记账。'),
        ('求解后', '看到真实运行记录和结果表，再用手算、边界或独立程序复核关键数字。'),
        ('写作前', '每问结果落实，图表能支持结论。先补缺失分析，再写摘要与正文。'),
        ('导出前', '编译本次论文并逐页查看；保留源码、数据、代码、图表和运行方法。'),
    ]:
        g.note(text, title, fill=PALE, size=12, gap=11)
    g.h('卡住时先看状态和日志')
    g.p('等待检查点就继续或提修改意见；执行报错就先记下步骤、预设、时间与错误。定位到单步后，先修正再单步重跑；模型或数据改变时同步更新图表与正文。')
    g.p('连接失败核Key、分组、模型ID、地址、余额与网络；编译失败先看首个实际错误。导出后从软件当前入口取得真实路径，不猜默认目录。', size=11.5, color=MUTED)
    g.p('仍有问题可用 ' + link('官方Issues', 'https://github.com/N-allpass/modex-mh-agent/issues') + ' 提交清理过的日志与复现步骤；公开反馈中不要放Key或私人材料。', size=11.5, color=MUTED)

    # 10
    g.page('Codex 1 / 3', '安装一套完整skills，先预检', '主选MathModelAgent当前skills链。实际入口是 $1start-mathmodel，不部署旧Web、Redis或Docker。')
    repo_line(g, 'MathModelAgent主选仓库', 'https://github.com/jihe520/MathModelAgent')
    g.p('固定commit：' + E(COMMIT), size=11.5, color=MUTED)
    g.p('准备：已安装登录的Codex CLI、Git、Python 3.12、uv、完整题目附件和可用模型额度。排版选Typst。Claude可加载同一套技能，本轮实际调用Codex。')
    g.code([
        'git clone https://github.com/Rain-dust/HowToCompeteBetter.git',
        'cd HowToCompeteBetter',
        'python scripts/setup_math_workspace.py --workspace ../my-math-run',
        '',
        '把题面复制到 ../my-math-run/inputs/problem.pdf',
        '附件保留原文件名，放在同一 inputs/ 目录。',
        '',
        'python scripts/run_codex_math.py --workspace ../my-math-run --preflight',
    ], '逐行执行，工作区安装在新目录')
    g.note('看到Codex版本、Python stack OK、Typst版本和<br/><b>Preflight passed; no model call.</b><br/>才启动模型。预检失败先修环境。', '预检通过的标志')
    g.p('安装器保留完整兄弟技能、模板和_references；Codex入口在.agents/skills/，Claude入口在.claude/skills/。只复制入口SKILL.md会缺资源。', size=11.5)
    g.p('上游是个人非商业限制许可，非MIT；本仓库不打包整套上游技能。Typst自动下载仅在Windows验证，其他系统先自行安装。', size=11.5, color=MUTED)

    # 11
    g.page('Codex 2 / 3', '一次给题，连续推进到完整产物', '先明确比赛、语言、排版和问数。已有偏好继续沿用，实质缺失信息如实指出。')
    g.code(['python scripts/run_codex_math.py --workspace ../my-math-run'], '通过预检后启动')
    g.p('也可以在Codex或Claude中打开my-math-run文件夹，确认技能被发现后，复制下面的任务。', size=11.5)
    g.code([
        '使用 $1start-mathmodel 完整处理 inputs/problem.pdf 与全部附件。',
        '偏好已确定：Typst、国赛中文，问数按题面。',
        '不要重复询问已给偏好；连续完成，不停在计划。',
        '依次完成分析建模、真实计算、图表、必要流程图、论文和验收。',
        '所有数字来自本次运行，注明假设、近似和策略范围。',
        '没有样本时仅做清楚标注的条件演示，不编造实测。',
        '完整重跑，编译 paper/main.pdf，并逐页渲染查看。',
        '失败修复后重验；未完成项不得标PASS。',
        '交付源码、结果、图表、完整论文与 VERIFY_REPORT.md，',
        '以及含版本、输入和产物hash的 RUN_MANIFEST.json。',
    ], '可复制的完整任务')
    g.h('连续推进时，证据也要连续留下')
    g.p('分析写入plan/todo，计算写入code/results，图表写入figures，论文写入paper。启动任务、事件和退出状态保留在run-logs。')
    g.note('脚本退出码0、技能自评通过或最后一句“完成”，都不能替代数学正确性、完整重跑和实际编译。教程要求高于上游允许的“无法检查但说明后通过”。', '这次验收加严了什么', size=11.5)

    # 12
    g.page('Codex 3 / 3', '保留原会话恢复，再核验关键结果', '本轮真实经历过workspace credits中断后恢复，不能描述为无中断的一键完成。')
    g.code([
        'cd ../my-math-run',
        'codex resume',
        '',
        '选择原会话后发送：',
        '保留代码和已算结果，从todo未完成项继续；修复后完整重验。',
    ], '额度恢复或环境修好后继续原会话')
    g.p('非交互恢复可用codex exec resume 会话ID -。图表或局部结论有问题时指出具体文件，重算相关结果并同步论文。', size=11.5)
    g.h('为什么只主推这一套')
    g.table(['候选', '本轮取舍'], [
        ['MathModelAgent', '主选；当前skills串完整链，Typst依赖较轻。'],
        ['Math-model-skills', '备选；MIT、机器门禁较完整，TeX依赖较重。'],
        ['mathmodel-skill', '问答和逐步确认较多，更适合协作式推进。'],
        ['MathModeling-skills', '当前main有人类Gate；旧自动分支不是当前主线。'],
        ['math-modeling-skills', '核读版本auto含占位成功与失败后继续，不选。'],
    ], [142, WIDTH - 142], size=11.5, leading=17, pad=7)
    g.note('五套候选的固定源码、技能和许可已核读；只对主选做真实模型运行。没有做五套横向性能或获奖率测评。', '选型证据的范围', size=11.5)
    g.p('常见环境问题与处理见 ' + local('完整Codex教程', 'docs/coding-agent.md') + '；固定commit和取舍见 ' + local('math-tools.json', 'data/math-tools.json') + '。', size=11.5, color=MUTED)

    # 13: These pages only exist when the independently verified run is present.
    g.page('真实运行 1 / 3', '2024国赛B：从题面到论文', '历史题《生产过程中的决策问题》。本轮调用Codex + 固定MathModelAgent技能链，不是Modex实测。')
    g.note('实际产物：四问计算、结果表、图表、可编辑Typst论文、<b>%d页论文PDF</b>和验收材料。历史题复现没有因此获得奖项。' % run['paper_pages'], '本次做到了什么')
    active = run.get('elapsed_active_minutes')
    time_text = ('可核算活跃用时约%.1f分钟。' % float(active)) if isinstance(active, (int, float)) else '中断与恢复分段记录，不填未经核实的单次完成工时。'
    g.p(E(run.get('driver', 'Codex CLI')) + '执行。' + E(time_text) + '<br/>' + E(run.get('interruption', '首次额度中断后恢复同一会话继续。')), size=11.5, color=MUTED)
    g.h('问题2：六种情形的固定策略结果')
    g.table(['情形', '策略', '期望利润 / 元'], [
        [str(row.get('case', i + 1)), E(str(row['policy'])), '%.8f' % float(row['profit'])]
        for i, row in enumerate(run['q2_summary'])
    ], [80, 120, WIDTH - 200], size=12, leading=18, pad=8)
    g.p('策略位依次表示零配件1检测、零配件2检测、成品检测与拆解。1为执行，0为不执行；成本、收益按本次定义的生产与回流模型计算。', size=11.5)
    g.note('问题1区分拒收与接收要求，并用动态规划/模拟检查序贯判定。边界p=0.1、最大样本数n=2000时，约86.407%仍未决，不能把截断当作高概率完成判定。', '问题1还有这个限制', size=11.5, fill=PALE)
    g.p('实际代码与数值来源：examples/cumcm2024b/code/、results/；完整解释见运行记录。', size=11.5, color=MUTED)

    # 14
    g.page('真实运行 2 / 3', '问题3和4，结果能说明什么', '把固定策略、随机模拟与假想数据写清楚，才能正确解释“算出来了”。')
    q3 = run['q3']
    g.h('问题3：固定策略空间内的计算')
    g.table(['指标', '本次结果'], [
        ['固定策略', E(str(q3.get('policy', '1111111111111101')))],
        ['枚举策略数', str(q3.get('enumerated', 65536))],
        ['适定策略数', str(q3.get('proper', 17060))],
        ['期望成本 / 元', '%.8f' % float(q3['cost'])],
        ['期望利润 / 元', '%.8f' % float(q3['profit'])],
    ], [180, WIDTH - 180], size=12, leading=18, pad=8)
    g.p('这里比较的是指定的固定策略及重复复检口径。没有枚举所有随检测历史变化的自适应策略，不能称无约束全局最优。')
    g.h('问题4：条件演示，不是真实抽样')
    g.note('使用假想样本量n=100或400，讨论次品率估计与策略敏感性。它展示不确定性分析的方法，没有采集真实工厂样本，也不能包装成实测样本结论。', '样本从哪里来', fill=PALE)
    checks = run.get('checks', {})
    g.h('独立核验检查了什么')
    g.p('Agent自身检查%d项；独立检查%d/%d项通过。生产事件模拟%d组、Q1模拟%d组、边界模拟%d组，分别保留记录。' %
        (checks.get('agent', 211), checks.get('independent_passed', 242), checks.get('independent', 242),
         checks.get('production_mc_groups', 79), checks.get('q1_mc_groups', 3), checks.get('boundary_mc_groups', 1)))
    g.p('通过这些检查支持本次模型与实现的可复算性；模型口径、自适应最优和真实数据外推仍有上述限制。', size=11.5, color=MUTED)

    # 15
    g.page('真实运行 3 / 3', '不调用模型，也能重跑结果', '公开成果包保留参数、源码、结果、图表、论文源文件与验收记录；原题PDF由读者自行下载。')
    g.code([
        'cd examples/cumcm2024b',
        'python -m venv .venv',
        '.venv/Scripts/python -m pip install -r requirements.txt',
        run.get('reproduce_command', 'python code/run_all.py').replace('python ', '.venv/Scripts/python ', 1),
        run.get('compile_command', 'typst compile --root . paper/main.typ paper/main.pdf'),
    ], '进入仓库后执行')
    g.p('建议Python 3.12；上面显式使用.venv中的Python，无需另行激活。requirements.txt锁定本轮8个直接依赖。编译另装官方Typst 0.15.1并加入PATH。纯计算只读inputs/parameters.json，无需题面PDF或模型Key。', size=11.5)
    g.table(['目录或文件', '用于复核'], [
        ['inputs/parameters.json', '固定参数；与原题表格对应。'],
        ['code/ 与 tools/', '计算、核验和辅助脚本。'],
        ['results/', '四问JSON、汇总CSV与检查结果。'],
        ['figures/', '论文图表及其实际计算来源。'],
        ['paper/main.typ 与 main.pdf', '可编辑论文源文件与编译成稿。'],
        ['reports/ 与运行清单', '分析、结果、环境和验收证据。'],
    ], [190, WIDTH - 190], size=11.5, leading=17, pad=8)
    g.note('在干净环境重跑，核对六个Q2策略与利润、Q3成本/利润及Q4假想样本标记。然后重新编译论文，逐页查看数字、图表、公式和排版。', '复现后的验收动作', size=12)
    g.p(local('打开示例README与完整复现说明', 'examples/cumcm2024b/README.md') + '<br/>' + local('查看run-summary.json', 'examples/cumcm2024b/run-summary.json') + '　|　' + link('下载成果ZIP', REPOSITORY + '/raw/refs/heads/main/examples/cumcm2024b-example.zip'), size=11.5)

    # 16: Other top-five routes are templates, not invented contest-specific winners.
    g.page('第02名 / 作品路线', '计算机设计：先做一个核心功能', '优先软件、数据与交互作品。历史Codex省奖自述与2026工具许可分开。')
    g.note('2026限定15款规定工具或自主知识产权工具，未查到Codex许可。以下开发任务用于赛前练习，或明确获准的范围；先核当届工具表。', '正式赛的前置条件', size=11.5)
    repo_line(g, '通用界面与浏览器测试技能', 'https://github.com/anthropics/skills')
    g.code([
        '从上面仓库安装完整 skills/frontend-design 和',
        'skills/webapp-testing 到本项目 .agents/skills/。',
        '保留脚本和资源，按SKILL.md建隔离依赖并配置Playwright。',
        '用最小网页实测一遍，报告commit、路径、截图与缺失依赖。',
        '安装后重开项目会话，确认两个技能已发现。',
    ], '可复制：让Agent安装并验证')
    g.code([
        '我要做计算机设计大赛软件作品，inputs/有规程与真实需求。',
        '先输出工具权限、评分点与验收动作对照表。',
        '练习或获准后，用 $frontend-design 做一个核心功能。',
        '用 $webapp-testing 测正常、空输入与异常场景。',
        '交付源码、部署说明、真实截图与同版本运行视频。',
        '把平台所需注释、过程、时间戳与支撑材料一起完成。',
    ], '可复制：启动制作')
    g.p('U01自述历史省奖；F03-F06、F21补充作品和答辩流程。X05/X06保留未获奖反例；能运行、展示与答辩都影响结果。', size=11.5, color=MUTED)
    g.p('可选演示视频：' + link('remotion-dev/skills', 'https://github.com/remotion-dev/skills') + '。技能组合是通用制作建议。', size=11.5, color=MUTED)

    # 17
    g.page('第03名 / 分赛项路线', 'RST：作品和仿真，先分清赛项', '第18届前沿技术挑战组与第19届机器鱼仿真分别记录，不扩展到硬件竞技。')
    g.note('未核到可信RST专用获奖skill。创新软件可复用通用开发技能；仿真要先读官方平台、SDK和评分口径，逐赛项核工具权限。', '先选平台，再选技能', size=11.5)
    repo_line(g, '创新软件作品的通用技能', 'https://github.com/anthropics/skills')
    g.p('安装frontend-design与webapp-testing，完整目录、隔离依赖和浏览器测试方法同第16页。Cline是另一套独立Agent，' + link('仓库在这里', 'https://github.com/cline/cline') + '，无需装入Codex技能目录。', size=11.5)
    g.code([
        '我要参加RST，inputs/有届次、赛道、组别、规则和SDK。',
        '先识别创新创业作品还是仿真竞技，逐项列出评分动作。',
        '创新作品：完成能运行并按评分点演示的小产品。',
        '仿真：先编译运行官方基线，记录环境与多次成绩。',
        '基线跑通后逐项改策略，同环境比较改动前后。',
        '输出每次分数、失败回放、日志与复跑命令。',
        '基线未运行成功先修环境，不能虚构成绩。',
        '最后按本组要求交源码、说明、真实视频与答辩包。',
    ], '可复制：启动具体赛项')
    g.h('交付时，留住同环境的对照')
    g.p('保存官方平台/SDK版本、配置、随机种子、基线和候选策略的多次结果。演示来自实际程序，别只交概念动画。')
    g.p('U01：第18届创新创业前沿技术挑战组省奖自述。X16：第19届机器鱼仿真国一自述，提及Gemini并附照片。图片中的Cline课程例子不足以证明其比赛用了Cline。', size=11.5, color=MUTED)

    # 18
    g.page('第04名 / 受限辅助路线', '统计建模：先守住研究原创范围', '制作适配高，2026正式赛禁止AI直接生成核心设计与论文正文。')
    g.note('禁止直接生成研究选题、假设、框架、调查方案与论文正文。文献整理、图表类型建议、语言格式校对按规范执行；数据和代码任务单独核权限。', '正式赛按当届AI规范执行', size=11.5)
    repo_line(g, 'Scientific Agent Skills', 'https://github.com/K-Dense-AI/scientific-agent-skills')
    g.code([
        '安装 skills/exploratory-data-analysis 和',
        'skills/statistical-analysis 到项目 .agents/skills/。',
        '保留引用资源，按SKILL.md建独立Python环境。',
        '用有缺失值、重复与分组的合成CSV做一次检查。',
        '报告commit、环境和结果；此安装用于赛前练习。',
    ], '可复制：安装并做练习验证')
    g.code([
        '先读inputs/的统计建模当届AI规范，列出允许的动作。',
        '正式赛仅做明确允许的检索整理、语言与格式校对。',
        '不要直接生成核心研究设计或论文正文。',
        '拟执行的数据、代码任务单独列出待核权限。',
        '练习模式用 $exploratory-data-analysis 和',
        '$statistical-analysis 对合成或历史练习数据审计。',
        '按我已给方案复现诊断，交可重跑代码和错误记录。',
    ], '可复制：区分正式赛与练习')
    g.p('F07/F08分别提供国三、省一经验，未与Agent主导制作绑定。X36有辅导关联，不能充独立证据。若目标是全程Agent直出参赛核心内容，本届不推荐。', size=11.5, color=MUTED)

    # 19
    g.page('第05名 / 工程路线', '软件杯：把评分点写成验收动作', '优先数据可得、无额外硬件、本机能跑的企业指定软件题。')
    repo_line(g, '界面、开发与浏览器测试技能', 'https://github.com/anthropics/skills')
    g.p('完整安装frontend-design和webapp-testing，方法同第16页。视频可选 ' + link('Remotion技能', 'https://github.com/remotion-dev/skills') + '；原生或后台系统另用对应测试工具。', size=11.5)
    g.note('产品要求使用某种模型，不等于外部Codex开发获准。指定平台、SDK、开发辅助、提交声明和现场答辩逐题核，不预设每题都有省赛。', '逐题核开发工具', size=11.5)
    g.code([
        '我要参加中国软件杯，inputs/有当届题目和评分标准，',
        '以及规定技术栈、工具条款、真实数据和接口说明。',
        '先把每个评分点写成可执行验收动作，核数据与硬件可得。',
        '做最小端到端系统，跑通输入、处理、输出与错误恢复。',
        '用 $frontend-design 打磨必要界面；',
        '用 $webapp-testing 验证Web评分动作与异常输入。',
        '先修稳定性再加功能，记录失败与修复。',
        '交源码、锁定环境、部署说明、同版本视频与答辩问答。',
        '保留AI开发过程，正式提交只用规则允许的范围。',
    ], '可复制：启动工程项目')
    g.h('验收至少覆盖三件事')
    g.bullet('评分动作跑得通，空数据、断网、接口错误等场景有真实处理。')
    g.bullet('换一台机器能按说明部署，视频与源码是同一版本。')
    g.bullet('队员能解释架构、数据流、关键算法和失败处理。')
    g.p('F12有Claude Code两天原型、两月完整项目过程，未披露奖项；X19/X21/X38有国奖自述，未披露Agent。两类材料不能拼成同队AI国奖。', size=11.5, color=MUTED)

    # 20
    g.page('把路线变成成果', '第一次练习，就完成这六步', '先拿一份历史题或真实小需求，跑完一条链，再决定是否扩展规模。')
    for i, (title, text) in enumerate([
        ('冻结输入', '题面、附件、规则和原始数据保留原件。把单位、列名、样本来源和缺失信息写清楚。'),
        ('运行最小基线', '数模先算一个情形，软件先跑一条核心用户路径，仿真先跑官方基线。'),
        ('做完整结果', '扩到全部问题或评分动作；结果由真实代码生成。保留失败记录，不只保留最好的一次。'),
        ('交叉核验', '用手算、边界、独立实现或真实事件模拟检查关键结论。查数据泄漏、重复计费和单位错位。'),
        ('同步表达', '从本次结果生成图表、论文或说明。摘要、正文、图、表与演示使用同一版本。'),
        ('干净重跑', '按README在新环境复现，编译并逐页查看成稿，整理可编辑源文件、依赖和真实演示。'),
    ], 1):
        g.p('<font color="#007e87"><b>%02d</b></font>  <b>%s</b>' % (i, E(title)), size=13, leading=19, gap=5)
        g.p(E(text), gap=17)
    g.note('别先用复杂度证明价值。先交一个能稳定复跑、能说明用途的小成果，再按评分缺口增加功能或模型。', '每一轮只解决一个明确缺口', size=11.5)

    # 21
    g.page('正式参赛前', '从练习转到比赛，再做一次核对', '全国性赛事、证书奖级和学校认定分别确认；具体赛项与下一届规则不能靠母赛名称推断。')
    g.h('先取得这五份材料')
    for i, text in enumerate([
        '当届正式通知：报名、阶段、资格、组队与费用。校内预通知和历史通知分别标记。',
        '具体赛项细则：主题、平台、SDK、数据、硬件和现场环节。',
        'AI条款与工具表：允许哪些动作、哪些工具、如何标注与披露。',
        '学校认定文件：学校是否认可、证书级别怎样计入，按本校原文确认。',
        '提交清单：格式、匿名、页数、材料、源码、数据、视频和答辩要求。',
    ], 1):
        g.bullet(text, i)
    g.note('MathorCup2026：AI仅辅助，核心建模、算法、求解与分析须队员独立完成。<br/>能源经济第13届：禁止使用生成式AI自动生成的作品参赛。', '这两项本轮补核了规则', size=11.5)
    g.p('能源经济第13届通知安排：2026-11-17至12-16报名；2027-02-22至03-13提交作品。时间与禁止AI自动生成作品的条款，均按2026-11-16读到的正式通知记录。', size=11.5)
    g.h('把AI使用记录变成真实材料')
    g.p('保留工具与版本、任务范围、关键交互、人工判断、修改和验证。由队员确认模型、事实、数据来源及可解释性；声明应与真实过程一致。')
    g.p('权限待核的项目，继续做历史题或非参赛练习；取得明确规则后再决定正式提交范围。', size=11.5, color=MUTED)

    # 22
    g.page('怎样读证据', '有成功，也保留失败与返工', '奖项自述、制作过程、固定源码核读和本轮实测，各自只能支持对应结论。')
    cases = [
        ('U01 / 作者亲历', '自述数模系列、计设、RST前沿组省奖。一个作者的一次自述；未给出的杯赛、届次和等级不补写。'),
        ('X44 / 同一作者的正反结果', '有GPT参与国赛省一自述，也有电工杯无奖；华数杯提到AI但未绑定本杯奖项。'),
        ('F01 / 有奖也有商业关联', '自述华中杯一等奖、Codex十来小时；另一次自主实验复审仍发现图文不符，文末有服务赞助。'),
        ('F02 / 有过程，未报奖项', 'Codex参与国赛读题、求解和整理，记录约束遗漏、版本撞名与论文压缩。不能因此计为AI获奖案例。'),
        ('F12 / 软件工程的真实投入', 'Claude Code两天做首版原型、完整项目两个月；耗时集中在稳定性与工程容错，未披露最终奖项。'),
        ('F18 / 论文报告的Agent奖项', 'MM-Agent论文报告辅助两支本科队获2025 Finalist。它支持数模Agent价值，不能替换成Codex无人值守获奖。'),
    ]
    for title, text in cases:
        g.p('<b>' + E(title) + '</b>', size=12, leading=18, gap=4)
        g.p(E(text), size=11.5, leading=17, gap=14)
    g.note('样本来自公开发布与筛选，有成功者、平台和宣传偏差；没有可比投入和完整总体，不能据此计算获奖率。', '这一组材料怎样使用', size=11.5, fill=PALE)

    # 23-24: Full clickable rule sources, at the end rather than interrupting tutorials.
    for lo, hi in [(1, 14), (15, 27)]:
        g.page('集中来源 / 规则', '赛事规则来源 %02d-%02d' % (lo, hi), '链接指向具体原文或发布页。核对日期来自排名数据；保留校方转载、主办方与待核状态的差别。')
        for row in ranking[lo - 1:hi]:
            refs = row.get('rule_sources') or []
            first = refs[0] if refs else None
            label = 'R%02d  %s' % (row['rank'], row['name'])
            label_html = link(label, first['url']) if first else E(label) + '（原文待核）'
            date = row.get('rules_checked_through', '未记录')
            origin = compact(first['label'], 42) if first else '不以参赛自述代替工具权限'
            g.p(label_html + '<br/><font color="#526673">' + E(origin) + '　|　' + E(date) + '</font>',
                size=10.8, leading=15.1, gap=9, kind='source_entry')
        g.p('每项全部补充来源、登记状态和证据边界见 ' + local('data/ranking.json', 'data/ranking.json') + '；完整赛事目录见 ' + local('competition-catalog.md', 'docs/competition-catalog.md') + '。', size=10.8, leading=16, color=MUTED)

    # 25: All tool and tutorial primary routes.
    g.page('集中来源 / 工具', '工具、手册与固定版本', '工具文档支持功能和安装方式；产品宣传、样例与内部评分不当作竞赛成果。')
    sources = [
        ('T01 Modex官方仓库：展示、能力、反馈', 'https://github.com/N-allpass/modex-mh-agent'),
        ('T02 Modex官网：下载与当前产品入口', 'https://www.mingheng.xin/'),
        ('T03 Modex官方使用手册（文档更新2026-09-06）', 'https://docs.qq.com/doc/DQk1LZWtBaFhRd0VF'),
        ('T04 Modex官网Windows分享：提取码wt5k', 'https://pan.baidu.com/s/1XN1OKUL2gtg71gDr6JpZCA?pwd=wt5k'),
        ('T05 MathModelAgent：本轮固定commit的skills', 'https://github.com/jihe520/MathModelAgent/tree/' + COMMIT + '/skills'),
        ('T06 MathModelAgent：固定commit的限制许可', 'https://github.com/jihe520/MathModelAgent/blob/' + COMMIT + '/docs/md/License.md'),
        ('T07 Codex CLI：安装与登录', 'https://learn.chatgpt.com/docs/cli'),
        ('T08 Codex：技能目录和加载方式', 'https://learn.chatgpt.com/docs/build-skills'),
        ('T09 Codex：非交互运行与恢复', 'https://learn.chatgpt.com/docs/non-interactive-mode'),
        ('T10 Claude Code：官方安装说明', 'https://code.claude.com/docs/en/setup'),
        ('T11 Typst：官方发行与下载', 'https://github.com/typst/typst/releases'),
        ('T12 uv：官方安装说明', 'https://docs.astral.sh/uv/getting-started/installation/'),
        ('T13 通用技能：Anthropic frontend-design / webapp-testing', 'https://github.com/anthropics/skills'),
        ('T14 科学数据技能：K-Dense-AI', 'https://github.com/K-Dense-AI/scientific-agent-skills'),
        ('T15 可选视频技能：Remotion', 'https://github.com/remotion-dev/skills'),
        ('T16 独立编程Agent：Cline', 'https://github.com/cline/cline'),
        ('T17 国赛2024题目官方发布页', 'https://dxs.moe.gov.cn/zx/a/hd_sxjm_sthb/240605/1887443.shtml'),
    ]
    for label, url in sources:
        g.p(link(label, url), size=11.5, leading=17, gap=9, kind='source_entry')
    g.rule()
    g.p(local('五套候选的完整commit、许可与源码取舍', 'data/math-tools.json') + '<br/>' +
        local('两条数模路线与详细操作', 'docs/math-modeling.md') + '<br/>' +
        local('历史题实测、环境和复现入口', 'examples/cumcm2024b/README.md'), size=11.5, leading=20)

    # 26: Preserve all external evidence and selected social IDs in a compact index.
    g.page('集中来源 / 反馈', '22份外部材料与原帖索引', 'F编号对应既有外部材料；X/T编号对应75篇社会反馈，完整分类、边界与原链接留在仓库。')
    for item in feedback['external']:
        label = '%s  %s' % (item['id'], compact(item['title'], 34))
        g.p(link(label, item['url']), size=10.8, leading=15.1, gap=6, kind='source_entry')
    g.rule()
    lookup = {item['record_id']: item for item in social['records']}
    selected = ['X01', 'X05', 'X06', 'X16', 'X19', 'X21', 'X23', 'X24', 'X29', 'X36', 'X38', 'X42', 'X44']
    selected_links = [link(key, lookup[key]['url']) for key in selected if key in lookup]
    g.p('本册提及的原帖：' + '　'.join(selected_links), size=10.8, leading=17, gap=8)
    g.p(local('75篇分类数据与原帖链接', 'data/social-feedback.json') + '　|　' +
        local('22份外部材料全文记录', 'data/feedback-records.json') + '<br/>' +
        local('来源解读与U01作者自述', 'docs/field-feedback.md'), size=10.8, leading=17, gap=7)
    g.p('项目：' + link('Rain-dust/HowToCompeteBetter', REPOSITORY) + '<br/>结构灵感：' +
        link('eternity4719/HowToLiveBetter', 'https://github.com/eternity4719/HowToLiveBetter') + '；内容独立整理。', size=10.8, leading=17, color=MUTED)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--validation', type=Path, default=DEFAULT_VALIDATION)
    parser.add_argument('--measure-only', action='store_true', help='Measure all real content in memory; write no artifact.')
    args = parser.parse_args()
    data = load_inputs()
    register_fonts()
    if args.measure_only:
        target = io.BytesIO()
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        target = str(args.output)
    guide = Guide(target)
    make_pages(guide, *data)
    guide.save()
    validation = {
        'schema_version': 1,
        'generated_at': '2026-11-16',
        'source': 'scripts/build_guide.py',
        'page_count': len(guide.pages),
        'paper_size': 'A4',
        'body_font_size': [11.5, 12],
        'source_font_size': 10.8,
        'bounds': {'left': LEFT, 'right': RIGHT, 'bottom': BOTTOM, 'top': CONTENT_TOP},
        'layout_bounds_passed': all(p['bounds_passed'] for p in guide.pages),
        'run_summary_required_status': 'verified',
        'ranking_continuous_1_to_27': True,
        'visual_review': {'status': 'pending', 'required': 'Render and inspect every page after building; geometry is not visual QA.'},
        'page_map': guide.pages,
    }
    if args.measure_only:
        print(json.dumps({'measure_only': True, 'pages': len(guide.pages), 'layout_bounds_passed': True,
                          'minimum_remaining_height': min(p['remaining_height'] for p in guide.pages)}, ensure_ascii=False))
        return
    validation['pdf'] = str(args.output.resolve())
    validation['pdf_sha256'] = hashlib.sha256(args.output.read_bytes()).hexdigest()
    args.validation.parent.mkdir(parents=True, exist_ok=True)
    args.validation.write_text(json.dumps(validation, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'pdf': validation['pdf'], 'pages': len(guide.pages), 'validation': str(args.validation.resolve())}, ensure_ascii=False))


if __name__ == '__main__':
    main()
