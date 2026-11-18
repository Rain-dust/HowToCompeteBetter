/* Browser interactions for the generated, self-hosted competition guide. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const REPO = 'https://github.com/Rain-dust/HowToCompeteBetter';
  const state = {data: null, searchTimer: null, contestTimer: null, lastRoute: null, returnRoute: null, homeReady: false, menuReturn: null};
  const views = ['home', 'chapter', 'contests', 'search'];
  const wideReading = window.matchMedia('(min-width: 1000px)');
  const tutorials = {
    N22: [['Modex 官方教程', '03'], ['Codex 实跑教程', '04']],
    N38: [['计设作品教程', '06', 's02']],
    N18: [['RST 仿真教程', '07', 's02']],
    N23: [['统计建模实践与规则', '08', 'statistics']],
    N02: [['软件杯作品教程', '06', 's03']]
  };
  const educationLabels = {undergraduate: '本科', vocational: '高职高专', graduate: '研究生', unknown: '资格待核'};
  const equipmentLabels = {software: '软件方向', hardware: '硬件方向', mixed: '软件与硬件', unknown: '设备待核'};
  const decisionLabels = {conditional: '有条件推进', rule_check: '先核赛项与工具', existing_project: '已有真实项目再考虑', auxiliary: '仅作获准辅助', restricted: '核心生成受限', allowlist: '工具名单待核', platform: '平台与现场要求'};

  function el(tag, cls, text) {
    const node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function anchor(text, href, cls) {
    const node = el('a', cls, text);
    node.href = href;
    return node;
  }

  function normalized(text) {
    return String(text || '').normalize('NFKC').toLowerCase();
  }

  function tokens(text) {
    return normalized(text).trim().split(/\s+/u).filter(Boolean);
  }

  function matches(text, terms) {
    const haystack = normalized(text);
    return terms.every(term => haystack.includes(term));
  }

  function route() {
    const hash = location.hash.slice(1) || '/home';
    const split = hash.indexOf('?');
    const pathname = split < 0 ? hash : hash.slice(0, split);
    const params = new URLSearchParams(split < 0 ? '' : hash.slice(split + 1));
    let parts;
    try {
      parts = pathname.split('/').filter(Boolean).map(decodeURIComponent);
    } catch {
      parts = ['missing'];
    }
    return {kind: parts[0] || 'home', parts, params};
  }

  function navigate(hash, replace = false) {
    if (replace) {
      history.replaceState(null, '', hash);
      render();
    } else if (location.hash === hash) {
      render();
    } else {
      location.hash = hash;
    }
  }

  function chapterRoute(id, section) {
    return '#/chapter/' + id + (section ? '/' + encodeURIComponent(section) : '');
  }

  function closeMenu(restoreFocus = false) {
    if (!document.body.classList.contains('menu-open')) return;
    const toggle = $('mobile-menu-toggle');
    const sidebar = $('sidebar');
    sidebar.classList.remove('is-open');
    sidebar.inert = true;
    $('main-content').inert = false;
    document.querySelector('.site-header').inert = false;
    if ($('sidebar-backdrop')) $('sidebar-backdrop').hidden = true;
    document.body.classList.remove('menu-open');
    if (toggle) {
      toggle.setAttribute('aria-expanded', 'false');
      toggle.setAttribute('aria-label', '打开章节目录');
    }
    if (restoreFocus && state.menuReturn) state.menuReturn.focus();
  }

  function openMenu() {
    state.menuReturn = document.activeElement;
    $('sidebar').classList.add('is-open');
    $('sidebar').inert = false;
    $('main-content').inert = true;
    document.querySelector('.site-header').inert = true;
    if ($('sidebar-backdrop')) $('sidebar-backdrop').hidden = false;
    document.body.classList.add('menu-open');
    $('mobile-menu-toggle')?.setAttribute('aria-expanded', 'true');
    $('mobile-menu-toggle')?.setAttribute('aria-label', '关闭章节目录');
    $('mobile-menu-close').focus();
  }

  function showView(kind) {
    views.forEach(name => {
      if ($('view-' + name)) $('view-' + name).hidden = name !== kind;
    });
  }

  function renderSidebar(activeId) {
    const container = $('chapter-nav');
    if (!container) return;
    const list = el('ol', 'chapter-list');
    state.data.chapters.forEach(chapter => {
      const item = el('li');
      const link = anchor('', chapterRoute(chapter.id), 'chapter-link');
      link.append(el('span', 'chapter-num', String(chapter.id).padStart(2, '0')), el('span', 'chapter-link-title', chapter.title));
      link.dataset.chapterId = chapter.id;
      if (chapter.id === activeId) {
        link.classList.add('is-active');
        link.setAttribute('aria-current', 'page');
      }
      item.append(link);
      if (chapter.id === activeId) {
        const sections = el('ol', 'section-list');
        (chapter.sections || []).forEach(section => {
          const li = el('li');
          li.append(anchor(section.title, chapterRoute(chapter.id, section.id), 'section-link'));
          sections.append(li);
        });
        item.append(sections);
      }
      list.append(item);
    });
    container.replaceChildren(list);
  }

  function copyButton(text, target, label = '复制', cls = '') {
    const button = el('button', 'copy-button' + (cls ? ' ' + cls : ''), label);
    button.type = 'button';

    let timer = null;
    button.addEventListener('click', async () => {
      clearTimeout(timer);
      try {
        if (!navigator.clipboard?.writeText) throw new Error('Clipboard unavailable');
        await navigator.clipboard.writeText(text);
        button.textContent = '已复制';
        button.dataset.copyStatus = 'success';
        $('copy-feedback').textContent = '已复制到剪贴板';
      } catch {
        const selection = window.getSelection();
        const range = document.createRange();
        range.selectNodeContents(target);
        selection.removeAllRanges();
        selection.addRange(range);
        button.textContent = '已选中，请手动复制';
        button.dataset.copyStatus = 'manual';
        $('copy-feedback').textContent = '文字已选中，请手动复制';
      }
      timer = window.setTimeout(() => {
        if (button.isConnected) {
          button.textContent = label;
          delete button.dataset.copyStatus;
        }
      }, 2800);
    });
    return button;
  }

  function commandBlock(text, label, cls = '', headerTitle = 'AGENT PROMPT') {
    const wrapper = el('div', 'code-block' + (cls ? ' ' + cls : ''));
    const pre = el('pre');
    const code = el('code', 'language-text', text);
    pre.append(code);
    const bar = el('div', 'code-toolbar');
    const caption = el('span', 'code-caption', headerTitle);
    const btn = copyButton(text, code, label, cls ? 'launch-copy' : '');
    bar.append(caption, btn);
    wrapper.append(bar, pre);
    return wrapper;
  }

  function homeTool(contest) {
    return contest.homepage_tool_label || contest.tool_name;
  }

  function applyDecisionAttr(node, code) {
    if (code) node.dataset.decision = code;
    return node;
  }


  let rankUpdateFrame = 0;
  function scheduleRankUpdate() {
    if (rankUpdateFrame || !state.homeReady || $('view-home').hidden) return;
    rankUpdateFrame = requestAnimationFrame(() => {
      rankUpdateFrame = 0;
      if ($('view-home').hidden) return;
      const readingLine = document.querySelector('.site-header').getBoundingClientRect().bottom + 48;
      const cards = $('home-top5').children;
      let rank = 1;
      for (const card of cards) {
        if (card.getBoundingClientRect().top > readingLine) break;
        rank = Number(card.dataset.rank);
      }
      for (const item of $('home-rank-overview').children) {
        const link = item.firstElementChild;
        if (Number(item.dataset.rank) === rank) link.setAttribute('aria-current', 'location');
        else link.removeAttribute('aria-current');
      }
    });
  }

  function scrollHomeSection(section) {
    if (!section) return;
    requestAnimationFrame(() => requestAnimationFrame(() => {
      const target = $(section);
      if (!target || !$('view-home').contains(target)) return;
      if (target.tagName === 'DETAILS') target.open = true;
      const header = document.querySelector('.site-header')?.getBoundingClientRect().height || 0;
      window.scrollTo({top: Math.max(0, target.getBoundingClientRect().top + window.scrollY - header - 16), behavior: 'instant'});
      const heading = target.querySelector('h2,h3,summary') || target;
      heading.tabIndex = -1;
      heading.focus({preventScroll: true});
    }));
  }

  function renderHome(section) {
    showView('home');
    renderSidebar(null);
    document.title = '比赛排名与开打指令 · 高性价比大学生竞赛指南';
    if (state.homeReady) {
      scheduleRankUpdate();
      scrollHomeSection(section);
      return;
    }
    const ranked = state.data.contests.filter(contest => Number.isInteger(contest.rank)).sort((a, b) => a.rank - b.rank);

    const overview = $('home-rank-overview');
    if (overview) {
      overview.replaceChildren(...ranked.slice(0, 5).map(contest => {
        const item = el('li', 'home-rank-item');
        item.dataset.rank = contest.rank;
        const link = anchor('', '#/home/top5-' + contest.rank, 'home-rank-link');
        const main = el('span', 'rank-main');
        main.append(el('strong', 'rank-name', contest.name), el('span', 'rank-tool', homeTool(contest)));
        const badge = applyDecisionAttr(el('span', 'rank-status', contest.decision_label), contest.decision_code);
        link.append(el('span', 'rank-number', String(contest.rank)), main, badge);
        item.append(link);
        return item;
      }));
    }

    const launches = $('home-top5');
    if (launches) {
      launches.replaceChildren(...ranked.slice(0, 5).map(contest => {
        const view = contest.top5_view || {};
        const card = el('article', 'launch-card');
        card.id = 'top5-' + contest.rank;
        card.dataset.id = contest.id;
        card.dataset.rank = contest.rank;

        const head = el('div', 'launch-card-head');
        const rankChip = el('span', 'launch-rank', String(contest.rank));
        const titleWrap = el('div', 'launch-title-wrap');
        const title = el('h3', 'launch-title');
        const aliasStart = contest.name.lastIndexOf('（');
        if (aliasStart > 0 && contest.name.endsWith('）')) {
          title.append(contest.name.slice(0, aliasStart), el('span', 'launch-alias', contest.name.slice(aliasStart)));
        } else {
          title.textContent = contest.name;
        }
        const decisionPill = applyDecisionAttr(el('span', 'launch-decision-pill', contest.decision_label), contest.decision_code);
        titleWrap.append(title, decisionPill);
        head.append(rankChip, titleWrap);

        const specs = el('div', 'launch-specs');
        const specTool = el('div', 'launch-spec launch-agent');
        specTool.append(el('span', 'spec-label', 'Agent / Skill'), el('strong', 'spec-value', homeTool(contest)));
        const specRoute = el('div', 'launch-spec launch-route');
        specRoute.append(el('p', 'spec-value', view.route || contest.summary));
        specs.append(specTool, specRoute);

        const repositories = el('div', 'launch-repos');
        repositories.setAttribute('aria-label', contest.name + '的工具 GitHub 链接');
        repositories.append(el('span', 'launch-repos-label', 'GitHub 仓库'));
        const repoList = el('div', 'launch-repos-chips');
        (view.github || []).forEach(([label, url]) => {
          const link = anchor(label + ' ↗', url, 'repo-chip');
          link.target = '_blank';
          link.rel = 'noopener noreferrer';
          repoList.append(link);
        });
        repositories.append(repoList);

        const boundaryBox = el('div', 'launch-boundary');
        const boundaryTitle = el('strong', 'launch-decision', '当届规则');
        const boundaryNote = el('span', 'launch-note', contest.decision_note);
        boundaryBox.append(boundaryTitle, boundaryNote);

        const promptCaption = contest.rank === 1
          ? '开打指令 · Codex / Claude'
          : '开打指令';
        const instruction = commandBlock(view.start || contest.getting_started || '', '复制开打指令', 'launch-command', promptCaption);

        const installation = el('details', 'launch-install');
        installation.append(
          el('summary', '', '安装 Skill 与运行环境'),
          commandBlock(view.install || '先读取完整赛事卡，确认具体平台与依赖。', '复制安装任务', 'launch-install-command', '环境与 Skill 安装任务')
        );

        const foot = el('div', 'launch-card-foot');
        const deliver = el('p', 'launch-deliver');
        deliver.append(el('strong', '', '目标交付物：'), document.createTextNode(view.deliver || contest.deliver));
        const links = el('div', 'launch-links');
        for (const [label, chapter, section] of tutorials[contest.id] || []) {
          links.append(anchor(label + ' →', chapterRoute(chapter, section), 'launch-action-primary'));
        }
        const evidenceLink = anchor('赛事详情与实测依据 ↗', '#/contest/' + contest.id, 'launch-action-secondary');
        foot.append(deliver, evidenceLink, anchor('返回前五名 ↑', '#/home/home-rank-overview', 'return-to-index'));

        const setup = el('div', 'launch-setup');
        setup.append(specs, repositories, boundaryBox);
        const start = el('div', 'launch-start');
        start.append(instruction, links, installation);
        card.append(head, setup, start, foot);
        return card;
      }));
    }

    const remaining = $('home-rest-ranking');
    if (remaining) {
      remaining.replaceChildren(...ranked.slice(5).map(contest => {
        const item = el('li', 'ranking-item');
        item.dataset.rank = contest.rank;
        item.dataset.id = contest.id;
        const title = anchor(contest.name, '#/contest/' + contest.id, 'ranking-name');
        const main = el('div', 'ranking-main');
        main.append(title, el('p', 'ranking-tool', contest.tool_name));
        const status = applyDecisionAttr(el('span', 'ranking-status', contest.decision_label), contest.decision_code);
        item.append(el('span', 'ranking-number', String(contest.rank)), main, status);
        return item;
      }));
    }

    const grid = $('chapter-grid');
    if (grid) {
      grid.replaceChildren(...state.data.chapters.map(chapter => {
        const card = el('article', 'chapter-card');
        card.append(
          el('span', 'chapter-number', '第 ' + Number(chapter.id) + ' 章'),
          anchor(chapter.title, chapterRoute(chapter.id), 'chapter-card-title'),
          el('p', 'chapter-summary', chapter.summary)
        );
        return card;
      }));
    }

    const questions = $('question-list');
    if (questions) {
      questions.replaceChildren(...state.data.chapters.map(chapter => {
        const item = el('li', 'question-item');
        item.append(
          anchor(chapter.question, chapterRoute(chapter.id)),
          el('span', 'question-chapter', '第 ' + Number(chapter.id) + ' 章 · ' + chapter.title)
        );
        return item;
      }));
    }
    state.homeReady = true;
    scheduleRankUpdate();
    scrollHomeSection(section);
  }

  function decorateArticle(container) {
    container.querySelectorAll('pre').forEach(pre => {
      if (pre.parentElement.classList.contains('code-block')) return;
      const code = pre.querySelector('code');
      const text = (code || pre).textContent;
      const langClass = [...(code?.classList || [])].find(c => c.startsWith('language-'));
      const lang = langClass ? langClass.replace('language-', '').toUpperCase() : '代码';
      const wrapper = el('div', 'code-block article-code-block');
      const bar = el('div', 'code-toolbar');
      bar.append(el('span', 'code-caption', lang === 'TEXT' || lang === 'PLAINTEXT' ? '命令 / 指令' : lang), copyButton(text, code || pre, '复制'));
      pre.before(wrapper);
      wrapper.append(bar, pre);
    });
    container.querySelectorAll('a[href^="https://"],a[href^="http://"]').forEach(link => {
      link.rel = 'noopener noreferrer';
      link.target = '_blank';
    });
    container.querySelectorAll('table').forEach(table => {
      if (!table.parentElement.classList.contains('table-scroll')) {
        const wrapper = el('div', 'table-scroll');
        wrapper.tabIndex = 0;
        wrapper.setAttribute('role', 'region');
        wrapper.setAttribute('aria-label', '数据表，可横向滚动');
        table.before(wrapper);
        wrapper.append(table);
      }
    });
  }

  function getHeadingTarget(id, container) {
    if (!id) return null;
    const direct = document.getElementById(id);
    if (direct && container.contains(direct)) return direct;
    return [...container.querySelectorAll('h1,h2,h3,h4')].find(h =>
      normalized(h.textContent).replace(/[^\p{L}\p{N}\s_-]/gu, '').replace(/\s+/g, '-') === normalized(id)
    );
  }

  function scrollToSection(section) {
    if (!section) return;
    requestAnimationFrame(() => requestAnimationFrame(() => {
      const target = getHeadingTarget(section, $('chapter-content'));
      if (!target) return;
      let ancestor = target.parentElement;
      while (ancestor && ancestor !== $('chapter-content')) {
        if (ancestor.tagName === 'DETAILS') ancestor.open = true;
        ancestor = ancestor.parentElement;
      }
      const marker = target.matches('a[id]:empty') ? target.closest('p') || target : target;
      const headingSelector = 'h1,h2,h3,h4';
      const heading = marker.matches(headingSelector) ? marker : marker.nextElementSibling;
      const destination = heading?.matches(headingSelector) ? heading : target;
      destination.scrollIntoView({block: 'start'});
      destination.tabIndex = -1;
      destination.focus({preventScroll: true});
    }));
  }

  function setReadingPage(title, html, metadata) {
    showView('chapter');
    if ($('chapter-title')) $('chapter-title').textContent = title;
    if ($('chapter-meta')) $('chapter-meta').textContent = metadata || '';
    const back = $('reading-back');
    back.href = state.returnRoute?.hash || '#/';
    back.textContent = state.returnRoute?.label || '← 返回比赛排名';
    $('chapter-content').innerHTML = html;
    const firstTitle = $('chapter-content').querySelector('h1');
    if (firstTitle) {
      if (firstTitle.id) {
        const target = el('span');
        target.id = firstTitle.id;
        firstTitle.before(target);
      }
      firstTitle.remove();
    }
    decorateArticle($('chapter-content'));
    document.title = title + ' · 高性价比大学生竞赛指南';
  }

  function setToc(items, hrefFor, section) {
    const container = $('chapter-toc');
    if (!container) return;
    const list = el('ol', 'toc-list');
    items.forEach(item => {
      const li = el('li');
      const link = anchor(item.title, hrefFor(item), 'toc-link');
      if (item.id === section) link.setAttribute('aria-current', 'location');
      li.append(link);
      list.append(li);
    });
    const details = el('details', 'toc-panel');
    details.open = wideReading.matches;
    const nav = el('nav');
    nav.setAttribute('aria-label', '本页目录');
    nav.append(list);
    details.append(el('summary', 'toc-heading', '本页目录'), nav);
    container.replaceChildren(details);
    container.hidden = !items.length;
  }

  function articleHeadings() {
    return [...$('chapter-content').querySelectorAll('h2,h3')].filter(h => h.id).map(h => ({id: h.id, title: h.textContent}));
  }

  function readingNavigation(previous, next) {
    const navigation = $('chapter-navigation');
    if (navigation) navigation.hidden = !previous && !next;
    [['chapter-prev', previous], ['chapter-next', next]].forEach(([id, value]) => {
      const a = $(id);
      if (!a) return;
      a.hidden = !value;
      if (value) {
        a.href = value.href;
        a.textContent = value.text;
      }
    });
  }

  function chapterContents(chapter) {
    const article = $('chapter-content');
    const label = [...article.children].find(node => node.matches('p') && node.textContent.trim() === '本章目录');
    const list = label?.nextElementSibling;
    if (!list?.matches('ul')) return chapter.sections;
    const links = [...list.querySelectorAll('a')];
    const exact = links.length === chapter.sections.length && links.every((link, index) =>
      link.getAttribute('href') === chapterRoute(chapter.id, chapter.sections[index].id)
    );
    if (!exact) return chapter.sections;
    label.remove();
    list.remove();
    return chapter.sections.map((section, index) => ({...section, title: links[index].textContent}));
  }

  function renderChapter(id, section) {
    const chapter = state.data.chapters.find(chapter => chapter.id === id);
    if (!chapter) return renderMissing();
    const index = state.data.chapters.indexOf(chapter);
    setReadingPage(Number(id) + '. ' + chapter.title, chapter.html, '第 ' + Number(id) + ' 章 · 共 ' + chapter.sections.length + ' 节');
    renderSidebar(id);
    setToc(chapterContents(chapter), item => chapterRoute(id, item.id), section);
    const previous = state.data.chapters[index - 1];
    const next = state.data.chapters[index + 1];
    readingNavigation(
      previous ? {text: '← ' + Number(previous.id) + '. ' + previous.title, href: chapterRoute(previous.id)} : {text: '← 返回排名首页', href: '#/home'},
      next ? {text: Number(next.id) + '. ' + next.title + ' →', href: chapterRoute(next.id)} : {text: '按条件找比赛 →', href: '#/contests'}
    );
    scrollToSection(section);
  }

  function renderContest(id, section) {
    const contest = state.data.contests.find(contest => contest.id === id);
    if (!contest) return renderMissing();
    setReadingPage(
      contest.name,
      contest.html,
      (contest.rank ? '连续参考第 ' + contest.rank + ' 项' : '补充参考入口') + ' · 规则核查截至 ' + contest.rules_checked_through
    );
    renderSidebar(null);
    setToc(articleHeadings(), item => '#/contest/' + encodeURIComponent(id) + '/' + encodeURIComponent(item.id), section);
    readingNavigation({text: '← 返回比赛筛选', href: state.returnRoute?.kind === 'contests' ? state.returnRoute.hash : '#/contests'}, {text: '查看排名与奖项方法 →', href: chapterRoute('02', 'ranking')});
    scrollToSection(section);
  }

  function renderSupplement(path, section) {
    const document = state.data.supplements.find(item => item.path === path);
    if (!document) return renderMissing();
    setReadingPage(document.title, document.html, '专题资料 · 核查日期见文内记录');
    renderSidebar(null);
    setToc(articleHeadings(), item => '#/page/' + encodeURIComponent(path) + '?section=' + encodeURIComponent(item.id), section);
    readingNavigation({text: '← 返回排名首页', href: '#/home'}, {text: '找比赛 →', href: '#/contests'});
    scrollToSection(section);
  }

  function renderMissing() {
    setReadingPage('没有找到这一页', '', '');
    const p = el('p', '', '这个章节或资料地址可能已经更新，请从目录重新查找。');
    $('chapter-content').append(p, anchor('返回排名与全书首页', '#/home', 'button-link'));
    renderSidebar(null);
    setToc([], () => '');
    readingNavigation(null, null);
  }

  function setOptions(id, placeholder, labels, values) {
    const select = $(id);
    if (!select) return;
    const options = [new Option(placeholder, '')];
    Object.entries(labels).filter(([key]) => values.has(key)).forEach(([key, label]) => options.push(new Option(label, key)));
    select.replaceChildren(...options);
  }

  function initFilters() {
    setOptions('filter-education', '不限学历', educationLabels, new Set(state.data.contests.flatMap(c => c.reader_filters?.education || [])));
    setOptions('filter-equipment', '不限设备', equipmentLabels, new Set(state.data.contests.flatMap(c => c.reader_filters?.software_hardware || [])));
    setOptions('filter-decision', '全部当届建议', decisionLabels, new Set(state.data.contests.map(c => c.decision_code)));
  }

  function readFilterState(params) {
    const filters = {
      view: params.get('view') === 'all' ? 'all' : 'rank',
      q: params.get('q') || '',
      education: params.get('education') || '',
      equipment: params.get('equipment') || '',
      decision: params.get('decision') || ''
    };
    ['education', 'equipment', 'decision'].forEach(key => {
      if (![...$('filter-' + key).options].some(option => option.value === filters[key])) filters[key] = '';
    });
    return filters;
  }

  function filtersFromControls() {
    return {
      view: $('filter-view').value,
      q: $('contest-query').value,
      education: $('filter-education').value,
      equipment: $('filter-equipment').value,
      decision: $('filter-decision').value
    };
  }

  function filterHash(filters) {
    const params = new URLSearchParams();
    if (filters.view === 'all') params.set('view', 'all');
    ['q', 'education', 'equipment', 'decision'].forEach(key => {
      if (filters[key]) params.set(key, filters[key]);
    });
    return '#/contests' + (params.size ? '?' + params : '');
  }

  function updateFilters(replace) {
    const filters = filtersFromControls();
    navigate(filterHash(filters), replace);
  }

  function contestSearchText(contest) {
    return [
      contest.name,
      contest.short,
      contest.summary,
      contest.scope,
      contest.deliver,
      contest.tool_name,
      contest.decision_label,
      contest.id,
      ...(contest.aliases || []),
      ...(contest.keys || [])
    ].join(' ');
  }

  function renderContests(params) {
    showView('contests');
    renderSidebar(null);
    document.title = '找比赛 · 高性价比大学生竞赛指南';
    const filters = readFilterState(params);
    const terms = tokens(filters.q);
    ['view', 'education', 'equipment', 'decision'].forEach(key => {
      const input = $('filter-' + key);
      input.value = filters[key];
      if (!input.value && key === 'view') input.value = 'rank';
    });
    if ($('contest-query').value !== filters.q) $('contest-query').value = filters.q;

    const contests = state.data.contests.filter(contest => {
      if (filters.view === 'rank' && !Number.isInteger(contest.rank)) return false;
      if (filters.education && !(contest.reader_filters?.education || []).includes(filters.education)) return false;
      if (filters.equipment && !(contest.reader_filters?.software_hardware || []).includes(filters.equipment)) return false;
      if (filters.decision && contest.decision_code !== filters.decision) return false;
      return matches(contestSearchText(contest), terms);
    }).sort((a, b) => (a.rank || 999) - (b.rank || 999) || a.id.localeCompare(b.id));

    const full = filters.view === 'rank'
      ? state.data.contests.filter(c => Number.isInteger(c.rank)).length
      : state.data.contests.length;
    $('contest-count').textContent = '找到 ' + contests.length + ' / ' + full + ' 条参考';

    $('contest-results').replaceChildren(...contests.map(contest => {
      const card = el('article', 'contest-card');
      card.dataset.id = contest.id;
      if (contest.rank) card.dataset.rank = contest.rank;
      const top = el('div', 'contest-card-head');
      top.append(el('span', 'contest-rank', contest.rank ? String(contest.rank) : '参考'));
      const heading = el('h2');
      heading.append(anchor(contest.name, '#/contest/' + contest.id, 'card-link'));
      top.append(heading);
      card.append(top);
      card.append(el('p', 'contest-summary', contest.summary));
      const tagRow = el('div', 'contest-card-tags');
      tagRow.append(applyDecisionAttr(el('span', 'contest-decision', contest.decision_label), contest.decision_code));
      if (contest.tool_name) tagRow.append(el('span', 'contest-tool-tag', contest.tool_name));
      card.append(tagRow);
      const facets = [
        ...(contest.reader_filters?.education || []).map(key => educationLabels[key] || key),
        ...(contest.reader_filters?.software_hardware || []).map(key => equipmentLabels[key] || key)
      ];
      const foot = el('div', 'contest-card-foot');
      foot.append(el('p', 'contest-meta', facets.join(' · ')), anchor('看详情、工具与开打 →', '#/contest/' + contest.id, 'contest-detail-link'));
      card.append(foot);
      return card;
    }));

    $('contest-empty').hidden = contests.length > 0;
    if (!contests.length) {
      const reset = el('button', 'button-link', '清空筛选，重新选择');
      reset.type = 'button';
      reset.addEventListener('click', () => navigate('#/contests'));
      $('contest-empty').replaceChildren(
        el('h2', '', '没有找到匹配的比赛'),
        el('p', '', '试试简称、减少一个条件，或切换到全部参考入口。未标明的资格与设备不等于不适合。'),
        reset
      );
    }
  }

  function snippet(text, terms) {
    const cleaned = String(text || '').replace(/\s+/g, ' ').trim();
    let start = 0;
    const haystack = normalized(cleaned);
    const first = terms.map(term => haystack.indexOf(term)).filter(index => index >= 0).sort((a, b) => a - b)[0];
    if (first !== undefined) start = Math.max(0, first - 38);
    return (start ? '…' : '') + cleaned.slice(start, start + 165) + (cleaned.length > start + 165 ? '…' : '');
  }

  function highlighted(text, terms) {
    const fragment = document.createDocumentFragment();
    if (!terms.length) {
      fragment.append(document.createTextNode(text));
      return fragment;
    }
    const haystack = normalized(text);
    let cursor = 0;
    let loops = 0;
    while (cursor < text.length && loops++ < 80) {
      let position = Infinity;
      let word = '';
      terms.forEach(term => {
        const index = haystack.indexOf(term, cursor);
        if (index >= 0 && index < position) {
          position = index;
          word = term;
        }
      });
      if (!Number.isFinite(position)) {
        fragment.append(document.createTextNode(text.slice(cursor)));
        break;
      }
      fragment.append(document.createTextNode(text.slice(cursor, position)));
      fragment.append(el('mark', '', text.slice(position, position + word.length)));
      cursor = position + word.length;
    }
    return fragment;
  }

  function collectSearch(query) {
    const terms = tokens(query);
    if (!terms.length) return [];
    const results = [];
    state.data.chapters.forEach(chapter => {
      const sections = chapter.searchSections?.length ? chapter.searchSections : [{id: '', title: chapter.title, text: chapter.text}];
      sections.forEach(section => {
        const title = chapter.title + ' · ' + section.title;
        const text = section.text || '';
        if (matches(title + ' ' + text, terms)) {
          results.push({
            type: '第 ' + Number(chapter.id) + ' 章',
            title,
            text,
            href: chapterRoute(chapter.id, section.id),
            priority: matches(title, terms) ? 0 : 1
          });
        }
      });
    });
    state.data.contests.forEach(contest => {
      const text = contestSearchText(contest) + ' ' + (contest.text || contest.rule || '') + ' ' + (contest.evidence_note || '');
      if (matches(text, terms)) {
        results.push({
          type: '赛事卡' + (contest.rank ? ' · 第 ' + contest.rank + ' 项' : ''),
          title: contest.name,
          text,
          href: '#/contest/' + contest.id,
          priority: matches(contest.name + ' ' + (contest.aliases || []).join(' '), terms) ? 0 : 2
        });
      }
    });
    state.data.supplements.filter(item => item.searchable !== false).forEach(item => {
      if (matches(item.title + ' ' + item.text, terms)) {
        results.push({
          type: '专题资料',
          title: item.title,
          text: item.text,
          href: '#/page/' + encodeURIComponent(item.path),
          priority: matches(item.title, terms) ? 0 : 3
        });
      }
    });
    return results.sort((a, b) => a.priority - b.priority);
  }

  function renderSearch(query) {
    showView('search');
    renderSidebar(null);
    document.title = (query ? '搜索：' + query : '搜索全书') + ' · 高性价比大学生竞赛指南';
    if ($('search-input').value !== query) $('search-input').value = query;
    if ($('search-clear')) $('search-clear').hidden = !query;
    const results = collectSearch(query);
    const terms = tokens(query);
    $('search-count').textContent = terms.length ? '“' + query + '” · 找到 ' + results.length + ' 条结果' : '搜索章节、开打指令和全部赛事卡';
    if (!terms.length) {
      const suggestions = el('p', 'search-suggestions');
      ['数模', 'RST', '计设', '答辩', '数据'].forEach(word =>
        suggestions.append(anchor(word, '#/search?q=' + encodeURIComponent(word), 'search-suggestion'))
      );
      $('search-results').replaceChildren(
        el('p', 'search-guide-hint', '输入比赛名字、简称，或你现在遇到的问题。多个关键词用空格分开：'),
        suggestions
      );
      return;
    }
    if (!results.length) {
      $('search-results').replaceChildren(
        el('div', 'empty-state search-empty', ''),
      );
      $('search-results').firstChild.append(
        el('h2', '', '暂时没有匹配结果'),
        el('p', '', '试试比赛简称、减少关键词，或点击右上角清除重新搜索。')
      );
      return;
    }
    $('search-results').replaceChildren(...results.map(result => {
      const card = el('article', 'search-result');
      card.append(el('p', 'search-result-type', result.type));
      const heading = el('h2');
      const a = anchor('', result.href);
      a.append(highlighted(result.title, terms));
      heading.append(a);
      card.append(heading);
      const description = el('p', 'search-snippet');
      description.append(highlighted(snippet(result.text, terms), terms));
      card.append(description);
      return card;
    }));
  }

  function render() {
    if (!state.data) return;
    clearTimeout(state.searchTimer);
    clearTimeout(state.contestTimer);
    const current = {...route(), hash: location.hash || '#/home'};
    const previous = state.lastRoute;
    const reading = ['chapter', 'contest', 'page'].includes(current.kind);
    const samePage = previous?.parts.slice(0, 2).join('/') === current.parts.slice(0, 2).join('/');
    if (!reading) state.returnRoute = null;
    else if (!samePage) {
      const returnLabels = {home: '← 返回比赛排名', contests: '← 返回筛选结果', search: '← 返回搜索结果'};
      if (returnLabels[previous?.kind]) {
        state.returnRoute = {hash: previous.hash, label: returnLabels[previous.kind], kind: previous.kind};
      } else {
        state.returnRoute = current.kind === 'contest' ? {hash: '#/contests', label: '← 返回比赛列表', kind: 'contests'} : null;
      }
    }
    const typing = document.activeElement?.matches('input,textarea,select');
    const wasMenuOpen = document.body.classList.contains('menu-open');
    closeMenu(false);
    if (!typing) window.scrollTo({top: 0, behavior: 'instant'});
    const activeTab = current.kind === 'chapter' || (current.kind === 'home' && current.parts[1] === 'home-guide-details')
      ? 'guide'
      : ['contests', 'contest'].includes(current.kind) ? 'contests' : current.kind === 'home' ? 'read' : '';
    document.querySelectorAll('.nav-link').forEach(a => {
      const active = a.dataset.view === activeTab;
      a.classList.toggle('is-active', active);
      if (active) a.setAttribute('aria-current', 'page');
      else a.removeAttribute('aria-current');
    });
    if (current.kind !== 'search') {
      $('search-input').value = '';
      $('search-clear').hidden = true;
    }
    if (current.kind === 'home') renderHome(current.parts.slice(1).join('/'));
    else if (current.kind === 'chapter') renderChapter(current.parts[1], current.parts.slice(2).join('/'));
    else if (current.kind === 'contest') renderContest(current.parts[1], current.parts.slice(2).join('/'));
    else if (current.kind === 'page') renderSupplement(current.parts.slice(1).join('/'), current.params.get('section'));
    else if (current.kind === 'contests') renderContests(current.params);
    else if (current.kind === 'search') renderSearch(current.params.get('q') || '');
    else renderMissing();
    if (wasMenuOpen) {
      const heading = document.querySelector('.view:not([hidden]) h1');
      if (heading) {
        heading.tabIndex = -1;
        heading.focus({preventScroll: true});
      }
    }
    state.lastRoute = current;
  }

  function bind() {
    document.querySelector('.skip-link')?.addEventListener('click', event => {
      event.preventDefault();
      const main = $('main-content');
      if (main) {
        main.tabIndex = -1;
        main.focus({preventScroll: true});
        main.scrollIntoView({block: 'start'});
      }
    });
    $('contest-filters')?.addEventListener('submit', event => {
      event.preventDefault();
      clearTimeout(state.contestTimer);
      updateFilters(false);
    });
    $('mobile-menu-close')?.addEventListener('click', () => closeMenu(true));
    $('mobile-menu-toggle')?.addEventListener('click', () => {
      if ($('mobile-menu-toggle').getAttribute('aria-expanded') === 'true') closeMenu(true);
      else openMenu();
    });
    $('sidebar-backdrop')?.addEventListener('click', () => closeMenu(true));
    $('sidebar').addEventListener('click', event => {
      const link = event.target.closest('a[href^="#/"]');
      if (link?.hash === location.hash) closeMenu(true);
    });
    $('global-search-form')?.addEventListener('submit', event => {
      event.preventDefault();
      clearTimeout(state.searchTimer);
      navigate('#/search' + ($('search-input').value ? '?q=' + encodeURIComponent($('search-input').value) : ''));
    });
    $('search-input')?.addEventListener('input', event => {
      if (event.isComposing) return;
      if ($('search-clear')) $('search-clear').hidden = !$('search-input').value;
      clearTimeout(state.searchTimer);
      state.searchTimer = setTimeout(
        () => navigate('#/search' + ($('search-input').value ? '?q=' + encodeURIComponent($('search-input').value) : ''), route().kind === 'search'),
        230
      );
    });
    $('search-clear')?.addEventListener('click', () => {
      clearTimeout(state.searchTimer);
      $('search-input').value = '';
      navigate('#/search', true);
      $('search-input').focus();
    });
    ['view', 'education', 'equipment', 'decision'].forEach(key =>
      $('filter-' + key)?.addEventListener('change', () => updateFilters(false))
    );
    $('contest-query')?.addEventListener('input', event => {
      if (event.isComposing) return;
      clearTimeout(state.contestTimer);
      state.contestTimer = setTimeout(() => updateFilters(true), 180);
    });
    $('filters-reset')?.addEventListener('click', () => navigate('#/contests'));
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape' && document.body.classList.contains('menu-open')) {
        event.preventDefault();
        closeMenu(true);
        return;
      }
      if (event.key === '/' && !event.ctrlKey && !event.metaKey && !event.altKey && !event.target.matches('input,textarea,select,[contenteditable="true"]')) {
        event.preventDefault();
        $('search-input').focus();
      }
      if (event.key === 'Tab' && document.body.classList.contains('menu-open')) {
        const focusable = [...$('sidebar').querySelectorAll('a[href],button:not([disabled]),input,select')].filter(node => node.getClientRects().length);
        if (!focusable.length) return;
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first.focus();
        }
      }
    });
    window.addEventListener('scroll', scheduleRankUpdate, {passive: true});
    window.addEventListener('resize', scheduleRankUpdate);
    $('home-rank-overview').addEventListener('click', event => {
      const link = event.target.closest('a');
      if (link?.hash !== location.hash || event.ctrlKey || event.metaKey || event.altKey || event.shiftKey) return;
      event.preventDefault();
      scrollHomeSection(link.hash.slice('#/home/'.length));
    });
    window.addEventListener('hashchange', render);
    wideReading.addEventListener('change', event => {
      const toc = $('chapter-toc').querySelector('details');
      if (toc) toc.open = event.matches;
    });
  }

  async function init() {
    bind();
    if ($('site-status')) {
      $('site-status').hidden = false;
      $('site-status').textContent = '正在载入全书与赛事数据…';
    }
    try {
      const response = await fetch('./content.json', {cache: 'no-cache'});
      if (!response.ok) throw new Error('content ' + response.status);
      const data = await response.json();
      if (!Array.isArray(data.chapters) || !Array.isArray(data.contests) || !Array.isArray(data.supplements)) {
        throw new Error('Incomplete content');
      }
      state.data = data;
      if ($('site-status')) {
        $('site-status').hidden = true;
        $('site-status').textContent = '';
      }
      initFilters();
      document.querySelectorAll('[data-count="chapters"]').forEach(node => { node.textContent = data.chapters.length; });
      document.querySelectorAll('[data-count="contests"]').forEach(node => { node.textContent = data.contests.length; });
      if (!location.hash) history.replaceState(null, '', '#/home');
      render();
    } catch (error) {
      if ($('site-status')) {
        $('site-status').hidden = false;
        $('site-status').dataset.error = 'true';
        const reload = el('button', 'status-reload', '重新加载');
        reload.type = 'button';
        reload.addEventListener('click', () => location.reload());
        $('site-status').replaceChildren(
          el('strong', '', '暂时未能载入指南完整数据。'),
          document.createTextNode(' 可先 '),
          reload,
          document.createTextNode('，或先打开 '),
          anchor('GitHub 全书目录 ↗', REPO + '/blob/main/book/README.md'),
          document.createTextNode(' 与 '),
          anchor('离线 PDF ↓', './guide.pdf'),
          document.createTextNode('。')
        );
      }
      console.error('Guide content failed to load:', error);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, {once: true});
  } else {
    init();
  }
})();
