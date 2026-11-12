# 高性价比大学生竞赛指南

HowToCompeteBetter

按 agent 工作流适配度，从夯到拉选比赛。先选赛，再拿现成工具开打。

[下载完整版 PDF](guide.pdf) · [前五名 GitHub 与复制指令](docs/top5-start.md) · [完整赛事资料](docs/competition-catalog.md) · [来源索引](docs/sources.md)

## 前五名

| 排名 | 比赛 | 优先方向 | 工具 |
| --- | --- | --- | --- |
| 1 | 全国大学生数学建模竞赛 | 高教社杯 CUMCM | mathmodel-skill / MathModelAgent |
| 2 | 全国大学生数字媒体科技作品及创意竞赛 | Web、游戏、可视化 | frontend-design + webapp-testing + Remotion |
| 3 | 中国大学生服务外包创新创业大赛 | OPC 创客类 | Codex + 开发/测试技能 + SlideMuse |
| 4 | 未来设计师·全国高校数字艺术设计大赛 | NCDA 创意编程 / AIGC | algorithmic-art + 界面/测试 + Remotion |
| 5 | 全国大学生软件创新大赛 | 当届指定的软件题 | Codex + 界面/测试 + SlideMuse |

**直接使用：[前五名安装和开打指令](docs/top5-start.md)。** PDF 第 4-8 页也各有一张专属指令卡。

数模有完整专用工作流；软件和数媒采用现成工具组合。NCDA 创意编程与 AIGC 的规则分开核，软件创新的外部 AI 开发权限按具体题确认。

## 这份资料有什么

- 43 页 PDF，结论和排名在前，来源在后。
- 67 条选赛资料，含分支、平台及同一赛事的省级入口，并非 67 项独立竞赛。
- 11 组工具：数模专用、软件与视觉组合、双创材料、答辩和数据 agent。
- 安装与开打提示词，均可复制给 Codex。
- JSON 资料，便于筛选和后续维护。

## 怎么看夯到拉

按已有工具、低硬件交付成本、能力复用和奖项路径排序。它衡量本次“主要用 agent 做作品”的适配度，不代表赛事含金量或获奖概率。

国赛 2026 允许 agent 辅助，要求核心建模与分析由参赛队主导和核验；4C 计算机设计有 AI 工具名单；统计建模和能源经济对直接生成核心内容另有限制。细则见 PDF 与各条来源。

全国性赛事、国家级/省级证书、校内 A/B/C 是三个口径。本项目不编造教育部全国统一 ABC 分类；加分前查本校当届认定。

## 文件导航

| 文件 | 内容 |
| --- | --- |
| [guide.pdf](guide.pdf) | 最新完整指南 |
| [docs/top5-start.md](docs/top5-start.md) | 前五名 GitHub、安装与开打指令 |
| [docs/competition-catalog.md](docs/competition-catalog.md) | 67 条完整资料与来源 |
| [docs/sources.md](docs/sources.md) | 原始来源索引 |
| [data/](data/) | 比赛、工具、前五名指令与来源 JSON |

## 日期与证据

修订：2026-11-12。赛事规则检索截至 2026-11-10，前五工具链接和安装文档于 2026-11-12 复核。当届主办方新通知优先。

MM-Agent 的 NeurIPS 2025 论文报告辅助两支队伍获 2025 美赛 Finalist；原系统和后来发布的 Codex 技能包分别说明。当前资料核对了公开说明、关键技能文件和配套资源，没有把静态核查写成端到端实测。

结构灵感来自 [eternity4719/HowToLiveBetter](https://github.com/eternity4719/HowToLiveBetter)。本项目赛事分析重新研究撰写，第三方工具只链接原仓库，其许可按各仓库处理。
