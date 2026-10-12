# 🔷 Zafira Programming Language

<p align="center">
  <img src="https://raw.githubusercontent.com/salomh46-rgb/Zafira-/main/vscode-zafira/icon.png" alt="Zafira Language Logo" width="128" height="128" />
</p>

<p align="center">
  <strong>"Rigid, crystal-clear, unbreakable — as flawless as a sapphire"</strong><br>
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

<p align="center">
  <strong>🇬🇧 English</strong> | <a href="README.uz.md">🇺🇿 O'zbekcha versiya</a>
</p>

---

## 📖 What is Zafira and Why Does It Exist?

**Zafira** is a modern **Silicon-Native & Dual-Mode** programming language designed specifically for the generative AI era. It communicates directly with silicon hardware (CPU, GPU, NPU) at the language grammar level while bridging high developer ergonomics with C/Rust-grade performance.

Historically, software engineers have been forced to make a painful compromise:
- Choose **Python** for its expressiveness, rapid iteration, and unmatched AI ecosystem — at the cost of slow single-threaded execution, memory bloat, and runtime type fragility.
- Choose **C++ or Rust** for bare-metal speed and type safety — at the cost of steep learning curves, verbose syntax, and long compile times.

**Zafira eliminates this tradeoff through its Dual-Mode Execution Architecture:**
1. **`draft` Mode**: Write freeform, dynamic code for ultra-fast prototyping without cumbersome boilerplate or strict annotations.
2. **`seal` Mode**: When preparing for production, seal functions with strict types and formal `where` invariants that are statically proven at compile-time before code ever runs.
3. **Zero-Overhead Python Bridge**: Seamlessly import any library in the Python universe (`import py.torch`, `import py.pandas`, `import py.numpy`) with zero FFI glue.

📚 **Official Documentation:**
- [Complete Language Specification (SPECIFICATION.md)](docs/SPECIFICATION.md)
- [1-Page High-Density Developer Cheatsheet (CHEATSHEET.md)](docs/CHEATSHEET.md)
- [Flagship Production Showcase (examples/v1_showcase.zf)](examples/v1_showcase.zf)

---

## ⚡ Language Comparison Matrix

| Feature | Python 🐍 | Rust 🦀 | C++ ⚙️ | **Zafira 🔷 (v1.0.0 LTS)** |
| :--- | :---: | :---: | :---: | :---: |
| **Developer Ergonomics & Simplicity** | Very High | Steep curve | Complex | **Very High (Modern & Expressive)** |
| **Execution Performance** | 1x (Base) | 50–100x | 50–100x | **50–100x (`seal` & hardware execution)** |
| **Dual-Mode (Draft vs Seal)** | ❌ No | ❌ Strict only | ❌ Strict only | **✅ Native (`draft` dynamic, `seal` verified)** |
| **Formal Invariants (`where`)** | ❌ No | ⚠️ External macros | ❌ No | **✅ Built-in static verification at grammar level** |
| **Asynchronous Concurrency** | Add-on `asyncio` | Tokio runtime | `std::coroutine` | **✅ Core native `async fn` / `await`** |
| **Exception Handling** | try/except | Result<T, E> | try/catch | **✅ `try` / `catch` / `throw` / `finally`** |
| **Struct OOP Methods** | class | impl Struct | class / struct | **✅ `impl Struct { fn method(self) }`** |
| **Pattern Matching** | match/case | match | switch | **✅ `match value { 1 => ..., 3..10 => ..., _ => ... }`** |
| **Native C FFI** | ctypes / cffi | extern "C" | Native | **✅ `std.ffi` (Dynamic `.dll` / `.so` libraries)** |
| **Built-in Cryptography & Regex** | hashlib, re | External crates | openssl, std::regex | **✅ `std.crypto` & `std.regex` built into stdlib** |
| **Multi-File Local Modules** | import | mod / use | #include | **✅ `import "./module.zf" as m` (Cached & Cycle-safe)** |
| **Package Manager (`zpm`)** | pip | cargo | conan/vcpkg | **✅ `zafira install`, `zafira add` (`zafira.lock`)** |
| **AOT Standalone Binary Packager** | PyInstaller | cargo build | CMake / gcc | **✅ `zafira pack` (Single self-contained `.exe`)** |
| **Python Ecosystem Bridge** | Native | ❌ Heavy FFI | ❌ Complex C-API | **✅ `import py.torch` (Zero glue required)** |
| **Silicon Directives** | Driver wrapper | CUDA crates | OpenCL / CUDA | **✅ `run @gpu`, `run @npu`, `run @auto`** |
| **Memory & Type Safety Guarantee** | GC (slow) | Borrow Checker | Manual (unsafe) | **✅ Static inference + verified invariants** |

