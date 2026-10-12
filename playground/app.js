/**
 * Zafira Online Studio - Interactive Web Playground
 * 2026 Elite Client Application
 */

// ─── 1. TAYYOR KOD NAMUNALARI ───
const TEMPLATES = {
  hello: `// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  ZAFIRA TILI - Salom Dunyo 🔷
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
let nomi = "Zafira"
let versiya = 0.1
const YARATUVCHI = "Jasper & Antigravity"

print("Salom, " + nomi + " tili!")
print("Versiya: " + String(versiya))
print("Yaratuvchi: " + YARATUVCHI)

// Oddiy funksiya
fn salomlash(ism) {
    return "Assalomu alaykum, " + ism + "!"
}

print(salomlash("Jasper"))

// Boshqaruv oqimi va tsikl
print("\\nHisoblaymiz:")
let yigindi = 0
for i in 1..6 {
    yigindi = yigindi + i
    print("  " + String(i) + " -> jami: " + String(yigindi))
}
`,

  factorial: `// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  ZAFIRA TILI - Faktorial & Seal funksiyalar
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

// "seal" rejimi: qat'iy tip va "where" invarianti
// Invariant sharti: n >= 0 bo'lishi SHART!
seal fn faktorial(n: Int) -> Int
    where n >= 0
{
    if n <= 1 {
        return 1
    }
    return n * faktorial(n - 1)
}

print("=== Zafira Seal Faktorial ===")
print("Invariant: n >= 0 sharti qat'iy tekshiriladi.\\n")

for i in 0..8 {
    print(String(i) + "! = " + String(faktorial(i)))
}
`,

  ai_tensors: `// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  ZAFIRA TILI - Silicon AI & Tensor Dvigateli
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
import std.ai

print("══════════════════════════════════════════════")
print("  🔷 Zafira AI & Tensor Silicon Engine 🔷")
print("══════════════════════════════════════════════")

// 1. Vektorlar va skalyar ko'paytma (dot)
let v1 = ai.tensor([1.0, 2.0, 3.0])
let v2 = ai.tensor([4.0, 5.0, 6.0])

print("Vektor 1: " + String(v1))
print("Vektor 2: " + String(v2))
print("v1 shape: " + String(v1.shape))

let dot_product = v1.dot(v2)
print("v1 dot v2 = " + String(dot_product))

// 2. 2D Matritsalar ko'paytmasi (Matrix Multiplication)
let mat_a = ai.tensor([
    [1.0, 2.0],
    [3.0, 4.0]
])
let mat_b = ai.tensor([
    [5.0, 6.0],
    [7.0, 8.0]
])

print("\\nMatritsalar ko'paytmasi (A * B):")
let mat_c = mat_a.dot(mat_b)
print(String(mat_c))
print("Jami yig'indi: " + String(mat_c.sum()))
print("O'rtacha qiymat: " + String(mat_c.mean()))

// 3. Silicon apparat bloki
run @gpu {
    print("\\n[Zafira Silicon] @gpu apparat akseleratsiyasi faol")
}
`,

  web_json: `// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  ZAFIRA TILI - Web & JSON Amallari (std.json)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
import std.json

print("=== 1. JSON Parser & Stringify ===")

let json_matn = "{\\"loyiha\\": \\"Zafira\\", \\"versiya\\": 1.0, \\"muallif\\": \\"Jasper\\", \\"tezlik\\": \\"Silicon-Native\\"}"
let obj = json.parse(json_matn)

print("Loyiha nomi: " + obj.loyiha)
print("Muallif: " + obj.muallif)
print("Tezlik: " + obj.tezlik)

// Ro'yxatni JSON ga aylantirish
let modullar = ["std.math", "std.string", "std.list", "std.ai", "std.json", "std.net"]
let modullar_json = json.stringify(modullar)
print("\\nModullar ro'yxati (JSON):")
print(modullar_json)
`,

  async: `// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  ZAFIRA TILI - Asinxron Dasturlash (async / await)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

struct Task {
    id: Int,
    nom: String
}

async fn yuklash(vazifa) {
    print("[Asinxron Boshlandi] Vazifa #" + String(vazifa.id) + ": " + vazifa.nom)
    let yigindi = 0
    for i in 1..50 {
        yigindi = yigindi + i
    }
    return "Natija: " + String(yigindi)
}

print("=== Zafira Native Async / Await Konveyeri ===")

let t1 = Task(101, "Ma'lumotlar oqimi")
let javob1 = await yuklash(t1)
print("[Kutilgan Natija 1] " + javob1)

let t2 = Task(102, "Tensor modellarini tekshirish")
let javob2 = await yuklash(t2)
print("[Kutilgan Natija 2] " + javob2)

print("\\nBarcha asinxron jarayonlar muvaffaqiyatli yakunlandi! 🚀")
`
};

