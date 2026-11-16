# DrawIO 图示生成报告

前序依据：ANALYSIS_MODELING_REPORT.md、RESULTS_REPORT.md与7张数据图已具备。本阶段未重算或改变模型结果。

## 图示清单

|文件|类型|依据|用途|状态|
|---|---|---|---|---|
|fig_roadmap.drawio / .pdf|四问技术路线|四问递进及统一验证|总体分析节|源文件及矢量PDF已生成|
|fig_assembly_tree.drawio / .pdf|装配树|原题第2页图1|第三问结构与递归说明|源文件及矢量PDF已生成|

## 未生成图示及原因

抽样停止边界已有数据图；第二问只需四位策略表；第四问沿用同一装配树。不重复绘制每问形式相同的流程图，不把统计图重画为DrawIO。

## Windows适配与导出

环境探测显示没有drawio/draw.io CLI。不安装新程序。在当前工作区新增tools/drawio_adapter.py，生成标准mxfile XML后再读取同一XML的文字、坐标和边连接，通过matplotlib导出PDF。支持本项目用到的圆角矩形、纯文本和直线有向边，属于受限子集适配器，并非官方DrawIO渲染器；任意复杂DrawIO样式不在其支持范围。源文件可用diagrams.net继续编辑，外部编辑后若使用新样式须另行官方导出。

命令：`python.exe tools/drawio_adapter.py`（cmd.exe）。源文件非空且XML可回读。两图节点坐标分离，连线按组连接；已在最终17页论文第4、10页实际打开查看，文字、箭头、图注无重叠或裁切，视觉检查PASS。证据绑定VISUAL_REVIEW.json中的最终PDF及页图hash。

## 论文插入规划

fig_roadmap.pdf放总体分析；fig_assembly_tree.pdf放第三问。7张数据图分别放第一问(2)、第二问(1)、第三问(1)、第四问(2)和灵敏度(1)，所有路径由对应章节直接引用。
