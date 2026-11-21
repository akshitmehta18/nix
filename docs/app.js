// Nix! — Framed Web Application & Live Support Platform

document.addEventListener('DOMContentLoaded', () => {
  initNixApp();
});

let currentStudioTab = 'tabChat';
let isStudioMode = false;
let isLiveServer = false;

// Authenticated Fallback Data for static deployment (e.g. GitHub Pages)
const FALLBACK_DATA = {
  overview: {
    health_score: 60,
    endpoints_count: 16,
    beans_count: 4,
    total_issues: 5
  },
  endpoints: [
    { method: "GET", path: "/api/products", controller: "ProductController", handler: "getAllProducts" },
    { method: "POST", path: "/api/products", controller: "ProductController", handler: "createProduct" },
    { method: "GET", path: "/api/products/{id}", controller: "ProductController", handler: "getProductById" },
    { method: "PUT", path: "/api/products/{id}", controller: "ProductController", handler: "updateProduct" },
    { method: "DELETE", path: "/api/products/{id}", controller: "ProductController", handler: "deleteProduct" },
    { method: "GET", path: "/api/products/search", controller: "ProductController", handler: "searchProducts" },
    { method: "GET", path: "/api/orders", controller: "OrderController", handler: "getAllOrders" },
    { method: "POST", path: "/api/orders", controller: "OrderController", handler: "createOrder" },
    { method: "GET", path: "/api/orders/{id}", controller: "OrderController", handler: "getOrderById" },
    { method: "PUT", path: "/api/orders/{id}/cancel", controller: "OrderController", handler: "cancelOrder" },
    { method: "GET", path: "/api/orders/customer/{customerId}", controller: "OrderController", handler: "getOrdersByCustomer" },
    { method: "GET", path: "/api/customers", controller: "CustomerController", handler: "getAllCustomers" },
    { method: "POST", path: "/api/customers", controller: "CustomerController", handler: "createCustomer" },
    { method: "GET", path: "/api/customers/{id}", controller: "CustomerController", handler: "getCustomerById" },
    { method: "PUT", path: "/api/customers/{id}", controller: "CustomerController", handler: "updateCustomer" },
    { method: "GET", path: "/api/audit/logs", controller: "AuditController", handler: "getAuditLogs" }
  ],
  beans: [
    { name: "ProductController", type: "Controller", file: "ProductController.java" },
    { name: "ProductService", type: "Service", file: "ProductService.java" },
    { name: "ProductRepository", type: "Repository", file: "ProductRepository.java" },
    { name: "AuditService", type: "Component", file: "AuditService.java" }
  ],
  issues: [
    { type: "N+1 Query", severity: "CRITICAL", description: "Repository method invoked inside for-each entity iteration loop.", file: "ProductService.java", line: 42 },
    { type: "Field Injection", severity: "HIGH", description: "@Autowired annotation detected on private field. Recommend constructor injection with Lombok @RequiredArgsConstructor.", file: "ProductController.java", line: 18 },
    { type: "Missing @Transactional", severity: "MEDIUM", description: "Database mutation method lacks transaction boundary annotation.", file: "OrderService.java", line: 34 },
    { type: "Unindexed Query", severity: "MEDIUM", description: "JPA query filters on non-indexed column 'sku_code'.", file: "ProductRepository.java", line: 19 },
    { type: "Hardcoded Secret", severity: "LOW", description: "Default fallback token present in configuration property.", file: "SecurityConfig.java", line: 27 }
  ]
};

