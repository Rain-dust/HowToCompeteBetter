# 前端修复与验收记录

更新于2026-11-18。

## 实际改动

恢复完整的全站样式后，在 site/style.css 末尾追加10行规则。首页开打指令区的顶部留白调整为65px，复制按钮距上、右边缘均为12px。

本轮实际代码差异集中在复制按钮与指令之间的留白。页面结构、工具指令和交互逻辑沿用已有实现。

## 独立验收

- 在320、390、561、768、1024、1280、1440px宽度运行浏览器检查，917项断言全部通过。
- 前五项复制按钮在默认、复制成功和复制权限被拒后的手动选择状态均通过文字遮挡检查。
- 20项功能流程通过，覆盖排名、工具链接、指令复制、章节、搜索、筛选、返回、分享链接与PDF下载。
- 网站构建、生成一致性、站内链接、章节目录及PDF导航检查通过。
- 已实际查看桌面首屏、手机首屏和手机开打卡截图，排版已恢复。

实际执行的主要命令如下。

~~~text
node scripts/build_site.mjs
node scripts/check_site.mjs
python scripts/check_reader.py --pdf
node research/accept-dsh-interactions.mjs
node research/test_site_v11.mjs
~~~

浏览器验收脚本与截图保存在本机研究目录。

## 发布记录

2026-11-18已部署到 https://rain-dust.github.io/HowToCompeteBetter/ 。GitHub Pages部署提交为 cf6d7a54454ac085308aa8d8f0a0f1a02cdd9d7e。

正式网站21项浏览器流程通过，其中包含七种屏幕宽度下的前五指令遮挡检查。真实剪贴板、排名、站内阅读、搜索、筛选与PDF下载均通过，控制台错误和请求失败均为0。
