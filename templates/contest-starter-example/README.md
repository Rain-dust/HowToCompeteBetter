# 3分钟小练习：合成工单数据变成一份结果

**这是自拟教学练习，不是历届赛题、真实校园调研或获奖作品。** 所有工单均为作者编写的合成记录，不包含学生、学校或个人信息。

你只需要已安装的Python 3.12或更新版本，不用模型、账号、密钥、网络和第三方库。`3分钟`是建议上手预算，不是完整竞赛耗时。

## 第一步，只运行这一条

在本目录打开终端：

~~~text
python run.py
~~~

如果仍在仓库根目录，也可运行：

~~~text
python templates/contest-starter-example/run.py
~~~

**你会得到：**

- [report.md](results/report.md)：中文结果和限制。
- [chart.svg](results/chart.svg)：浏览器可打开的平均响应时长图，带合成数据标识。
- [summary.json](results/summary.json)、[summary.csv](results/summary.csv)：程序真实生成的汇总。
- [rejected.csv](results/rejected.csv)：未通过检查的原始行及原因。
- [checks.json](results/checks.json)：验收结果。

## 跑完核这三行

| 要核对什么 | 固定练习输入的正确结果 |
| --- | --- |
| 输入 / 有效 / 剔除记录数 | 15 / 10 / 5 |
| 有效记录总响应时长 | 450分钟 |
| 图书馆 / 宿舍 / 教学楼平均响应 | 30 / 60 / 40分钟 |

这里的“响应时长”只是样例字段。样本不是随机调查，不能由此推断真实校园服务情况，也不能把结果写进正式竞赛当实测。

想看空模板应该怎么填：打开[已填项目卡](PROJECT_BRIEF.md)、[已填来源台账](data-provenance.csv)和[已填评分-证据表](score-evidence.csv)。表里的验收来自本练习任务，不冒充真实比赛评分。

## 下一步，把一件事情交给Agent

在这个练习目录打开你已有的coding agent，发送：

~~~text
请读取 PROJECT_BRIEF.md、inputs/task.md、data/raw/tickets.csv和run.py。
先运行现有流程，核对15条输入、10条有效、5条剔除和450分钟总量。
保留原始数据，增加一个“各类别记录数”的图，沿用合成数据水印；已有图和报告由同一结果生成。
检查新增图中的每个数字能追到summary.json，再交付真实输出和一个限制。
这只是练习，不编造学校、用户、调研、奖项或正式参赛许可。
~~~

这个任务的完成标志是：**多一张可打开的图，数字与现有结果一致，重新运行仍能生成它。** 不要求先做整套PPT、商业计划书或复杂模型。

熟悉以后，再复制[空白工作区](../contest-starter/README.md)，替换成你自己的获准输入。[完整交付打法](../../docs/project-delivery.md)
