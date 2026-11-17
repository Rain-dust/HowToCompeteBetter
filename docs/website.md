# 在线阅读站维护

[打开网站](https://rain-dust.github.io/HowToCompeteBetter/) · [回项目首页](../README.md)

网站将章节目录、全文搜索、比赛筛选、站内详情和PDF入口放在同一个阅读界面。内容来自本仓库；网站不另维护比赛排名、工具指令或获奖结论。

首页先显示比赛排名：前五项能直接查看Agent、GitHub和完整开打指令，第6–27项继续连续排列。章节目录和问题导航位于后面的阅读资料区。前五的指令与当届建议仍读取 `data/competitions.json`，不在网页代码中另写一套。

## 改哪里

| 要改的内容 | 修改入口 |
| --- | --- |
| 赛事事实、连续排名、前五工具与任务 | `data/competitions.json` |
| 章节顺序、问题和小节 | `data/chapters.json` |
| 教程与来源解释 | 对应的 `docs/` 源文 |
| 网站页面、样式和交互 | `site/` |
| 网站内容生成与链接转换 | `scripts/build_site.mjs` |

先更新源文，再重新生成章节和网站。`book/`与`_site/`都是生成视图，不直接手改。网站保留规则原核查日期，页面更新日期不代表全部当届资料已重查。

## 本地构建与预览

需要Python 3和Node.js。Markdown解析器已随仓库附带，并保留MIT许可，不用额外安装npm依赖。

在仓库根目录运行：

~~~text
python scripts/build_all.py --skip-pdf
python scripts/check_reader.py
node scripts/build_site.mjs
python -m http.server 8000 --directory _site
~~~

然后打开 `http://localhost:8000/`。通过HTTP预览，不要直接双击HTML：网站需要读取同目录的内容文件。

正文只改展示结构时，可沿用已验收的PDF；如果PDF内容改变，按贡献说明重新构建并逐页核查，再生成网站，确保网站下载的版本一致。

## 发布到GitHub Pages

网站地址固定为：

[https://rain-dust.github.io/HowToCompeteBetter/](https://rain-dust.github.io/HowToCompeteBetter/)

发布源为`gh-pages`分支的根目录；源文、生成器与网站代码继续维护在`main`。第一次配置时，在GitHub仓库的 **Settings → Pages → Deploy from a branch** 选择 `gh-pages` 和 `/ (root)`。本项目已按这个方式部署。

在仓库根目录执行：

~~~text
python scripts/deploy_site.py
~~~

脚本先构建并检查网站，再使用本机已有Git登录把网站产物普通推送到`gh-pages`，保留发布历史，不使用强制推送。不会替你登录GitHub。若Node.js或Git不在PATH，可通过 `--node`、`--git` 指定可执行文件路径。已手动构建时可用 `--skip-build`，跳过构建后仍执行检查。

发布范围仅为网站产物。请勿将研究原始材料、账户凭据、环境文件或整个工作目录复制到发布分支。

每次修改源文后，先更新章节和读者视图，再重新运行发布脚本：

~~~text
python scripts/build_all.py --skip-pdf
python scripts/check_reader.py
python scripts/deploy_site.py
~~~

目前没有自动部署CI，不能只修改`main`上的源文就认为线上已更新。部署完成后，实际打开线上地址核对版本，并验证下载的PDF与本地待发布文件一致。

## 发布前看这几件事

1. 十章目录、章内锚点和前后章跳转是否正常。
2. 全文搜索能否找到章节与赛事，空结果是否能清除条件。
3. 主榜是否仍连续1–27；全部入口是否为73条，组合筛选是否准确。
4. 安装和开打指令能否复制，复制内容是否完整。
5. 手机目录能否收起，正文是否可读，代码和表格是否只在自身区域横向滚动。
6. PDF预览和下载是否有效，原项目致谢是否保留。

首页另核对：

- 打开390px宽的手机首页，首屏是否已经出现具体比赛排名，而不是只有介绍和导航。
- 前五项的Agent与GitHub链接是否直接可见，全部链接是否与 `top5_view.github` 一致；开打文本是否完整显示，无需打开章节或展开安装说明。
- 分别复制五项开打指令，是否与 `top5_view.start` 完全一致（系统换行差异除外），当届建议是否仍在对应比赛旁。
- 前五与后续列表合在一起是否连续1–27，无重复或缺号；手机单列卡片、按钮和指令是否可读且不让整个页面横向溢出。

网站沿用[高性价比人生指南](https://github.com/eternity4719/HowToLiveBetter)的书式阅读思路；布局、交互和竞赛资料由本项目独立实现。
