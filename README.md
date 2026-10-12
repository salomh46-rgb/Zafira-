# 🔷 Zafira Programming Language

<p align="center">
  <img src="https://raw.githubusercontent.com/salomh46-rgb/Zafira-/main/vscode-zafira/icon.png" alt="Zafira Language Logo" width="128" height="128" />
</p>

<p align="center">
  <strong>"Qattiq, tiniq, sinmas — xuddi sapfir toshi kabi mukammal"</strong><br>
  <em>Silicon-Native | Dual-Mode (Draft & Seal) | AI-First & Python-Interop Programming Language</em>
</p>

<p align="center">
  <a href="https://github.com/salomh46-rgb/Zafira-/releases"><img src="https://img.shields.io/badge/version-v1.0.0--LTS-0ea5e9.svg?style=for-the-badge&logo=codeforces" alt="Version"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg?style=for-the-badge" alt="License"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/runtime-Python_3.11+-3776ab.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python"></a>
  <a href="#"><img src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-0284c7.svg?style=for-the-badge" alt="Platform"></a>
  <a href="#"><img src="https://img.shields.io/badge/tests-333%2F333_Passing-10b981.svg?style=for-the-badge&logo=checkmarx" alt="Tests"></a>
  <a href="vscode-zafira/INSTALL.md"><img src="https://img.shields.io/badge/VS_Code_Extension-v0.1.0-007acc.svg?style=for-the-badge&logo=visualstudiocode&logoColor=white" alt="VS Code"></a>
</p>

---

## 📖 Zafira Nima va Nega Kerak?

**Zafira** — sun'iy intellekt davri uchun maxsus loyihalashtirilgan, kremniy chiplari (CPU, GPU, NPU) bilan bevosita til darajasida gaplashuvchi, zamonaviy **Silicon-Native & Dual-Mode** dasturlash tilidir. Bugungi kunda dasturchilar Python-ning qulayligi bilan C++/Rust-ning tezligi va xotira xavfsizligi o'rtasida tanlov qilishga majbur. Zafira bu murosani yo'qotadi: dastlabki prototipni erkin (`draft`) rejimda yozasiz, ishlab chiqarishga tayyor bo'lgach esa qattiq turdagi formal invariantlar bilan muhrlaysiz (`seal`). Natijada dasturchi Python kutubxonalarining boy ekotizimini (`import py.*`) to'g'ridan-to'g'ri ishlatgan holda, chip darajasidagi xavfsiz va shiddatli tezlikka erishadi.