// ─── 2. DOM ELEMENTLAR ───
const codeEditor = document.getElementById('code-editor');
const lineNumbers = document.getElementById('line-numbers');
const templateSelect = document.getElementById('template-select');
const btnRun = document.getElementById('btn-run');
const btnAst = document.getElementById('btn-ast');
const btnTokens = document.getElementById('btn-tokens');
const btnCopy = document.getElementById('btn-copy');
const btnClear = document.getElementById('btn-clear');

const outputConsole = document.getElementById('output-console');
const statusBanner = document.getElementById('status-banner');
const astConsole = document.getElementById('ast-console');
const tokensContainer = document.getElementById('tokens-container');
const execTimeBadge = document.getElementById('exec-time-badge');

const cursorInfo = document.getElementById('cursor-info');
const charCount = document.getElementById('char-count');
const statusDot = document.getElementById('status-dot');
const statusText = document.getElementById('status-text');
const toastEl = document.getElementById('toast');

const diagTime = document.getElementById('diag-time');
const diagTokens = document.getElementById('diag-tokens');
const diagAstStatus = document.getElementById('diag-ast-status');

// ─── 3. MUHARRIR VA QATOR RAQAMLARI ───
function updateLineNumbers() {
  const lines = codeEditor.value.split('\n').length;
  let numbersHtml = '';
  for (let i = 1; i <= lines; i++) {
    numbersHtml += `<div>${i}</div>`;
  }
  lineNumbers.innerHTML = numbersHtml;
}

function updateCursorInfo() {
  const text = codeEditor.value;
  const selStart = codeEditor.selectionStart;
  const linesUpToCursor = text.substring(0, selStart).split('\n');
  const line = linesUpToCursor.length;
  const col = linesUpToCursor[linesUpToCursor.length - 1].length + 1;

  cursorInfo.textContent = `Qator: ${line}, Ustun: ${col}`;
  charCount.textContent = `${text.length} belgi`;
}

// Skroll sinxronizatsiyasi
codeEditor.addEventListener('scroll', () => {
  lineNumbers.scrollTop = codeEditor.scrollTop;
});

// Matn o'zgarganda
codeEditor.addEventListener('input', () => {
  updateLineNumbers();
  updateCursorInfo();
});

codeEditor.addEventListener('click', updateCursorInfo);
codeEditor.addEventListener('keyup', updateCursorInfo);

// Tab tugmasini 4 bo'shliqqa almashtirish
codeEditor.addEventListener('keydown', (e) => {
  if (e.key === 'Tab') {
    e.preventDefault();
    const start = codeEditor.selectionStart;
    const end = codeEditor.selectionEnd;
    const value = codeEditor.value;
    codeEditor.value = value.substring(0, start) + '    ' + value.substring(end);
    codeEditor.selectionStart = codeEditor.selectionEnd = start + 4;
    updateLineNumbers();
    updateCursorInfo();
  } else if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
    e.preventDefault();
    runCode();
  } else if ((e.ctrlKey || e.metaKey) && e.key === 's') {
    e.preventDefault();
    runCode();
  }
});

// ─── 4. TABLARNI BOSHQARISH ───
const tabButtons = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');

function switchTab(tabName) {
  tabButtons.forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === tabName);
  });
  tabContents.forEach(content => {
    content.classList.toggle('active', content.id === `tab-${tabName}`);
  });
}

tabButtons.forEach(btn => {
  btn.addEventListener('click', () => {
    switchTab(btn.dataset.tab);
  });
});

// ─── 5. TOAST XABARLAR ───
let toastTimer = null;
function showToast(msg) {
  toastEl.textContent = msg;
  toastEl.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toastEl.classList.remove('show');
  }, 2500);
}

// ─── 6. SERVER BILAN ALOQA VA IJRO ───
let isRunning = false;