const CLI_COMMANDS = {
  doctor: `$ nix doctor
  ✓ Python 3.14.0 (arm64 darwin)
  ✓ Tree-sitter Java Grammar: INSTALLED & ACTIVE
  ✓ Multi-Provider LLM Engine: Groq / Gemini / OpenAI / Anthropic / Ollama / AST Fallback
  ✓ Target Project: demo_store (Spring Boot 3.2.4)
  ✓ AST Parser: 9 files indexed in 38ms
  ✓ Health Score: 100% READY`,

  scan: `$ nix scan
  [+] Scanning project directory: nix/samples/demo_store
  [+] Parsing Java source AST with tree-sitter-java...
      -> ProductController.java (5 endpoints)
      -> OrderController.java (6 endpoints)
      -> CustomerController.java (5 endpoints)
  [+] Detected 4 Spring Components & Repositories
  [+] Static checks identified 5 performance & security issues
  [✓] Index cached in .nix/index/methods_fallback.json`,

  endpoints: `$ nix endpoints
  METHOD  ROUTE                           HANDLER
  GET     /api/products                   ProductController.getAllProducts()
  POST    /api/products                   ProductController.createProduct()
  GET     /api/products/{id}              ProductController.getProductById()
  PUT     /api/products/{id}              ProductController.updateProduct()
  DELETE  /api/products/{id}              ProductController.deleteProduct()
  GET     /api/orders                     OrderController.getAllOrders()
  POST    /api/orders                     OrderController.createOrder()
  GET     /api/orders/{id}                OrderController.getOrderById()
  PUT     /api/orders/{id}/cancel         OrderController.cancelOrder()
  GET     /api/customers                  CustomerController.getAllCustomers()`,

  beans: `$ nix beans
  NAME                 TYPE         FILE
  ProductController    @Controller  ProductController.java
  ProductService       @Service     ProductService.java
  ProductRepository    @Repository  ProductRepository.java
  AuditService         @Component   AuditService.java
  [✓] Dependency graph verified. 0 circular injection paths detected.`,

  issues: `$ nix issues
  [CRITICAL] N+1 Query Detected
             Location: ProductService.java:42
             Issue: Repository query inside entity iteration loop.
             Fix: Use JOIN FETCH or @EntityGraph on findWithCategories().

  [HIGH]     Field Injection (@Autowired on private field)
             Location: ProductController.java:18
             Fix: Refactor to constructor injection with Lombok @RequiredArgsConstructor.

  [MEDIUM]   Missing @Transactional on Mutation
             Location: OrderService.java:34
             Fix: Add @Transactional(rollbackFor = Exception.class).`,

  app: `$ nix app --path nix/samples/demo_store
  ┌────────────────────────────────────────────────────────────┐
  │                                                            │
  │  🚀 Nix - AI Spring Boot Assistant & Live Support Platform │
  │                                                            │
  │  Local App:   http://127.0.0.1:8765                        │
  │  Project:     demo_store                                   │
  │  Tunnel URL:  https://spanking-dreams-recorded-amsterdam   │
  │                                                            │
  │  Live Support Hub | Endpoints Tester | Beans Graph | Fixes │
  └────────────────────────────────────────────────────────────┘`
};

function initNixApp() {
  setupThemeToggle();
  setupFramedNavigation();
  setupHeroDock();
  setupCliSimulator();
  setupChat();
  setupEndpoints();
  setupBeans();
  setupIssues();
  setupLiveTester();
  setupDiagnostician();
  loadProjectOverview();
}

// DARK MODE & THEME TOGGLE
function setupThemeToggle() {
  const btn = document.getElementById('btnThemeToggle');
  const savedTheme = localStorage.getItem('nix_theme');
  const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;

  function applyTheme(isDark) {
    if (isDark) {
      document.body.classList.add('dark-mode');
      document.documentElement.classList.add('dark-mode');
      if (btn) {
        btn.textContent = '☀️';
        btn.setAttribute('aria-label', 'Switch to Light Mode');
        btn.title = 'Switch to Light Mode';
      }
    } else {
      document.body.classList.remove('dark-mode');
      document.documentElement.classList.remove('dark-mode');
      if (btn) {
        btn.textContent = '🌙';
        btn.setAttribute('aria-label', 'Switch to Dark Mode');
        btn.title = 'Switch to Dark Mode';
      }
    }
  }

  // Initial theme determination: Saved preference > OS system preference
  if (savedTheme === 'dark') {
    applyTheme(true);
  } else if (savedTheme === 'light') {
    applyTheme(false);
  } else {
    applyTheme(prefersDark);
  }

  // User click toggle
  if (btn) {
    btn.addEventListener('click', () => {
      const isCurrentlyDark = document.body.classList.contains('dark-mode');
      const nextDark = !isCurrentlyDark;
      applyTheme(nextDark);
      localStorage.setItem('nix_theme', nextDark ? 'dark' : 'light');
    });
  }

  // Dynamic OS preference listener (only if user hasn't set explicit override)
  if (window.matchMedia) {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      if (!localStorage.getItem('nix_theme')) {
        applyTheme(e.matches);
      }
    });
  }
}

// COPY COMMAND TO CLIPBOARD WITH TOAST
function copyCommand(text) {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(() => {
      showToast(`Copied to clipboard: ${text}`);
    }).catch(() => {
      showToast(`Command: ${text}`);
    });
  } else {
    showToast(`Command: ${text}`);
  }
}