---

## 📦 Features Matrix Across Releases

| Feature | v0.1 | v0.3 | v0.5 | v0.7 | v0.8 | **v1.0.0 (Grand LTS)** |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Lexer & Pratt Parser & AST** | ✅ | ✅ | ✅ | ✅ | ✅ | **✅ Production** |
| **Tree-walking Interpreter & REPL** | ✅ | ✅ | ✅ | ✅ | ✅ | **✅ Production** |
| **Dual-Mode (`fn` draft / seal) & `where`** | Initial | ✅ Full | ✅ | ✅ | ✅ | **✅ Production** |
| **Python Interop (`import py.*`)** | ❌ | ✅ | ✅ | ✅ | ✅ | **✅ Production** |
| **Static Type Checker & Proof Engine** | ❌ | ✅ | ✅ | ✅ | ✅ | **✅ Production** |
| **VS Code Syntax Extension (`.vsix`)** | ❌ | ✅ | ✅ | ✅ | ✅ | **✅ Production** |
| **C Transpiler & Standalone Binary (`.exe`)**| ❌ | ✅ | ✅ | ✅ | ✅ | **✅ Production** |
| **Standard Library (All 13 Modules)** | ❌ | 4 mods | 6 mods | 9 mods | 12 mods | **✅ 13 Complete Modules** |
| **Package Manager (`zpm`: init, run, test, build)** | ❌ | ❌ | ✅ | ✅ | ✅ | **✅ Production** |
| **Silicon AI & Tensor Engine (`std.ai`, @gpu)** | ❌ | ❌ | ✅ | ✅ | ✅ | **✅ Production** |
| **Web Suite (`std.net`, `std.json`, HTTP Server)** | ❌ | ❌ | ✅ | ✅ | ✅ | **✅ Production** |
| **Async Concurrency (`async fn`, `await`)** | ❌ | ❌ | ✅ | ✅ | ✅ | **✅ Production** |
| **Web Interactive Playground Studio** | ❌ | ❌ | ✅ | ✅ | ✅ | **✅ Production** |
| **Exception Handling (`try/catch/finally`)** | ❌ | ❌ | ❌ | ✅ | ✅ | **✅ Production** |
| **File System Engine (`std.fs`) & Local Modules** | ❌ | ❌ | ❌ | ✅ | ✅ | **✅ Production** |
| **Struct Methods (`impl`) & Pattern Matching** | ❌ | ❌ | ❌ | ✅ | ✅ | **✅ Production** |
| **Cryptography (`std.crypto`) & `std.regex`** | ❌ | ❌ | ❌ | ❌ | ✅ | **✅ Production** |
| **Native C FFI (`std.ffi`: load C libraries)** | ❌ | ❌ | ❌ | ❌ | ✅ | **✅ Production** |
| **Remote ZPM Registry (`zafira install`, `zafira add`)**| ❌ | ❌ | ❌ | ❌ | ❌ | **✅ v1.0.0** |
| **Single-Binary Packager (`zafira pack`)** | ❌ | ❌ | ❌ | ❌ | ❌ | **✅ v1.0.0** |

---

## 🚀 Quick Start (Up & Running in 60 Seconds)

### Step 1: Clone the Repository
```bash
git clone https://github.com/salomh46-rgb/Zafira-.git
cd Zafira-
```

### Step 2: Check Python Runtime
Zafira runs on Python 3.11+ (CPython or PyPy):
```bash
python --version
```

### Step 3: Run the Flagship v1.0 Showcase
Execute the complete multi-module showcase exercising every single language capability:
```bash
py -3 -X utf8 zafira.py run examples/v1_showcase.zf
```

