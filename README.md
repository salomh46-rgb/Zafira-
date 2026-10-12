# 🔷 Zafira Lang

> **"Qattiq, tiniq, sinmas — xuddi sapfir toshi"**
> Silicon-Native | Dual-Mode | AI-First Programming Language

```
╔══════════════════════════════════════════════╗
║   🔷  Z A F I R A   L A N G U A G E  🔷     ║
║        v0.1.0-alpha  |  Silicon-Native       ║
╚══════════════════════════════════════════════╝
```

---

## Nima uchun Zafira?

| Muammo | Python | Rust | **Zafira** |
|:-------|:------:|:----:|:----------:|
| O'rganish qulayligi | ✅ Oson | ❌ Qiyin | ✅ Juda oson |
| Tezlik (vs Python) | 1x | 50-100x | 50-100x (seal rejimida) |
| AI / GPU integratsiyasi | Drayver kerak | Murakkab | **`@gpu`, `@npu`, `@auto` — til grammatikasida** |
| Xotira xavfsizligi | ❌ | ✅ Borrow checker | ✅ `seal` rejimi + `where` invariantlar |
| Python kutubxonalari | ✅ | ❌ | ✅ `import py.torch` — Zero-Copy |

---

## Sintaksis (Bir nazar)

```zafira
// O'zgaruvchilar
let ism = "Zafira"
const VERSIYA = 0.1

// Funksiya (draft — erkin rejim)
fn salomlash(nomi) {
    return "Salom, " + nomi + "!"
}

// Seal funksiya — invariant bilan
seal fn bo'lish(a: Int, b: Int) -> Float
    where b > 0           // b = 0 kelsa kod KOMPILYATSIYA BO'LMAYDI
{
    return a / b
}

// Hardware direktivalari
run @gpu {
    let natija = ai_model.forward(inputs)
}

// Struct
struct Talaba {
    ism: String,
    ball: Int
}

// Ro'yxat va tsikl
let sonlar = [1, 2, 3, 4, 5]
for n in 1..10 {
    print(n)
}
```

---

## O'rnatish va Ishga Tushirish

```bash
git clone https://github.com/jasper/zafira-lang
cd zafira-lang

# Faylni bajarish
py -3 -X utf8 zafira.py run examples/hello.zf

# Interaktiv REPL
py -3 -X utf8 zafira.py repl

# Debug: tokenlarni ko'rish
py -3 -X utf8 zafira.py tokens examples/hello.zf

# Debug: AST daraxti
py -3 -X utf8 zafira.py ast examples/hello.zf
```

---

## Arxitektura

```
zafira-lang/
├── src/
│   ├── lexer.py        # Tokenizatsiya (50+ token turi)
│   ├── parser.py       # Pratt Parser → AST
│   └── interpreter.py  # Tree-walking Interpreter (draft mode)
├── examples/
│   ├── hello.zf        # Salom dunyo
│   └── advanced.zf     # Ilg'or xususiyatlar
├── zafira.py           # CLI: run | repl | tokens | ast
└── README.md
```

### Kompilyatsiya Pog'onaları (Roadmap)

```
Manba Kod (.zf)
     ↓
  [Lexer]  → Tokenlar oqimi
     ↓
  [Parser] → AST daraxti (Pratt Parsing)
     ↓
  [Type Checker] → Tip xavfsizligi (seal mode) ← KEYINGI QADAM
     ↓
  [Compiler] → LLVM IR / Python / C transpiler ← KEYINGI QADAM
     ↓
  Mashina kodi (CPU / GPU / NPU)
```

---

## Xususiyatlar (v0.1.0-alpha)

- [x] **Lexer** — 50+ token, `//` va `/* */` izohlar, Unicode satrlar
- [x] **Parser** — Pratt Parsing algoritmi, to'liq AST
- [x] **Interpreter** — Tree-walking, leksik qamrov (lexical scoping)
- [x] **O'zgaruvchilar** — `let`, `const` (o'zgarmas)
- [x] **Funksiyalar** — `fn`, rekursiya, closures
- [x] **`seal` / `draft` rejimlar** — Dual-mode execution
- [x] **`where` invariantlar** — Formal verifikatsiya (runtime)
- [x] **Struct** — Ma'lumot tuzilmalari
- [x] **Ro'yxatlar** — `.push()`, `.pop()`, `.len`, indekslash
- [x] **Range** — `1..10` sintaksisi
- [x] **`run @gpu / @npu / @auto` bloklar** — Hardware direktivalar
- [x] **REPL** — Interaktiv rejim
- [x] **CLI** — `run`, `repl`, `tokens`, `ast` buyruqlari

### Keyingi bosqich (v0.2.0):

- [ ] **Statik Tip Tekshiruvi** (`seal` rejimida kompilyatsiya vaqtida)
- [ ] **Python Interop** — `import py.torch` → to'g'ridan-to'g'ri PyTorch chaqirish
- [ ] **LLVM / C Transpiler** — Tezkor mashina kodiga kompilyatsiya
- [ ] **Standart kutubxona** — `std.math`, `std.io`, `std.net`
- [ ] **VS Code / Neovim** — Sintaksis ajratish (Syntax Highlighting)

---

## Yaratuvchilar

- **Jasper (Javohirbek Asqarov)** — G'oya, til falsafasi va dizayn
- **Antigravity AI** — Arxitektura, dasturlash va implementatsiya

> *"Kelajak dasturchisi sintaksis bilan emas, g'oya bilan ovora bo'lishi kerak."*