function showToast(msg) {
  const toast = document.getElementById('toast');
  if (!toast) return;
  toast.textContent = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 2800);
}

// INTERACTIVE CLI SIMULATOR
function setupCliSimulator() {
  const body = document.getElementById('cliSimulatorBody');
  const tabs = document.querySelectorAll('.cmd-tab-btn');
  if (!body) return;

  function renderCmd(cmd) {
    body.textContent = CLI_COMMANDS[cmd] || CLI_COMMANDS.doctor;
    tabs.forEach(t => t.classList.toggle('active', t.dataset.cmd === cmd));
  }

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      renderCmd(tab.dataset.cmd);
    });
  });

  renderCmd('doctor');
}

// STATUS BADGE UPDATE
function updateServerStatus(isLive) {
  isLiveServer = isLive;
  const badge = document.getElementById('connectionBadge');
  if (!badge) return;
  if (isLive) {
    badge.className = 'connection-badge';
    badge.textContent = '● Live Server Connected';
  } else {
    badge.className = 'connection-badge demo-mode';
    badge.textContent = '● Interactive Demo Mode (GitHub Pages)';
  }
}

// NAVIGATION & VIEW SWITCHING
function setupFramedNavigation() {
  const toggleBtn = document.getElementById('btnToggleStudioMode');
  const toggleLabel = document.getElementById('studioModeLabel');

  if (toggleBtn && toggleLabel) {
    toggleBtn.addEventListener('click', () => {
      isStudioMode = !isStudioMode;
      if (isStudioMode) {
        showSection('studioSection');
        toggleLabel.textContent = 'Showcase View';
      } else {
        showSection('heroSection');
        toggleLabel.textContent = 'Switch to Studio View';
      }
    });
  }

  // Studio tabs
  document.querySelectorAll('.studio-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      openStudioTab(tab.dataset.tab);
    });
  });

  // Quick Chips in Chat
  document.querySelectorAll('.quick-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const q = chip.dataset.query;
      const input = document.getElementById('chatInput');
      const form = document.getElementById('chatForm');
      if (input && form) {
        input.value = q;
        form.dispatchEvent(new Event('submit'));
      }
    });
  });
}

function showSection(sectionId) {
  const hero = document.getElementById('heroSection');
  const studio = document.getElementById('studioSection');
  const toggleLabel = document.getElementById('studioModeLabel');

  if (!hero || !studio) return;

  if (sectionId === 'heroSection') {
    hero.style.display = 'flex';
    studio.style.display = 'none';
    isStudioMode = false;
    if (toggleLabel) toggleLabel.textContent = 'Switch to Studio View';
  } else {
    hero.style.display = 'none';
    studio.style.display = 'flex';
    isStudioMode = true;
    if (toggleLabel) toggleLabel.textContent = 'Showcase View';
  }
}

function openStudioTab(tabId) {
  showSection('studioSection');
  currentStudioTab = tabId;

  document.querySelectorAll('.studio-tab').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === tabId);
  });
  document.querySelectorAll('.pane-content').forEach(pane => {
    pane.classList.toggle('active', pane.id === tabId);
  });

  if (tabId === 'tabEndpoints') loadEndpointsData();
  if (tabId === 'tabBeans') loadBeansData();
  if (tabId === 'tabIssues') loadIssuesData();
  if (tabId === 'tabOverview') loadProjectOverview();
}

// HERO ACTION DOCK
function setupHeroDock() {
  const input = document.getElementById('dockQueryInput');
  const submitBtn = document.getElementById('btnDockSubmit');

  function handleDockAction() {
    const query = input ? input.value.trim() : '';
    openStudioTab('tabChat');
    if (query) {
      const chatInput = document.getElementById('chatInput');
      const form = document.getElementById('chatForm');
      if (chatInput && form) {
        chatInput.value = query;
        form.dispatchEvent(new Event('submit'));
      }
      if (input) input.value = '';
    }
  }

  if (submitBtn) submitBtn.addEventListener('click', handleDockAction);
  if (input) {
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') handleDockAction();
    });
  }
}

// CHAT & LIVE SUPPORT
function setupChat() {
  const form = document.getElementById('chatForm');
  const input = document.getElementById('chatInput');

  if (!form || !input) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = input.value.trim();
    if (!query) return;

    appendChatBubble('user', query);
    input.value = '';

    const thinkingBubble = appendChatBubble('ai', '⚡ Analyzing Spring Boot codebase...');

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: query })
      });
      const data = await res.json();
      thinkingBubble.remove();

      if (data.error) {
        appendChatBubble('ai', `⚠️ Error: ${data.error}`);
      } else {
        appendChatBubble('ai', data.response);
      }
    } catch (err) {
      thinkingBubble.remove();
      appendChatBubble('ai', getFallbackChatResponse(query));
    }
  });
}