### Step 4: Interactive REPL
Fire up the lightning-fast Zafira terminal REPL:
```bash
py -3 -X utf8 zafira.py repl
```
```
zf> let name = "World"
zf> "Hello, " + name + "!"
=> Hello, World!
zf> 2 ** 10
=> 1024
```

### Step 5: Web Interactive Studio
Launch the dark-mode obsidian web studio directly in your browser:
```bash
py -3 -X utf8 zafira.py playground
```

---

## 💻 Code Examples & Syntax Tour

### 1. Variables, Constants, and Invariants
```zafira
let balance = 1000.0             // Mutable variable
const MAX_RETRIES = 5           // Immutable constant (compile-time protected)

// Sealed function with static invariant guarantee:
seal fn calculate_commission(amount: Float, rate: Float) -> Float
    where amount > 0.0 and rate >= 0.0  // If violated, fails statically!
{
    return amount * rate
}
```

### 2. Structs and `impl` Methods (OOP)
```zafira
struct User {
    id: String,
    username: String,
    score: Int
}

impl User {
    fn introduce(self) {
        return "User: " + self.username + " (Score: " + String(self.score) + ")"
    }

    fn add_score(self, points: Int) {
        self.score = self.score + points
        return self.score
    }
}

let user = User("uuid-123", "jasper", 100)
user.add_score(50)
print(user.introduce()) // "User: jasper (Score: 150)"
```

### 3. Pattern Matching (`match =>`)
```zafira
let score = 85

let grade = match score {
    90..101 => "A+",
    80..90  => "A",
    70..80  => "B",
    60..70  => "C",
    _       => "F"
}

print("Final Grade: " + grade)
```

### 4. Async / Await Concurrency
```zafira
async fn fetch_telemetry(sensor_id: Int) {
    // Simulates non-blocking network I/O
    return "Telemetry Data for Sensor #" + String(sensor_id)
}

// Kick off tasks concurrently across worker threads:
let t1 = fetch_telemetry(101)
let t2 = fetch_telemetry(102)

// Await values without blocking the event loop:
print(await t1)
print(await t2)
```

### 5. Silicon Directives (`@gpu`, `@npu`, `@auto`) & Tensors
```zafira
import std.ai

run @auto {
    let v1 = ai.tensor([0.2, 0.4, 0.8, 1.0])
    let v2 = ai.tensor([0.2, 0.4, 0.8, 1.0])
    
    // Dot product on hardware tensor core:
    let similarity = ai.similarity(v1, v2)
    print("Cosine Similarity: " + String(similarity)) // 1.0
}
```

### 6. Full Exception Handling (`try / catch / throw / finally`)
```zafira
try {
    let denominator = 0
    if denominator == 0 {
        throw "Division by zero intercepted!"
    }
} catch (error) {
    print("Caught safely: " + error)
} finally {
    print("Audit log closed.")
}
```

### 7. File System (`std.fs`) and Cryptography (`std.crypto`)
```zafira
import std.fs
import std.crypto

let secret_token = crypto.uuid()
fs.write_text("token.txt", "TOKEN=" + secret_token)

if fs.exists("token.txt") {
    let content = fs.read_text("token.txt")
    print("Saved: " + content)
    fs.remove("token.txt")
}
```

### 8. Native C FFI (`std.ffi`)
Call functions directly from shared libraries (`.dll`, `.so`, `.dylib`) without writing C headers:
```zafira
import std.ffi

let libc = ffi.load("libc")
let absolute_val = libc.call("abs", [-123], "int")
print("Absolute value from C: " + String(absolute_val)) // 123
```

---

## 🏛️ System Architecture

