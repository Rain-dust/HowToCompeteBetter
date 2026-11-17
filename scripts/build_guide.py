"""Build the navigable v8 guide from the canonical contest source and verified run.

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
DEFAULT_OUTPUT = ROOT / 'output/pdf/高性价比大学生竞赛指南_v8_2026-11-17.pdf'
DEFAULT_VALIDATION = ROOT / 'research/pdf-v8-validation.json'
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


def jump(label, page):
    return link(label, '#page-%02d' % page)


def load_inputs():
    contests = read_json('data/competitions.json')
    ordered = sorted((r for r in contests if isinstance(r.get('rank'), int)), key=lambda r: r['rank'])
    ranking = [dict(r['ranking_view'], rank=r['rank'], catalog_id=r['id'],
                    card_path=r['card_path'], decision_label=r['decision_label'],
                    decision_note=r['decision_note'], cost_summary=r['cost_summary']) for r in ordered]
    top5 = [dict(r['top5_view']) for r in ordered[:5]]
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
        self.c.setTitle('高性价比大学生竞赛指南 - v8 / 2026-11-17')
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
        destination = 'page-%02d' % num
        c.bookmarkPage(destination)
        c.addOutlineEntry('%02d  %s' % (num, title), destination, level=0, closed=False)
        c.setFillColor(TEAL)
        c.rect(LEFT, H - 37, 23, 3, fill=1, stroke=0)
        c.setFont('GuideBody', 9)
        c.setFillColor(MUTED)
        c.drawString(LEFT + 33, H - 38, 'HOW TO COMPETE BETTER  /  ' + section)
        c.setStrokeColor(LINE)
        c.setLineWidth(.55)
        c.line(LEFT, 34, RIGHT, 34)
        c.setFont('GuideBody', 8.5)
        c.drawString(LEFT, 21, 'v8 · 2026-11-17   |   制作参考与当届参赛建议分开')
        c.setFillColor(TEAL)
        c.drawRightString(RIGHT - 35, 21, '返回导航')
        c.linkRect('', 'page-02', (RIGHT - 96, 13, RIGHT - 31, 31), relative=0, thickness=0)
        c.setFillColor(MUTED)
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
        self.p(local(title, row['card_path']), size=12.2, leading=16, bold=True, gap=3, kind='ranking_title')
        self.p(E(track), size=11.5, leading=15.7, color=MUTED, gap=3, kind='ranking_track')
        self.p('<font color="#007e87">' + E(row['decision_label']) + '</font>  |  ' + E(evidence),
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
        if len(self.pages) != 30:
            raise AssertionError('Expected exactly 30 designed pages, got %d.' % len(self.pages))
        self.c.save()


def compact(text, limit):
    text = str(text)
    return text if len(text) <= limit else text[:limit - 1] + '…'


def repo_line(g, label, url):
    g.p(link(label, url), bold=True, size=11.5, gap=3)
    g.p(E(url), size=11.5, color=MUTED, gap=11)


def make_pages(g, ranking, top5, feedback, social, run):
    contests = read_json('data/competitions.json')
    knowledge = read_json('data/knowledge-import.json')
    supplements = [r for r in read_json('data/competitions.json') if r['id'] in ['L01', 'L02', 'L03', 'L04', 'L05']]
    if len(knowledge['records']) != 33 or len(supplements) != 5:
        raise ValueError('Expected 33 source notes and five supplemental entries.')
    # 01: Lead with a usable conclusion, not the research apparatus.
    g.page('先选入口', '高性价比大学生竞赛指南', '先找到自己的路径，再看工具、投入与证据。版本：2026-11-17。')
    g.note(jump('还没选比赛：先看资格、奖项路径和投入', 23) + '<br/>' +
           jump('已有Codex想做数模：从准备检查直接开跑', 10) + '<br/>' +
           jump('已有项目准备参赛：核评分、补证据与演示', 24), '点这里，直接开始', size=12)
    g.h('先看参考前五，当届建议单列')
    targets = {1: 10, 2: 16, 3: 17, 4: 18, 5: 19}
    for row in ranking[:5]:
        g.p('<font color="#007e87"><b>%02d</b></font>  <b>%s</b><br/><font color="#526673">%s</font>' %
            (row['rank'], jump(row['name'], targets[row['rank']]), E(row['decision_label'])), size=12, leading=18, gap=12)
    g.p('序号用于浏览制作适配，不是当届推荐或获奖率。计设许可待核、统计核心生成受限，不能因名次靠前就直接报名。', color=MUTED, size=11.5)
    g.rule()
    g.p(jump('打开完整导航', 2) + '　|　' + jump('不装模型，先跑小样例', 20) + '　|　' + jump('比较前五投入', 3), size=12, leading=20)

    # 02: A clickable task-based contents page.
    g.page('导航 / 可点击', '你现在要解决什么', '点击蓝色文字跳转；任意页底都能返回这里，阅读器侧栏也有30个章节书签。')
    g.table(['现在想做什么', '直接跳到'], [
        ['还没选比赛，先看条件与投入', jump('前五投入对照 / 第03页', 3) + '<br/>' + jump('选赛三关 / 第23页', 23)],
        ['浏览全部1-27连续参考顺序', jump('第04页开始', 4)],
        ['已有Codex，直接处理历史数模题', jump('准备、安装、运行 / 第10-12页', 10)],
        ['想用Windows现成软件', jump('Modex官方教程 / 第07-09页', 7)],
        ['先看实际论文与可复现结果', jump('2024国赛B记录 / 第13-15页', 13)],
        ['先跑一个不需要模型的小练习', jump('合成数据完整小样例 / 第20页', 20)],
        ['已有作品，准备材料与答辩', jump('数据与交付 / 第24页', 24)],
        ['核对规则、工具与参赛反馈', jump('集中来源 / 第26-30页', 26)],
    ], [255, WIDTH - 255], size=11.5, leading=17, pad=9)
    g.h('想查某一项的完整情况')
    g.p(local('打开全部%d张赛事卡目录' % len(contests), 'docs/competition-catalog.md') + '：每项分别写资格、奖项路径、人数、时间、费用、人工任务与资料日期。', size=11.5)
    g.p(link('下载离线筛选页后，用浏览器打开', REPOSITORY + '/releases/latest/download/explorer.html') + '；筛选在本地运行，跳到GitHub赛事详情需要联网。', size=11.5)
    g.note('第一次练习默认走已跑通的Codex路线。Modex是官方步骤整理，未安装实测；Claude兼容安装不等于本轮端到端测试。', '先看清验证状态', size=11.5)

    # 03: Comparable effort fields without invented prices or probabilities.
    g.page('投入 / 人工任务', '参考前五，还要自己做什么', '费用未知就保留未知。旧版人时估算不是实测，不能拿它与模型运行分钟数比较。')
    for row in ranking[:5]:
        cost = row['cost_summary']
        registration = '待核' if '待核' in cost['registration_fee'] else compact(cost['registration_fee'], 16)
        model_cost = '未取得单次账单' if '未测' in cost['model_fee'] else compact(cost['model_fee'], 16)
        g.p('<b>%02d  %s</b>　%s' % (row['rank'], E(row['name']), jump('看做法', targets[row['rank']])), size=12.5, leading=18, gap=4)
        g.p('<font color="#007e87">%s</font><br/>人要做：%s' % (E(row['decision_label']), E(compact(cost['human'], 61))), size=11.5, leading=17, gap=5)
        g.p('组队：%s<br/>报名费：%s；模型费：%s。' % (E(cost['team']), E(registration), E(model_cost)), size=11, leading=16, color=MUTED, gap=14)
    g.note('数模本机记录约35.52分钟，仅为两次CLI运行墙钟合计；含额度中断后的恢复，不含暂停、环境、外部审计与打包。它不是完整备赛工时或费用账单。', '实际测量与估算分开', size=11.5)

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
        g.page('连续制作参考顺序', '参考顺序 %02d-%02d' % (lo, hi), '接续前五，不分档。点比赛名打开赛事卡；蓝色为当届建议，序号不表示当前获准或拿奖概率。')
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
    g.p('准备：Codex CLI、Git、Python 3.12、uv、完整附件与可用模型额度。已测Windows 10 build19045，其他系统未端到端验证。', size=11.5)
    g.note('装了桌面版不等于CLI就绪。在普通终端运行 <b>codex --version</b> 与 <b>codex login status</b>，确认命令可用且已登录，再继续安装。', '先检查这两条', size=11.5)
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
        ['code/ 与 audit/', '计算源码与独立核验脚本。'],
        ['results/', '四问JSON、汇总CSV与检查结果。'],
        ['figures/', '论文图表及其实际计算来源。'],
        ['paper/main.typ 与 main.pdf', '可编辑论文源文件与编译成稿。'],
        ['reports/ 与运行清单', '分析、结果、环境和验收证据。'],
    ], [190, WIDTH - 190], size=11.5, leading=17, pad=8)
    g.note('在干净环境重跑，核对六个Q2策略与利润、Q3成本/利润及Q4假想样本标记。然后重新编译论文，逐页查看数字、图表、公式和排版。', '复现后的验收动作', size=12)
    g.p(local('打开示例README与完整复现说明', 'examples/cumcm2024b/README.md') + '<br/>' + local('查看run-summary.json', 'examples/cumcm2024b/run-summary.json') + '　|　' + link('下载成果ZIP', REPOSITORY + '/raw/refs/heads/main/examples/cumcm2024b-example.zip'), size=11.5)

    # 16-19: Install/start text is rendered from the canonical top5_view.
    route_titles = {2: '计算机设计：先确认工具范围', 3: 'RST：先定赛项和官方平台', 4: '统计建模：核心生成受限', 5: '软件杯：按评分做完整系统'}
    for row in ranking[1:5]:
        task = next(t for t in top5 if t['rank'] == row['rank'])
        g.page('参考第%02d项 / 做法' % row['rank'], route_titles[row['rank']], '完整安装和启动来自唯一赛事数据源；练习与正式参赛范围分开。')
        g.note(E(row['decision_note']), row['decision_label'], size=11.5)
        github = task.get('github', [])
        if github:
            g.p('工具出处：' + '　'.join(link(label, url) for label, url in github[:2]), size=11.5, leading=17)
        g.code(task.get('install', '先读具体平台与规则，按赛事卡配置环境。'), '可复制：安装与准备')
        g.code(task.get('start', '读取当届赛题与评分表，先跑完整基线。'), '可复制：启动任务')
        g.p('交付：' + E(task.get('deliver', '按具体赛项要求整理可复现成果。')), size=11.5, leading=17)
        g.p(local('打开本项完整赛事卡、投入和证据', row['card_path']), size=11.5)

    # 20: A filled, deterministic, no-model starter rather than another blank checklist.
    g.page('第一次练习 / 无需模型', '先跑一个有完整输入的小样例', '自拟合成工单练习；不是历届赛题、真实校园调研或获奖作品。3分钟是建议上手预算。')
    g.note('只需已安装Python 3.12或更新版本，不用模型账号、密钥、网络或第三方库。先看一次完整输入如何变成结果。', '最少准备', size=12)
    g.code(['python templates/contest-starter-example/run.py'], '在仓库根目录运行')
    g.table(['固定练习输入', '应得到的真实计算结果'], [
        ['输入 / 有效 / 剔除', '15 / 10 / 5 条'],
        ['有效记录总响应时长', '450 分钟'],
        ['图书馆 / 宿舍 / 教学楼平均值', '30 / 60 / 40 分钟'],
    ], [245, WIDTH - 245], size=11.5, leading=17, pad=9)
    g.p('打开results/report.md与chart.svg，看结果和图。summary.json/CSV、rejected.csv与checks.json保留计算和验收。所有输出都明确标注合成数据，不能当作真实调查。', size=11.5)
    g.h('然后只给Agent一个小任务')
    g.code(['读已填项目卡、原始工单和现有代码，先重跑。', '增加各类别记录数图，沿用合成数据标识。', '每个数字能追到结果文件，重跑仍能生成。'], '完成标志：多一张可核验的图')
    g.p(local('打开已填样例与完整命令', 'templates/contest-starter-example/README.md') + '<br/>' + local('熟悉后复制空白工作区', 'templates/contest-starter/README.md'), size=11.5, leading=20)

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

    # 23-25: Newly distilled operational guidance, not copied third-party prose.
    g.page('选赛 / 先过三关', '别先报名，先查你已有的底座', '吸收浪尖知识库的学校资源与项目路径思路，改写为Agent项目的执行方法。时间预算不是拿奖统计。')
    for title, text in [
        ('01  本校认不认', '查当学年认定、具体赛项、奖级、团队排序和校内推荐要求。全国性赛事、国奖证书、本校A类分别确认。'),
        ('02  允许这样打吗', '查当届身份、工具表、AI任务范围、现场操作与复用限制。历史获奖经历不覆盖新规则。'),
        ('03  资源现在拿得到吗', '题面、真实数据、接口、平台、设备、队友与指导教师逐项确认。先跑一条基线，再决定投入。'),
    ]:
        g.h(title)
        g.p(E(text), gap=16)
    g.note('按顺序查本校：教务/双创/团委通知 → 近两年获奖与指导教师 → 大创公示和已有团队 → 实验室与课程项目。名单人数不代表有空位，联系后再确认。', '先找资源，再另起项目', size=11.5)
    g.p('大创是训练计划，不是另一个竞赛奖项。同一底座能否转投其他比赛，要核主题、原创、已获奖作品与重复申报限制。', size=11.5)
    g.code(['读inputs/的本校认定、当届规程和现有项目。', '最多保留两个候选，逐项列依据、缺口与新增工作。', '先用历史题或练习任务跑最小基线，不编获奖率。'], '可复制：先做选赛卡')
    g.p(local('完整选赛、组队与条件复用表', 'docs/competition-playbook.md'), size=11.5)

    g.page('数据 / 交付', '每个结论，都有拿得出的证据', '先找原表，再清洗、计算、作图。没有真实样本的合成演示，不能写成调研或营业实绩。')
    g.table(['需要什么', '先查哪里 / 注意什么'], [
        ['国内地区指标', '国家统计局、国家数据；核单位、年份、统计口径和行政区划。'],
        ['跨国发展数据', 'World Bank、UNdata；核指标代码、缺失值与发布机构。'],
        ['地理环境数据', '国家地球系统科学数据中心、资源环境平台；核许可、坐标与分辨率。'],
        ['企业经营事实', '巨潮资讯年报与公告；核报告页码、合并口径和实际年度。'],
    ], [125, WIDTH - 125], size=11.5, leading=17, pad=9)
    g.note('原始URL、发布者、表号/页码、数据期、单位、使用条件、文件hash、清洗脚本和对应图表一起登记。找到入口不代表已下载或可再分发。', '来源链比链接堆更有用', size=11.5)
    g.h('先做评分-证据表，再写材料')
    g.p('评分原文 → 验收动作 → 实际文件 → 运行版本 → 缺口 → 负责人。项目说明回答能否做成；商业材料需要真实用户与成本；论文需要可复算结果。', size=11.5)
    g.code(['按正式评分表验收源码、结果、文稿和演示。', '逐项核同版本数字、图表和功能，缺证据写缺失。', '给出12个追问，每个答案指向现有证据。', '不编用户、访谈、营收、合作、专利或奖项。'], '可复制：让Agent做挑错评委')
    g.p(local('数据入口与来源台账', 'docs/data-sources.md') + '　|　' + local('作品、演示与答辩', 'docs/project-delivery.md') + '<br/>' + local('复制开赛工作区与启动指令', 'templates/contest-starter/README.md'), size=11.5, leading=19)

    g.page('新增线索 / 逐项筛选', '补充五个入口，不硬塞进主榜', '目录共有%d条参考，包含分支与平台；补齐了原第8项漏掉的华中杯卡。新线索不自动改变参考顺序。' % len(contests) + '')
    verdicts = {
        'L01': '高职优先研究软件/AI作品；别套本科资格和工具表。先看高职通知，再做可运行核心功能。',
        'L02': '用现有数模链做历史题迁移练习。完整AI细则未读到，正式提交范围和学校认定待核。',
        'L03': '专用经营模拟平台赛，不是只交BP。先拿训练账号和真实记录，Agent用于获准的策略复盘。',
        'L04': '先筛软件/仿真方向，核设备、PLC、授权与现场条件。官方基线跑不通，先别谈自动代打。',
        'L05': '2026为43赛道，AI等指定范围有普通本科组别。要学校推荐，也要现场操作与讲解。',
    }
    for row in supplements:
        g.p('<b>' + E(row['name']) + '</b>', size=12.5, leading=18, gap=5)
        g.p(E(verdicts[row['id']]), size=11.5, leading=17, gap=17)
    g.note('2026国赛为9月10日18时至13日20时，共74小时；各校报名可能更早。旧“84项”目录不能推出教育部统一ABC。匿名故事、融资额与培训保奖承诺不计独立成功案例。', '这轮没有照抄的内容', size=11.5)
    g.p(local('五项完整资格、权限、官方依据与知识库取舍', 'docs/knowledge-integration.md'), size=11.5)

    # 26-27: Full clickable rule sources, at the end rather than interrupting tutorials.
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

    g.page('集中来源 / 本轮整合', '新增官方依据与知识库出处', '知识库用于启发检索和执行方法；资格、赛制和权限另外核原文。核查日期：2026-11-16。')
    for label, url in [
        ('K01 高职计设2026：校方当届通知', 'https://it.hceb.edu.cn/info/1053/25691.htm'),
        ('K02 高职计设2026：全国决赛信息', 'https://www.shanghai.gov.cn/nw15343/20260826/45f8f2a0b59a44928dfed0e89024876a.html'),
        ('K03 中青杯2026：官方通知入口，附件未完整读取', 'https://zqb.52jingsai.com/newss.php?id=42'),
        ('K04 学创杯2026：西安交大组织通知', 'https://dean.xjtu.edu.cn/info/1172/10073.htm'),
        ('K05 西门子杯2026：组委会初赛通知', 'https://www.siemenscup-cimc.org.cn/notice/NoticeDetail?id=2432'),
        ('K06 西门子杯2026：参赛与官方学习说明', 'https://www.siemenscup-cimc.org.cn/joinflow/index'),
        ('K07 世界职业院校技能大赛：2026教育部方案', 'https://www.moe.gov.cn/srcsite/A07/s7055/202608/t20260820_1447374.html'),
        ('K08 大创：教育部训练计划管理办法', 'https://www.moe.gov.cn/srcsite/A08/s5672/201907/t20190724_392132.html'),
        ('K09 国赛2026：中科大报名与正式赛时间', 'https://math.ustc.edu.cn/2026/0520/c18650a741197/pagem.htm'),
    ]:
        g.p(link(label, url), size=11.3, leading=17, gap=8, kind='source_entry')
    g.rule()
    g.p('数据原始入口：' + link('国家统计局', 'https://www.stats.gov.cn/') + '　' + link('国家数据', 'https://data.stats.gov.cn/') + '　' + link('World Bank', 'https://data.worldbank.org/') + '　' + link('UNdata', 'https://data.un.org/') + '<br/>' + link('国家地球系统科学数据中心', 'https://www.geodata.cn/') + '　' + link('资源环境平台', 'https://www.resdc.cn/') + '　' + link('巨潮资讯', 'https://www.cninfo.com.cn/'), size=11.3, leading=19, gap=16)
    g.p(link('浪尖知识库2026：原站', 'https://langjian-knowledge-2026.pages.dev/') + '<br/>' + local('33条标题、原链接、重点16条与采纳/未采纳说明', 'data/knowledge-import.json') + '<br/>' + local('本项目改写后的完整工作流与核对方法', 'docs/knowledge-integration.md'), size=11.3, leading=20)
    g.note('仅发布短摘要、链接和自主改写，不分发原文、课程、登录信息或站内用户资料。二手整理与直播口播不增加独立获奖样本；原来的75篇社会反馈与22份外部材料保持不变。', '来源与使用范围', size=11.5, fill=PALE)


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
        'generated_at': '2026-11-17',
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
