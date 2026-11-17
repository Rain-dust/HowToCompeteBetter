# 高性价比大学生竞赛指南

**找到适合自己的比赛，用 Agent 做出完整作品。**

| 你现在想做什么 | 从这里开始 |
| --- | --- |
| **还没选比赛** | [按学历、设备和目标找比赛](docs/competition-catalog.md) |
| **已有 Codex，想做数模** | [准备检查 → 安装 → 启动](docs/coding-agent.md) |
| **已有项目，准备参赛** | [核评分、补证据、做演示与答辩](docs/project-delivery.md) |

[PDF预览](guide.pdf) · [下载PDF](https://github.com/Rain-dust/HowToCompeteBetter/raw/refs/heads/main/guide.pdf) · [先看真实数模成果](examples/cumcm2024b/README.md) · [零依赖小样例](templates/contest-starter-example/README.md)

## 先看这五项

**序号是制作参考顺序；当届建议单独看。** 计设的Codex许可待核，统计建模核心生成受限，不能仅凭排在前面决定报名。[排序怎么读](docs/how-to-read-ranking.md)

| 参考序号 / 赛事详情 | 当届怎么选 | 工具与开打 |
| --- | --- | --- |
| **1. [全国大学生数学建模竞赛（高教社杯/CUMCM）](docs/contests/N22.md)** | **先练习；正式赛仅辅助**<br>2026允许AI辅助，核心建模和分析由队员主导。先跑历史题，正式参赛另核当届规则。 | [教程](docs/coding-agent.md) · [GitHub](https://github.com/jihe520/MathModelAgent) |
| **2. [中国大学生计算机设计大赛（4C）](docs/contests/N38.md)** | **外部Codex许可待核**<br>2026限定工具名单，未查到Codex获准依据；历史省奖经历不能代替当届许可。 | [教程](docs/contests/N38.md#安装和启动) · [GitHub](https://github.com/anthropics/skills) |
| **3. [先进机器人及仿真技术大赛（RST）](docs/contests/N18.md)** | **先定赛项，再跑官方基线**<br>创新作品、仿真竞技和硬件赛分别核平台及AI范围；已熟悉平台者再比较投入。 | [教程](docs/contests/N18.md#安装和启动) · [可选技能GitHub](https://github.com/anthropics/skills) |
| **4. [全国大学生统计建模大赛](docs/contests/N23.md)** | **正式赛核心生成受限**<br>2026禁止AI直接生成核心研究设计与正文；这届不推荐作为Agent全程直出参赛路线。 | [教程](docs/contests/N23.md#安装和启动) · [GitHub](https://github.com/K-Dense-AI/scientific-agent-skills) |
| **5. [“中国软件杯”大学生软件设计大赛](docs/contests/N02.md)** | **纯软件题可研究；先核工具**<br>优先数据和接口可得的题；产品模型、开发辅助、SDK与现场要求分开核。 | [教程](docs/contests/N02.md#安装和启动) · [GitHub](https://github.com/anthropics/skills) |

<details>
<summary><strong>前五：展开复制安装和启动指令</strong></summary>

先按上表选择练习或正式赛范围。数模只有一条默认安装主线；其他项目按具体赛项和环境配置。

### 1. 全国大学生数学建模竞赛（高教社杯/CUMCM）

**先练习；正式赛仅辅助。** [完整赛事卡](docs/contests/N22.md)

[Codex完整安装与开跑](docs/coding-agent.md) · [Modex官方步骤](docs/modex.md)

启动：

~~~text
使用 $1start-mathmodel，完整处理 inputs/problem.pdf 与全部附件。偏好已给：Typst、国赛中文、问数按题面，不重复确认。连续完成建模、实际计算、图表、论文和验收；所有数字来自真实运行，缺失样本不伪造。完整重跑并编译PDF、逐页查看，交付代码、结果、图表、paper/main.pdf与验收清单。
~~~

### 2. 中国大学生计算机设计大赛（4C）

**外部Codex许可待核。** [完整赛事卡](docs/contests/N38.md)

安装：

~~~text
请从 https://github.com/anthropics/skills 将 skills/frontend-design 和 skills/webapp-testing 两个完整目录安装到当前项目 .agents/skills/。保留脚本和资源，按 SKILL.md 建隔离依赖并配置 Playwright 浏览器。已有技能先核对并复用。用最小网页做一次主流程测试，报告安装路径、commit、实际截图与缺失依赖。安装后在此项目重开会话或确认技能已被发现。
~~~

启动：

~~~text
我要做中国大学生计算机设计大赛软件作品。inputs/ 有当届规程、赛道要求和真实需求。先输出工具权限与评分项对照表：2026规程限制AI工具范围，不能默认Codex在名单内。用于赛前练习，或确认当前参赛范围允许后，用 $frontend-design 完成一个单一核心功能的可运行系统；用 $webapp-testing 测正常、空输入和异常场景。交付实际运行视频、源码、部署说明和过程材料；演示必须来自同一版本，别只做PPT。
~~~

### 3. 先进机器人及仿真技术大赛（RST）

**先定赛项，再跑官方基线。** [完整赛事卡](docs/contests/N18.md)

安装：

~~~text
先读 inputs/ 的具体RST届次、赛项、平台和SDK。仿真竞技先配置官方环境并运行基线，不预装无关网页技能。只有创新作品确实需要Web界面时，才从 https://github.com/anthropics/skills 完整安装 frontend-design 与 webapp-testing 到项目 .agents/skills/ 并做最小验证。报告实际平台版本、基线成绩、日志和缺失依赖。
~~~

启动：

~~~text
我要参加RST，具体届次、赛道、组别、官方规则和平台SDK已放 inputs/。先识别这是创新创业作品还是仿真竞技，不能混用评审方式。创新作品：完成一个能运行并按评分点演示的小产品；仿真：先跑官方基线、记录多次成绩，再逐项改策略，输出同环境的对照、失败回放和日志。按我的具体组别整理源码、说明、视频与答辩。官方基线未跑通前先修环境，不虚构成绩。
~~~

### 4. 全国大学生统计建模大赛

**正式赛核心生成受限。** [完整赛事卡](docs/contests/N23.md)

安装：

~~~text
请从 https://github.com/K-Dense-AI/scientific-agent-skills 安装 skills/exploratory-data-analysis 与 skills/statistical-analysis 两个完整目录到当前项目 .agents/skills/，连同引用资源一起保留。按各 SKILL.md 配置独立 Python 环境，不安装无关科学栈。用本地合成CSV完成一次有缺失值、重复和分组信息的检查，报告环境、commit与结果。此安装用于赛前练习，不代表获准生成正式参赛核心内容。
~~~

启动：

~~~text
请先读 inputs/ 的全国大学生统计建模大赛当届AI规范。2026正式赛模式只执行规则明确允许的文献检索整理、语言格式校对等环节；不要直接生成研究选题、假设、框架、调查方案或论文正文。把拟执行的数据与代码任务单独列出待核权限。赛前练习模式下，可用 $exploratory-data-analysis 和 $statistical-analysis 对合成/历史练习数据做审计、按已给方案复现与诊断，输出可重跑代码和错误记录。正式提交内容以获准范围和人工原创方案为准。
~~~

### 5. “中国软件杯”大学生软件设计大赛

**纯软件题可研究；先核工具。** [完整赛事卡](docs/contests/N02.md)

安装：

~~~text
请从 https://github.com/anthropics/skills 将 skills/frontend-design 和 skills/webapp-testing 两个完整目录安装到当前项目 .agents/skills/。保留脚本和资源，按 SKILL.md 建隔离依赖并配置 Playwright 浏览器。已有技能先核对并复用。用最小网页做一次主流程测试，报告安装路径、commit、实际截图与缺失依赖。安装后在此项目重开会话或确认技能已被发现。
~~~

启动：

~~~text
我要参加中国软件杯。inputs/ 有当届题目、评分标准、规定技术栈、工具条款与原始数据。先把每个评分点写成可操作验收动作，确认数据、接口和硬件可得，再做最小端到端系统。用 $frontend-design 打磨界面，用 $webapp-testing 验证Web评分动作与异常输入；原生部分另用对应测试工具。先修稳定性再加功能，最后交源码、环境锁定、部署说明、同版本演示视频和答辩问答，保留AI开发记录。
~~~

</details>

<details>
<summary><strong>完整连续参考顺序 1–27：点名字直接看赛事卡</strong></summary>

| 参考序号 | 比赛 | 当届建议 |
| :--: | --- | --- |
| 1 | [全国大学生数学建模竞赛（高教社杯/CUMCM）](docs/contests/N22.md) | 先练习；正式赛仅辅助 |
| 2 | [中国大学生计算机设计大赛（4C）](docs/contests/N38.md) | 外部Codex许可待核 |
| 3 | [先进机器人及仿真技术大赛（RST）](docs/contests/N18.md) | 先定赛项，再跑官方基线 |
| 4 | [全国大学生统计建模大赛](docs/contests/N23.md) | 正式赛核心生成受限 |
| 5 | [“中国软件杯”大学生软件设计大赛](docs/contests/N02.md) | 纯软件题可研究；先核工具 |
| 6 | [美国大学生数学建模竞赛（MCM/ICM）](docs/contests/E06.md) | 允许负责任AI辅助，须披露 |
| 7 | [MathorCup数学应用挑战赛](docs/contests/E02.md) | 核心独立完成，AI仅辅助 |
| 8 | [华中杯大学生数学建模挑战赛](docs/contests/H01.md) | 先核具体赛项与工具范围 |
| 9 | [“中国电机工程学会杯”全国大学生电工数学建模竞赛](docs/contests/E05.md) | 先核具体赛项与工具范围 |
| 10 | [“泰迪杯”数据挖掘挑战赛](docs/contests/E01.md) | 先核具体赛项与工具范围 |
| 11 | [中国大学生服务外包创新创业大赛](docs/contests/N01.md) | 有真实产品需求，再查OPC |
| 12 | [全国大学生数字媒体科技作品及创意竞赛](docs/contests/N10.md) | 先核具体赛项与工具范围 |
| 13 | [未来设计师·全国高校数字艺术设计大赛（NCDA）](docs/contests/N11.md) | 先核具体赛项与工具范围 |
| 14 | [全国大学生软件创新大赛](docs/contests/N03.md) | 先核具体赛项与工具范围 |
| 15 | [全球校园人工智能算法精英大赛](docs/contests/N09.md) | 先核具体赛项与工具范围 |
| 16 | [中国高校计算机大赛-人工智能创意赛](docs/contests/N04.md) | 先核具体赛项与工具范围 |
| 17 | [华为ICT大赛-创新赛](docs/contests/N28.md) | 先核具体赛项与工具范围 |
| 18 | [中国高校智能机器人创意大赛](docs/contests/N15.md) | 先核具体赛项与工具范围 |
| 19 | [睿抗机器人开发者大赛（RAICOM）](docs/contests/N17.md) | 先核具体赛项与工具范围 |
| 20 | [全国大学生电子商务“创新、创意及创业”挑战赛（三创赛）](docs/contests/N20.md) | 已有真实项目再考虑 |
| 21 | [中国国际大学生创新大赛（原“互联网+”）](docs/contests/N30.md) | 已有真实项目再考虑 |
| 22 | [“挑战杯”全国大学生课外学术科技作品竞赛](docs/contests/N31.md) | 已有真实项目再考虑 |
| 23 | [“挑战杯”中国大学生创业计划竞赛](docs/contests/N32.md) | 已有真实项目再考虑 |
| 24 | [全国大学生市场调查与分析大赛（正大杯）](docs/contests/N21.md) | 核心由人完成，辅助范围另核 |
| 25 | [全国大学生能源经济学术创意大赛](docs/contests/N24.md) | 不适合AI自动生成作品参赛 |
| 26 | [“华数杯”大学生数学建模竞赛](docs/contests/E03.md) | 先核具体赛项与工具范围 |
| 27 | [华为杯中国研究生数学建模竞赛](docs/contests/G01.md) | 先核研究生资格；AI仅辅助 |

</details>

## 选好以后，完成第一步

| 卡在哪里 | 直接拿走 |
| --- | --- |
| 不知道自己能报什么、学校认不认 | [三关选赛卡与校内资源](docs/competition-playbook.md) |
| 没有数据或不知道怎么引用 | [原始数据入口与来源台账](docs/data-sources.md) |
| 第一次让Agent做完整项目 | [已填小样例](templates/contest-starter-example/README.md) → [空白模板](templates/contest-starter/README.md) |
| 想看代码、论文和实际运行结果 | [2024国赛B：17页论文与复现包](examples/cumcm2024b/README.md) |

## 下载与查阅

- [指南PDF](guide.pdf)：有章节书签、可点击导航和返回导航入口。
- [全部73条参考](docs/competition-catalog.md)：统一赛事卡，分别写资格、奖项路径、成本、人工任务与依据。
- [下载离线筛选页](https://github.com/Rain-dust/HowToCompeteBetter/releases/latest/download/explorer.html)：保存HTML后用浏览器打开；筛选无需联网，打开详情需要联网。
- [开赛模板ZIP](templates/contest-starter.zip) · [版本下载](https://github.com/Rain-dust/HowToCompeteBetter/releases/latest)

<details>
<summary>PDF首页预览</summary>

<a href="guide.pdf"><img src="assets/ranking-preview.png" alt="指南首页，点击查看有导航的完整PDF" width="380"></a>

</details>

## 依据与更新

数模记录：Codex实际完成历史国赛B题，经中断恢复与修正；Modex整理官方教程，Claude未做本轮端到端运行。历史练习与获奖验证分开。

[真实参赛反馈](docs/field-feedback.md) · [证据与来源](docs/research/README.md) · [更新记录](CHANGELOG.md) · [贡献方式](CONTRIBUTING.md)

反馈库保留75篇原帖、22份外部材料；二手知识整理单列，不能推出获奖率。各赛事卡显示资料核查日期，页面更新不表示所有当届规则已重查。

[提交参赛经历](https://github.com/Rain-dust/HowToCompeteBetter/issues/new?template=experience.yml) · [纠错与补规则](https://github.com/Rain-dust/HowToCompeteBetter/issues/new?template=correction.yml)

页面更新：**2026-11-17**。结构灵感来自[高性价比人生指南](https://github.com/eternity4719/HowToLiveBetter)，竞赛资料独立整理。

<!-- Generated by scripts/build_readme.py from data/competitions.json. -->