```
                      Zafira Source Code (.zf)
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │    Lexer / Scanner    │  ───► 50+ Tokens (UTF-8, Comments, Directives)
                     └───────────────────────┘
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │  Pratt AST Parser     │  ───► Abstract Syntax Tree (Precedence-aware)
                     └───────────────────────┘
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │  Static Type Checker  │  ───► Seal Verification & Where Proofs
                     │     (Seal Guard)      │       • Param/Return match & Invariants
                     └───────────────────────┘       • Const checks & Typo suggestions
                                 │
             ┌───────────────────┴───────────────────┐
             ▼                                       ▼
 ┌───────────────────────┐               ┌───────────────────────┐
 │ Tree-Walk Interpreter │               │   AOT / C Compiler    │
 │     (Draft Mode)      │               │      (Seal Mode)      │
 └───────────────────────┘               └───────────────────────┘
             │                                       │
             ▼                                       ▼
 ┌───────────────────────┐               ┌───────────────────────┐
 │ Python Interop Bridge │               │ Standalone Executable │
 │ (py.torch, py.pandas) │               │   (myapp.exe / ELF)   │
 └───────────────────────┘               └───────────────────────┘
             │                                       │
             └───────────────────┬───────────────────┘
                                 ▼
               ┌───────────────────────────────────┐
               │         Hardware Engines          │
               │   CPU Cores  │  GPU  │  NPU Core   │
               └───────────────────────────────────┘
```

---

## 🛠️ CLI Tooling & Package Manager (`zpm`)

Zafira includes a comprehensive developer toolchain right out of the box:

| Command | Description |
| :--- | :--- |
| `python zafira.py run <file.zf \| dir>` | Execute a script or project entrypoint |
| `python zafira.py repl` | Launch interactive REPL environment |
| `python zafira.py init <name>` | Scaffold a new project with `zafira.json` |
| `python zafira.py test [dir]` | Auto-discover and run all `tests/*.zf` test suites |
| `python zafira.py build [dir]` | Transpile project to clean, self-contained C99 code |
| `python zafira.py pack [dir] -o <app.exe>` | Bundle entire project into a single native binary |
| `python zafira.py install [dir]` | Install all dependencies declared in `zafira.json` |
| `python zafira.py add <pkg> [dir]` | Add a new dependency and generate `zafira.lock` |
| `python zafira.py compile <file.zf>` | Compile file directly to binary using local GCC/Clang |
| `python zafira.py transpile <file.zf>` | Emit pure C99 code without invoking a C compiler |
| `python zafira.py tokens <file.zf>` | Inspect lexer token stream (debug utility) |
| `python zafira.py ast <file.zf>` | Print pretty-printed Abstract Syntax Tree |
| `python zafira.py playground` | Open local Dark-mode Obsidian Web Studio in browser |

---

## 🧩 Visual Studio Code Extension

Official syntax highlighting, bracket matching, and code snippets are available for VS Code:

<p align="center">
  <img src="https://raw.githubusercontent.com/salomh46-rgb/Zafira-/main/vscode-zafira/icon.png" width="64" height="64" alt="VS Code Extension Icon">
</p>

### Installation:
1. Locate the package at `vscode-zafira/zafira-lang-0.1.0.vsix`.
2. In VS Code, press `Ctrl + Shift + P` -> **"Extensions: Install from VSIX..."**
3. Select `zafira-lang-0.1.0.vsix` and enjoy first-class `.zf` syntax highlighting!

For more details, see [VS Code Extension Installation Guide](vscode-zafira/INSTALL.md).

---

## 🧪 Verification & Test Suite

The language engine enforces **Zero-Regression Doubt-Driven Development**. Every commit is backed by automated tests:

```bash
# Run the entire test suite (333 tests):
py -3 -m unittest discover tests
```

Output:
```
......................................................................................
Ran 333 tests in 59.812s
OK (100% Passing, 0 errors, 0 regressions)
```

---

## 🤝 Contributing

We welcome open-source contributions from developers worldwide!

1. **Fork** the repository on GitHub.
2. Create your feature branch:
   ```bash
   git checkout -b feature/cutting-edge-feature
   ```
3. Run the automated test suite to ensure 100% green compliance:
   ```bash
   py -3 -m unittest discover tests
   ```
4. Commit your changes:
   ```bash
   git commit -m "feat: added new silicon tensor operator"
   ```
5. Push to your branch and open a **Pull Request (PR)**.

---

## 👥 Authors & Credits

- **Jasper (Javohirbek Asqarov)** — Founder, Language Philosophy, Architecture, and Lead Designer.
- **Antigravity AI** — Systems Engineering, Pratt AST Parsers, Type Checker Verification, and Compilers.

---

## 📄 License

Zafira is open-source software licensed under the **[MIT License](LICENSE)**.

<p align="center">
  <sub>Established in 2026 | Tashkent, Uzbekistan 🇺🇿</sub>
</p>
