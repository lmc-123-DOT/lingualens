/* 语镜 LinguaLens — a paper-and-ink reading desk. */
(() => {
  'use strict';

  // ---------------------------------------------------------------- utilities
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
  const esc = (value) => String(value ?? '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  const attr = (value) => esc(value);
  const pad = (n) => String(n).padStart(2, '0');

  const ICONS = {
    arrow: '<path d="M5 12h14M13 6l6 6-6 6"/>',
    arrowLeft: '<path d="M19 12H5M11 18l-6-6 6-6"/>',
    upRight: '<path d="M7 17 17 7M8 7h9v9"/>',
    upload: '<path d="M12 16V4M7 9l5-5 5 5"/><path d="M4 16v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3"/>',
    link: '<path d="M10 13a5 5 0 0 0 7.1 0l2-2a5 5 0 0 0-7.1-7.1l-1.1 1.1"/><path d="M14 11a5 5 0 0 0-7.1 0l-2 2A5 5 0 0 0 12 20.1l1.1-1.1"/>',
    spark: '<path d="m12 3 1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9L12 3Z"/><path d="M19 15l.9 2.1L22 18l-2.1.9L19 21l-.9-2.1L16 18l2.1-.9L19 15Z"/>',
    trash: '<path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13M10 11v5M14 11v5"/>',
    copy: '<rect x="9" y="9" width="11" height="11" rx="2"/><path d="M15 9V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h3"/>',
    download: '<path d="M12 4v12M7 11l5 5 5-5"/><path d="M4 20h16"/>',
    settings: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-2 3.4-.2-.1a1.7 1.7 0 0 0-1.8 0l-.5.3a1.7 1.7 0 0 0-.9 1.5v.2h-4v-.2a1.7 1.7 0 0 0-.9-1.5l-.5-.3a1.7 1.7 0 0 0-1.8 0l-.2.1-2-3.4.1-.1A1.7 1.7 0 0 0 4.6 15l-.1-.5a1.7 1.7 0 0 0-1.3-1.2H3v-4h.2a1.7 1.7 0 0 0 1.3-1.2l.1-.5a1.7 1.7 0 0 0-.3-1.9l-.1-.1 2-3.4.2.1a1.7 1.7 0 0 0 1.8 0l.5-.3a1.7 1.7 0 0 0 .9-1.5V1h4v.2a1.7 1.7 0 0 0 .9 1.5l.5.3a1.7 1.7 0 0 0 1.8 0l.2-.1 2 3.4-.1.1a1.7 1.7 0 0 0-.3 1.9l.1.5a1.7 1.7 0 0 0 1.3 1.2h.2v4h-.2a1.7 1.7 0 0 0-1.3 1.2l-.1.5Z"/>',
    folder: '<path d="M3 7a2 2 0 0 1 2-2h5l2 2h7a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7Z"/>',
    scan: '<path d="M4 8V5a1 1 0 0 1 1-1h3M16 4h3a1 1 0 0 1 1 1v3M20 16v3a1 1 0 0 1-1 1h-3M8 20H5a1 1 0 0 1-1-1v-3"/><path d="M7 12h10"/>',
    play: '<path d="m8 5 11 7-11 7V5Z"/>',
    x: '<path d="M6 6l12 12M18 6 6 18"/>',
    check: '<path d="m5 12 4 4L19 6"/>',
    alert: '<path d="M12 9v5M12 17h.01"/><path d="M10.3 3.9 2.4 18a2 2 0 0 0 1.8 3h15.6a2 2 0 0 0 1.8-3L13.7 3.9a2 2 0 0 0-3.4 0Z"/>',
    search: '<circle cx="11" cy="11" r="7"/><path d="m16.5 16.5 4 4"/>',
    book: '<path d="M4 19.5V5a2 2 0 0 1 2-2h13v18H6a2 2 0 0 0-2 2.5Z"/><path d="M8 7h7M8 11h5"/>',
    layers: '<path d="m12 3 9 5-9 5-9-5 9-5Z"/><path d="m3 13 9 5 9-5M3 18l9 5 9-5"/>',
    history: '<path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5M12 7v5l3 2"/>',
    globe: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.6 2.5 4 5.5 4 9s-1.4 6.5-4 9c-2.6-2.5-4-5.5-4-9s1.4-6.5 4-9Z"/>',
    file: '<path d="M6 2h8l5 5v15H6V2Z"/><path d="M14 2v6h5M9 13h6M9 17h6"/>',
    refresh: '<path d="M20 11a8 8 0 0 0-14.9-4L3 10M3 4v6h6M4 13a8 8 0 0 0 14.9 4L21 14M21 20v-6h-6"/>',
    shield: '<path d="M12 3 4 6v6c0 5 3.4 8 8 9 4.6-1 8-4 8-9V6l-8-3Z"/><path d="m9 12 2 2 4-4"/>',
    clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    star: '<path d="m12 3 2.8 5.7 6.2.9-4.5 4.4 1.1 6.2-5.6-2.9-5.6 2.9 1.1-6.2L3 9.6l6.2-.9L12 3Z"/>',
    external: '<path d="M14 3h7v7M21 3l-9 9"/><path d="M19 14v5a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h5"/>',
    chevron: '<path d="m9 6 6 6-6 6"/>',
    swap: '<path d="M4 8h15M15 4l4 4-4 4M20 16H5M9 12l-4 4 4 4"/>',
    columns: '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M12 4v16"/>',
    speaker: '<path d="M11 5 6 9H3v6h3l5 4V5Z"/><path d="M15.5 8.5a5 5 0 0 1 0 7M18.5 5.5a9 9 0 0 1 0 13"/>',
    sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    moon: '<path d="M20.5 14.5A8.5 8.5 0 0 1 9.5 3.5 8.5 8.5 0 1 0 20.5 14.5Z"/>',
    droplet: '<path d="M12 3s6 6.2 6 10.2a6 6 0 0 1-12 0C6 9.2 12 3 12 3Z"/>',
    braille: '<circle cx="8" cy="7" r="1"/><circle cx="16" cy="7" r="1"/><circle cx="8" cy="12" r="1"/><circle cx="16" cy="12" r="1"/><circle cx="8" cy="17" r="1"/><circle cx="16" cy="17" r="1"/>',
    quote: '<path d="M9 11H5a4 4 0 0 1 4-4M9 11v6H5v-6M19 11h-4a4 4 0 0 1 4-4M19 11v6h-4v-6"/>',
    menu: '<path d="M4 7h16M4 12h16M4 17h16"/>',
  };
  const icon = (name, size = 16) => `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[name] || ''}</svg>`;

  const LANGS = {
    'zh-CN': { name: '简体中文', native: '简体中文', short: '中' },
    'zh-TW': { name: '繁体中文', native: '繁體中文', short: '繁' },
    en: { name: '英语', native: 'English', short: 'EN' },
    ja: { name: '日语', native: '日本語', short: '日' },
    ko: { name: '韩语', native: '한국어', short: '한' },
    fr: { name: '法语', native: 'Français', short: 'FR' },
    de: { name: '德语', native: 'Deutsch', short: 'DE' },
    es: { name: '西班牙语', native: 'Español', short: 'ES' },
    pt: { name: '葡萄牙语', native: 'Português', short: 'PT' },
    it: { name: '意大利语', native: 'Italiano', short: 'IT' },
    ru: { name: '俄语', native: 'Русский', short: 'RU' },
    ar: { name: '阿拉伯语', native: 'العربية', short: 'AR' },
    vi: { name: '越南语', native: 'Tiếng Việt', short: 'VI' },
    th: { name: '泰语', native: 'ไทย', short: 'TH' },
    auto: { name: '自动检测', native: 'Auto', short: 'A' },
    unknown: { name: '未知语言', native: 'Unknown', short: '?' },
  };
  const lang = (code) => LANGS[code] || { name: code || '未知', native: code || '', short: (code || '?').slice(0, 2).toUpperCase() };
  const THEMES = {
    paper: { name: '纸墨', icon: 'droplet', color: '#f4efe4' },
    night: { name: '暗夜', icon: 'sun', color: '#0f1512' },
    clear: { name: '清透', icon: 'moon', color: '#f7faf8' },
  };
  const themeIcon = (theme) => icon(THEMES[theme]?.icon || 'droplet', 17);
  const MOD_KEY = /Mac|iPhone|iPad|iPod/i.test(navigator.platform || navigator.userAgent) ? '⌘' : 'Ctrl';
  const targetLangs = ['zh-CN', 'en', 'ja', 'ko', 'fr', 'de', 'es', 'ru', 'zh-TW'];
  const sourceLangs = ['auto', ...targetLangs];

  const SAMPLES = {
    en: {
      source: 'en', target: 'zh-CN', label: '英文 · 阅读随笔',
      title: 'The Quiet Power of Reading',
      text: `# The Quiet Power of Reading

Reading is not a race. It is a conversation between a mind and a page.

Many people read only to finish. They count pages, not ideas. But a book that changes you is rarely the one you finish fastest. It is the one you return to, the one whose sentences keep working inside you long after you close it.

I have kept a list of such books for years. Some were written by writers who are now almost forgotten; others were found by accident in a second-hand shop. None of them was recommended by an algorithm. Perhaps that is why they stayed.

If I had known how much a single paragraph could change a person, I would have read more slowly when I was young. But reading slowly is a skill, and like every skill it requires practice. You have to learn to sit with a difficult sentence without reaching for your phone.

What makes a sentence stay? It is not always beauty. Sometimes it is precision — the feeling that someone has named a thing you had noticed but could never describe. At other times it is rhythm, the way a clause opens and closes like a door.

Not until I began to translate did I understand how much grammar shapes that rhythm. The passive voice can hide a person; a relative clause can hold two ideas in suspension; a single inversion can make an ordinary statement feel like a discovery. Grammar is not a set of rules to memorize. It is the architecture of meaning.

So read slowly. Let the sentence finish. Then look again at how it was built.`,
    },
    ja: {
      source: 'ja', target: 'zh-CN', label: '日文 · 随筆',
      title: '静かな読書の力',
      text: `# 静かな読書の力

読書は競争ではない。それは、ひとつの心と一枚のページのあいだで交わされる対話だ。

多くの人は、読み終えることだけを目的にしている。ページの数を数え、考えの数は数えない。しかし、あなたを変える本は、いちばん早く読み終えた本ではない。何度も戻ってしまう本であり、閉じたあとも、その文が心の中で働き続ける本なのだ。

私は何年も、そんな本のリストをつけてきた。その中には、今ではほとんど忘れられた作家の本もある。古本屋で偶然見つけた本もある。どれも、アルゴリズムに勧められた本ではない。だからこそ、残ったのかもしれない。

若い頃にもっとゆっくり読んでいればよかった、と思う。しかし、ゆっくり読むことは技術であり、技術である以上、練習が必要だ。難しい一文の前に座り、スマートフォンに手を伸ばさずにいることを、まず覚えなければならない。

一文を記憶に残すものは、美しさだけではない。正確さのこともある。自分が気づいていたのに、言葉にできなかったことを、誰かが名づけてくれたと感じる瞬間だ。リズムのこともある。節がドアのように開き、閉じるその形だ。

翻訳を始めてから、文法がそのリズムをどれほど形づくっているかを知った。受動態は人を隠すことができ、関係節は二つの考えを宙づりにし、たった一つの倒置が、普通の文を発見のように変える。文法は暗記する規則ではない。意味の建築なのだ。

だから、ゆっくり読もう。文が終わるまで待とう。そして、それがどのように建てられたのかを、もう一度見てみよう。`,
    },
    zh: {
      source: 'zh-CN', target: 'en', label: '中文 · 随笔',
      title: '阅读的安静力量',
      text: `# 阅读的安静力量

阅读不是一场竞赛。它是一个心灵与一页纸之间的对话。

很多人读书只是为了读完。他们数页数，却不数想法。可是，真正改变你的书，很少是你读得最快的那一本。它是你会一再回去的那一本，是合上书以后，句子仍在心里继续工作的那一本。

多年来，我一直保留着这样一份书单。有些书出自如今几乎被遗忘的作家，有些是在旧书店里偶然遇见的。它们没有一本是算法推荐的。也许正因为如此，它们才留了下来。

如果我早知道一个段落能改变一个人，年轻时我一定会读得更慢。但慢读是一种能力，而凡是能力，都需要练习。你得学会与一个难懂的句子坐在一起，而不伸手去拿手机。

让一个句子留下来的，并不总是美。有时是准确——你隐约注意到某件事，却始终说不清楚，而有人替你命了名。有时是节奏——从句像一扇门一样打开，又合上。

直到开始翻译，我才明白语法在多大程度上塑造了这种节奏。被动语态可以隐藏一个人；定语从句可以让两个念头悬在半空；一个倒装就能让普通的陈述变成发现。语法不是要背下来的规则，它是意义的建筑。

所以，慢一点读。让句子说完。然后再看一次：它是怎么被建起来的。`,
    },
  };

  const state = {
    health: null,
    settings: null,
    providers: [],
    article: null,
    draftSource: '',
    loading: false,
    loadingTimer: null,
    view: 'translation',
    theme: 'paper',
    readingScale: 1,
    historyQuery: '',
    compareView: 'translation',
    wordCache: new Map(),
    wordHistory: [],
    activeWordToken: null,
    sourceLang: 'auto',
    targetLang: 'zh-CN',
    provider: 'auto',
    route: '/',
    library: null,
    libraryMap: {},
    grammarFilters: { lang: '', category: '', q: '' },
    batchScan: null,
    batchJob: null,
    batchTimer: null,
    history: null,
    modalCleanup: null,
    importing: false,
    clearKey: false,
    currentGrammar: null,
    contextArticle: null,
    scrollBlock: null,
    installPrompt: null,
  };
  window.addEventListener('beforeinstallprompt', (event) => {
    event.preventDefault();
    state.installPrompt = event;
  });
  window.addEventListener('appinstalled', () => {
    state.installPrompt = null;
    toast('语镜已安装到桌面', 'success');
  });

  // ---------------------------------------------------------------- api
  async function api(path, options = {}) {
    const { method = 'GET', body, timeout = 240000 } = options;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeout);
    try {
      const res = await fetch(path, {
        method,
        headers: body ? { 'Content-Type': 'application/json' } : undefined,
        body: body ? JSON.stringify(body) : undefined,
        signal: controller.signal,
      });
      const text = await res.text();
      let data = {};
      try { data = text ? JSON.parse(text) : {}; } catch { throw new Error(`服务器返回了非 JSON 内容（${res.status}）`); }
      if (!res.ok || data.ok === false) throw new Error(data.error || `请求失败（${res.status}）`);
      return data;
    } catch (err) {
      if (err.name === 'AbortError') throw new Error('请求超时，请稍后重试');
      throw err;
    } finally {
      clearTimeout(timer);
    }
  }

  function toast(message, type = '') {
    const root = $('#toast-root');
    if (!root) return;
    const node = document.createElement('div');
    node.className = `toast ${type}`;
    node.innerHTML = `${icon(type === 'error' ? 'alert' : type === 'success' ? 'check' : 'spark', 14)}<span>${esc(message)}</span>`;
    root.appendChild(node);
    setTimeout(() => {
      node.classList.add('is-out');
      setTimeout(() => node.remove(), 280);
    }, type === 'error' ? 5200 : 3400);
  }

  const fmtBytes = (bytes) => {
    if (!bytes) return '0 B';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  };
  const fmtNumber = (n) => Number(n || 0).toLocaleString('zh-CN');
  const fmtDate = (iso) => {
    if (!iso) return '';
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return `${d.getFullYear()}.${pad(d.getMonth() + 1)}.${pad(d.getDate())}`;
  };
  const timeAgo = (iso) => {
    if (!iso) return '';
    const d = new Date(iso);
    const diff = (Date.now() - d.getTime()) / 1000;
    if (diff < 60) return '刚刚';
    if (diff < 3600) return `${Math.floor(diff / 60)} 分钟前`;
    if (diff < 86400) return `${Math.floor(diff / 3600)} 小时前`;
    if (diff < 86400 * 7) return `${Math.floor(diff / 86400)} 天前`;
    return fmtDate(iso);
  };
  const providerLabel = (id) => ({
    auto: '自动优选', ai: 'AI 精准模式', mymemory: 'MyMemory', google: 'Google',
    offline: '离线预览', mixed: 'AI + 免费引擎', cache: '翻译记忆', copy: '原文（同语）', none: '—',
  }[id] || id || '—');

  function safeUrl(url) {
    try {
      const u = new URL(url, location.origin);
      return (u.protocol === 'http:' || u.protocol === 'https:') ? u.href : '#';
    } catch { return '#'; }
  }

  // ---------------------------------------------------------------- shell
  function activeNav(path) {
    if (path === '/') return 'translate';
    if (path === '/compare') return 'compare';
    if (path.startsWith('/grammar')) return 'grammar';
    if (path.startsWith('/batch')) return 'batch';
    if (path.startsWith('/history')) return 'history';
    return '';
  }

  function topbar(path) {
    const active = activeNav(path);
    const aiReady = !!state.health?.aiConfigured;
    return `<header class="topbar">
      <div class="topbar-inner">
        <a class="brand" href="/" data-link aria-label="语镜首页">
          <span class="brand-mark">语</span>
          <span class="brand-word"><strong>语镜</strong><small>LinguaLens</small></span>
        </a>
        <nav class="nav" aria-label="主导航">
          <a href="/" data-link class="${active === 'translate' ? 'is-active' : ''}">翻译台</a>
          <a href="/compare" data-link class="${active === 'compare' ? 'is-active' : ''}">对照阅读</a>
          <a href="/grammar" data-link class="${active === 'grammar' ? 'is-active' : ''}">语法索引</a>
          <a href="/batch" data-link class="${active === 'batch' ? 'is-active' : ''}">文件夹批译</a>
          <a href="/history" data-link class="${active === 'history' ? 'is-active' : ''}">历史</a>
        </nav>
        <div class="top-actions">
          <span id="status-pill" class="status-pill" title="${aiReady ? 'AI 精准模式已就绪' : '未配置 AI 时使用免费引擎'}">
            <span class="status-dot ${aiReady ? '' : 'warn'}"></span>
            ${aiReady ? 'AI 已就绪' : '免费引擎'}
          </span>
          <button class="icon-btn theme-btn" id="theme-btn" data-action="cycle-theme" aria-label="切换主题" title="切换主题">${themeIcon(state.theme)}</button>
          <button class="icon-btn" data-action="open-settings" aria-label="设置" title="设置">${icon('settings', 17)}</button>
        </div>
      </div>
    </header>`;
  }

  function footer() {
    const total = state.health?.grammar?.total || 106;
    return `<footer class="site-footer">
      <span class="seal"><i></i> 语镜 LinguaLens</span>
      <span>本地优先的阅读工作台 · 语法库 ${total} 条</span>
      <span class="spacer"></span>
      <span>翻译由你选择的引擎完成 · 语法分析在本地运行</span>
      <span>v${esc(state.health?.version || '1.0.0')}</span>
    </footer>`;
  }

  function renderRoute() {
    clearBatchTimer();
    clearInterval(state.loadingTimer);
    state.loadingTimer = null;
    closeWordCard();
    const path = normalizePath(location.pathname);
    state.route = path;
    const query = new URLSearchParams(location.search);
    let content = '';
    let after = null;

    if (path === '/') {
      state.view = 'translation';
      content = workspaceHTML();
      after = afterWorkspace;
    } else if (path === '/compare') {
      content = compareHTML();
      after = afterCompare;
    } else if (path === '/grammar') {
      content = grammarIndexHTML();
      after = afterGrammarIndex;
    } else if (path.startsWith('/grammar/')) {
      content = grammarDetailSkeleton(path.split('/')[2] || '');
      after = () => afterGrammarDetail(path.split('/')[2] || '', query);
    } else if (path === '/batch') {
      content = batchHTML();
      after = afterBatch;
    } else if (path === '/history') {
      content = historyHTML();
      after = afterHistory;
    } else {
      content = notFoundHTML();
    }

    document.body.classList.toggle('has-article', !!state.article && path === '/');
    $('#app').innerHTML = `${topbar(path)}<main id="main" class="shell">${content}</main>${footer()}`;
    document.title = titleFor(path);
    if (typeof after === 'function') after();
    syncStatusPill();
  }

  function normalizePath(path) {
    const clean = (path || '/').replace(/\/+$/, '');
    return clean || '/';
  }

  function titleFor(path) {
    if (path === '/') return '语镜 LinguaLens · 读懂每一句的骨架';
    if (path === '/compare') return '对照阅读 · 语镜 LinguaLens';
    if (path === '/grammar') return '语法索引 · 语镜 LinguaLens';
    if (path.startsWith('/grammar/')) return '语法讲解 · 语镜 LinguaLens';
    if (path === '/batch') return '文件夹批译 · 语镜 LinguaLens';
    if (path === '/history') return '历史记录 · 语镜 LinguaLens';
    return '语镜 LinguaLens';
  }

  function navigate(path, { replace = false, scroll = true } = {}) {
    if (replace) history.replaceState({}, '', path);
    else history.pushState({}, '', path);
    renderRoute();
    if (scroll) window.scrollTo({ top: 0, behavior: 'instant' });
  }

  function syncStatusPill() {
    const pill = $('#status-pill');
    if (!pill) return;
    const aiReady = !!state.health?.aiConfigured;
    pill.innerHTML = `<span class="status-dot ${aiReady ? '' : 'warn'}"></span>${aiReady ? 'AI 已就绪' : '免费引擎'}`;
    pill.title = aiReady ? 'AI 精准模式已就绪' : '未配置 AI 时使用免费引擎';
  }

  function applyTheme(theme, { persist = true, notify = false } = {}) {
    state.theme = THEMES[theme] ? theme : 'paper';
    document.documentElement.dataset.theme = state.theme;
    try { localStorage.setItem('ll.theme', state.theme); } catch { /* private mode */ }
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute('content', THEMES[state.theme].color);
    const button = $('#theme-btn');
    if (button) {
      button.innerHTML = themeIcon(state.theme);
      button.title = `当前：${THEMES[state.theme].name} · 点击切换`;
    }
    $$('[data-theme-choice]').forEach((el) => el.classList.toggle('is-active', el.dataset.themeChoice === state.theme));
    if (persist) {
      api('/api/settings', { method: 'POST', body: { theme: state.theme }, timeout: 5000 }).catch(() => {});
    }
    if (notify) toast(`已切换到「${THEMES[state.theme].name}」主题`, 'success');
  }

  function cycleTheme() {
    const order = ['paper', 'night', 'clear'];
    const next = order[(order.indexOf(state.theme) + 1) % order.length];
    applyTheme(next, { notify: true });
  }

  // ---------------------------------------------------------------- workspace
  function heroHTML() {
    const total = state.health?.grammar?.total || 106;
    const langCount = targetLangs.length || 9;
    return `<section class="hero">
      <div class="hero-copy">
        <p class="eyebrow">TRANSLATE · TRACE · UNDERSTAND</p>
        <h1>把一篇文章，<br>读成<em>自己的语言</em>。</h1>
        <p class="lede">语镜先逐段翻译，再把句子里的语法骨架拆给你看。每一个语法点都能跳转到完整讲解，也能顺着例句回到原文。</p>
        <div class="hero-meta">
          <span>${langCount} 种语言</span><i class="dot"></i>
          <span>14 种文章格式</span><i class="dot"></i>
          <span>${total} 个语法点</span><i class="dot"></i>
          <span>本地运行 · 原文不出内网</span>
        </div>
      </div>
      <div class="hero-aside" aria-hidden="true">
        <div class="hero-number">${total}<small>GRAMMAR ENTRIES</small></div>
        <div class="hero-stamp">${icon('shield', 13)} PRIVATE BY DEFAULT</div>
      </div>
    </section>`;
  }

  function readingBarHTML(article) {
    if (!article) return '';
    const src = article.source || {};
    const tgt = article.target || {};
    const grammarCount = article.grammar?.summary?.total || 0;
    return `<div class="reading-bar">
      <div class="reading-id">
        <span>NOW READING · ${esc(fmtDate(article.createdAt))}</span>
        <h2>${esc(article.title || '未命名文章')}</h2>
      </div>
      <div class="reading-badges">
        <span class="chip">${esc(src.label || lang(src.lang).name)} <b>→</b> ${esc(tgt.label || lang(tgt.lang).name)}</span>
        <span class="chip">${fmtNumber(src.stats?.words)} 词</span>
        <span class="chip jade">${grammarCount} 个语法点</span>
        <span class="chip outline">${esc(tgt.cached ? '翻译记忆' : providerLabel(tgt.provider))}</span>
      </div>
      <div class="reading-actions">
        <a class="btn btn-sm btn-ghost" href="/compare" data-link>${icon('columns', 13)} 对照阅读</a>
        <button class="btn btn-sm btn-ghost" data-action="copy-translation">${icon('copy', 13)} 复制译文</button>
        <button class="btn btn-sm btn-ghost" data-action="download-word">${icon('file', 13)} Word</button>
        <button class="btn btn-sm btn-ghost" data-action="download-article">${icon('download', 13)} 导出</button>
      </div>
    </div>`;
  }

  function sourceLangOptions(selected) {
    return sourceLangs.map((code) => `<option value="${code}" ${selected === code ? 'selected' : ''}>${esc(code === 'auto' ? '自动检测' : `${lang(code).name} · ${lang(code).native}`)}</option>`).join('');
  }
  function targetLangOptions(selected) {
    return targetLangs.map((code) => `<option value="${code}" ${selected === code ? 'selected' : ''}>${esc(`${lang(code).name} · ${lang(code).native}`)}</option>`).join('');
  }
  function providerOptions(selected) {
    const list = state.providers.length ? state.providers : [
      { id: 'auto', label: '自动优选', available: true, note: '' },
      { id: 'ai', label: 'AI 精准模式', available: false, note: '先在设置中填入 API Key' },
      { id: 'mymemory', label: 'MyMemory 免费引擎', available: true, note: '' },
      { id: 'google', label: 'Google 免费引擎', available: true, note: '' },
    ];
    return list.map((p) => `<option value="${p.id}" ${selected === p.id ? 'selected' : ''} ${p.available === false ? 'disabled' : ''}>${esc(p.label)}${p.available === false ? '（需配置）' : ''}</option>`).join('');
  }

  function studioHTML() {
    const article = state.article;
    const sourceText = state.draftSource !== undefined && state.draftSource !== null && state.draftSource !== ''
      ? state.draftSource
      : (article?.source?.text || '');
    const stats = article?.source?.stats;
    const loading = state.loading;
    return `<section class="studio" id="studio">
      <div class="studio-toolbar">
        <div class="lang-group">
          <div class="select-wrap select-sm"><label class="sr-only" for="source-lang">原文语言</label><select id="source-lang">${sourceLangOptions(state.sourceLang)}</select></div>
          <button class="swap-btn" data-action="swap-langs" title="交换语言" aria-label="交换语言">${icon('swap', 14)}</button>
          <div class="select-wrap select-sm"><label class="sr-only" for="target-lang">目标语言</label><select id="target-lang">${targetLangOptions(state.targetLang)}</select></div>
        </div>
        <div class="select-wrap provider-select">
          <label class="sr-only" for="provider-select">翻译引擎</label>
          <select id="provider-select" title="翻译引擎">${providerOptions(state.provider)}</select>
        </div>
        <span class="toolbar-spacer"></span>
        <button class="btn btn-primary" data-action="translate" ${loading ? 'disabled' : ''}>
          ${loading ? `<span class="spinner" style="border-color:rgba(255,255,255,.35);border-top-color:#fff"></span> 翻译中` : `${icon('spark', 15)} 开始翻译 <span class="kbd">${MOD_KEY} ↵</span>`}
        </button>
      </div>
      <div class="workspace-grid">
        <section class="pane source-pane" aria-label="原文输入">
          <div class="pane-head">
            <div class="pane-title"><span class="ord">01</span> 原文 <span class="count" id="source-count">${stats ? `${fmtNumber(stats.words)} 词 · ${fmtNumber(stats.chars)} 字` : '等待输入'}</span></div>
            <div class="pane-tools">
              <span class="dirty-flag">${icon('alert', 12)} 有改动</span>
              <button class="icon-btn" data-action="clear" title="清空" aria-label="清空">${icon('trash', 15)}</button>
            </div>
          </div>
          <div class="pane-body source-area-wrap">
            <textarea id="source-text" spellcheck="false" placeholder="粘贴一篇文章，或拖入 TXT / Markdown / Word / PDF / EPUB 文件…">${esc(sourceText)}</textarea>
            <div class="drop-overlay" id="drop-overlay">${icon('upload', 28)}<strong>松手，交给语镜</strong><span>支持 PDF、Word、EPUB、Markdown、字幕等 11 种格式</span></div>
            <div class="source-foot">
              <button class="btn btn-sm" data-action="upload">${icon('upload', 13)} 导入文件</button>
              <button class="btn btn-sm" data-action="open-url">${icon('link', 13)} 网页链接</button>
              <button class="btn btn-sm" data-action="load-sample" data-sample="en">${icon('book', 13)} 示例</button>
              <span class="meta" id="source-meta">${stats ? `${fmtNumber(stats.paragraphs)} 段 · 约 ${stats.minutes} 分钟` : 'Ctrl / ⌘ + Enter 翻译'}</span>
            </div>
          </div>
        </section>

        <section class="pane result-pane" aria-label="翻译结果" style="--reading-scale:${state.readingScale}">
          <div class="pane-head">
            <div class="pane-title"><span class="ord">02</span> 译文</div>
            <div class="pane-tools">
              <a class="btn btn-sm btn-ghost" href="/compare" data-link>${icon('columns', 13)} 对照阅读</a>
              <div class="font-controls" title="阅读字号">
                <button data-action="font-smaller" aria-label="缩小字号">A−</button>
                <span id="font-value">${Math.round(state.readingScale * 100)}%</span>
                <button data-action="font-larger" aria-label="放大字号">A+</button>
              </div>
              <button class="icon-btn" data-action="copy-translation" title="复制译文" aria-label="复制译文" ${article ? '' : 'disabled'}>${icon('copy', 15)}</button>
              <button class="icon-btn" data-action="download-article" title="导出 Markdown" aria-label="导出" ${article ? '' : 'disabled'}>${icon('download', 15)}</button>
            </div>
          </div>
          <div class="result-body" id="result-body">${resultBodyHTML()}</div>
        </section>
      </div>
    </section>`;
  }

  function workspaceHTML() {
    return `${heroHTML()}${readingBarHTML(state.article)}${studioHTML()}
      ${featuresHTML()}
      <div id="recent-strip"></div>`;
  }

  function featuresHTML() {
    return `<div class="section-head"><h2>一张纸，四件事</h2><p>翻译、对照、语法、批译，彼此连着</p><span class="line"></span></div>
      <section class="features">
        <article class="feature"><span class="no">01 / IMPORT</span><span class="icon">${icon('upload', 17)}</span><h3>多格式进入</h3><p>PDF、Word、PPT、Excel、EPUB、网页、字幕，拖进来就排版。</p></article>
        <article class="feature"><span class="no">02 / TRANSLATE</span><span class="icon">${icon('braille', 17)}</span><h3>逐段精准翻译</h3><p>保留段落编号与标题层级，译文和原文一一对应，不漏段。</p></article>
        <article class="feature"><span class="no">03 / GRAMMAR</span><span class="icon">${icon('layers', 17)}</span><h3>语法雷达</h3><p>从文中定位时态、助词、句式，点开就是一整页讲解。</p></article>
        <article class="feature"><span class="no">04 / FOLDER</span><span class="icon">${icon('folder', 17)}</span><h3>整夹批译</h3><p>选一个文件夹，递归翻译并输出双语 Markdown。</p></article>
      </section>`;
  }

  function resultBodyHTML() {
    if (state.loading) {
      return `<div class="loading-state">
        <div class="loading-note"><span class="spinner"></span><span id="loading-note-text">正在切分段落，逐段翻译…</span></div>
        <div class="skeleton-line title"></div>
        <div class="skeleton-line"></div><div class="skeleton-line"></div><div class="skeleton-line"></div>
        <div class="skeleton-line title" style="width:38%;margin-top:16px"></div>
        <div class="skeleton-line"></div><div class="skeleton-line"></div>
        <div class="skeleton-line"></div><div class="skeleton-line"></div>
      </div>`;
    }
    if (!state.article) {
      return `<div class="empty-state">
        <div class="empty-glyph">译</div>
        <h3>译文会在这里展开</h3>
        <p>左边放入文章，或从一份示例开始。翻译完成后点「对照阅读」，进入独立的左右对照页。</p>
        <div class="empty-actions">
          <button class="btn btn-sm btn-primary" data-action="load-sample" data-sample="en">英文示例</button>
          <button class="btn btn-sm" data-action="load-sample" data-sample="ja">日文示例</button>
          <button class="btn btn-sm" data-action="load-sample" data-sample="zh">中文示例</button>
        </div>
      </div>`;
    }
    const article = state.article;
    const warnings = (article.warnings || []).map((w) => `<div class="warning-item">${icon('alert', 13)}<span>${esc(w)}</span></div>`).join('');
    let body = '';
    if (state.view === 'grammar') body = grammarResultHTML(article);
    else if (state.view === 'bilingual') body = bilingualHTML(article);
    else body = translatedHTML(article);
    const tgt = article.target || {};
    return `${warnings ? `<div class="warning-list">${warnings}</div>` : ''}
      ${body}
      <div class="result-foot">
        <span>${esc(tgt.cached ? '翻译记忆命中' : (tgt.providerLabel || providerLabel(tgt.provider)))} · ${(tgt.blocks || []).length} 段 · ${esc(String(article.elapsed || '—'))}s</span>
        ${tgt.cached ? `<span class="chip">命中缓存 ${tgt.cached} 段</span>` : ''}
        <button class="result-foot-link" data-action="open-grammar-index">语法全图 ${icon('arrow', 11)}</button>
      </div>`;
  }

  function articleBlocks(article) {
    return article.target?.blocks || [];
  }

  function translatedHTML(article) {
    const blocks = articleBlocks(article);
    if (!blocks.length) return `<div class="empty-state"><p>译文为空。</p></div>`;
    let html = '<article class="article-prose">';
    let inList = false;
    for (const block of blocks) {
      if (block.type === 'list') {
        if (!inList) { html += '<ul class="art-list">'; inList = true; }
        html += `<li id="block-${block.id}" data-block="${block.id}">${esc(block.target)}</li>`;
        continue;
      }
      if (inList) { html += '</ul>'; inList = false; }
      const text = esc(block.target).replace(/\n/g, '<br>');
      if (block.type === 'heading') {
        const level = Math.min(4, Math.max(1, Number(block.level) || 2));
        html += `<h${level} class="art-h${level}" id="block-${block.id}" data-block="${block.id}">${text}</h${level}>`;
      } else if (block.type === 'quote') {
        html += `<blockquote id="block-${block.id}" data-block="${block.id}">${text}</blockquote>`;
      } else if (block.type === 'code') {
        html += `<pre class="art-code" id="block-${block.id}" data-block="${block.id}">${esc(block.source)}</pre>`;
      } else if (block.type === 'table') {
        html += `<div class="art-table" id="block-${block.id}" data-block="${block.id}"><pre>${esc(block.source)}</pre></div>`;
      } else {
        html += `<p class="art-p" id="block-${block.id}" data-block="${block.id}">${text}</p>`;
      }
    }
    if (inList) html += '</ul>';
    html += '</article>';
    return html;
  }

  function grammarByBlock(article) {
    const map = {};
    for (const point of article.grammar?.points || []) {
      for (const occ of point.occurrences || []) {
        const key = String(occ.blockId || 0);
        if (!map[key]) map[key] = [];
        if (!map[key].some((p) => p.id === point.id)) map[key].push(point);
      }
    }
    return map;
  }

  function bilingualHTML(article) {
    const blocks = articleBlocks(article);
    if (!blocks.length) return `<div class="empty-state"><p>没有可对照的段落。</p></div>`;
    const byBlock = grammarByBlock(article);
    return `<div class="bilingual-list">${blocks.map((b) => {
      const chips = (byBlock[String(b.id)] || []).slice(0, 3).map((p) =>
        `<a class="chip jade" href="/grammar/${encodeURIComponent(p.id)}?from=${encodeURIComponent(article.id)}" data-link>${esc(p.title)}</a>`).join('');
      return `<div class="bi-row ${b.type === 'heading' ? 'is-heading' : ''} ${b.type === 'code' || b.type === 'table' ? 'is-code' : ''}" id="block-${b.id}" data-block="${b.id}">
        <div class="bi-num">${pad(Number(b.id) || 0)}</div>
        <div class="bi-source">${esc(b.source).replace(/\n/g, '<br>')}</div>
        <div class="bi-target">${esc(b.target).replace(/\n/g, '<br>')}${chips ? `<div class="bi-chips">${chips}</div>` : ''}</div>
      </div>`;
    }).join('')}</div>`;
  }

  function grammarResultHTML(article) {
    const points = article.grammar?.points || [];
    if (!points.length) {
      return `<div class="empty-state"><div class="empty-glyph">法</div><h3>这篇文章没有命中语法规则</h3><p>可能是文本太短，或属于尚未建立规则的语言。你仍然可以在「对照阅读」中逐段阅读。</p></div>`;
    }
    return `<div class="grammar-result-list">
      <div class="grammar-result-head"><span>${points.length} 个语法点</span><span>按出现次数排序</span></div>
      ${points.map((p, index) => `<article class="grammar-result-card">
        <div class="grc-index">${pad(index + 1)}</div>
        <div class="grc-main">
          <div class="grc-top"><span class="chip">${esc(p.category)}</span><span class="chip gold">${esc(p.cefr)}</span><span class="grc-count">${p.count} 处</span></div>
          <h3><a href="/grammar/${encodeURIComponent(p.id)}?from=${encodeURIComponent(article.id)}" data-link>${esc(p.title)}</a><small>${esc(p.english)}</small></h3>
          <p class="grc-summary">${esc(p.summary)}</p>
          <div class="grc-formula">${esc(p.formula)}</div>
          ${(p.occurrences || []).slice(0, 2).map((o) => `<blockquote class="grc-quote">${esc(o.sentence)}</blockquote>`).join('')}
          <a class="grc-link" href="/grammar/${encodeURIComponent(p.id)}?from=${encodeURIComponent(article.id)}" data-link>查看完整讲解 ${icon('arrow', 12)}</a>
        </div>
      </article>`).join('')}
    </div>`;
  }

  function railHTML() {
    const article = state.article;
    const points = article?.grammar?.points || [];
    const count = points.length;
    const categories = article?.grammar?.summary?.categories || {};
    const catList = Object.entries(categories).sort((a, b) => b[1] - a[1]).slice(0, 5);
    const totalCat = catList.reduce((s, [, n]) => s + n, 0) || 1;
    const bars = catList.map(([, n]) => `<span style="width:${Math.max(4, (n / totalCat) * 100)}%"></span>`).join('');
    const list = points.length
      ? points.map((p) => `<button class="grammar-mini" data-goto="/grammar/${encodeURIComponent(p.id)}?from=${encodeURIComponent(article.id)}">
          <div class="grammar-mini-top"><span class="chip outline">${esc(p.cefr)}</span><span class="cat">${esc(p.category)}</span><span class="times">${p.count} 处</span></div>
          <h4>${esc(p.title)}<small>${esc(p.english)}</small></h4>
          <p class="formula">${esc(p.formula)}</p>
          <span class="open-hint">完整讲解 ${icon('arrow', 11)}</span>
        </button>`).join('')
      : `<div class="rail-empty"><div class="seal">法</div><p>翻译完成后，这里会出现文章里的语法点。<br>每一个都能点开完整讲解。</p></div>`;
    return `<div class="rail-head">
        <div class="rail-title"><h3>语法雷达</h3><span class="count-badge">${count}</span></div>
        <p class="rail-sub">${count ? '从原文中定位，点击展开完整讲解' : '等待一篇文章'}</p>
        <div class="rail-stats">${bars}</div>
      </div>
      <div class="rail-scroll">${list}</div>
      <div class="rail-foot"><button class="btn btn-sm" data-action="open-grammar-index">${icon('layers', 13)} 打开完整语法图谱 ${icon('arrow', 11)}</button></div>`;
  }

  function afterWorkspace() {
    const textarea = $('#source-text');
    if (textarea && state.loading) textarea.setAttribute('readonly', 'readonly');
    if (state.loading) {
      let i = 0;
      const notes = ['正在切分段落，逐段翻译…', '正在对齐原文与译文…', '正在扫描时态、助词与句式…', '还在处理长句，请稍候…'];
      clearTimeout(state.loadingTimer);
      state.loadingTimer = setInterval(() => {
        const node = $('#loading-note-text');
        if (!node) return;
        i = (i + 1) % notes.length;
        node.textContent = notes[i];
      }, 2600);
    }
    if (state.scrollBlock) {
      const target = $(`#block-${state.scrollBlock}`);
      if (target) setTimeout(() => target.scrollIntoView({ block: 'center', behavior: 'smooth' }), 120);
      state.scrollBlock = null;
    }
    if (!state.article) loadRecentStrip();
    // Textarea counters
    if (textarea) {
      textarea.addEventListener('input', onSourceInput);
    }
  }

  function onSourceInput(e) {
    state.draftSource = e.target.value;
    document.querySelector('.source-pane')?.classList.add('is-dirty');
    const stats = roughStats(e.target.value);
    const count = $('#source-count');
    const meta = $('#source-meta');
    if (count) count.textContent = stats.words ? `${fmtNumber(stats.words)} 词 · ${fmtNumber(stats.chars)} 字` : '等待输入';
    if (meta) meta.textContent = stats.words ? `${fmtNumber(stats.paragraphs)} 段 · 约 ${stats.minutes} 分钟` : 'Ctrl / ⌘ + Enter 翻译';
  }

  function roughStats(text) {
    const latin = (text.match(/[A-Za-zÀ-ÖØ-öø-ÿ]+(?:['’\-][A-Za-zÀ-ÖØ-öø-ÿ]+)*/g) || []).length;
    const cjk = (text.match(/[\u3040-\u30ff\u3400-\u9fff\uac00-\ud7a3]/g) || []).length;
    const chars = text.replace(/\s/g, '').length;
    return { words: latin + cjk, chars, paragraphs: text.split(/\n\s*\n/).filter((p) => p.trim()).length, minutes: Math.max(1, Math.round((latin + cjk) / 260)) || 0 };
  }

  async function loadRecentStrip() {
    try {
      const data = await api('/api/history?limit=3');
      const items = data.items || [];
      const container = $('#recent-strip');
      if (!container || !items.length) return;
      container.innerHTML = `<div class="section-head"><h2>最近的纸页</h2><p>从上次读到的地方继续</p><span class="line"></span><a href="/history" data-link class="section-more">全部历史 ${icon('arrow', 12)}</a></div>
        <div class="recent-grid">${items.map((item) => `<button class="recent-card" data-open-history="${attr(item.id)}">
          <span class="recent-top"><span class="chip">${esc(lang(item.sourceLang).short)} → ${esc(lang(item.targetLang).short)}</span><span class="recent-time">${esc(timeAgo(item.createdAt))}</span></span>
          <strong>${esc(item.title)}</strong>
          <span class="recent-excerpt">${esc(item.translatedExcerpt || item.excerpt)}</span>
          <span class="recent-bottom">${item.grammarCount} 个语法点 ${icon('arrow', 11)}</span>
        </button>`).join('')}</div>`;
    } catch { /* history is a bonus */ }
  }

  function readControls() {
    const source = $('#source-lang');
    const target = $('#target-lang');
    const provider = $('#provider-select');
    if (source) state.sourceLang = source.value;
    if (target) state.targetLang = target.value;
    if (provider) state.provider = provider.value;
    persistPrefs();
  }

  function persistPrefs() {
    try {
      localStorage.setItem('ll.prefs', JSON.stringify({
        sourceLang: state.sourceLang, targetLang: state.targetLang, provider: state.provider, view: state.view,
      }));
    } catch { /* private mode */ }
  }

  async function doTranslate() {
    const textarea = $('#source-text');
    const text = (textarea ? textarea.value : state.draftSource || '').trim();
    if (!text) { toast('先放入一篇文章，或载入示例。', 'error'); textarea?.focus(); return; }
    readControls();
    if (text.length > 160000) { toast('文章太长，请控制在 16 万字符以内。', 'error'); return; }
    state.draftSource = text;
    if (state.article && state.article.source?.text !== text) state.article = null;
    state.loading = true;
    state.view = 'translation';
    renderRoute();
    try {
      const data = await api('/api/translate', {
        method: 'POST',
        body: { text, source: state.sourceLang, target: state.targetLang, provider: state.provider },
      });
      state.article = data.article;
      state.draftSource = data.article.source.text;
      state.loading = false;
      try { sessionStorage.setItem('ll.article', JSON.stringify(data.article)); } catch { /* quota */ }
      renderRoute();
      const warnings = data.article.warnings || [];
      if (data.article.target?.provider === 'offline') toast('在线引擎不可用，当前是离线预览。', 'error');
      else if (warnings.length) toast(warnings[0], 'error');
      else toast(`翻译完成 · ${data.article.grammar?.summary?.total || 0} 个语法点已定位`, 'success');
    } catch (err) {
      state.loading = false;
      renderRoute();
      toast(err.message || '翻译失败', 'error');
    }
  }

  // ---------------------------------------------------------------- file / URL import
  function pickFile() {
    const input = $('#file-input');
    if (!input) return;
    input.value = '';
    input.click();
  }

  async function handleFile(file) {
    if (!file) return;
    if (file.size > 40 * 1024 * 1024) { toast('文件超过 40MB，请拆分后再导入。', 'error'); return; }
    state.importing = true;
    toast(`正在解析 ${file.name}…`);
    try {
      const dataUrl = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = () => reject(new Error('读取文件失败'));
        reader.readAsDataURL(file);
      });
      const data = await api('/api/extract', { method: 'POST', body: { filename: file.name, data: dataUrl } });
      state.article = null;
      state.draftSource = data.text;
      state.sourceLang = 'auto';
      state.view = 'translation';
      toast(`已导入 ${data.meta?.formatLabel || file.name} · ${fmtNumber(data.stats?.chars)} 字`, 'success');
      renderRoute();
      setTimeout(doTranslate, 120);
    } catch (err) {
      toast(err.message || '文件解析失败', 'error');
    } finally {
      state.importing = false;
    }
  }

  function openUrlDialog() {
    openModal(`<div class="modal-head"><h2>从网页取一篇文章</h2><span class="sub">正文会被提取，而不是整页 HTML</span><button class="icon-btn modal-close" data-action="close-modal" aria-label="关闭">${icon('x', 16)}</button></div>
      <form id="url-form">
        <div class="modal-body url-dialog">
          <div class="field"><label for="url-input">文章网址</label><input id="url-input" type="url" placeholder="https://example.com/article" autocomplete="off" required />
            <span class="hint">支持公开网页与 PDF 链接。部分需要登录或反爬的站点可能无法抓取。</span></div>
          <div class="callout">${icon('shield', 14)}<span>抓取只发生在你的电脑上。内网地址与本地文件不会被访问。</span></div>
        </div>
        <div class="modal-foot"><span class="spacer"></span><button type="button" class="btn" data-action="close-modal">取消</button><button type="submit" class="btn btn-primary">${icon('link', 14)} 抓取并翻译</button></div>
      </form>`, (modal) => {
      setTimeout(() => $('#url-input')?.focus(), 80);
      $('#url-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const input = $('#url-input');
        const submit = e.target.querySelector('button[type=submit]');
        if (!input?.value.trim()) return;
        const url = input.value.trim();
        submit.disabled = true;
        submit.innerHTML = `<span class="spinner" style="border-color:rgba(255,255,255,.4);border-top-color:#fff"></span> 抓取中`;
        try {
          const data = await api('/api/extract-url', { method: 'POST', body: { url } });
          closeModal();
          state.article = null;
          state.draftSource = data.text;
          state.sourceLang = 'auto';
          toast(`已抓取：${data.title || '网页文章'}`, 'success');
          renderRoute();
          setTimeout(doTranslate, 120);
        } catch (err) {
          toast(err.message || '抓取失败', 'error');
          submit.disabled = false;
          submit.innerHTML = `${icon('link', 14)} 抓取并翻译`;
        }
      });
    });
  }

  // ---------------------------------------------------------------- samples
  function loadSample(key) {
    const sample = SAMPLES[key];
    if (!sample) return;
    state.article = null;
    state.draftSource = sample.text;
    state.sourceLang = sample.source;
    state.targetLang = sample.target;
    state.view = 'translation';
    renderRoute();
    setTimeout(doTranslate, 120);
  }

  // ---------------------------------------------------------------- copy / export
  async function copyText(text) {
    try {
      await navigator.clipboard.writeText(text);
      toast('已复制', 'success');
    } catch {
      const ta = document.createElement('textarea');
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      try { document.execCommand('copy'); toast('已复制', 'success'); }
      catch { toast('复制失败，请手动选择。', 'error'); }
      ta.remove();
    }
  }

  async function copyTranslation() {
    const text = state.article?.target?.text;
    if (!text) { toast('还没有可复制的译文。', 'error'); return; }
    try {
      await navigator.clipboard.writeText(text);
      toast('译文已复制', 'success');
    } catch {
      const ta = document.createElement('textarea');
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      try { document.execCommand('copy'); toast('译文已复制', 'success'); }
      catch { toast('复制失败，请手动选择。', 'error'); }
      ta.remove();
    }
  }

  function downloadArticle() {
    const article = state.article;
    if (!article) { toast('还没有可导出的译文。', 'error'); return; }
    if (article.id && !article.id.startsWith('art-temp')) {
      window.location.href = `/api/history/${encodeURIComponent(article.id)}/export?format=md`;
      return;
    }
    const blob = new Blob([`# ${article.title}\n\n## 译文\n\n${article.target.text}\n\n---\n\n## 原文\n\n${article.source.text}\n`], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `${article.title || 'lingualens'}.md`; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  function downloadWord() {
    const article = state.article;
    if (!article?.id) { toast('还没有可导出的译文。', 'error'); return; }
    window.location.href = `/api/history/${encodeURIComponent(article.id)}/export?format=docx`;
  }

  function setReadingScale(scale) {
    state.readingScale = Math.min(1.3, Math.max(0.85, Math.round(scale * 100) / 100));
    const pane = $('.result-pane');
    if (pane) pane.style.setProperty('--reading-scale', state.readingScale);
    const label = $('#font-value');
    if (label) label.textContent = `${Math.round(state.readingScale * 100)}%`;
    try { localStorage.setItem('ll.fontScale', String(state.readingScale)); } catch { /* */ }
  }

  // ---------------------------------------------------------------- compare reader
  function compareHTML() {
    return `<section class="compare-page">
      <div class="compare-breadcrumb"><a href="/" data-link>翻译台</a><span>/</span><span>对照阅读</span></div>
      <div id="compare-root">
        <div class="compare-loading"><span class="spinner"></span><span>正在铺开原文与译文…</span></div>
      </div>
    </section>`;
  }

  async function afterCompare() {
    const root = $('#compare-root');
    if (!root) return;
    const params = new URLSearchParams(location.search);
    const id = params.get('id');
    let article = null;
    try {
      if (id) {
        const data = await api(`/api/history/${encodeURIComponent(id)}`);
        article = data.article;
      } else if (state.article?.id) {
        article = state.article;
      } else {
        const latest = await api('/api/history?limit=1');
        const first = (latest.items || [])[0];
        if (first) {
          const data = await api(`/api/history/${encodeURIComponent(first.id)}`);
          article = data.article;
        }
      }
    } catch (err) {
      root.innerHTML = `<div class="empty-page"><div class="glyph">?</div><h2>这篇文章没找回来</h2><p>${esc(err.message)}</p><a class="btn btn-primary" href="/" data-link>回到翻译台</a></div>`;
      return;
    }
    if (!article) {
      root.innerHTML = `<div class="empty-page compare-empty"><div class="glyph">读</div><h2>还没有可以对照的文章</h2><p>先去翻译台翻一篇，再回来逐句读原文和译文。</p><a class="btn btn-primary" href="/" data-link>去翻译第一篇 ${icon('arrow', 13)}</a></div>`;
      return;
    }
    state.article = article;
    state.compareView = state.compareView || 'translation';
    renderCompare(article);
    if (state.scrollBlock) {
      const blockId = state.scrollBlock;
      state.scrollBlock = null;
      requestAnimationFrame(() => {
        const target = document.querySelector(`[data-block="${CSS.escape(blockId)}"]`);
        if (target) {
          target.scrollIntoView({ block: 'center', behavior: 'smooth' });
          target.classList.add('is-target');
          setTimeout(() => target.classList.remove('is-target'), 1800);
        }
      });
    }
  }

  function langTag(code) {
    const value = String(code || '').toLowerCase();
    if (value.startsWith('zh')) return 'zh-Hans';
    if (value === 'ja') return 'ja';
    if (value === 'ko') return 'ko';
    if (value === 'fr') return 'fr';
    if (value === 'de') return 'de';
    if (value === 'es') return 'es';
    if (value === 'ru') return 'ru';
    return 'en';
  }

  function tokenizeHTML(text, lang) {
    const raw = String(text || '');
    if (!raw) return '';
    let segmenter = null;
    try { segmenter = new Intl.Segmenter(langTag(lang), { granularity: 'word' }); } catch { /* older browser */ }
    if (!segmenter) {
      return esc(raw).replace(/([A-Za-z][A-Za-z'’-]*|[\u3400-\u9fff\u3040-\u30ff]+)/g, (word) => `<span class="word-token" data-word="${attr(word)}" data-lang="${attr(lang)}">${esc(word)}</span>`);
    }
    let result = '';
    for (const part of segmenter.segment(raw)) {
      const value = part.segment;
      if (!value) continue;
      if (part.isWordLike && value.length <= 64) {
        result += `<span class="word-token" data-word="${attr(value)}" data-lang="${attr(lang)}" tabindex="0" role="button">${esc(value)}</span>`;
      } else {
        result += esc(value).replace(/\n/g, '<br>');
      }
    }
    return result;
  }

  function compareStreamHTML(article, side) {
    const blocks = (article.target?.blocks || []);
    const lang = side === 'source' ? article.source?.lang : article.target?.lang;
    return blocks.map((block, index) => {
      const text = side === 'source' ? block.source : block.target;
      if (!text) return '';
      const type = block.type || 'paragraph';
      const context = attr(String(text).slice(0, 240));
      if (type === 'code') {
        return `<div class="cmp-line cmp-code" data-block="${attr(block.id || index)}"><span class="cmp-no">${String(index + 1).padStart(2, '0')}</span><pre>${esc(text)}</pre></div>`;
      }
      const tag = type === 'heading' ? 'h3' : type === 'quote' ? 'blockquote' : 'p';
      return `<div class="cmp-line cmp-${attr(type)}" data-block="${attr(block.id || index)}" data-context="${context}">
        <span class="cmp-no">${String(index + 1).padStart(2, '0')}</span>
        <${tag} class="cmp-text">${tokenizeHTML(text, lang)}</${tag}>
      </div>`;
    }).join('');
  }

  function compareGrammarHTML(article) {
    const points = article.grammar?.points || [];
    if (!points.length) return `<div class="cmp-side-empty"><span class="glyph-sm">法</span><p>这篇文章没有识别到明显的语法点。</p><a class="btn btn-sm btn-ghost" href="/grammar" data-link>去语法索引 ${icon('arrow', 12)}</a></div>`;
    return `<div class="cmp-grammar-list">${points.map((point) => `
      <a class="cmp-grammar-card" href="/grammar/${encodeURIComponent(point.id)}?from=${encodeURIComponent(article.id)}" data-link>
        <div class="cg-top"><span class="cg-cat">${esc(point.category || '语法')}</span><span class="cg-count">${point.count || 1} 处</span></div>
        <h4>${esc(point.title)}<small>${esc(point.english || '')}</small></h4>
        <p>${esc(point.summary || '')}</p>
        <span class="cg-link">查看完整讲解 ${icon('arrow', 12)}</span>
      </a>`).join('')}</div>`;
  }

  function compareWordsHTML() {
    if (!state.wordHistory.length) {
      return `<div class="cmp-side-empty"><span class="glyph-sm">词</span><p>在左边原文或右边译文里点一个词，这里会记住你查过的词。</p></div>`;
    }
    return `<div class="cmp-word-list">${state.wordHistory.map((item, index) => `
      <button type="button" class="cmp-word-card" data-action="reopen-word" data-index="${index}">
        <span class="cw-word">${esc(item.word)}</span>
        ${item.phonetic ? `<span class="cw-phon">/${esc(item.phonetic)}/</span>` : ''}
        <span class="cw-pos">${esc((item.pos || []).slice(0, 2).join(' · '))}</span>
        <span class="cw-first">${esc(item.meanings?.[0]?.text || '')}</span>
      </button>`).join('')}</div>`;
  }

  function compareRightHTML(article) {
    if (state.compareView === 'grammar') return compareGrammarHTML(article);
    if (state.compareView === 'words') return compareWordsHTML();
    return compareStreamHTML(article, 'target');
  }

  function renderCompare(article) {
    const root = $('#compare-root');
    if (!root) return;
    const stats = article.source?.stats || {};
    const points = article.grammar?.points?.length || article.grammar?.summary?.total || 0;
    root.innerHTML = `
      <div class="compare-head">
        <div class="compare-title-row">
          <div>
            <h1>${esc(article.title || '未命名文章')}</h1>
            <p>${esc(article.source?.label || article.source?.lang || '原文')} <span class="arr">→</span> ${esc(article.target?.label || article.target?.lang || '译文')} ｜ ${fmtNumber(stats.paragraphs || 0)} 段 ｜ ${fmtNumber(points)} 个语法点</p>
          </div>
          <div class="compare-actions">
            <a class="btn btn-sm btn-ghost" href="/" data-link>${icon('arrowLeft', 13)} 回翻译台</a>
            <button class="btn btn-sm btn-ghost" data-action="download-word">${icon('file', 13)} Word</button>
            <button class="btn btn-sm btn-ghost" data-action="copy-link">${icon('link', 13)} 复制链接</button>
          </div>
        </div>
        <div class="compare-tip">${icon('spark', 12)} 点击任意单词，查看释义、词性和例句；原文与译文各自独立成页。</div>
      </div>
      <div class="compare-columns">
        <section class="cmp-col cmp-left" aria-label="原文">
          <div class="cmp-col-head"><span>原文</span><span class="cmp-lang">${esc((article.source?.label || article.source?.lang || '').toUpperCase())}</span></div>
          <div class="cmp-stream">${compareStreamHTML(article, 'source')}</div>
        </section>
        <section class="cmp-col cmp-right" aria-label="译文和辅助内容">
          <div class="cmp-col-head">
            <span>译文</span>
            <div class="cmp-tabs" role="tablist">
              <button data-action="compare-tab" data-view="translation" class="${state.compareView === 'translation' ? 'is-active' : ''}">译文</button>
              <button data-action="compare-tab" data-view="grammar" class="${state.compareView === 'grammar' ? 'is-active' : ''}">语法 <b>${points}</b></button>
              <button data-action="compare-tab" data-view="words" class="${state.compareView === 'words' ? 'is-active' : ''}">查词</button>
            </div>
          </div>
          <div class="cmp-stream" id="cmp-right">${compareRightHTML(article)}</div>
        </section>
      </div>`;
  }

  function switchCompareView(view) {
    state.compareView = ['translation', 'grammar', 'words'].includes(view) ? view : 'translation';
    $$('[data-action="compare-tab"]').forEach((button) => button.classList.toggle('is-active', button.dataset.view === state.compareView));
    const right = $('#cmp-right');
    if (right) right.innerHTML = compareRightHTML(state.article);
  }

  // ---------------------------------------------------------------- word card
  function ensureWordCard() {
    if ($('#word-card')) return;
    const card = document.createElement('div');
    card.id = 'word-card';
    card.className = 'word-card';
    card.hidden = true;
    card.setAttribute('role', 'dialog');
    card.setAttribute('aria-label', '单词卡片');
    document.body.appendChild(card);
  }

  function wordCardLoading(word) {
    return `<div class="wc-head"><div><span class="wc-word">${esc(word)}</span><span class="wc-phon">查询中…</span></div><button class="wc-close" data-action="close-word" aria-label="关闭">${icon('x', 14)}</button></div>
      <div class="wc-loading"><span class="spinner"></span><span>正在查词典…</span></div>`;
  }

  function wordCardHTML(data) {
    const meanings = (data.meanings || []).map((meaning, index) => `
      <li><span class="wc-index">${index + 1}</span><span class="wc-pos">${esc(meaning.pos || '释义')}</span><span class="wc-mean">${esc(meaning.text || '')}</span></li>`).join('');
    return `<div class="wc-head">
      <div class="wc-title"><span class="wc-word">${esc(data.word)}</span>${data.phonetic ? `<span class="wc-phon">/${esc(data.phonetic)}/</span>` : ''}</div>
      <button class="wc-close" data-action="close-word" aria-label="关闭">${icon('x', 14)}</button>
    </div>
    <div class="wc-pos-row">${(data.pos || []).map((pos) => `<span class="wc-chip">${esc(pos)}</span>`).join('')}</div>
    <ol class="wc-meanings">${meanings}</ol>
    ${data.context ? `<div class="wc-context"><span>原句</span><p>${esc(data.context)}</p></div>` : ''}
    <div class="wc-foot"><span class="wc-source">释义来自 ${esc(data.source || '词典')}</span><div class="wc-actions"><button class="wc-icon" data-action="speak-word" title="朗读">${icon('speaker', 14)}</button><button class="wc-icon" data-action="copy-word" title="复制">${icon('copy', 14)}</button></div></div>`;
  }

  function positionWordCard(token) {
    const card = $('#word-card');
    if (!card || card.hidden) return;
    const rect = token.getBoundingClientRect();
    const width = card.offsetWidth || 320;
    const height = card.offsetHeight || 220;
    const gap = 10;
    const below = rect.bottom + gap;
    const above = rect.top - height - gap;
    const useAbove = below + height > window.innerHeight - 12 && above > 8;
    const top = Math.max(72, useAbove ? above : below);
    const left = Math.min(window.innerWidth - width - 12, Math.max(12, rect.left + rect.width / 2 - width / 2));
    card.classList.toggle('is-above', useAbove);
    card.style.left = `${left}px`;
    card.style.top = `${top}px`;
    card.style.setProperty('--arrow-x', `${Math.min(width - 26, Math.max(26, rect.left + rect.width / 2 - left))}px`);
  }

  function closeWordCard() {
    const card = $('#word-card');
    if (card) card.hidden = true;
    state.activeWordToken?.classList.remove('is-active');
    state.activeWordToken = null;
  }

  function showWordFromData(data, anchor) {
    ensureWordCard();
    const card = $('#word-card');
    if (!card) return;
    closeWordCard();
    card.dataset.word = data.word;
    card.dataset.lang = data.lang;
    card.innerHTML = wordCardHTML(data);
    card.hidden = false;
    positionWordCard(anchor);
  }

  async function openWordCard(token) {
    ensureWordCard();
    const card = $('#word-card');
    const word = token.dataset.word || token.textContent || '';
    const lang = token.dataset.lang || 'en';
    const context = token.dataset.context || token.closest('.cmp-line')?.dataset.context || '';
    if (!word || !card) return;
    closeWordCard();
    state.activeWordToken = token;
    token.classList.add('is-active');
    card.dataset.word = word;
    card.dataset.lang = lang;
    card.hidden = false;
    card.innerHTML = wordCardLoading(word);
    positionWordCard(token);
    const key = `${lang}:${word.toLowerCase()}`;
    try {
      let data = state.wordCache.get(key);
      if (!data) {
        data = await api(`/api/word?q=${encodeURIComponent(word)}&lang=${encodeURIComponent(lang)}&context=${encodeURIComponent(context)}`);
        if (!data.ok) throw new Error(data.error || '没有找到释义');
        state.wordCache.set(key, data);
      }
      if (!card.hidden) {
        card.innerHTML = wordCardHTML(data);
        state.wordHistory = [data, ...state.wordHistory.filter((item) => !(item.word === data.word && item.lang === data.lang))].slice(0, 12);
        requestAnimationFrame(() => positionWordCard(token));
        if (state.compareView === 'words' && $('#cmp-right')) $('#cmp-right').innerHTML = compareWordsHTML();
      }
    } catch (err) {
      if (!card.hidden) {
        card.innerHTML = `<div class="wc-head"><div><span class="wc-word">${esc(word)}</span></div><button class="wc-close" data-action="close-word" aria-label="关闭">${icon('x', 14)}</button></div><div class="wc-error">${esc(err.message || '查询失败')}<br><span>可以试试更短的词，或检查网络。</span></div>`;
        requestAnimationFrame(() => positionWordCard(token));
      }
    }
  }

  function speakWord() {
    const card = $('#word-card');
    const word = card?.dataset.word;
    if (!word || !('speechSynthesis' in window)) { toast('当前浏览器不支持朗读。', 'error'); return; }
    const utterance = new SpeechSynthesisUtterance(word);
    utterance.lang = card?.dataset.lang === 'zh' ? 'zh-CN' : card?.dataset.lang === 'ja' ? 'ja-JP' : card?.dataset.lang === 'fr' ? 'fr-FR' : 'en-US';
    speechSynthesis.cancel();
    speechSynthesis.speak(utterance);
  }

  // ---------------------------------------------------------------- grammar index
  function grammarIndexHTML() {
    const stats = state.health?.grammar || {};
    return `<section class="page-hero">
      <div>
        <p class="eyebrow">GRAMMAR ATLAS</p>
        <h1>语法的骨架，<br>值得单独看。</h1>
        <p class="lede">${stats.total || 106} 个语法点，覆盖英语、日语、中文与另外五种语言。每一条都有结构公式、语感解释、例句、易错点和外部权威参考。</p>
      </div>
      <div class="page-hero-stats">
        <div class="big-stat"><strong>${stats.total || 106}</strong><span>语法条目</span></div>
        <div class="big-stat"><strong>${Object.keys(stats.byLanguage || {}).length || 8}</strong><span>语言</span></div>
      </div>
    </section>
    <div class="index-layout">
      <aside class="filter-panel">
        <div class="search-box">${icon('search', 15)}<input id="grammar-search" type="search" placeholder="搜语法名、公式、用法…" autocomplete="off" /></div>
        <div class="filter-group"><h4>语言</h4><div class="filter-list" id="lang-filters"></div></div>
        <div class="filter-group"><h4>类别</h4><div class="filter-list" id="cat-filters"></div></div>
        <p class="filter-note">点进任意一条，能看到完整讲解、文中例句和外部词典/语法站链接。</p>
      </aside>
      <section>
        <div class="index-toolbar">
          <span class="result-count"><strong id="grammar-result-count">${stats.total || 106}</strong> 条语法</span>
          <span class="muted" style="font-size:10px">每条都可独立打开、复制链接</span>
          <div class="select-wrap select-sm sort"><select id="grammar-sort"><option value="default">按语言与类别</option><option value="level">按难度</option><option value="name">按名称</option></select></div>
        </div>
        <div class="grammar-grid" id="grammar-grid">${Array.from({ length: 6 }).map(() => `<div class="grammar-card skeleton-card"><div class="skeleton-line" style="width:35%;height:10px"></div><div class="skeleton-line title" style="width:60%;margin-top:12px"></div><div class="skeleton-line"></div><div class="skeleton-line"></div></div>`).join('')}</div>
      </section>
    </div>`;
  }

  async function afterGrammarIndex() {
    try {
      if (!state.library) {
        const data = await api('/api/grammar');
        state.library = data.items || [];
        state.libraryMap = Object.fromEntries(state.library.map((e) => [e.id, e]));
      }
      renderGrammarFilters();
      applyGrammarFilters();
      $('#grammar-search')?.addEventListener('input', debounce((e) => {
        state.grammarFilters.q = e.target.value.trim();
        applyGrammarFilters();
      }, 140));
      $('#grammar-sort')?.addEventListener('change', applyGrammarFilters);
    } catch (err) {
      const grid = $('#grammar-grid');
      if (grid) grid.innerHTML = `<div class="empty-index"><h3>语法库没加载出来</h3><p>${esc(err.message)}</p></div>`;
    }
  }

  function renderGrammarFilters() {
    const langFilters = $('#lang-filters');
    const catFilters = $('#cat-filters');
    if (!langFilters || !catFilters) return;
    const stats = state.health?.grammar || {};
    const byLang = stats.byLanguage || {};
    const byCat = stats.byCategory || {};
    const langNames = { en: '英语', ja: '日语', zh: '中文', ko: '韩语', fr: '法语', de: '德语', es: '西班牙语', ru: '俄语' };
    const languages = ['', ...Object.keys(byLang).sort((a, b) => (byLang[b] || 0) - (byLang[a] || 0))];
    langFilters.innerHTML = languages.map((code) => `<button class="filter-btn ${state.grammarFilters.lang === code ? 'is-active' : ''}" data-filter="lang" data-value="${attr(code)}">${code ? esc(langNames[code] || code) : '全部'}<span class="filter-count">${code ? byLang[code] || 0 : stats.total || 0}</span></button>`).join('');
    const categories = ['', ...Object.keys(byCat).sort((a, b) => (byCat[b] || 0) - (byCat[a] || 0))];
    catFilters.innerHTML = categories.map((cat) => `<button class="filter-btn ${state.grammarFilters.category === cat ? 'is-active' : ''}" data-filter="category" data-value="${attr(cat)}">${cat ? esc(cat) : '全部'}</button>`).join('');
  }

  function applyGrammarFilters() {
    if (!state.library) return;
    const f = state.grammarFilters;
    const sort = $('#grammar-sort')?.value || 'default';
    let items = state.library.filter((e) => {
      if (f.lang && e.language !== f.lang) return false;
      if (f.category && e.category !== f.category) return false;
      if (f.q) {
        const hay = `${e.title} ${e.english} ${e.summary} ${e.formula} ${e.category}`.toLowerCase();
        if (!hay.includes(f.q.toLowerCase())) return false;
      }
      return true;
    });
    if (sort === 'level') items = [...items].sort((a, b) => String(a.cefr).localeCompare(String(b.cefr)));
    else if (sort === 'name') items = [...items].sort((a, b) => a.title.localeCompare(b.title, 'zh'));
    const grid = $('#grammar-grid');
    const count = $('#grammar-result-count');
    if (count) count.textContent = items.length;
    if (!grid) return;
    if (!items.length) {
      grid.innerHTML = `<div class="empty-index"><h3>没有找到这条语法</h3><p>换一个关键词，或点“全部”重置筛选。</p></div>`;
      return;
    }
    const langNames = { en: '英语', ja: '日语', zh: '中文', ko: '韩语', fr: '法语', de: '德语', es: '西班牙语', ru: '俄语' };
    grid.innerHTML = items.map((e, i) => `<a class="grammar-card" href="/grammar/${encodeURIComponent(e.id)}" data-link style="animation-delay:${Math.min(i, 12) * 18}ms">
      <div class="grammar-card-top"><span class="lang">${esc((langNames[e.language] || e.language).toUpperCase())}</span><span class="chip outline">${esc(e.cefr)}</span><span class="spacer"></span><span class="chip">${esc(e.category)}</span></div>
      <h3>${esc(e.title)}</h3>
      <p class="en">${esc(e.english)}</p>
      <p class="sum">${esc(e.summary)}</p>
      <div class="formula">${esc(e.formula)}</div>
      <span class="card-foot">查看完整讲解 ${icon('arrow', 12)}</span>
    </a>`).join('');
    // active filter buttons
    $$('[data-filter]').forEach((btn) => {
      const current = btn.dataset.filter === 'lang' ? f.lang : f.category;
      btn.classList.toggle('is-active', btn.dataset.value === current);
    });
  }

  // ---------------------------------------------------------------- grammar detail
  function grammarDetailSkeleton(id) {
    return `<div class="detail-top"><div class="breadcrumb"><a href="/grammar" data-link>语法索引</a><span class="sep">/</span><span>加载中…</span></div></div>
      <div class="detail-hero"><div><div class="skeleton-line" style="width:30%;height:12px"></div><div class="skeleton-line title" style="width:58%;height:40px;margin-top:18px"></div><div class="skeleton-line" style="width:42%;margin-top:10px"></div><div class="skeleton-line" style="width:75%;margin-top:20px"></div></div><div class="formula-card"><div class="skeleton-line" style="width:50%"></div><div class="skeleton-line" style="margin-top:12px"></div></div></div>`;
  }

  async function afterGrammarDetail(id, query) {
    try {
      let entry = state.libraryMap[id];
      if (!entry) {
        const data = await api(`/api/grammar/${encodeURIComponent(id)}`);
        entry = data.grammar;
        state.libraryMap[id] = entry;
      }
      state.currentGrammar = entry;
      const from = query.get('from');
      let context = null;
      if (from) {
        if (state.article?.id === from) context = state.article;
        else {
          try { context = (await api(`/api/history/${encodeURIComponent(from)}`)).article; } catch { context = null; }
        }
      } else if (state.article && (state.article.grammar?.points || []).some((p) => p.id === id)) {
        context = state.article;
      }
      state.contextArticle = context;
      $('#main').innerHTML = grammarDetailHTML(entry, context);
      document.title = `${entry.title} · 语法讲解 · 语镜`;
      window.scrollTo({ top: 0, behavior: 'instant' });
      // related cards need the library
      if (!state.library) {
        api('/api/grammar').then((data) => {
          state.library = data.items || [];
          state.libraryMap = Object.fromEntries(state.library.map((e) => [e.id, e]));
          const related = $('#related-grid');
          if (related) related.innerHTML = relatedHTML(entry);
        }).catch(() => {});
      }
    } catch (err) {
      $('#main').innerHTML = `<div class="empty-page"><div class="glyph">?</div><h2>这条语法没有找到</h2><p>${esc(err.message)}</p><a class="btn btn-primary" href="/grammar" data-link>回到语法索引</a></div>`;
    }
  }

  function grammarDetailHTML(entry, context) {
    const point = context?.grammar?.points?.find((p) => p.id === entry.id);
    const occurrences = point?.occurrences || [];
    const langNames = { en: '英语', ja: '日语', zh: '中文', ko: '韩语', fr: '法语', de: '德语', es: '西班牙语', ru: '俄语' };
    const sections = (entry.sections || []).map((sec, i) => `<section class="content-section">
      <h2><span class="num">${pad(i + 1)}</span>${esc(sec.heading || '用法')}</h2>
      <p>${esc(sec.body || '')}</p>
      ${sec.bullets?.length ? `<ul class="bullet-list">${sec.bullets.map((b) => `<li>${esc(b)}</li>`).join('')}</ul>` : ''}
    </section>`).join('');
    const examples = (entry.examples || []).map((ex, i) => `<div class="example-card"><span class="ex-no">${pad(i + 1)}</span><div><p class="ex-src">${esc(ex.source)}</p><p class="ex-tr">${esc(ex.translation)}</p></div></div>`).join('');
    const pitfalls = (entry.pitfalls || []).map((p) => `<div class="pitfall-card">
      <div class="pitfall-cell bad"><span class="tag">${icon('x', 10)} 容易写成</span><p>${esc(p.wrong)}</p></div>
      <div class="pitfall-cell good"><span class="tag">${icon('check', 10)} 更自然</span><p>${esc(p.right)}</p></div>
      <div class="pitfall-why">${esc(p.why)}</div>
    </div>`).join('');
    const links = (entry.links || []).map((l) => `<a class="side-link" href="${attr(safeUrl(l.url))}" target="_blank" rel="noopener noreferrer">${icon('external', 12)}<span>${esc(l.label)}</span><span class="site">${esc(l.site || '')}</span></a>`).join('');
    const occHTML = occurrences.length ? occurrences.map((o, i) => `<div class="occurrence"><div class="occ-label">OCCURRENCE ${pad(i + 1)} · 第 ${o.blockId || '—'} 段</div><p>${esc(o.sentence)}</p></div>`).join('') : `<p class="side-empty">从翻译结果点进来，就能看到这个语法点在本文中的具体位置和例句。</p>`;
    const related = relatedHTML(entry);
    const back = context ? `<a class="btn btn-sm btn-ghost" href="/" data-link data-action="back-to-article" data-block="${attr(occurrences[0]?.blockId || '')}">${icon('arrowLeft', 13)} 回到文章</a>` : '';
    return `<div class="detail-top">
      <div class="breadcrumb"><a href="/grammar" data-link>语法索引</a><span class="sep">/</span><span>${esc(langNames[entry.language] || entry.language)}</span><span class="sep">/</span><span>${esc(entry.category)}</span></div>
    </div>
    <header class="detail-hero">
      <div>
        <div class="detail-kicker"><span class="chip jade">${esc(langNames[entry.language] || entry.language)}</span><span class="chip">${esc(entry.category)}</span><span class="chip gold">${esc(entry.cefr)}</span>${entry.source === 'ai' ? '<span class="chip coral">AI 补充</span>' : ''}</div>
        <h1>${esc(entry.title)}</h1>
        <p class="en-title">${esc(entry.english)}</p>
        <p class="detail-summary">${esc(entry.summary)}</p>
        <div class="detail-actions">${back}<button class="btn btn-sm" data-action="copy-link">${icon('link', 13)} 复制本页链接</button><a class="btn btn-sm btn-ghost" href="/grammar" data-link>${icon('layers', 13)} 语法索引</a></div>
      </div>
      <div class="formula-card">
        <div class="label">STRUCTURE / 结构</div>
        <div class="formula">${esc(entry.formula)}</div>
        <div class="mini-note">${esc(entry.english)} · ${esc(entry.category)} · ${esc(entry.cefr)}</div>
      </div>
    </header>
    <div class="detail-layout">
      <div class="detail-main">
        ${sections}
        ${examples ? `<section class="content-section"><h2><span class="num">例</span>文中可以这样用</h2><div class="example-list">${examples}</div></section>` : ''}
        ${pitfalls ? `<section class="content-section"><h2><span class="num">!</span>容易踩的坑</h2><div class="pitfall-grid">${pitfalls}</div></section>` : ''}
        ${related ? `<section class="content-section"><h2><span class="num">↗</span>顺藤摸瓜</h2><div class="related-grid" id="related-grid">${related}</div></section>` : '<div id="related-grid"></div>'}
      </div>
      <aside class="detail-side">
        <div class="side-card"><h3>在文章中出现</h3>${occHTML}${context ? `<a class="side-link" href="/" data-link data-action="back-to-article" data-block="${attr(occurrences[0]?.blockId || '')}">${icon('arrowLeft', 12)} <span>回到《${esc(context.title)}》</span></a>` : ''}</div>
        <div class="side-card"><h3>权威参考</h3>${links || '<p class="side-empty">这条由 AI 补充，暂无固定外链。</p>'}</div>
        <div class="side-card"><h3>关于这个语法点</h3>
          <div class="side-link">${icon('globe', 12)}<span>语言</span><span class="site">${esc(langNames[entry.language] || entry.language)}</span></div>
          <div class="side-link">${icon('book', 12)}<span>难度</span><span class="site">${esc(entry.cefr)}</span></div>
          <div class="side-link">${icon('layers', 12)}<span>类别</span><span class="site">${esc(entry.category)}</span></div>
        </div>
      </aside>
    </div>`;
  }

  function relatedHTML(entry) {
    const items = (entry.related || []).map((id) => state.libraryMap[id]).filter(Boolean);
    if (!items.length) return '';
    const langNames = { en: '英语', ja: '日语', zh: '中文', ko: '韩语', fr: '法语', de: '德语', es: '西班牙语', ru: '俄语' };
    return items.map((e) => `<a class="related-card" href="/grammar/${encodeURIComponent(e.id)}" data-link><span class="rc-cat">${esc(langNames[e.language] || e.language)} · ${esc(e.category)}</span><h4>${esc(e.title)}</h4><p>${esc(e.english)}</p></a>`).join('');
  }

  // ---------------------------------------------------------------- batch
  function batchHTML() {
    return `<section class="batch-hero">
      <div>
        <p class="eyebrow">FOLDER TRANSLATION</p>
        <h1>把一整个文件夹，<br>交给语镜。</h1>
        <p>递归扫描子文件夹，自动识别语言与格式，逐篇翻译，输出「译文 + 原文 + 语法索引」的双语 Markdown。整个过程在本机完成。</p>
        <div class="format-strip">${['TXT', 'Markdown', 'PDF', 'Word', 'PPT', 'Excel', 'EPUB', 'HTML', 'SRT', 'VTT', 'CSV', 'RTF'].map((f) => `<span class="chip">${f}</span>`).join('')}</div>
      </div>
      <div class="page-hero-stats">
        <div class="big-stat"><strong>14</strong><span>输入格式</span></div>
        <div class="big-stat"><strong>∞</strong><span>递归层级</span></div>
      </div>
    </section>
    <div class="batch-shell">
      <section class="panel-card">
        <div class="panel-card-head"><span class="step">1</span><h2>选择文件夹</h2><span class="right chip">本地路径</span></div>
        <div class="panel-card-body">
          <div class="folder-input">
            <input id="batch-folder" type="text" placeholder="D:\文章\待翻译" autocomplete="off" spellcheck="false" />
            <button class="btn" data-action="browse-folder">${icon('folder', 14)} 浏览</button>
          </div>
          <div class="folder-tips"><span>${icon('check', 11)} 自动跳过隐藏文件</span><span>${icon('check', 11)} 保留原目录结构</span><span>${icon('check', 11)} 输出到「语镜译文」</span></div>
          <div class="batch-controls">
            <div class="field"><label for="batch-target">目标语言</label><div class="select-wrap"><select id="batch-target">${targetLangOptions(state.targetLang)}</select></div></div>
            <div class="field"><label for="batch-provider">翻译引擎</label><div class="select-wrap"><select id="batch-provider">${providerOptions(state.provider)}</select></div></div>
            <button class="btn" data-action="scan-folder">${icon('scan', 14)} 扫描文章</button>
          </div>
          <div class="scan-result" id="scan-result"></div>
          <div class="privacy-note">${icon('shield', 12)}<span>文件只在本机读取。使用 AI 精准模式时，正文会发送到你配置的模型服务；使用免费引擎时，正文会发送到对应翻译服务。</span></div>
        </div>
      </section>
      <section class="panel-card">
        <div class="panel-card-head"><span class="step">2</span><h2>批量任务</h2><span class="right chip" id="job-head-chip">等待扫描</span></div>
        <div class="panel-card-body" id="job-panel">${jobPanelHTML()}</div>
      </section>
    </div>
    <section class="recent-jobs" id="recent-jobs"></section>`;
  }

  function afterBatch() {
    const folder = $('#batch-folder');
    if (folder && state.batchFolder) folder.value = state.batchFolder;
    if (folder) folder.addEventListener('keydown', (e) => { if (e.key === 'Enter') scanFolder(); });
    if (state.batchScan) renderScanResult();
    if (state.batchJob) {
      renderJobPanel(state.batchJob);
      if (!['completed', 'completed_with_errors', 'cancelled', 'failed'].includes(state.batchJob.status)) pollBatch(state.batchJob.id);
    }
    loadRecentJobs();
  }

  function jobPanelHTML() {
    if (!state.batchJob) {
      return `<div class="job-empty"><div class="ring">${icon('layers', 25)}</div><h3>还没有开始批译</h3><p>先在左侧选择一个文件夹。扫描后，你能看到文件数量、格式和输出位置，再决定是否开始。</p></div>`;
    }
    const job = state.batchJob;
    const total = job.total || 0;
    const done = (job.done || 0) + (job.failed || 0);
    const pct = total ? Math.round((done / total) * 100) : 0;
    const running = !['completed', 'completed_with_errors', 'cancelled', 'failed'].includes(job.status);
    const statusLabel = { queued: '排队中', running: '翻译中', cancelling: '正在停止', completed: '已完成', completed_with_errors: '完成（有失败）', cancelled: '已停止', failed: '失败' }[job.status] || job.status;
    const files = (job.files || []).map((f) => `<div class="job-file ${esc(f.status)}">
      <span class="state">${f.status === 'done' ? icon('check', 8) : f.status === 'failed' ? icon('x', 8) : ''}</span>
      <span class="name" title="${attr(f.relative)}">${esc(f.relative)}${f.error ? `<span class="error"> · ${esc(f.error)}</span>` : ''}</span>
      <span class="meta">${f.status === 'done' ? `${f.grammarCount || 0} 语法 · ${esc(f.sourceLangLabel || '')}` : f.status === 'failed' ? '失败' : f.status === 'running' ? '处理中' : esc(f.format || '')}</span>
    </div>`).join('');
    return `<div class="job-live is-on">
      <div class="job-head"><span class="job-status"><span class="pulse"></span>${esc(statusLabel)}</span><span class="job-id">${esc(job.id || '')}</span></div>
      <div class="progress-wrap">
        <div class="progress-meta"><strong>${done}<span style="font-size:13px;color:var(--muted)"> / ${total}</span></strong><span>篇</span><span class="pct">${pct}%</span></div>
        <div class="progress-bar"><span style="width:${pct}%"></span></div>
        <div class="job-current">${job.current ? `正在处理：${esc(job.current)}` : (running ? '准备下一批…' : `${esc(job.targetLabel || '')} · 输出到 ${esc(job.outputDir || '')}`)}</div>
      </div>
      <div class="job-files">${files || '<div class="job-file"><span></span><span class="name">没有文件</span><span></span></div>'}</div>
      ${job.warnings?.length ? `<div class="warning-list" style="margin-top:10px">${job.warnings.slice(0, 3).map((w) => `<div class="warning-item">${icon('alert', 12)}<span>${esc(w)}</span></div>`).join('')}</div>` : ''}
      <div class="job-actions">
        ${running ? `<button class="btn btn-sm" data-action="cancel-batch">${icon('x', 12)} 停止任务</button>` : ''}
        ${!running ? `<button class="btn btn-sm btn-primary" data-action="download-zip">${icon('download', 12)} 下载 ZIP</button>` : ''}
        <button class="btn btn-sm" data-action="reveal-output">${icon('folder', 12)} 打开输出文件夹</button>
        ${!running ? `<button class="btn btn-sm btn-ghost" data-action="new-batch">${icon('refresh', 12)} 新任务</button>` : ''}
      </div>
    </div>`;
  }

  function renderJobPanel(job) {
    state.batchJob = job;
    const panel = $('#job-panel');
    if (panel) panel.innerHTML = jobPanelHTML();
    const chip = $('#job-head-chip');
    if (chip) chip.textContent = { running: '运行中', completed: '已完成', completed_with_errors: '有失败', cancelled: '已停止' }[job.status] || '任务';
  }

  async function scanFolder() {
    const input = $('#batch-folder');
    const folder = input?.value.trim();
    if (!folder) { toast('先选择或粘贴一个文件夹路径。', 'error'); return; }
    const btn = $('[data-action="scan-folder"]');
    if (btn) { btn.disabled = true; btn.innerHTML = `<span class="spinner"></span> 扫描中`; }
    try {
      const data = await api('/api/batch/scan', { method: 'POST', body: { folder } });
      state.batchFolder = folder;
      state.batchScan = data;
      renderScanResult();
      if (!data.count) toast('这个文件夹里没有找到支持的文章。', 'error');
      else toast(`找到 ${data.count} 篇文章`, 'success');
    } catch (err) {
      toast(err.message || '扫描失败', 'error');
    } finally {
      if (btn) { btn.disabled = false; btn.innerHTML = `${icon('scan', 14)} 扫描文章`; }
    }
  }

  function renderScanResult() {
    const data = state.batchScan;
    const box = $('#scan-result');
    if (!box || !data) return;
    box.classList.add('is-on');
    const formats = (data.formats || []).map((f) => `<span class="chip">${esc(f.toUpperCase())}</span>`).join('');
    box.innerHTML = `<div class="scan-summary"><div class="big">${data.count}<small>篇</small></div><div style="font-size:10px;color:var(--muted)">${fmtBytes(data.totalBytes)} · ${formats}</div><div class="out-path" title="${attr(data.outputDir)}">${esc(data.outputDir)}</div></div>
      <div class="file-list">${data.files.slice(0, 60).map((f) => `<div class="file-row"><span class="fmt">${esc(f.format)}</span><span class="name" title="${attr(f.relative)}">${esc(f.relative)}</span><span class="size">${fmtBytes(f.size)}</span></div>`).join('')}${data.files.length > 60 ? `<div class="file-row"><span></span><span class="name">还有 ${data.files.length - 60} 个文件…</span><span></span></div>` : ''}</div>
      <div class="batch-controls" style="margin-top:12px"><button class="btn btn-primary" data-action="start-batch">${icon('play', 13)} 开始翻译这 ${data.count} 篇</button></div>`;
  }

  async function startBatch() {
    if (!state.batchScan?.count) { toast('先扫描文件夹。', 'error'); return; }
    const folder = $('#batch-folder')?.value.trim() || state.batchScan.folder;
    const target = $('#batch-target')?.value || state.targetLang;
    const provider = $('#batch-provider')?.value || state.provider;
    const btn = $('[data-action="start-batch"]');
    if (btn) { btn.disabled = true; btn.innerHTML = `<span class="spinner" style="border-color:rgba(255,255,255,.35);border-top-color:#fff"></span> 创建任务`; }
    try {
      const data = await api('/api/batch/start', { method: 'POST', body: { folder, target, provider } });
      state.batchJob = data.job;
      renderJobPanel(data.job);
      pollBatch(data.job.id);
      toast(`任务已开始 · ${data.job.total} 篇`, 'success');
    } catch (err) {
      toast(err.message || '任务创建失败', 'error');
      if (btn) { btn.disabled = false; btn.innerHTML = `${icon('play', 13)} 开始翻译`; }
    }
  }

  function clearBatchTimer() {
    if (state.batchTimer) { clearInterval(state.batchTimer); state.batchTimer = null; }
  }

  function pollBatch(id) {
    clearBatchTimer();
    state.batchTimer = setInterval(async () => {
      if (state.route !== '/batch') { clearBatchTimer(); return; }
      try {
        const data = await api(`/api/batch/${encodeURIComponent(id)}`);
        const job = data.job;
        renderJobPanel(job);
        if (['completed', 'completed_with_errors', 'cancelled', 'failed'].includes(job.status)) {
          clearBatchTimer();
          toast(job.status === 'completed' ? `批译完成 · ${job.done} 篇` : `任务结束 · 成功 ${job.done} / 失败 ${job.failed}`, job.failed ? 'error' : 'success');
          loadRecentJobs();
        }
      } catch (err) {
        clearBatchTimer();
        toast(err.message || '无法获取任务状态', 'error');
      }
    }, 1200);
  }

  async function loadRecentJobs() {
    try {
      const data = await api('/api/batch');
      const items = data.items || [];
      const box = $('#recent-jobs');
      if (!box || !items.length) return;
      box.innerHTML = `<div class="section-head"><h2>最近的批译</h2><p>任务记录保存在本地</p><span class="line"></span></div>
        ${items.map((j) => `<div class="recent-job-row"><span class="folder" title="${attr(j.folder)}">${esc(j.folder)}</span><span class="time">${esc(timeAgo(j.createdAt))}</span><span class="ratio">${j.done}/${j.total}</span><button class="btn btn-sm" data-load-batch="${attr(j.id)}">查看</button></div>`).join('')}`;
    } catch { /* optional */ }
  }

  async function loadBatch(id) {
    try {
      const data = await api(`/api/batch/${encodeURIComponent(id)}`);
      state.batchJob = data.job;
      state.batchScan = { folder: data.job.folder, outputDir: data.job.outputDir, count: data.job.total, totalBytes: data.job.bytes, formats: [], files: data.job.files || [] };
      renderJobPanel(data.job);
      if (!['completed', 'completed_with_errors', 'cancelled', 'failed'].includes(data.job.status)) pollBatch(id);
    } catch (err) { toast(err.message, 'error'); }
  }

  // ---------------------------------------------------------------- history
  function historyHTML() {
    return `<section class="page-hero">
      <div><p class="eyebrow">READING ARCHIVE</p><h1>读过的，都留在这里。</h1><p class="lede">最近 200 篇翻译记录保存在本机 SQLite 中。可以重新打开、导出双语 Markdown，或单独回看某个语法点。</p></div>
      <div class="page-hero-stats"><div class="big-stat"><strong id="history-total">—</strong><span>篇文章</span></div></div>
    </section>
    <div class="history-toolbar">
      <div class="search-box">${icon('search', 15)}<input id="history-search" type="search" placeholder="搜标题、原文或译文…" autocomplete="off" /></div>
      <span class="history-count" id="history-count"></span>
    </div>
    <div class="history-list" id="history-list">${Array.from({ length: 3 }).map(() => `<div class="history-card"><div></div><div><div class="skeleton-line title"></div><div class="skeleton-line"></div></div><div></div></div>`).join('')}</div>`;
  }

  async function afterHistory() {
    try {
      const data = await api('/api/history?limit=100');
      state.history = data.items || [];
      renderHistoryList();
      $('#history-search')?.addEventListener('input', debounce((e) => {
        state.historyQuery = e.target.value.trim().toLowerCase();
        renderHistoryList();
      }, 140));
    } catch (err) {
      $('#history-list').innerHTML = `<div class="empty-page"><div class="glyph">史</div><h2>历史没加载出来</h2><p>${esc(err.message)}</p></div>`;
    }
  }

  function renderHistoryList() {
    const allItems = state.history || [];
    const q = state.historyQuery;
    const items = q ? allItems.filter((item) => `${item.title} ${item.excerpt} ${item.translatedExcerpt}`.toLowerCase().includes(q)) : allItems;
    const total = $('#history-total');
    if (total) total.textContent = allItems.length;
    const count = $('#history-count');
    if (count) count.textContent = q ? `${items.length} / ${allItems.length} 篇` : `${allItems.length} 篇`;
    const list = $('#history-list');
    if (!list) return;
    if (!items.length) {
      list.innerHTML = q
        ? `<div class="empty-page"><div class="glyph">搜</div><h2>没有匹配的记录</h2><p>换一个标题、原文或译文关键词试试。</p></div>`
        : `<div class="empty-page"><div class="glyph">空</div><h2>还没有翻过一篇文章</h2><p>回到翻译台，放入第一篇。</p><a class="btn btn-primary" href="/" data-link>去翻译 ${icon('arrow', 13)}</a></div>`;
      return;
    }
    list.innerHTML = items.map((item) => {
      const d = item.createdAt ? new Date(item.createdAt) : null;
      const date = d && !Number.isNaN(d.getTime()) ? d : null;
      return `<article class="history-card" data-history-card="${attr(item.id)}">
        <div class="history-date"><strong>${date ? pad(date.getDate()) : '—'}</strong><span>${date ? `${date.getFullYear()} · ${pad(date.getMonth() + 1)}月` : ''}</span></div>
        <div class="history-main">
          <h3>${esc(item.title)}</h3>
          <div class="meta"><span class="chip">${esc(lang(item.sourceLang).short)} → ${esc(lang(item.targetLang).short)}</span><span class="chip jade">${item.grammarCount} 语法</span><span class="muted" style="font-size:9.5px">${esc(providerLabel(item.provider))} · ${esc(timeAgo(item.createdAt))}</span></div>
          <p>${esc(item.translatedExcerpt || item.excerpt)}</p>
        </div>
        <div class="history-side">
          <div class="history-actions">
            <button class="icon-btn star-btn ${item.starred ? 'is-on' : ''}" data-action="star-history" data-id="${attr(item.id)}" title="收藏" aria-label="收藏">${icon('star', 14)}</button>
            <a class="icon-btn" href="/api/history/${encodeURIComponent(item.id)}/export?format=md" title="导出 Markdown" aria-label="导出" download>${icon('download', 14)}</a>
            <button class="icon-btn" data-action="delete-history" data-id="${attr(item.id)}" title="删除" aria-label="删除">${icon('trash', 14)}</button>
          </div>
          <button class="btn btn-sm btn-ghost" data-open-history="${attr(item.id)}">打开 ${icon('arrow', 12)}</button>
        </div>
      </article>`;
    }).join('');
  }

  async function openHistory(id) {
    try {
      const data = await api(`/api/history/${encodeURIComponent(id)}`);
      state.article = data.article;
      state.draftSource = data.article.source.text;
      state.sourceLang = 'auto';
      state.targetLang = data.article.target.lang;
      state.view = 'translation';
      try { sessionStorage.setItem('ll.article', JSON.stringify(data.article)); } catch { /* */ }
      navigate('/');
    } catch (err) { toast(err.message, 'error'); }
  }

  async function deleteHistory(id) {
    if (!window.confirm('删除这条翻译记录？原文和译文会从本地历史中移除。')) return;
    try {
      await api(`/api/history/${encodeURIComponent(id)}`, { method: 'DELETE' });
      state.history = (state.history || []).filter((x) => x.id !== id);
      renderHistoryList();
      toast('已删除', 'success');
    } catch (err) { toast(err.message, 'error'); }
  }

  async function starHistory(id) {
    try {
      const data = await api(`/api/history/${encodeURIComponent(id)}/star`, { method: 'POST', body: {} });
      const item = (state.history || []).find((x) => x.id === id);
      if (item) item.starred = data.starred;
      const card = document.querySelector(`[data-history-card="${CSS.escape(id)}"] .star-btn`);
      if (card) card.classList.toggle('is-on', !!data.starred);
    } catch (err) { toast(err.message, 'error'); }
  }

  // ---------------------------------------------------------------- settings
  function openSettings() {
    const settings = state.settings || {};
    const ai = settings.ai || {};
    const keySet = !!ai.apiKeySet;
    openModal(`<div class="modal-head"><h2>设置</h2><span class="sub">只保存在本机</span><button class="icon-btn modal-close" data-action="close-modal" aria-label="关闭">${icon('x', 16)}</button></div>
      <div class="modal-body">
        <div class="modal-tabs"><button class="modal-tab is-active" data-settings-tab="engine">翻译引擎</button><button class="modal-tab" data-settings-tab="output">输出与语法</button><button class="modal-tab" data-settings-tab="about">关于</button></div>
        <div class="settings-tab-panel" data-settings-panel="engine">
          <div class="form-section">
            <h3>默认翻译引擎</h3>
            <div class="field"><label for="set-provider">新文章默认使用</label><div class="select-wrap"><select id="set-provider">${providerOptions(settings.provider || 'auto')}</select></div><span class="hint">“自动优选”会在配置了 AI Key 时优先使用 AI，否则走免费引擎。</span></div>
          </div>
          <div class="form-section">
            <h3>AI 精准模式 <span class="chip jade" style="margin-left:6px">可选</span></h3>
            <div class="callout" style="margin-bottom:14px">${icon('spark', 14)}<span>配置任意 OpenAI 兼容接口即可。AI 会按整段上下文翻译，术语和语气更稳，也能补充更深的语法讲解。</span></div>
            <div class="field-row">
              <div class="field"><label for="set-base">API Base URL</label><input id="set-base" type="url" value="${attr(ai.baseUrl || 'https://api.deepseek.com/v1')}" placeholder="https://api.deepseek.com/v1" /><span class="hint">DeepSeek 默认：https://api.deepseek.com/v1</span></div>
              <div class="field"><label for="set-model">模型</label><input id="set-model" type="text" value="${attr(ai.model || 'deepseek-chat')}" placeholder="deepseek-chat" /></div>
            </div>
            <div class="field" style="margin-top:12px"><label for="set-key">API Key</label><input id="set-key" type="password" placeholder="${keySet ? '已设置，留空则不修改' : 'sk-...'}" autocomplete="off" /><div class="key-status ${keySet ? 'ok' : ''}"><span class="dot"></span>${keySet ? `已设置 ${esc(ai.apiKeyHint || '')} · ${ai.apiKeySource === 'env' ? '来自环境变量' : '保存在本地数据库'}` : '未设置，当前使用免费引擎'}</div></div>
            <div style="display:flex;gap:8px;margin-top:12px;flex-wrap:wrap"><button class="btn btn-sm" data-action="test-ai">${icon('spark', 12)} 测试连接</button><button class="btn btn-sm btn-ghost" data-action="clear-key">清除 Key</button><a class="btn btn-sm btn-ghost" href="https://platform.deepseek.com/api_keys" target="_blank" rel="noopener noreferrer">获取 DeepSeek Key ${icon('external', 11)}</a></div>
            <div id="ai-test-result" style="margin-top:10px;font-size:10.5px"></div>
          </div>
          <div class="form-section">
            <h3>翻译偏好</h3>
            <div class="field"><label for="set-style">翻译风格</label><div class="select-wrap"><select id="set-style">
              <option value="natural" ${settings.translationStyle === 'natural' ? 'selected' : ''}>自然流畅 · 像目标语言写作</option>
              <option value="faithful" ${settings.translationStyle === 'faithful' ? 'selected' : ''}>忠实克制 · 保留原文句法</option>
              <option value="academic" ${settings.translationStyle === 'academic' ? 'selected' : ''}>正式学术 · 术语精确</option>
              <option value="literary" ${settings.translationStyle === 'literary' ? 'selected' : ''}>文学 · 保留节奏与语气</option>
            </select></div><span class="hint">AI 精准模式会按这个风格翻译；免费引擎主要依靠下方术语表。</span></div>
            <div class="field" style="margin-top:12px"><label for="set-glossary">术语表（每行：原文 = 译文）</label><textarea id="set-glossary" rows="4" placeholder="OpenAI = OpenAI&#10;LinguaLens = 语镜&#10;machine learning = 机器学习">${esc(settings.glossary || '')}</textarea><span class="hint">术语表对所有引擎生效，按行替换，适合人名、品牌、专业词。</span></div>
          </div>
        </div>
        <div class="settings-tab-panel" data-settings-panel="output" hidden>
          <div class="form-section"><h3>界面主题</h3>
            <div class="theme-grid">
              <button type="button" class="theme-choice ${state.theme === 'paper' ? 'is-active' : ''}" data-theme-choice="paper"><span class="theme-preview paper"></span><strong>纸墨</strong><small>温暖纸感 · 当前默认</small></button>
              <button type="button" class="theme-choice ${state.theme === 'night' ? 'is-active' : ''}" data-theme-choice="night"><span class="theme-preview night"></span><strong>暗夜</strong><small>深色底 · 晚上读长文</small></button>
              <button type="button" class="theme-choice ${state.theme === 'clear' ? 'is-active' : ''}" data-theme-choice="clear"><span class="theme-preview clear"></span><strong>清透</strong><small>白底细线 · 更现代</small></button>
            </div>
            <span class="hint">也可以点右上角的主题按钮，三套主题循环切换。</span>
          </div>
          <div class="form-section"><h3>语法分析</h3>
            <div class="toggle-row"><div class="text"><strong>AI 深度语法补充</strong><span>在规则识别之外，让 AI 找出进阶句式，并保存为可打开的本地讲解页。</span></div><label class="switch"><input id="set-grammar" type="checkbox" ${settings.aiGrammar !== false ? 'checked' : ''}><span class="track"></span></label></div>
            <div class="toggle-row"><div class="text"><strong>翻译记忆缓存</strong><span>相同的段落不重复请求，节省免费额度与 AI 费用。</span></div><label class="switch"><input type="checkbox" checked disabled><span class="track"></span></label></div>
          </div>
          <div class="form-section"><h3>文件夹批译</h3>
            <div class="field"><label for="set-output">输出子文件夹名</label><input id="set-output" type="text" value="${attr(settings.batchOutput || '语镜译文')}" /><span class="hint">会创建在所选的文件夹内，自动跳过自身，避免递归翻译。</span></div>
          </div>
          <div class="form-section"><h3>缓存</h3><div style="display:flex;gap:8px"><button class="btn btn-sm" data-action="clear-cache">${icon('trash', 12)} 清空翻译缓存</button></div></div>
        </div>
        <div class="settings-tab-panel" data-settings-panel="about" hidden>
          <div class="form-section"><h3>语镜 LinguaLens</h3><p style="font-size:13px;line-height:1.9;color:var(--ink-soft);margin:0 0 12px">一个本地优先的阅读工作台：多格式文章翻译、逐段对照、语法提取，以及可以独立打开的语法图谱。</p>
            <div class="side-link">${icon('layers', 12)}<span>语法库</span><span class="site">${state.health?.grammar?.total || 106} 条</span></div>
            <div class="side-link">${icon('globe', 12)}<span>版本</span><span class="site">v${esc(state.health?.version || '1.0.0')}</span></div>
            <div class="side-link">${icon('shield', 12)}<span>数据</span><span class="site">本机 SQLite</span></div>
            <div style="margin-top:14px"><button class="btn btn-sm" data-action="install-app">${icon('download', 12)} 安装到桌面</button><span class="hint" style="margin-left:8px">需要 Chrome / Edge，通过 localhost 打开</span></div>
            <div style="margin-top:10px"><button class="btn btn-sm btn-ghost" data-action="quit-app">${icon('x', 12)} 退出语镜（桌面版）</button></div>
          </div>
          <div class="callout">${icon('book', 14)}<span>翻译质量取决于引擎。免费引擎适合快速阅读；需要出版级精度时，建议配置 AI，并使用「AI 精准模式」。</span></div>
        </div>
      </div>
      <div class="modal-foot"><span class="spacer"></span><button class="btn" data-action="close-modal">取消</button><button class="btn btn-primary" data-action="save-settings">${icon('check', 14)} 保存设置</button></div>`, (modal) => {
      $$('.modal-tab', modal).forEach((tab) => tab.addEventListener('click', () => {
        $$('.modal-tab', modal).forEach((t) => t.classList.toggle('is-active', t === tab));
        $$('[data-settings-panel]', modal).forEach((p) => { p.hidden = p.dataset.settingsPanel !== tab.dataset.settingsTab; });
      }));
      state.clearKey = false;
    });
  }

  async function saveSettings() {
    const provider = $('#set-provider')?.value || 'auto';
    const ai = {
      baseUrl: $('#set-base')?.value.trim() || 'https://api.deepseek.com/v1',
      model: $('#set-model')?.value.trim() || 'deepseek-chat',
      apiKey: $('#set-key')?.value.trim() || '',
    };
    if (state.clearKey) ai.clearKey = true;
    const payload = {
      provider,
      ai,
      aiGrammar: $('#set-grammar') ? $('#set-grammar').checked : true,
      translationStyle: $('#set-style')?.value || 'natural',
      glossary: $('#set-glossary')?.value.trim() || '',
      batchOutput: $('#set-output')?.value.trim() || '语镜译文',
      theme: state.theme,
    };
    try {
      const data = await api('/api/settings', { method: 'POST', body: { settings: payload } });
      state.settings = data.settings;
      state.health.aiConfigured = !!data.settings.ai?.apiKeySet;
      state.providers = (await api('/api/providers')).providers || state.providers;
      closeModal();
      syncStatusPill();
      toast('设置已保存', 'success');
    } catch (err) { toast(err.message || '保存失败', 'error'); }
  }

  async function testAI() {
    const box = $('#ai-test-result');
    const btn = $('[data-action="test-ai"]');
    const ai = {
      apiKey: $('#set-key')?.value.trim() || '',
      baseUrl: $('#set-base')?.value.trim() || '',
      model: $('#set-model')?.value.trim() || '',
    };
    if (!ai.apiKey) {
      if (box) box.innerHTML = `<span style="color:var(--coral-dark)">先填写 API Key；如果已经保存过，留空表示沿用旧 Key，但测试需要重新输入。</span>`;
      return;
    }
    if (btn) btn.disabled = true;
    if (box) box.innerHTML = `<span class="muted">正在连接 ${esc(ai.baseUrl || '服务')}…</span>`;
    try {
      const data = await api('/api/ai/test', { method: 'POST', body: { ai }, timeout: 45000 });
      if (box) box.innerHTML = `<span style="color:var(--jade-dark)">${icon('check', 12)} 连接成功 · 模型回复：${esc(data.reply || 'OK')}</span>`;
    } catch (err) {
      if (box) box.innerHTML = `<span style="color:var(--coral-dark)">${icon('alert', 12)} ${esc(err.message)}</span>`;
    } finally { if (btn) btn.disabled = false; }
  }

  // ---------------------------------------------------------------- modal
  function openModal(inner, onMount) {
    closeModal();
    const root = $('#modal-root');
    const backdrop = document.createElement('div');
    backdrop.className = 'modal-backdrop';
    backdrop.innerHTML = `<div class="modal" role="dialog" aria-modal="true">${inner}</div>`;
    backdrop.addEventListener('click', (e) => { if (e.target === backdrop) closeModal(); });
    root.appendChild(backdrop);
    document.body.style.overflow = 'hidden';
    const onKey = (e) => { if (e.key === 'Escape') closeModal(); };
    document.addEventListener('keydown', onKey);
    state.modalCleanup = () => document.removeEventListener('keydown', onKey);
    if (typeof onMount === 'function') onMount(backdrop);
    setTimeout(() => { const focusable = backdrop.querySelector('input, select, textarea, button'); focusable?.focus(); }, 80);
  }

  function closeModal() {
    const root = $('#modal-root');
    if (root) root.innerHTML = '';
    document.body.style.overflow = '';
    if (state.modalCleanup) { state.modalCleanup(); state.modalCleanup = null; }
  }

  // ---------------------------------------------------------------- events
  function debounce(fn, wait) {
    let timer;
    return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), wait); };
  }

  async function onDocumentClick(e) {
    const wordToken = e.target.closest('.word-token');
    if (wordToken) {
      e.preventDefault();
      openWordCard(wordToken);
      return;
    }
    if (!e.target.closest('#word-card')) closeWordCard();
    const compareTab = e.target.closest('[data-action="compare-tab"]');
    if (compareTab) {
      switchCompareView(compareTab.dataset.view);
      return;
    }
    const reopen = e.target.closest('[data-action="reopen-word"]');
    if (reopen) {
      const item = state.wordHistory[Number(reopen.dataset.index)];
      if (item) showWordFromData(item, reopen);
      return;
    }
    const back = e.target.closest('[data-action="back-to-article"]');
    if (back) {
      e.preventDefault();
      state.view = 'translation';
      persistPrefs();
      state.scrollBlock = back.dataset.block || null;
      navigate('/compare');
      return;
    }
    const link = e.target.closest('a[href^="/"]');
    if (link && !link.hasAttribute('download') && !link.target && !e.metaKey && !e.ctrlKey && !e.shiftKey) {
      e.preventDefault();
      navigate(link.getAttribute('href'));
      return;
    }
    const goto = e.target.closest('[data-goto]');
    if (goto) {
      navigate(goto.dataset.goto);
      return;
    }
    const openHistoryBtn = e.target.closest('[data-open-history]');
    if (openHistoryBtn) {
      openHistory(openHistoryBtn.dataset.openHistory);
      return;
    }
    const loadBatchBtn = e.target.closest('[data-load-batch]');
    if (loadBatchBtn) {
      loadBatch(loadBatchBtn.dataset.loadBatch);
      return;
    }
    const filter = e.target.closest('[data-filter]');
    if (filter) {
      if (filter.dataset.filter === 'lang') state.grammarFilters.lang = filter.dataset.value;
      else state.grammarFilters.category = filter.dataset.value;
      applyGrammarFilters();
      return;
    }
    const themeChoice = e.target.closest('[data-theme-choice]');
    if (themeChoice) {
      applyTheme(themeChoice.dataset.themeChoice, { notify: true });
      return;
    }
    const tab = e.target.closest('[data-action="view-tab"]');
    if (tab) {
      state.view = tab.dataset.view;
      persistPrefs();
      $$('[data-action="view-tab"]').forEach((b) => b.classList.toggle('is-active', b === tab));
      const body = $('#result-body');
      if (body) body.innerHTML = resultBodyHTML();
      return;
    }
    const action = e.target.closest('[data-action]');
    if (!action) return;
    const a = action.dataset.action;
    if (a === 'close-word') { closeWordCard(); return; }
    if (a === 'speak-word') { speakWord(); return; }
    if (a === 'copy-word') {
      const card = $('#word-card');
      const word = card?.dataset.word || '';
      const first = card?.querySelector('.wc-mean')?.textContent || '';
      copyText(`${word}${first ? `：${first}` : ''}`);
      return;
    }
    switch (a) {
      case 'translate': doTranslate(); break;
      case 'cycle-theme': cycleTheme(); break;
      case 'clear':
        state.article = null; state.draftSource = ''; state.loading = false;
        try { sessionStorage.removeItem('ll.article'); } catch { /* */ }
        renderRoute(); break;
      case 'swap-langs': {
        readControls();
        const from = state.sourceLang === 'auto' ? (state.article?.source?.lang || 'en') : state.sourceLang;
        state.sourceLang = state.targetLang;
        state.targetLang = from === state.targetLang ? 'en' : from;
        renderRoute();
        toast('语言已交换，点击「开始翻译」重新生成。');
        break;
      }
      case 'upload': pickFile(); break;
      case 'open-url': openUrlDialog(); break;
      case 'load-sample': loadSample(action.dataset.sample || 'en'); break;
      case 'copy-translation': copyTranslation(); break;
      case 'download-article': downloadArticle(); break;
      case 'download-word': downloadWord(); break;
      case 'font-smaller': setReadingScale(state.readingScale - 0.05); break;
      case 'font-larger': setReadingScale(state.readingScale + 0.05); break;
      case 'open-settings': openSettings(); break;
      case 'close-modal': closeModal(); break;
      case 'open-grammar-index': navigate('/grammar'); break;
      case 'copy-link':
        try {
          await navigator.clipboard.writeText(location.href);
          toast('链接已复制', 'success');
        } catch { toast('复制失败，请手动复制地址栏。', 'error'); }
        break;
      case 'back-to-article':
        state.scrollBlock = action.dataset.block || null;
        navigate('/'); break;
      case 'save-settings': saveSettings(); break;
      case 'test-ai': testAI(); break;
      case 'quit-app':
        if (!window.confirm('退出语镜？桌面服务会停止，网页将断开。')) break;
        api('/api/quit', { method: 'POST', body: {}, timeout: 5000 })
          .then(() => { closeModal(); toast('语镜已退出，可以关闭这个页面了。', 'success'); })
          .catch((err) => toast(err.message || '退出失败；网页版请在启动窗口中关闭。', 'error'));
        break;
      case 'install-app':
        if (state.installPrompt) {
          state.installPrompt.prompt();
          state.installPrompt.userChoice.then(() => { state.installPrompt = null; });
        } else {
          toast('在浏览器菜单中选择「安装语镜」或「创建快捷方式」即可。');
        }
        break;
      case 'clear-key':
        state.clearKey = true;
        if ($('#set-key')) $('#set-key').value = '';
        toast('保存后会清除已存 Key。');
        break;
      case 'clear-cache':
        api('/api/cache/clear', { method: 'POST', body: {} }).then(() => toast('缓存已清空', 'success')).catch((err) => toast(err.message, 'error'));
        break;
      case 'browse-folder': browseFolder(); break;
      case 'scan-folder': scanFolder(); break;
      case 'start-batch': startBatch(); break;
      case 'cancel-batch':
        if (state.batchJob) api(`/api/batch/${encodeURIComponent(state.batchJob.id)}/cancel`, { method: 'POST', body: {} }).then(() => toast('正在停止任务…')).catch((err) => toast(err.message, 'error'));
        break;
      case 'download-zip':
        if (state.batchJob) window.location.href = `/api/batch/${encodeURIComponent(state.batchJob.id)}/zip`;
        break;
      case 'reveal-output':
        if (state.batchJob?.outputDir) api('/api/reveal', { method: 'POST', body: { path: state.batchJob.outputDir } }).then(() => toast('已打开输出文件夹', 'success')).catch((err) => toast(err.message, 'error'));
        break;
      case 'new-batch':
        state.batchJob = null; state.batchScan = null; clearBatchTimer(); renderRoute(); break;
      case 'delete-history': deleteHistory(action.dataset.id); break;
      case 'star-history': starHistory(action.dataset.id); break;
      case 'retry': location.reload(); break;
      default: break;
    }
  }

  async function browseFolder() {
    toast('正在打开系统文件夹选择器…');
    try {
      const data = await api('/api/folder-picker', { method: 'POST', body: {} });
      if (data.folder) {
        const input = $('#batch-folder');
        if (input) input.value = data.folder;
        state.batchFolder = data.folder;
        scanFolder();
      }
    } catch (err) {
      toast('无法打开系统选择器，请直接粘贴路径。', 'error');
    }
  }

  function onDocumentKeydown(e) {
    if (e.key === 'Escape') { closeWordCard(); closeModal(); }
    if ((e.key === 'Enter' || e.key === ' ') && e.target.closest?.('.word-token')) {
      e.preventDefault();
      openWordCard(e.target.closest('.word-token'));
    }
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter' && state.route === '/') {
      if ($('#modal-root')?.childElementCount) return;
      e.preventDefault();
      doTranslate();
    }
  }

  function setupFileInput() {
    const input = $('#file-input');
    if (!input) return;
    input.addEventListener('change', () => {
      const file = input.files?.[0];
      if (file) handleFile(file);
    });
  }

  function setupDragDrop() {
    let depth = 0;
    const isSource = (e) => e.target.closest?.('.source-pane');
    document.addEventListener('dragenter', (e) => {
      if (!isSource(e)) return;
      e.preventDefault();
      depth++;
      $('#drop-overlay')?.classList.add('is-on');
    });
    document.addEventListener('dragover', (e) => {
      if (!isSource(e)) return;
      e.preventDefault();
      e.dataTransfer.dropEffect = 'copy';
    });
    document.addEventListener('dragleave', (e) => {
      if (!isSource(e)) return;
      depth = Math.max(0, depth - 1);
      if (depth === 0) $('#drop-overlay')?.classList.remove('is-on');
    });
    document.addEventListener('drop', (e) => {
      if (!isSource(e)) return;
      e.preventDefault();
      depth = 0;
      $('#drop-overlay')?.classList.remove('is-on');
      const items = Array.from(e.dataTransfer.items || []);
      const directory = items.find((item) => item.webkitGetAsEntry?.()?.isDirectory);
      if (directory) {
        toast('文件夹请使用「文件夹批译」，可以一次处理整夹。', 'error');
        return;
      }
      const file = e.dataTransfer.files?.[0];
      if (file) handleFile(file);
      else toast('没有读到文件。', 'error');
    });
    // Prevent the browser from opening a dropped file outside the target zone.
    window.addEventListener('dragover', (e) => e.preventDefault());
    window.addEventListener('drop', (e) => e.preventDefault());
  }

  function setupPopState() {
    window.addEventListener('popstate', () => renderRoute());
  }

  // ---------------------------------------------------------------- 404
  function notFoundHTML() {
    return `<div class="empty-page"><div class="glyph">404</div><h2>这一页不在书里</h2><p>地址可能写错了，或者这篇文章已经被删除。</p><a class="btn btn-primary" href="/" data-link>回到翻译台 ${icon('arrow', 13)}</a></div>`;
  }

  // ---------------------------------------------------------------- init
  async function init() {
    try {
      const [health, settings, providers] = await Promise.all([
        api('/api/health'),
        api('/api/settings'),
        api('/api/providers'),
      ]);
      state.health = health;
      state.settings = settings.settings;
      state.providers = providers.providers || [];
      try {
        const savedTheme = localStorage.getItem('ll.theme');
        state.theme = THEMES[savedTheme] ? savedTheme : (THEMES[state.settings?.theme] ? state.settings.theme : 'paper');
      } catch {
        state.theme = THEMES[state.settings?.theme] ? state.settings.theme : 'paper';
      }
      applyTheme(state.theme, { persist: false });
      try {
        const scale = parseFloat(localStorage.getItem('ll.fontScale') || '1');
        if (Number.isFinite(scale)) state.readingScale = Math.min(1.3, Math.max(0.85, scale));
      } catch { /* */ }
      try {
        const prefs = JSON.parse(localStorage.getItem('ll.prefs') || '{}');
        if (prefs.sourceLang) state.sourceLang = prefs.sourceLang;
        if (prefs.targetLang) state.targetLang = prefs.targetLang;
        if (prefs.provider) state.provider = prefs.provider;
        if (prefs.view) state.view = prefs.view;
      } catch { /* */ }
      if (state.settings?.provider && (!localStorage.getItem('ll.prefs'))) state.provider = state.settings.provider;
      try {
        const saved = JSON.parse(sessionStorage.getItem('ll.article') || 'null');
        if (saved?.source?.text) {
          state.article = saved;
          state.draftSource = saved.source.text;
          state.targetLang = saved.target?.lang || state.targetLang;
          state.provider = saved.target?.provider || state.provider;
        }
      } catch { /* */ }
      const availableProviders = new Set(state.providers.filter((p) => p.available !== false).map((p) => p.id));
      if (state.provider !== 'auto' && !availableProviders.has(state.provider)) state.provider = 'auto';
      renderRoute();
      ensureWordCard();
      setupFileInput();
      document.addEventListener('click', onDocumentClick);
      document.addEventListener('keydown', onDocumentKeydown);
      window.addEventListener('scroll', () => {
        if (state.activeWordToken && !$('#word-card')?.hidden) positionWordCard(state.activeWordToken);
      }, { passive: true });
      window.addEventListener('resize', () => {
        if (state.activeWordToken && !$('#word-card')?.hidden) positionWordCard(state.activeWordToken);
      });
      setupDragDrop();
      setupPopState();
      if ('serviceWorker' in navigator && location.protocol.startsWith('http')) {
        navigator.serviceWorker.register('/sw.js').catch(() => {});
      }
      setTimeout(() => $('#boot')?.classList.add('is-done'), 180);
      setTimeout(() => $('#boot')?.remove(), 850);
      // Warm the grammar library for detail pages.
      api('/api/grammar').then((data) => {
        state.library = data.items || [];
        state.libraryMap = Object.fromEntries(state.library.map((e) => [e.id, e]));
      }).catch(() => {});
    } catch (err) {
      $('#boot')?.remove();
      $('#app').innerHTML = `<main class="shell"><div class="empty-page" style="min-height:100vh"><div class="glyph">!</div><h2>语镜没能连接到本地服务</h2><p>${esc(err.message)}<br>请确认启动窗口仍然开着，然后刷新页面。</p><button class="btn btn-primary" data-action="retry">重新加载</button></div></main>`;
      document.addEventListener('click', (e) => { if (e.target.closest('[data-action="retry"]')) location.reload(); });
    }
  }

  init();
})();
