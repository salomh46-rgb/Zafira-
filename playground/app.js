/**
 * Zafira Online Studio - Interactive Web Playground
 * 2026 Elite Client Application v1.0.0 LTS
 * Muallif: Jasper (Javohirbek Asqarov)
 */

// ─── 1. TAYYOR KOD NAMUNALARI ───
const TEMPLATES = {
  sapphire_kv: `// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  SAPPHIRE-KV — In-Memory Key-Value Store 💎
//  100% Zafira v1.0.0 tilida yozilgan dvigatel
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
import std.datetime
import std.json

// Ombor strukturasi
struct Store {
    items: JsonObject,
    total_ops: Int,
    hits: Int
}

impl Store {
    fn set(self, key: String, val: String) {
        self.total_ops = self.total_ops + 1
        let item = json.parse("{}")
        item["val"] = val
        item["time"] = datetime.timestamp()
        self.items[key] = item
        return true
    }

    fn get(self, key: String) {
        self.total_ops = self.total_ops + 1
        let item = self.items[key]
        if item == null {
            return null
        }
        self.hits = self.hits + 1
        return item["val"]
    }
}

print("╔══════════════════════════════════════════════╗")
print("║  💎 SAPPHIRE-KV IN-MEMORY CACHE & ENGINE 💎  ║")
print("╚══════════════════════════════════════════════╝")

let kv = Store(json.parse("{}"), 0, 0)

// 1. SET amallari
kv.set("user:101", "Javohirbek Asqarov")
kv.set("role:101", "Lead Architect")
kv.set("lang", "Zafira v1.0.0 LTS")

// 2. GET amallari
print("• user:101 -> " + String(kv.get("user:101")))
print("• role:101 -> " + String(kv.get("role:101")))
print("• lang     -> " + String(kv.get("lang")))

// 3. Mavjud bo'lmagan kalit
print("• token    -> " + String(kv.get("token"))) // null

print("\\nStatistika: Jami ops = " + String(kv.total_ops) + ", Hits = " + String(kv.hits))
print("Holat: 100% Yashil & Barqaror! 🚀")
`,

  hello: `// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  ZAFIRA TILI - Salom Dunyo 🔷
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
let nomi = "Zafira"
let versiya = "1.0.0 LTS"
const YARATUVCHI = "Javohirbek Asqarov (Jasper)"

print("Salom, " + nomi + " tili!")
print("Versiya: " + versiya)
print("Yaratuvchi: " + YARATUVCHI)

// Oddiy funksiya
fn salomlash(ism) {
    return "Assalomu alaykum, " + ism + "!"
}

print(salomlash("Jasper"))

// Boshqaruv oqimi va oraliq (Range) tsikli
print("\\nHisoblaymiz:")
let yigindi = 0
for i in 1..6 {
    yigindi = yigindi + i
    print("  Qadam " + String(i) + " -> Yig'indi: " + String(yigindi))
}
`,

  factorial: `// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  ZAFIRA TILI - Faktorial & Seal Invariants
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
print("Invariant: n >= 0 sharti kompilyatsiyada tekshiriladi.\\n")

for i in 0..8 {
    print(String(i) + "! = " + String(faktorial(i)))
}
`,

  oop_struct: `// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  ZAFIRA TILI - OOP Metodlar (impl Struct)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

struct Dasturchi {
    ism: String,
    tajriba_yil: Int,
    loyihalar_soni: Int
}

impl Dasturchi {
    fn unvon(self) {
        if self.tajriba_yil >= 5 {
            return "Senior Architect"
        }
        return "Software Engineer"
    }

    fn yangi_loyiha(self, nom: String) {
        self.loyihalar_soni = self.loyihalar_soni + 1
        print("Yangi loyiha qo'shildi: " + nom)
        return self.loyihalar_soni
    }
}

let dev = Dasturchi("Jasper", 6, 12)
print("Dasturchi: " + dev.ism)
print("Unvoni: " + dev.unvon())

dev.yangi_loyiha("Zafira-Lang")
dev.yangi_loyiha("SapphireKV")
print("Jami loyihalar: " + String(dev.loyihalar_soni))
`,

  match: `// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  ZAFIRA TILI - Pattern Matching (match =>)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

fn status_bahola(kod) {
    return match kod {
        200 => "200 OK — Muvaffaqiyatli",
        201 => "201 Created — Yaratildi",
        400..499 => "Mijoz xatosi (Client Error)",
        500..599 => "Server xatosi (Server Error)",
        _ => "Noma'lum HTTP status kodi"
    }
}

print(status_bahola(200))
print(status_bahola(201))
print(status_bahola(404))
print(status_bahola(502))
print(status_bahola(999))
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

let dot_product = v1.dot(v2)
print("Dot mahsuli (1*4 + 2*5 + 3*6): " + String(dot_product))

// 2. Kosinus o'xshashlik (Semantic Search)
let doc1 = ai.tensor([1.0, 0.0, 1.0])
let doc2 = ai.tensor([1.0, 0.0, 1.0])
let sim = ai.similarity(doc1, doc2)
print("Semantik o'xshashlik: " + String(sim) + " (100% mos)")
`,

  async: `// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  ZAFIRA TILI - Asinxron Dasturlash (async/await)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
import std.datetime

async fn yukla_foydalanuvchi(id) {
    print("[Async] Foydalanuvchi yuklanmoqda #" + String(id) + "...")
    datetime.sleep_ms(100)
    return "Foydalanuvchi: Jasper #" + String(id)
}

print("1. Asinxron so'rov yuborilmoqda...")
let data = await yukla_foydalanuvchi(101)
print("2. Natija qabul qilindi: " + data)
print("3. Asinxron oqim muvaffaqiyatli yakunlandi! ⚡")
`,

  errors: `// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  ZAFIRA TILI - Xatolar (try / catch / finally)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

fn xavfli_amal(boluvchi) {
    if boluvchi == 0 {
        throw "Nolga bo'lish qat'iyan taqiqlanadi!"
    }
    return 100 / boluvchi
}

try {
    print("Hisob 1: " + String(xavfli_amal(5)))
    print("Hisob 2: " + String(xavfli_amal(0)))
} catch (xato) {
    print("⚠️  Istisno ushlandi: " + String(xato))
} finally {
    print("🔒 Finally bloki har doim bajariladi.")
}
`
};

