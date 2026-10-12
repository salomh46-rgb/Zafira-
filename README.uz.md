# 🔷 Zafira Dasturlash Tili (O'zbekcha Hujjat)

<p align="center">
  <img src="https://raw.githubusercontent.com/salomh46-rgb/Zafira-/main/vscode-zafira/icon.png" alt="Zafira Language Logo" width="128" height="128" />
</p>

<p align="center">
  <strong>"Qattiq, tiniq, sinmas — xuddi sapfir toshi kabi mukammal"</strong><br>
  <em>Silicon-Native | Dual-Mode (Draft & Seal) | AI-First & Python-Interop Dasturlash Tili</em>
</p>

<p align="center">
  <a href="https://github.com/salomh46-rgb/Zafira-/releases"><img src="https://img.shields.io/badge/version-v1.0.0--LTS-0ea5e9.svg?style=for-the-badge&logo=codeforces" alt="Version"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg?style=for-the-badge" alt="License"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/runtime-Python_3.11+-3776ab.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python"></a>
  <a href="#"><img src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-0284c7.svg?style=for-the-badge" alt="Platform"></a>
  <a href="#"><img src="https://img.shields.io/badge/tests-333%2F333_Passing-10b981.svg?style=for-the-badge&logo=checkmarx" alt="Tests"></a>
  <a href="vscode-zafira/INSTALL.md"><img src="https://img.shields.io/badge/VS_Code_Extension-v0.1.0-007acc.svg?style=for-the-badge&logo=visualstudiocode&logoColor=white" alt="VS Code"></a>
</p>

<p align="center">
  <a href="README.md">🇬🇧 Read in English</a> | <strong>🇺🇿 O'zbekcha versiya</strong>
</p>

---

## 📖 Zafira Nima va Nega Kerak?

**Zafira** — sun'iy intellekt davri uchun maxsus loyihalashtirilgan, kremniy chiplari (CPU, GPU, NPU) bilan bevosita til darajasida gaplashuvchi, zamonaviy **Silicon-Native & Dual-Mode** dasturlash tilidir. Bugungi kunda dasturchilar Python-ning qulayligi bilan C++/Rust-ning tezligi va xotira xavfsizligi o'rtasida tanlov qilishga majbur. Zafira bu murosani yo'qotadi: dastlabki prototipni erkin (`draft`) rejimda yozasiz, ishlab chiqarishga tayyor bo'lgach esa qattiq turdagi formal invariantlar bilan muhrlaysiz (`seal`). Natijada dasturchi Python kutubxonalarining boy ekotizimini (`import py.*`) to'g'ridan-to'g'ri ishlatgan holda, chip darajasidagi xavfsiz va shiddatli tezlikka erishadi.

📚 **Rasmiy Hujjatlar va Flagman Loyihalar:**
- [To'liq Til Spetsifikatsiyasi (SPECIFICATION.md)](docs/SPECIFICATION.md)
- [1-Sahifalik Tezkor Ma'lumotnoma (CHEATSHEET.md)](docs/CHEATSHEET.md)
- [💎 SapphireKV — In-Memory Kesh va Kalit-Qiymat Ombori (100% Zafira)](examples/sapphire_kv/README.md)
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

## 🚀 Tezkor Boshlash

```bash
git clone https://github.com/salomh46-rgb/Zafira-.git
cd Zafira-
py -3 -X utf8 zafira.py run examples/v1_showcase.zf
```

---

## 👥 Yaratuvchilar

- **Jasper (Javohirbek Asqarov)** — Asoschi, til falsafasi, arxitektura va dizayn.
- **Antigravity AI** — Tizimli dasturlash, algoritmlar, tip tekshiruvi va muhandislik.

---

## 📄 Litsenziya

Zafira dasturlash tili ochiq manbali bo'lib, [MIT Litsenziyasi](LICENSE) asosida tarqatiladi.