function getFallbackChatResponse(query) {
  const q = query.toLowerCase();
  if (q.includes('endpoint') || q.includes('route') || q.includes('api')) {
    return "You have **16 REST endpoints** indexed across `ProductController`, `OrderController`, and `CustomerController`:\n* `GET /api/products` (Product list)\n* `POST /api/products` (Create product)\n* `GET /api/orders` (Order list)\n* `PUT /api/orders/{id}/cancel` (Order cancellation)\n\nSwitch to the **Endpoints** tab to test them live!";
  }
  if (q.includes('issue') || q.includes('bug') || q.includes('security') || q.includes('audit')) {
    return "Nix detected **5 static issues** in your Spring Boot application:\n1. **[CRITICAL] N+1 Query** in `ProductService.java:42`\n2. **[HIGH] Field Injection** in `ProductController.java:18`\n3. **[MEDIUM] Missing @Transactional** in `OrderService.java:34`\n4. **[MEDIUM] Unindexed Query** in `ProductRepository.java:19`\n5. **[LOW] Hardcoded Secret** in `SecurityConfig.java:27`\n\nCheck the **Issues** tab to inspect automated fix recommendations.";
  }
  if (q.includes('bean') || q.includes('wire') || q.includes('inject')) {
    return "Nix mapped **4 Spring Beans**: `ProductController` (@Controller), `ProductService` (@Service), `ProductRepository` (@Repository), and `AuditService` (@Component). The dependency wiring graph is healthy with zero circular references.";
  }
  return `I'm Nix, your AI Spring Boot engineer! I can help you with:\n* **REST Endpoints Mapping**: Run \`nix endpoints\` or explore the **Endpoints** tab.\n* **Static Security & Bug Audit**: Detecting N+1 queries and missing \`@Transactional\` boundaries.\n* **Bean Dependency Graphs**: Inspecting \`@Service\` and \`@Repository\` injection wiring.\n* **Error Diagnostics**: Paste any Java stack trace into the **Diagnostics** tab!`;
}

function appendChatBubble(role, text) {
  const container = document.getElementById('chatMessages');
  if (!container) return { remove: () => {} };

  const bubble = document.createElement('div');
  bubble.className = `chat-bubble ${role}`;

  const avatar = role === 'user' ? '👤' : '⚡';
  const author = role === 'user' ? 'You' : 'Nix Copilot';

  bubble.innerHTML = `
    <div class="bubble-avatar">${avatar}</div>
    <div class="bubble-content">
      <strong>${author}</strong><br>
      ${renderMarkdown(text)}
    </div>
  `;

  container.appendChild(bubble);
  container.scrollTop = container.scrollHeight;
  return bubble;
}

function renderMarkdown(text) {
  if (!text) return '';
  return text
    .replace(/```([\s\S]*?)```/g, '<pre style="background:#18221d;color:#86efac;padding:10px;border-radius:6px;font-family:monospace;font-size:12px;overflow:auto;margin:8px 0;"><code>$1</code></pre>')
    .replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>');
}

// OVERVIEW METRICS
async function loadProjectOverview() {
  let data = null;
  try {
    const res = await fetch('/api/overview');
    if (res.ok) {
      data = await res.json();
      updateServerStatus(true);
    }
  } catch (err) {
    updateServerStatus(false);
  }

  if (!data) {
    data = FALLBACK_DATA.overview;
  }

  const scoreElem = document.getElementById('overviewScore');
  const epElem = document.getElementById('overviewEndpoints');
  const beanElem = document.getElementById('overviewBeans');
  const issElem = document.getElementById('overviewIssues');

  if (scoreElem) scoreElem.innerHTML = `${data.health_score ?? 60}<span class="stat-sub">/100</span>`;
  if (epElem) epElem.textContent = data.endpoints_count || 16;
  if (beanElem) beanElem.textContent = data.beans_count || 4;
  if (issElem) issElem.textContent = data.total_issues || 5;

  const dockEp = document.getElementById('dockCounterEndpoints');
  const dockBean = document.getElementById('dockCounterBeans');
  const dockIss = document.getElementById('dockCounterIssues');

  if (dockEp) dockEp.textContent = data.endpoints_count || 16;
  if (dockBean) dockBean.textContent = data.beans_count || 4;
  if (dockIss) dockIss.textContent = data.total_issues || 5;
}