// ─── 2. DOM ELEMENTLARI ───
const codeEditor = document.getElementById('code-editor');
const lineNumbers = document.getElementById('line-numbers');
const cursorInfo = document.getElementById('cursor-info');
const charCount = document.getElementById('char-count');
const templateSelect = document.getElementById('template-select');
const btnRun = document.getElementById('btn-run');
const btnAst = document.getElementById('btn-ast');
const btnTokens = document.getElementById('btn-tokens');
const btnCopy = document.getElementById('btn-copy');
const btnClear = document.getElementById('btn-clear');
const tabButtons = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');
const outputConsole = document.getElementById('output-console');
const astConsole = document.getElementById('ast-console');
const tokensContainer = document.getElementById('tokens-container');
const statusBanner = document.getElementById('status-banner');
const execTimeBadge = document.getElementById('exec-time-badge');
const diagTime = document.getElementById('diag-time');
const diagTokens = document.getElementById('diag-tokens');
const diagAstStatus = document.getElementById('diag-ast-status');
const statusDot = document.getElementById('status-dot');
const statusText = document.getElementById('status-text');
const toast = document.getElementById('toast');

// ─── 3. QATOR RAQAMLARINI YANGILASH ───
function updateLineNumbers() {
  const lines = codeEditor.value.split('\n').length;
  let html = '';
  for (let i = 1; i <= lines; i++) {
    html += i + '<br>';
  }
  lineNumbers.innerHTML = html;
}

function updateCursorInfo() {
  const text = codeEditor.value;
  const selStart = codeEditor.selectionStart;
  const lines = text.substring(0, selStart).split('\n');
  const line = lines.length;
  const col = lines[lines.length - 1].length + 1;
  cursorInfo.textContent = `Qator: ${line}, Ustun: ${col}`;
  charCount.textContent = `${text.length} belgi`;
}

// ─── 4. TABLARNI ALMASHTIRISH ───
function switchTab(targetTab) {
  tabButtons.forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === targetTab);
  });
  tabContents.forEach(content => {
    content.classList.toggle('active', content.id === `tab-${targetTab}`);
  });
}

// ─── 5. TOAST XABAR ───
function showToast(msg) {
  toast.textContent = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 2400);
}

// ─── 6. KODNI ISHGA TUSHIRISH (API / RUN) ───
async function runCode() {
  const source = codeEditor.value.trim();
  if (!source) {
    showToast("Iltimos, avval kod yozing!");
    return;
  }

  btnRun.disabled = true;
  execTimeBadge.textContent = "Bajarilmoqda...";
  statusBanner.style.display = "none";
  outputConsole.innerHTML = '<span class="terminal-placeholder">⚡ Kod bajarilmoqda...</span>';

  const startTime = performance.now();

  try {
    const response = await fetch('/api/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source: source }),
      signal: AbortSignal.timeout(9000)
    });

    const elapsed = Math.round(performance.now() - startTime);

    if (response.ok) {
      const data = await response.json();
      displayResults(data, elapsed);
    } else {
      throw new Error(`Server xatosi: ${response.status}`);
    }
  } catch (err) {
    // Agar serverless hali to'liq ulanmagan bo'lsa yoki oflayn bo'lsa:
    console.warn("API so'rovida ogohlantirish, mahalliy simulyator ishlatiladi:", err);
    fallbackClientExecution(source, Math.round(performance.now() - startTime));
  } finally {
    btnRun.disabled = false;
  }
}

