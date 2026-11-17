# 一起补齐竞赛信息差

最有价值的贡献是具体赛项的真实经历和新规则，不必只分享获奖。

[提交参赛复盘](https://github.com/Rain-dust/HowToCompeteBetter/issues/new?template=experience.yml) · [纠错/补规则](https://github.com/Rain-dust/HowToCompeteBetter/issues/new?template=correction.yml)

请写届次、赛项、学历组、工具/技能、人工投入、结果和失败点。奖级按证书原名写；历史省奖不自动覆盖新的赛道或工具权限。公开证据可选，遮掉证书编号等个人信息，不上传凭据。

排名是制作适配顺序，规则与证据单独记录。新增条目先提供官方入口和同赛项反馈，再说明值得放在哪一行；不按点赞、星数或“保奖”宣传计算获奖率。

## 改哪份文件

赛事事实与前五安装/启动任务只改 `data/competitions.json`。其中 `ranking_view`、`top5_view` 保留兼容字段，`rank` 是连续参考序号；`decision_label/note` 是单独的当届建议。未知费用、资格或工具许可保持待核。

不要直接修改生成的赛事卡、总索引、首页、兼容JSON或离线筛选页。它们由同一事实源生成，避免出现新教程和旧指令两套答案。

## 维护章节和目录

`book/` 是面向读者的编号章节，每章都有结论、章内目录和前后章导航。章节顺序、问题与小节配置在 `data/chapters.json`，正文由 `scripts/build_book.py` 读取已有教程和赛事数据生成。修改教程内容时，改对应的 `docs/` 源文；修改前五工具和开打任务时，仍改 `data/competitions.json`。不要直接改生成的 `book/*.md`。

README 的问题导航和章节目录也读取同一份章节配置。术语表由 `scripts/build_book.py` 中的术语定义生成。每次更新后执行以下命令，保证首页、章节、赛事卡和下载资料相互指向正确：

~~~text
python scripts/build_all.py --skip-pdf
python scripts/check_reader.py
~~~

构建PDF另需ReportLab、pypdf以及Windows中文字体（当前生成器使用Deng与黑体）；完整发布运行：

~~~text
python scripts/build_all.py
python scripts/check_reader.py --pdf
~~~

发布前把PDF和SVG渲染成图片检查；程序边界检查不能代替实际视觉检查。若只改资料展示，不必重跑未改变的整套数模计算；历史题结果或求解代码改变时，要重新计算与独立核验，不能只改论文数字。
