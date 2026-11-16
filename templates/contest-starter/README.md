# 复制这个目录，开始一个比赛项目

把本目录复制到独立工作区，不要在指南仓库里放真实参赛数据或个人信息。无需安装新skill；这是给现有coding agent读取的文件模板。

建议目录：

~~~text
inputs/           当届规则、评分表、本校认定、题面与需求
data/raw/        获准使用的原始数据
data/processed/  脚本生成的清洗数据
code/            可复跑实现
results/         真实结果
docs/            决策、说明、证据与答辩
run-logs/        本次运行与失败记录
~~~

1. 先填 [PROJECT_BRIEF.md](PROJECT_BRIEF.md)，未知就写待核。
2. 数据填 [data-provenance.csv](data-provenance.csv)，评分与实际证据填 [score-evidence.csv](score-evidence.csv)。空表不是已完成的检查。
3. 把 [START_PROMPT.txt](START_PROMPT.txt) 发给Codex/Claude Code。先跑最小闭环，之后再补模型、功能与展示。

这是非数模通用模板，不替代专用软件、比赛资格或工具许可。数模从[完整技能链教程](../../docs/coding-agent.md)开始。