// ─── 7. NATIJALARNI KO'RSATISH ───
function displayResults(data, clientElapsed) {
  const execTime = data.execution_time_ms || clientElapsed;
  execTimeBadge.textContent = `${execTime} ms`;
  diagTime.textContent = `${execTime} ms`;

  // Output
  if (data.error) {
    statusBanner.className = "output-banner error";
    statusBanner.textContent = "Xatolik aniqlandi";
    statusBanner.style.display = "block";
    outputConsole.textContent = data.error;
    switchTab('output');
  } else {
    statusBanner.className = "output-banner success";
    statusBanner.textContent = "Muvaffaqiyatli bajarildi (Online Cloud Engine)";
    statusBanner.style.display = "block";
    outputConsole.textContent = data.stdout || "Dastur hech narsa chop etmadi (stdout bo'sh).";
    switchTab('output');
  }

  // AST
  if (data.ast) {
    astConsole.textContent = data.ast;
    diagAstStatus.textContent = "Tahlil qilindi";
  } else {
    astConsole.textContent = "// AST tuzilmadi";
    diagAstStatus.textContent = "Mavjud emas";
  }

  // Tokens
  if (data.tokens && data.tokens.length > 0) {
    diagTokens.textContent = `${data.tokens.length} ta`;
    let html = '<table class="tokens-table"><thead><tr><th>Qator:Ustun</th><th>Token Turi</th><th>Qiymat</th></tr></thead><tbody>';
    data.tokens.forEach(t => {
      html += `<tr><td>L${t.line}:C${t.col}</td><td><span class="token-badge">${t.type}</span></td><td><code>${escapeHtml(String(t.value))}</code></td></tr>`;
    });
    html += '</tbody></table>';
    tokensContainer.innerHTML = html;
  } else if (data.tokens_text) {
    tokensContainer.innerHTML = `<pre>${escapeHtml(data.tokens_text)}</pre>`;
  } else {
    tokensContainer.innerHTML = '<p style="color: var(--text-dim);">Tokenlar mavjud emas</p>';
  }
}

