# Codex数模：安装一次，再给完整赛题

**主选：[MathModelAgent 当前 skills 链](https://github.com/jihe520/MathModelAgent)，入口 `$1start-mathmodel`。不用部署旧版 Web、Redis 或 Docker。**

固定版本：`03f4eb388b3862b7bde55b508dceaf3d6b39d5ac`。[2024 国赛 B 实测记录](../examples/cumcm2024b/README.md)单列实际成果。下面默认走已跑通的Codex CLI路线；Claude入口放在后面。

## 先检查你现在能不能跑

**已经装了桌面版，不代表这份命令行教程已准备好。** 先在普通终端检查以下条件，不要先启动模型。

| 条件 | 你需要看到什么 | 没准备好时 |
| --- | --- | --- |
| 系统 | 本项目验证：Windows 10 build19045；其他系统未端到端验证 | Mac/Linux先自行配Typst与中文字体，再预检；不保证照抄Windows路径可用 |
| Codex CLI | `codex --version`能运行；本例版本0.167.0-alpha.3.2 | 仅桌面版可用时，按[官方CLI安装](https://learn.chatgpt.com/docs/cli)补齐终端命令 |
| CLI登录 | `codex login status`返回已登录；实际模式可能是ChatGPT或API | 按[官方认证说明](https://learn.chatgpt.com/docs/auth?surface=cli)完成登录，不把密钥发进聊天 |
| 基础工具 | `git --version`、`python --version`、`uv --version`可运行 | 安装[Git](https://git-scm.com/downloads)、[Python](https://www.python.org/downloads/)与[uv](https://docs.astral.sh/uv/getting-started/installation/)；目标Python为3.12 |
| 排版 | 安装脚本会准备Typst；已有编译器可传路径 | Windows自动下载已测，其他系统先装[官方Typst](https://github.com/typst/typst/releases) |
| 费用与时间 | 有可用模型额度；单次实付费用未知 | 先预检。35.52分钟只统计本例两次CLI运行，含恢复，不是总准备或备赛时间 |
| 题目 | 完整题面PDF、全部附件和历史题/正式赛用途明确 | 先用[公开历史题入口](https://dxs.moe.gov.cn/zx/a/hd_sxjm_sthb/240605/1887443.shtml)，不要只给标题 |

**准备好后只走下面三步：建工作区 → 预检 → 启动。** 本项目不替你测算购买订阅或模型服务的价格；本例复用已有ChatGPT登录，确实遇到额度耗尽。其他CLI版本先预检，参数变化查[官方命令参考](https://learn.chatgpt.com/docs/cli/reference)。核对日期：2026-11-17。

## 1. 创建工作区

逐行执行，安装在新目录，不修改全局 Python：

~~~text
git clone https://github.com/Rain-dust/HowToCompeteBetter.git
cd HowToCompeteBetter
python scripts/setup_math_workspace.py --workspace ../my-math-run
~~~

脚本固定上游版本，复制分析、代码、图示、论文和验收的完整兄弟技能及 `_references`。Codex入口在 `.agents/skills/`，Claude入口在 `.claude/skills/`；建立独立环境并下载官方 Typst。不会调用模型或读取密钥。

上游有个人免费、限制商业用途和闭源分发的许可，本仓库不打包整套上游技能。[许可原件](https://github.com/jihe520/MathModelAgent/blob/03f4eb388b3862b7bde55b508dceaf3d6b39d5ac/docs/md/License.md)

已有 Typst 可传 `--typst 完整路径`。编译器自动下载仅在 Windows 验证；其他系统先自行安装 Typst。脚本会拒绝覆盖没有标记的非空目录。

## 2. 放题目，先预检

把题面存成 `../my-math-run/inputs/problem.pdf`，附件保留原文件名放在 `inputs/`。历史案例：[官方发布页](https://dxs.moe.gov.cn/zx/a/hd_sxjm_sthb/240605/1887443.shtml)、[题面PDF镜像](https://jichu.greathiit.com/uploadfile/2024/1015/20241015214235830.pdf)。本仓库不转载题面文件。

~~~text
python scripts/run_codex_math.py --workspace ../my-math-run --preflight
~~~

看到 Codex 版本、`Python stack OK`、Typst版本与 `Preflight passed; no model call.` 才开跑。否则先修环境，避免花模型额度处理安装。

## 3. 一次启动完整链

~~~text
python scripts/run_codex_math.py --workspace ../my-math-run
~~~

复用已登录的 Codex，使用工作区沙箱与自动审批，不用 `--yolo`。任务与事件日志在 `run-logs/UTC时间-唯一编号/`，每次启动与恢复均保留独立目录；脚本的退出码0不代表数学正确。

若使用Codex桌面界面，在其中打开 **my-math-run文件夹**，确认技能已发现后，也可复制下面这条任务。不要在指南仓库根目录直接调用未安装的技能：

~~~text
使用 $1start-mathmodel 完整处理 inputs/problem.pdf 与同目录附件。
偏好已确定：Typst、国赛中文，问数按题面；不要重复询问已给偏好。
依次完成分析建模、真实计算、图表、必要流程图、论文和验收，不停在计划。
所有数字必须来自本次运行；标明假设、近似和策略范围。没有样本时只做明确标注的条件演示，不编造实测。
完整重跑，编译 paper/main.pdf，并将最终PDF逐页渲染查看；失败修复后重验。
交付源码、结果、图表、完整论文、VERIFY_REPORT.md与含版本/输入和产物hash的RUN_MANIFEST.json。未完成项不得标PASS。
~~~

美赛改为英文与 MCM 模板，其他杯赛改成对应比赛。首条任务提前给清偏好是为了连续推进；实质信息缺失仍应如实补充，不假写成人工批准。

## 其他coding-agent入口

**已在用Claude Code的人**：安装脚本同时准备 `.claude/skills/`，在新工作区重开Claude Code并确认技能可用，再发送上面的完整任务。[官方安装](https://code.claude.com/docs/en/setup)。本项目没有做Claude端到端实测，不需要为了跟教程再装第二个agent。

想用Windows成品界面而非自己管理依赖，另看[Modex官方步骤](modex.md)。这不会改变本页默认的Codex路线。

## 4. 成果在哪里

~~~text
my-math-run/
  plan.md、todo.md
  code/           计算和验证源码
  results/        数值表、JSON与模拟证据
  figures/        图表及数据来源
  reports/        分析、结果和验收
  paper/main.typ  论文源文件
  paper/main.pdf  实际编译的论文
  run-logs/       启动任务、事件与退出状态
~~~

原上游允许无法编译或视觉检查时解释后通过；本教程加严为两项都实际完成。不要只看最后一句“已完成”。

## 5. 中断后继续

保留原工作区与日志，恢复额度或修复环境后，在目录中运行 `codex resume`，选择原会话，发送“保留代码和已算结果，从todo未完成项继续，修复后重验”。使用本仓库启动器可运行 `python scripts/run_codex_math.py --workspace ../my-math-run --resume 会话ID`；原生命令为 `codex exec resume 会话ID -`；[官方说明](https://learn.chatgpt.com/docs/non-interactive-mode)。本轮实际遇到额度中断并恢复，详见运行记录。

不要因为一张图有问题就重生成整篇；指出具体文件，要求同步重算受影响的结果。

## 6. 常见卡点

| 现象 | 处理 |
| --- | --- |
| 找不到技能 | 在正确工作区重开会话；保留兄弟技能、模板和_references，不能只装一个SKILL.md |
| 重复询问引擎 | 首条任务预先写明Typst/比赛/语言/问数，并沿用已给偏好 |
| 只有Markdown没PDF | 先看编译错误；检查Typst、中文字体、图路径，编译成功才算交付 |
| Windows引号报SyntaxError | 把长代码写成.py再执行；别混用cmd/PowerShell转义 |
| 本机PowerShell CET崩溃 | 本轮测试改用cmd.exe；这是测试机环境故障，非模型算法错误 |
| writing_check.sh跑不了 | 需Git Bash和python3；Windows安装脚本提供python3.exe别名，或做工作区内等效适配并记录 |
| 没drawio导出器 | 保留可编辑XML，以记录在案的适配器导出；不能说已用DrawIO软件导出 |
| workspace is out of credits | 保存成果，恢复额度后继续原会话 |
| 自检全过但结论可疑 | 再用独立公式、边界和物理事件模拟交叉核验，不能只让同一实现自证 |

## 为什么只主推这一套

本轮核读5套固定版本，只主选做真实模型运行；没有做五套横向性能测评，也不能推出最高获奖率。

| 项目 | 取舍 |
| --- | --- |
| [MathModelAgent](https://github.com/jihe520/MathModelAgent) | 主选：入口串起全流程；Typst依赖较轻，保留实际验收 |
| [Math-model-skills](https://github.com/WuXinbo-bo/Math-model-skills) | 备选：MIT，机器门禁较完整；TeX依赖更重，有阶段检查点 |
| [mathmodel-skill](https://github.com/handsomeZR-netizen/mathmodel-skill) | 偏问答与逐步确认，Friendly Mode与本轮自动持续目标不完全一致 |
| [MathModeling-skills](https://github.com/zhnnky329/MathModeling-skills) | 当前主线含人工Gate，不能拿旧全自动分支冒充主线 |
| [math-modeling-skills](https://github.com/xuec699-sudo/math-modeling-skills) | 本轮核读的auto有占位返回成功及失败后继续，不选 |

[选型数据与固定commit](../data/math-tools.json)。内部评分、论文页数或完成状态均不是正式竞赛成绩。