async function runCode(targetTab = null) {
  if (isRunning) return;
  const code = codeEditor.value;

  isRunning = true;
  btnRun.disabled = true;
  btnRun.style.opacity = '0.7';
  execTimeBadge.textContent = "Bajarilmoqda...";

  if (targetTab) {
    switchTab(targetTab);
  }

  try {
    const res = await fetch('/api/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code })
    });

    if (!res.ok) {
      throw new Error(`Server xatosi (HTTP ${res.status})`);
    }

    const data = await res.json();
    renderResult(data);
    updateServerStatus(true);
  } catch (err) {
    console.error("Ijro xatosi:", err);
    updateServerStatus(false);
    renderError(`Serverga ulanishda xatolik yuz berdi: ${err.message}\nIltimos, server ishlayotganligini tekshiring: python zafira.py playground`);
  } finally {
    isRunning = false;
    btnRun.disabled = false;
    btnRun.style.opacity = '1';
  }
}

function renderResult(data) {
  const { stdout, error, ast, tokens, execution_time_ms } = data;

  // 1. Output konsoli
  if (error) {
    statusBanner.style.display = 'flex';
    statusBanner.className = 'output-banner error';
    statusBanner.innerHTML = `<span>⚠️ ${escapeHtml(error)}</span><span style="font-size:0.75rem">${execution_time_ms} ms</span>`;
    outputConsole.innerHTML = `<span style="color:#f87171;">${escapeHtml(error)}</span>\n` + (stdout ? `<span style="color:#94a3b8;">${escapeHtml(stdout)}</span>` : '');
    execTimeBadge.textContent = `Xatolik (${execution_time_ms} ms)`;
  } else {
    statusBanner.style.display = 'flex';
    statusBanner.className = 'output-banner success';
    statusBanner.innerHTML = `<span>✅ Muvaffaqiyatli bajarildi</span><span style="font-size:0.75rem">${execution_time_ms} ms</span>`;
    outputConsole.textContent = stdout || '(Natija bo\'sh — hech narsa chop etilmadi)';
    execTimeBadge.textContent = `${execution_time_ms} ms`;
  }

  // 2. AST ko'rinishi
  if (ast) {
    astConsole.textContent = typeof ast === 'string' ? ast : JSON.stringify(ast, null, 2);
    diagAstStatus.textContent = "Muvaffaqiyatli";
    diagAstStatus.style.color = "#34d399";
  } else {
    astConsole.textContent = error ? `// AST mavjud emas (xatolik tufayli)\n// ${error}` : '// AST bo\'sh';
    diagAstStatus.textContent = error ? "Xatolik" : "Bo'sh";
    diagAstStatus.style.color = "#f87171";
  }

  // 3. Tokenlar ko'rinishi
  renderTokens(tokens);

  // 4. Diagnostika
  diagTime.textContent = `${execution_time_ms || 0} ms`;
  diagTokens.textContent = `${tokens ? tokens.length : 0} ta`;
}

function renderTokens(tokens) {
  if (!tokens || tokens.length === 0) {
    tokensContainer.innerHTML = '<p style="color:var(--text-dim); font-style:italic;">// Tokenlar mavjud emas</p>';
    return;
  }

  let html = `
    <table class="tokens-table">
      <thead>
        <tr>
          <th>Joylashuv</th>
          <th>Token Turi</th>
          <th>Qiymati</th>
        </tr>
      </thead>
      <tbody>
  `;

  tokens.forEach(t => {
    let badgeClass = 'token-DELIMITER';
    const type = t.type;
    if (['LET', 'CONST', 'FN', 'RETURN', 'IF', 'ELSE', 'WHILE', 'FOR', 'IN', 'STRUCT', 'IMPORT', 'SEAL', 'DRAFT', 'WHERE', 'RUN'].includes(type)) {
      badgeClass = 'token-KEYWORD';
    } else if (type === 'IDENT') {
      badgeClass = 'token-IDENT';
    } else if (['INT', 'FLOAT'].includes(type)) {
      badgeClass = 'token-NUMBER';
    } else if (type === 'STRING') {
      badgeClass = 'token-STRING';
    } else if (['PLUS', 'MINUS', 'STAR', 'SLASH', 'ASSIGN', 'EQ', 'NEQ', 'LT', 'GT', 'LTE', 'GTE', 'AND', 'OR', 'NOT'].includes(type)) {
      badgeClass = 'token-OPERATOR';
    }

    html += `
      <tr>
        <td style="color:var(--text-dim); font-family:var(--font-mono);">L${t.line}:C${t.col}</td>
        <td><span class="token-badge ${badgeClass}">${escapeHtml(t.type)}</span></td>
        <td style="color:#e2e8f0; font-family:var(--font-mono);">${escapeHtml(t.value)}</td>
      </tr>
    `;
  });

  html += '</tbody></table>';
  tokensContainer.innerHTML = html;
}