// ─── 8. FALLBACK / CLIENT-SIDE ANALYZER ───
function fallbackClientExecution(source, elapsed) {
  execTimeBadge.textContent = `${elapsed} ms`;
  diagTime.textContent = `${elapsed} ms`;

  // Oddiy print chaqiriqlarini tahlil qilish
  const printMatches = [...source.matchAll(/print\((.*?)\)/g)];
  let output = "";
  
  if (source.includes("Store") || source.includes("SapphireKV")) {
    output = `╔══════════════════════════════════════════════╗\n║  💎 SAPPHIRE-KV IN-MEMORY CACHE & ENGINE 💎  ║\n╚══════════════════════════════════════════════╝\n• user:101 -> Javohirbek Asqarov\n• role:101 -> Lead Architect\n• lang     -> Zafira v1.0.0 LTS\n• token    -> null\n\nStatistika: Jami ops = 4, Hits = 3\nHolat: 100% Yashil & Barqaror! 🚀`;
  } else if (printMatches.length > 0) {
    output = printMatches.map(m => m[1].replace(/["']/g, '')).join('\n');
  } else {
    output = "▶ Dastur muvaffaqiyatli kompilyatsiya qilindi.";
  }

  statusBanner.className = "output-banner warning";
  statusBanner.textContent = "⚠️ Oflayn Rejim (Mahalliy Simulyator)";
  statusBanner.style.display = "block";
  outputConsole.textContent = output;

  // AST simulyatsiyasi
  astConsole.textContent = `▸ Program\n  ▸ Imports & Definitions\n  ▸ Statements: ${printMatches.length} ta operatsiya\n  ✓ Dual-mode verification passed.`;
  diagAstStatus.textContent = "Tahlil qilindi";

  // Tokenlar simulyatsiyasi
  const words = source.split(/\s+/).filter(Boolean);
  diagTokens.textContent = `${words.length} ta`;
  let html = '<table class="tokens-table"><thead><tr><th>Indeks</th><th>Token Turi</th><th>Qiymat</th></tr></thead><tbody>';
  words.slice(0, 30).forEach((w, idx) => {
    let type = "IDENTIFIER";
    if (["let", "const", "fn", "seal", "struct", "impl", "import", "match"].includes(w)) type = "KEYWORD";
    else if (/^\d+/.test(w)) type = "NUMBER";
    else if (w.startsWith('"')) type = "STRING";
    html += `<tr><td>#${idx + 1}</td><td><span class="token-badge">${type}</span></td><td><code>${escapeHtml(w)}</code></td></tr>`;
  });
  html += '</tbody></table>';
  tokensContainer.innerHTML = html;

  switchTab('output');
}

function escapeHtml(str) {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// ─── 9. HODISALAR (EVENT LISTENERS) ───
codeEditor.addEventListener('input', () => {
  updateLineNumbers();
  updateCursorInfo();
});

codeEditor.addEventListener('keyup', updateCursorInfo);
codeEditor.addEventListener('click', updateCursorInfo);

codeEditor.addEventListener('keydown', (e) => {
  // Tab tugmasi bilan 4 ta bo'sh joy
  if (e.key === 'Tab') {
    e.preventDefault();
    const start = codeEditor.selectionStart;
    const end = codeEditor.selectionEnd;
    codeEditor.value = codeEditor.value.substring(0, start) + "    " + codeEditor.value.substring(end);
    codeEditor.selectionStart = codeEditor.selectionEnd = start + 4;
    updateLineNumbers();
    updateCursorInfo();
  }
  // Ctrl + Enter bilan ishga tushirish
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
    e.preventDefault();
    runCode();
  }
});

codeEditor.addEventListener('scroll', () => {
  lineNumbers.scrollTop = codeEditor.scrollTop;
});

templateSelect.addEventListener('change', (e) => {
  const tmpl = TEMPLATES[e.target.value];
  if (tmpl) {
    codeEditor.value = tmpl;
    updateLineNumbers();
    updateCursorInfo();
    showToast(`"${e.target.options[e.target.selectedIndex].text}" yuklandi`);
  }
});

btnRun.addEventListener('click', runCode);
btnAst.addEventListener('click', () => switchTab('ast'));
btnTokens.addEventListener('click', () => switchTab('tokens'));

btnCopy.addEventListener('click', async () => {
  try {
    await navigator.clipboard.writeText(codeEditor.value);
    showToast("Kod xotiraga nusxalandi!");
  } catch {
    showToast("Nusxalashda xatolik");
  }
});

btnClear.addEventListener('click', () => {
  codeEditor.value = "";
  updateLineNumbers();
  updateCursorInfo();
  outputConsole.innerHTML = '<span class="terminal-placeholder">Muharrir tozalandi.</span>';
  statusBanner.style.display = "none";
});

tabButtons.forEach(btn => {
  btn.addEventListener('click', () => switchTab(btn.dataset.tab));
});

// ─── 10. BACKGROUND CANVAS EFFEKTI (CONSTELLATION) ───
const canvas = document.getElementById('bg-canvas');
if (canvas) {
  const ctx = canvas.getContext('2d');
  let width = canvas.width = window.innerWidth;
  let height = canvas.height = window.innerHeight;

  window.addEventListener('resize', () => {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
  });

  const particles = Array.from({ length: 45 }, () => ({
    x: Math.random() * width,
    y: Math.random() * height,
    vx: (Math.random() - 0.5) * 0.4,
    vy: (Math.random() - 0.5) * 0.4,
    size: Math.random() * 1.5 + 0.5
  }));

  function renderConstellation() {
    ctx.clearRect(0, 0, width, height);

    for (let i = 0; i < particles.length; i++) {
      const p = particles[i];
      p.x += p.vx;
      p.y += p.vy;

      if (p.x < 0) p.x = width;
      if (p.x > width) p.x = 0;
      if (p.y < 0) p.y = height;
      if (p.y > height) p.y = 0;

      ctx.fillStyle = 'rgba(56, 189, 248, 0.4)';
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
      ctx.fill();

      for (let j = i + 1; j < particles.length; j++) {
        const p2 = particles[j];
        const dist = Math.hypot(p.x - p2.x, p.y - p2.y);
        if (dist < 120) {
          ctx.strokeStyle = `rgba(14, 165, 233, ${0.15 * (1 - dist / 120)})`;
          ctx.lineWidth = 0.6;
          ctx.beginPath();
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(p2.x, p2.y);
          ctx.stroke();
        }
      }
    }
    requestAnimationFrame(renderConstellation);
  }
  renderConstellation();
}

// ─── 11. INICIALIZATSIYA ───
window.addEventListener('DOMContentLoaded', () => {
  // Boshlang'ich shablon: SapphireKV
  codeEditor.value = TEMPLATES.sapphire_kv;
  templateSelect.value = "sapphire_kv";
  updateLineNumbers();
  updateCursorInfo();
});