// ENDPOINTS LIST
function setupEndpoints() {
  const filterInput = document.getElementById('endpointFilter');
  if (!filterInput) return;

  filterInput.addEventListener('input', () => {
    const q = filterInput.value.toLowerCase();
    document.querySelectorAll('.endpoint-row-card').forEach(row => {
      const path = row.dataset.path?.toLowerCase() || '';
      const method = row.dataset.method?.toLowerCase() || '';
      row.style.display = (path.includes(q) || method.includes(q)) ? 'flex' : 'none';
    });
  });
}

async function loadEndpointsData() {
  const list = document.getElementById('endpointsList');
  if (!list) return;

  list.innerHTML = '<div style="padding:20px;text-align:center;color:#718279;">Scanning codebase for REST controllers...</div>';

  let endpoints = [];
  try {
    const res = await fetch('/api/endpoints');
    if (res.ok) {
      const data = await res.json();
      endpoints = data.endpoints || [];
      updateServerStatus(true);
    }
  } catch (err) {
    updateServerStatus(false);
  }

  if (!endpoints.length) {
    endpoints = FALLBACK_DATA.endpoints;
  }

  list.innerHTML = '';
  endpoints.forEach(ep => {
    const card = document.createElement('div');
    card.className = 'endpoint-row-card';
    const m = ep.method || 'GET';
    card.dataset.method = m;
    card.dataset.path = ep.path || '/';

    card.innerHTML = `
      <div style="display:flex;align-items:center;">
        <span class="endpoint-method method-${m}">${m}</span>
        <span class="endpoint-path">${ep.path || '/'}</span>
        <span class="endpoint-handler">${ep.controller || 'Controller'}.${ep.handler || 'method'}()</span>
      </div>
      <button class="pill-btn-toggle" style="padding:4px 12px;font-size:12px;" onclick="testRoute('${m}', '${ep.path || '/'}')">
        Test ↗
      </button>
    `;
    list.appendChild(card);
  });
}

function testRoute(method, path) {
  openStudioTab('tabTester');
  const mInput = document.getElementById('testerMethod');
  const uInput = document.getElementById('testerUrl');
  if (mInput) mInput.value = method;
  if (uInput) uInput.value = `http://localhost:8080${path.startsWith('/') ? path : '/' + path}`;
}

// BEANS
function setupBeans() {}

async function loadBeansData() {
  const container = document.getElementById('beansContainer');
  if (!container) return;

  container.innerHTML = '<div style="padding:20px;text-align:center;color:#718279;">Mapping Spring components...</div>';

  let beans = [];
  try {
    const res = await fetch('/api/beans');
    if (res.ok) {
      const data = await res.json();
      beans = data.beans?.beans || [];
      updateServerStatus(true);
    }
  } catch (err) {
    updateServerStatus(false);
  }

  if (!beans.length) {
    beans = FALLBACK_DATA.beans;
  }

  container.innerHTML = '';
  beans.forEach(b => {
    const card = document.createElement('div');
    card.className = 'bean-card-item';
    card.innerHTML = `
      <div class="bean-card-type">@${b.type || 'Component'}</div>
      <div class="bean-card-name">${b.name || 'Bean'}</div>
      <div class="bean-card-file">${b.file || ''}</div>
    `;
    container.appendChild(card);
  });
}

// ISSUES AUDITOR
function setupIssues() {}

async function loadIssuesData() {
  const list = document.getElementById('issuesList');
  if (!list) return;

  list.innerHTML = '<div style="padding:20px;text-align:center;color:#718279;">Running static checks...</div>';

  let issues = [];
  try {
    const res = await fetch('/api/issues');
    if (res.ok) {
      const data = await res.json();
      issues = data.issues || [];
      updateServerStatus(true);
    }
  } catch (err) {
    updateServerStatus(false);
  }

  if (!issues.length) {
    issues = FALLBACK_DATA.issues;
  }

  list.innerHTML = '';
  issues.forEach(iss => {
    const card = document.createElement('div');
    card.className = 'issue-card-item';

    card.innerHTML = `
      <div>
        <div class="issue-card-title">${iss.type || 'Issue'} [${(iss.severity || 'MEDIUM').toUpperCase()}]</div>
        <div class="issue-card-desc">${iss.message || iss.description || 'Static analysis alert.'}</div>
        <div class="issue-card-loc">📁 ${iss.file || iss.file_path || 'Source'}:${iss.line || 1}</div>
      </div>
    `;
    list.appendChild(card);
  });
}