function renderError(msg) {
  statusBanner.style.display = 'flex';
  statusBanner.className = 'output-banner error';
  statusBanner.innerHTML = `<span>⚠️ ${escapeHtml(msg)}</span>`;
  outputConsole.innerHTML = `<span style="color:#f87171;">${escapeHtml(msg)}</span>`;
  execTimeBadge.textContent = "Ulanish xatosi";
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// ─── 7. SERVER STATUS CHECK ───
async function checkServerHealth() {
  try {
    const res = await fetch('/api/health');
    if (res.ok) {
      updateServerStatus(true);
    } else {
      updateServerStatus(false);
    }
  } catch (e) {
    updateServerStatus(false);
  }
}

function updateServerStatus(online) {
  if (online) {
    statusDot.className = 'status-dot';
    statusText.textContent = 'Server: Faol (5000)';
  } else {
    statusDot.className = 'status-dot offline';
    statusText.textContent = 'Server: Offline';
  }
}

// ─── 8. EVENT LISTENERS ───
btnRun.addEventListener('click', () => {
  runCode('output');
});

btnAst.addEventListener('click', () => {
  runCode('ast');
});

btnTokens.addEventListener('click', () => {
  runCode('tokens');
});

templateSelect.addEventListener('change', (e) => {
  const chosen = e.target.value;
  if (TEMPLATES[chosen]) {
    codeEditor.value = TEMPLATES[chosen];
    updateLineNumbers();
    updateCursorInfo();
    showToast(`"${e.target.options[e.target.selectedIndex].text}" namunasi yuklandi`);
  }
});

btnCopy.addEventListener('click', () => {
  navigator.clipboard.writeText(codeEditor.value).then(() => {
    showToast('Kod buferga nusxalandi! 📋');
  });
});

btnClear.addEventListener('click', () => {
  if (confirm('Kodni tozalashni xohlaysizmi?')) {
    codeEditor.value = '';
    updateLineNumbers();
    updateCursorInfo();
    outputConsole.innerHTML = '<span class="terminal-placeholder">// Tozalandi</span>';
    statusBanner.style.display = 'none';
    showToast('Muharrir tozalandi');
  }
});

// ─── 9. BACKGROUND STARFIELD / PARTICLES CANVAS ───
function initCanvas() {
  const canvas = document.getElementById('bg-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  let width = (canvas.width = window.innerWidth);
  let height = (canvas.height = window.innerHeight);

  window.addEventListener('resize', () => {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
  });

  const particles = [];
  const PARTICLE_COUNT = 45;

  for (let i = 0; i < PARTICLE_COUNT; i++) {
    particles.push({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.35,
      vy: (Math.random() - 0.5) * 0.35,
      radius: Math.random() * 1.5 + 0.5,
      alpha: Math.random() * 0.4 + 0.1
    });
  }

  function render() {
    ctx.clearRect(0, 0, width, height);

    for (let i = 0; i < particles.length; i++) {
      const p = particles[i];
      p.x += p.vx;
      p.y += p.vy;

      if (p.x < 0) p.x = width;
      if (p.x > width) p.x = 0;
      if (p.y < 0) p.y = height;
      if (p.y > height) p.y = 0;

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(14, 165, 233, ${p.alpha})`;
      ctx.fill();

      // Yaqin zarrachalar o'rtasida nozik chiziqlar
      for (let j = i + 1; j < particles.length; j++) {
        const p2 = particles[j];
        const dx = p.x - p2.x;
        const dy = p.y - p2.y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist < 120) {
          ctx.beginPath();
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(p2.x, p2.y);
          ctx.strokeStyle = `rgba(14, 165, 233, ${0.12 * (1 - dist / 120)})`;
          ctx.lineWidth = 0.6;
          ctx.stroke();
        }
      }
    }

    requestAnimationFrame(render);
  }

  render();
}

// ─── 10. BOSHLANG'ICH YUKLANISH ───
window.addEventListener('DOMContentLoaded', () => {
  // Hello World namunasini default qo'yish
  codeEditor.value = TEMPLATES.hello;
  updateLineNumbers();
  updateCursorInfo();
  initCanvas();
  checkServerHealth();
});