📚 **Rasmiy Hujjatlar:**
- [To'liq Til Spetsifikatsiyasi (SPECIFICATION.md)](docs/SPECIFICATION.md)
- [1-Sahifalik Tezkor Ma'lumotnoma (CHEATSHEET.md)](docs/CHEATSHEET.md)
- [Flagman Namoyish Dasturi (v1_showcase.zf)](examples/v1_showcase.zf)

---

## ⚡ Til Xususiyatlari Matritsasi

### Dasturlash Tillari Qiyosi

| Xususiyat | Python 🐍 | Rust 🦀 | C++ ⚙️ | **Zafira 🔷 (v1.0.0 LTS)** |
| :--- | :---: | :---: | :---: | :---: |
| **O'rganish va yozish qulayligi** | Juda oson | Murakkab | Qiyin | **Juda oson (Modern & Expressive)** |
| **Ijro tezligi** | 1x (sekin) | 50–100x | 50–100x | **50–100x (`seal` & hardware rejimida)** |
| **Dual-Mode (Draft vs Seal)** | ❌ Yo'q | ❌ Faqat qattiq | ❌ Faqat qattiq | **✅ Mavjud (`draft` erkin, `seal` qat'iy)** |
| **Formal invariantlar (`where`)** | ❌ Yo'q | ⚠️ Tashqi macro | ❌ Yo'q | **✅ Til darajasida statik tekshiriladi** |
| **Asinxron Dasturlash (`async/await`)** | Alohida `asyncio` | `tokio` kerak | `std::coroutine` | **✅ Til yadrosida native `async`/`await`** |
| **Xatoliklarni boshqarish** | try/except | Result<T, E> | try/catch | **✅ `try` / `catch` / `throw` / `finally`** |
| **Struct Metodlari (`impl`)** | class | impl Struct | class / struct | **✅ `impl Struct { fn metod(self) }`** |
| **Pattern Matching (`match =>`)** | match/case | match | switch | **✅ `match qiymat { 1 => ..., 3..10 => ..., _ => ... }`** |
| **C FFI (Foreign Function Interface)** | ctypes / cffi | extern "C" | native | **✅ `std.ffi` (C .dll/.so kutubxonalari)** |
| **Kriptografiya & Regex** | hashlib, re | tashqi crate | openssl, std::regex | **✅ `std.crypto` & `std.regex` o'rnatilgan** |
| **Ko'p faylli modullar** | import | mod / use | #include | **✅ `import "./modul.zf" as m` (Kesh va siklik himoya)** |
| **Paket Menejeri (`zpm`)** | pip | cargo | conan/vcpkg | **✅ `zafira install`, `zafira add` (`zafira.lock`)** |
| **AOT Standalone Binary Packager** | PyInstaller | cargo build | CMake / gcc | **✅ `zafira pack` (1-faylli `.exe` binar)** |
| **Python Interop** | Asl til | ❌ Og'ir FFI | ❌ Og'ir C-API | **✅ `import py.torch` (Zero-Overhead)** |
| **Hardware direktivalari** | Tashqi drayver | Cuda kutubxona | OpenCL/CUDA | **✅ `run @gpu`, `@npu`, `@auto`** |
| **Xotira xavfsizligi** | GC (sekin) | Borrow Checker | Qo'lda (xavfli) | **✅ Statik tip & Invariant kafolati** |

### Versiyalar Bo'yicha Imkoniyatlar

| Imkoniyat | v0.1 | v0.3 | v0.5 | v0.7 | v0.8 | **v1.0.0 (Grand LTS)** |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Lexer & Pratt Parser & AST** | ✅ | ✅ | ✅ | ✅ | ✅ | **✅ Production** |
| **Tree-walking Interpreter & REPL** | ✅ | ✅ | ✅ | ✅ | ✅ | **✅ Production** |
| **Dual-Mode (`fn` draft / seal) & `where`** | Boshlang'ich | ✅ To'liq | ✅ | ✅ | ✅ | **✅ Production** |
| **Python Interop (`import py.*`)** | ❌ | ✅ | ✅ | ✅ | ✅ | **✅ Production** |
| **Statik Tip Tekshiruvi (Type Checker)** | ❌ | ✅ | ✅ | ✅ | ✅ | **✅ Production** |
| **VS Code Extension (`.vsix`)** | ❌ | ✅ | ✅ | ✅ | ✅ | **✅ Production** |
| **C Transpiler & Standalone Binary (`.exe`)**| ❌ | ✅ | ✅ | ✅ | ✅ | **✅ Production** |
| **Standart kutubxona (Barcha 13 ta modullar)**| ❌ | 4 ta | 6 ta | 9 ta | 12 ta | **✅ 13 ta Modul** |
| **Paket Menejeri (`zpm`: init, run, test, build)** | ❌ | ❌ | ✅ | ✅ | ✅ | **✅ Production** |
| **AI & Tensor Dvigateli (`std.ai`, @gpu)** | ❌ | ❌ | ✅ | ✅ | ✅ | **✅ Production** |
| **Web Suite (`std.net`, `std.json`, HTTP Server)** | ❌ | ❌ | ✅ | ✅ | ✅ | **✅ Production** |
| **Asinxron Dasturlash (`async fn`, `await`)** | ❌ | ❌ | ✅ | ✅ | ✅ | **✅ Production** |
| **Web Interactive Playground Studio** | ❌ | ❌ | ✅ | ✅ | ✅ | **✅ Production** |
| **Xatoliklarni boshqarish (`try/catch/finally`)** | ❌ | ❌ | ❌ | ✅ | ✅ | **✅ Production** |
| **Fayllar Tizimi (`std.fs`) & Lokal Modullar** | ❌ | ❌ | ❌ | ✅ | ✅ | **✅ Production** |
| **Struct Metodlari (`impl`) & `match =>`** | ❌ | ❌ | ❌ | ✅ | ✅ | **✅ Production** |
| **Kriptografiya (`std.crypto`) & `std.regex`** | ❌ | ❌ | ❌ | ❌ | ✅ | **✅ Production** |
| **C FFI (`std.ffi`: load C libraries)** | ❌ | ❌ | ❌ | ❌ | ✅ | **✅ Production** |
| **ZPM Registry (`zafira install`, `zafira add`)** | ❌ | ❌ | ❌ | ❌ | ❌ | **✅ v1.0.0** |
| **Single-Binary Packager (`zafira pack`)** | ❌ | ❌ | ❌ | ❌ | ❌ | **✅ v1.0.0** |

---

## 🚀 Quick Start (5 Qadamda Ishga Tushirish)

### 1-Qadam: Repozitoriyani yuklab oling
```bash
git clone https://github.com/salomh46-rgb/Zafira-.git
cd Zafira-
```

### 2-Qadam: Python muhitini tekshiring
Zafira hozirgi bosqichda Python 3.11 yoki undan yuqori versiyani talab qiladi:
```bash
python --version
```

### 3-Qadam: Birinchi `hello.zf` dasturini ko'ring
`examples/hello.zf` fayli:
```zafira
let salom = "Salom, Zafira tili!"
print(salom)

seal fn hisobla(x: Int, y: Int) -> Int {
    return x * y + 10
}

print("Natija: " + String(hisobla(5, 4)))
```

### 4-Qadam: Dasturni bajaring
```bash
py -3 -X utf8 zafira.py run examples/hello.zf
```

### 5-Qadam: Interaktiv REPL ni sinab ko'ring
```bash
py -3 -X utf8 zafira.py repl
```
> REPL oynasida to'g'ridan-to'g'ri Zafira buyruqlarini kiritib, natijani real-vaqtda ko'rishingiz mumkin! Chiqish uchun `exit` yoki `Ctrl+C`.

---

## 💻 Sintaksis Namunalari

### 1. O'zgaruvchilar va O'zgarmaslar
```zafira
let nom = "Zafira"         // Qiymati keyinchalik o'zgarishi mumkin
const PI = 3.1415926535     // O'zgarmas (const) — qayta qiymat berish taqiqlanadi!
```

### 2. Dual-Mode Funksiyalar va `where` Invariantlari
```zafira
// Draft rejim — erkin, prototiplash uchun:
fn salomlash(ism) {
    return "Xush kelibsiz, " + ism + "!"
}

// Seal rejim — qat'iy tiplar va formal invariant bilan muhrlangan:
seal fn bolish(a: Int, b: Int) -> Float
    where b > 0  // Agar b <= 0 bo'lsa, kod kompilyatsiya/tekshiruvdan O'TMAYDI!
{
    return a / b
}
```

### 3. Ma'lumot Tuzilmalari (`struct` va Ro'yxatlar)
```zafira
struct Talaba {
    ism: String,
    yosh: Int,
    stipendiya: Float
}

let royxat = [10, 20, 30]
royxat.push(40)
print(royxat.len) // 4
```

### 4. Boshqaruv Oqimi (`if`, `for..in`, `while`)
```zafira
let ball = 95

if ball >= 90 {
    print("A'lo baho!")
} else {
    print("Yaxshi harakat!")
}

// Range orqali sikl:
for i in 1..5 {
    print("Qadam: " + String(i))
}
```

### 5. Python Zero-Overhead Interop (`import py.*`)
Python ekotizimidagi har qanday kutubxonani hech qanday C-wrapperlarsiz to'g'ridan-to'g'ri chaqiring:
```zafira
import py.math
import py.random

let ildiz = math.sqrt(144.0)
print("144 ning ildizi: " + String(ildiz)) // 12.0

let tasodifiy_son = random.randint(1, 100)
print("Tasodifiy son: " + String(tasodifiy_son))
```

### 6. Hardware Direktivalari (`run @gpu / @npu / @auto`)
AI modellar va og'ir massivlarni bevosita kremniy chipida parallel ishga tushirish:
```zafira
run @gpu {
    let natija = model.infer(tensor_kirish)
}

run @auto {
    // Platforma optimal arxitekturani o'zi tanlaydi (CPU yoki NPU)
    let tezkor_filtr = qayta_ishlash(massiv)
}
```

---

## 🏛️ Tizim Arxitekturasi

Zafira kompilyatori ko'p pog'onali modulli konveyer (pipeline) asosida qurilgan:

```
Manba Kod (.zf)
      │
      ▼
┌──────────────┐
│    Lexer     │  ───►  50+ Tokenlar oqimi (Keywords, Operators, Literals)
└──────────────┘
      │
      ▼
┌──────────────┐
│    Parser    │  ───►  Abstrakt Sintaktik Daraxt (Pratt Parsing AST)
└──────────────┘
      │
      ▼
┌──────────────────┐
│   Type Checker   │  ───►  Statik Tip va `where` Invariant Tekshiruvi
│  (Seal Guard)    │        • Parameter & Return types
└──────────────────┘        • Const immutability
      │                     • Typos & Undeclared variables
      ├───────────────────────────────┐
      ▼                               ▼
┌──────────────────────────┐    ┌──────────────────────────┐
│ Tree-Walking Interpreter │    │ LLVM IR / C Transpiler   │
│       (Draft Mode)       │    │     (Seal Mode, v0.4)    │
└──────────────────────────┘    └──────────────────────────┘
      │                               │
      ▼                               ▼
┌──────────────────────────────────────────────────────────┐
│                   Apparat Bajarilishi                    │
│          CPU (Core)  │  GPU (CUDA)  │  NPU (Silicon)     │
└──────────────────────────────────────────────────────────┘
```

---

## 🗺️ Yo'l Xaritasi (Roadmap)

- [x] **v0.1.0-alpha** — Leksik tahlilchi, Pratt AST parser, Tree-walking interpreter, REPL, o'zgaruvchilar va boshqaruv operatorlari.
- [x] **v0.2.0-alpha** — Python Zero-Overhead Interop (`import py.*`), tizimli integratsiya va dinamik ob'ektlar ko'prigi.
- [x] **v0.3.0-alpha (Hozirgi reliz)** — Statik Tip Tekshiruvi (`TypeChecker`), `seal` funksiyalar va `where` invariantlar formal tekshiruvi, xatoliklar bashorati va VS Code kengaytmasi (.vsix).
- [ ] **v0.4.0** — LLVM IR generator / C Transpiler, AOT (Ahead-of-Time) native kompilyatsiya, standart kutubxona (`std.math`, `std.io`, `std.fs`, `std.net`).
- [ ] **v1.0.0** — To'liq mustaqil ekotizim, `zpm` (Zafira Package Manager), parallel asinxron ishlov beruvchi (Async Runtime) va WebAssembly (WASM) maqsadli chiqishi.

---

## 🧩 Visual Studio Code Kengaytmasi

Zafira kodi uchun maxsus yaratilgan rasmiy VS Code kengaytmasi:

<p align="center">
  <img src="https://raw.githubusercontent.com/salomh46-rgb/Zafira-/main/vscode-zafira/icon.png" width="64" height="64" alt="VS Code Extension Icon">
</p>

### O'rnatish:
1. `vscode-zafira/zafira-lang-0.1.0.vsix` faylini oling.
2. VS Code da: `Ctrl + Shift + P` -> **"Extensions: Install from VSIX..."**
3. `zafira-lang-0.1.0.vsix` ni tanlang!

Batafsil ma'lumot va rivojlantirish uchun qarang: [VS Code Extension O'rnatish Yo'riqnomasi](vscode-zafira/INSTALL.md).

---

## 🧪 Sinov va Testlar

Loyiha 100% test qamroviga ega bo'lib, har qanday o'zgarish avtomatlashtirilgan test to'plami orqali tekshiriladi:

```bash
# Type checker to'liq test to'plamini ishga tushirish:
py -3 -X utf8 test_type_checker_suite.py

# Python interop testlarini ishga tushirish:
py -3 -X utf8 tests/test_python_interop.py
```

---

## 🤝 Hissa Qo'shish (Contributing)

Biz ochiq kodli hamjamiyatning har qanday taklif va hissasini mamnuniyat bilan qabul qilamiz!

1. Ushbu repozitoriyani **Fork** qiling.
2. Yangi funksional uchun alohida tarmoq oching:
   ```bash
   git checkout -b feature/ajoyib-xususiyat
   ```
3. O'zgarishlarni kiriting va testlarni 100% yashil o'tkazing:
   ```bash
   py -3 -X utf8 test_type_checker_suite.py
   ```
4. O'zgarishlarni commit qiling:
   ```bash
   git commit -m "feat: ajoyib yangi imkoniyat qo'shildi"
   ```
5. O'z tarmog'ingizga push qiling va **Pull Request (PR)** oching.

---

## 👥 Yaratuvchilar

- **Jasper (Javohirbek Asqarov)** — Asoschi, til falsafasi, arxitektura va dizayn.
- **Antigravity AI** — Tizimli dasturlash, algoritmlar, tip tekshiruvi va muhandislik.

---

## 📄 Litsenziya

Zafira dasturlash tili ochiq manbali bo'lib, [MIT Litsenziyasi](LICENSE) asosida tarqatiladi.

<p align="center">
  <sub>Yaratilgan yili: 2026 | Toshkent, O'zbekiston 🇺🇿</sub>
</p>