// LIVE TESTER
function setupLiveTester() {
  const btn = document.getElementById('btnExecuteTest');
  if (!btn) return;

  btn.addEventListener('click', async () => {
    const methodElem = document.getElementById('testerMethod');
    const urlElem = document.getElementById('testerUrl');
    const bodyElem = document.getElementById('testerBody');
    const viewer = document.getElementById('testerResponseViewer');

    const method = methodElem ? methodElem.value : 'GET';
    const url = urlElem ? urlElem.value.trim() : '';
    const bodyStr = bodyElem ? bodyElem.value.trim() : '';

    if (viewer) viewer.textContent = 'Connecting...';

    let bodyData = null;
    if (bodyStr && ['POST', 'PUT', 'PATCH'].includes(method)) {
      try { bodyData = JSON.parse(bodyStr); } catch (e) { bodyData = bodyStr; }
    }

    try {
      const res = await fetch('/api/test-api', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ method, url, body: bodyData })
      });
      const data = await res.json();

      if (viewer) {
        if (data.error) {
          viewer.textContent = `${data.error}\n\n${data.hint || ''}`;
        } else {
          viewer.textContent = typeof data.body === 'object' ? JSON.stringify(data.body, null, 2) : data.body;
        }
      }
    } catch (err) {
      if (viewer) {
        viewer.textContent = JSON.stringify({
          status: 200,
          protocol: "HTTP/1.1",
          route: url || "/api/products",
          method: method,
          message: "Simulated response from Nix API Tester (Demo Mode)",
          timestamp: new Date().toISOString(),
          sample_payload: bodyData || { id: 101, name: "Sample Item", price: 49.99, in_stock: true }
        }, null, 2);
      }
    }
  });
}

// DIAGNOSTICIAN
function setupDiagnostician() {
  const btn = document.getElementById('btnRunDiagnose');
  const sampleBtn = document.getElementById('btnSampleError');
  const input = document.getElementById('stackTraceInput');
  const resBox = document.getElementById('diagnoseResult');

  if (sampleBtn && input) {
    sampleBtn.addEventListener('click', () => {
      input.value = `java.lang.NullPointerException: Cannot invoke "Product.getStock()" because "p" is null
    at com.example.store.service.ProductService.updateStock(ProductService.java:38)`;
    });
  }

  if (btn && input && resBox) {
    btn.addEventListener('click', async () => {
      const text = input.value.trim();
      if (!text) return;

      resBox.style.display = 'block';
      resBox.innerHTML = 'Diagnosing stack trace...';

      try {
        const res = await fetch('/api/diagnose', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ stack_trace: text })
        });
        const data = await res.json();
        renderDiagnoseResult(data);
      } catch (err) {
        renderDiagnoseResult(getFallbackDiagnose(text));
      }
    });
  }
}

function renderDiagnoseResult(data) {
  const resBox = document.getElementById('diagnoseResult');
  if (!resBox) return;

  let html = `<p><strong>Exception:</strong> ${data.error_type || 'Error'}</p>`;
  if (data.file) html += `<p><strong>Offending Line:</strong> <code>${data.file}:${data.line || ''}</code></p>`;
  if (data.cause) html += `<p><strong>Cause:</strong> ${data.cause}</p>`;
  if (data.recommendation) {
    html += `<div style="margin-top:10px;background:#fef08a;padding:10px;border-radius:6px;color:#854d0e;">
      <strong>Fix Recommendation:</strong><br>${data.recommendation}
    </div>`;
  }
  resBox.innerHTML = html;
}

function getFallbackDiagnose(stackTrace) {
  const isNpe = stackTrace.includes('NullPointerException');
  return {
    error_type: isNpe ? "NullPointerException" : "Spring Boot Exception",
    file: isNpe ? "ProductService.java" : "Application.java",
    line: isNpe ? 38 : 14,
    cause: isNpe ? "Attempting to invoke a method on a null reference (p == null)." : "Unchecked runtime exception in Spring Boot service layer.",
    recommendation: isNpe 
      ? "Wrap access in an Optional check or null guard: `if (product != null) { ... }` or use `Optional.ofNullable(product).orElseThrow(...)`."
      : "Verify your bean injection and configuration properties in application.properties."
  };
}

// INITIALIZR & SETTINGS (no-op stubs if elements absent)
function setupStarter() {}
function setupSettings() {}
