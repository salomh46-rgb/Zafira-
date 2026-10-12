# 🔷 Zafira Programming Language v1.0.0
# Official Language Specification

<p align="center">
  <strong>"Rigid, crystal-clear, unbreakable — as flawless as a sapphire"</strong><br>
  <em>Silicon-Native | Dual-Mode (Draft & Seal) | AI-First & Python-Interop Programming Language</em>
</p>

---

## 📑 Table of Contents

1. [Introduction and Philosophy](#1-introduction-and-philosophy)
2. [Lexical Grammar](#2-lexical-grammar)
3. [Type System](#3-type-system)
4. [Variables and Constants (`let`, `const`)](#4-variables-and-constants-let-const)
5. [Functions and Dual-Mode Architecture (`fn`, `seal`, `draft`)](#5-functions-and-dual-mode-architecture-fn-seal-draft)
6. [Formal Invariants (`where` Clauses)](#6-formal-invariants-where-clauses)
7. [Data Structures and Methods (`struct`, `impl`, `self`)](#7-data-structures-and-methods-struct-impl-self)
8. [Control Flow](#8-control-flow)
9. [Pattern Matching (`match =>`)](#9-pattern-matching-match-)
10. [Asynchronous Programming (`async`, `await`)](#10-asynchronous-programming-async-await)
11. [Error Handling (`try`, `catch`, `throw`, `finally`)](#11-error-handling-try-catch-throw-finally)
12. [Silicon Hardware Directives (`run @gpu / @npu / @auto`)](#12-silicon-hardware-directives-run-gpu--npu--auto)
13. [Foreign Interop Bridge (`import py.*` and C FFI)](#13-foreign-interop-bridge-import-py-and-c-ffi)
14. [Standard Library (13 Batteries Included Modules)](#14-standard-library-13-batteries-included-modules)
15. [ZPM Package Manager and CLI Suite](#15-zpm-package-manager-and-cli-suite)

---

## 1. Introduction and Philosophy

**Zafira** is a high-performance modern programming language designed for the generative AI era and heterogeneous silicon hardware (CPU, GPU, NPU).

### Core Pillars:
1. **Dual-Mode Paradigm**: Write rapid dynamic prototypes with zero type annotations in `draft` mode; seal functions into strictly verified production assets with formal `where` invariants in `seal` mode.
2. **Silicon-Native**: AI tensor operations communicate with silicon compute backends directly in the syntax (`run @gpu`, `@npu`, `@auto`).
3. **Zero-Overhead Python & C Interop**: Call any Python library (`import py.torch`, `import py.numpy`) or native C shared libraries (`std.ffi`) with zero glue code.
4. **Mathematical Contract Invariants**: Guarantee input validity at compile time via `where` clauses, preventing runtime errors before execution begins.

---

## 2. Lexical Grammar

### 2.1. Encoding and File Format
* Zafira source files must be valid **UTF-8**.
* Canonical extension: `.zf`.

### 2.2. Comments
* Single-line comments start with `//` and run to the end of the line:
  ```zafira
  // Single-line comment
  let count = 42 // Inline comment
  ```

### 2.3. Identifiers
* Identifiers start with an ASCII letter (`a-z`, `A-Z`) or underscore `_`, followed by letters, digits, or underscores.
* Identifiers are strictly case-sensitive.

### 2.4. Keywords
The following tokens are reserved keywords:
```
let, const, fn, seal, draft, where, run, struct, impl, import, as,
match, async, await, return, if, else, while, for, in, and, or, not,
try, catch, throw, finally, true, false, null
```

---

## 3. Type System

Zafira features a sound static-first type system with dynamic inference:

| Type Name | Category | Description | Example |
| :--- | :--- | :--- | :--- |
| `Int` | Value | 64-bit signed integer | `42`, `-10`, `0xFF`, `0b1010` |
| `Float` | Value | 64-bit IEEE 754 floating point | `3.14159`, `-0.5`, `1e-4` |
| `String` | Value | Immutable UTF-8 text | `"Zafira"`, `"Line\n"` |
| `Bool` | Value | Boolean truth values | `true`, `false` |
| `Null` | Value | Unit null value | `null` |
| `List` | Reference | Heterogeneous or typed array | `[1, 2, 3]`, `["a", "b"]` |
| `JsonObject` | Reference | Dynamic structured key-value map | `json.parse("{}")` |
| `Tensor` | Reference | Multi-dimensional accelerated tensor | `ai.tensor([1.0, 2.0])` |
| `Task` | Reference | Asynchronous future handle | `async fn f() { ... }` |

---

## 4. Variables and Constants (`let`, `const`)

```zafira
// Mutable binding:
let counter = 1
counter = counter + 1

// Immutable binding (compile-time & runtime protected):
const MAX_CONCURRENCY = 100
// MAX_CONCURRENCY = 200 // -> Compile Error: Cannot reassign constant

// Explicit type annotation:
let user_id: Int = 1001
const APP_NAME: String = "Zafira Core"
```

---

## 5. Functions and Dual-Mode Architecture (`fn`, `seal`, `draft`)

### 5.1. Draft Mode (Dynamic)
```zafira
fn calculate(x, y) {
    return x * y + 10
}
```

### 5.2. Seal Mode (Strict Static Verification)
```zafira
seal fn calculate_strict(x: Float, y: Float) -> Float {
    return x * y + 10.0
}
```

---

## 6. Formal Invariants (`where` Clauses)

Invariants are mathematical pre-conditions that must hold true when invoking a sealed function:

```zafira
seal fn withdraw(balance: Float, amount: Float) -> Float
    where amount > 0.0 && balance >= amount
{
    return balance - amount
}

seal fn safe_divide(numerator: Float, denominator: Float) -> Float
    where denominator != 0.0
{
    return numerator / denominator
}
```
If an invariant fails, execution is immediately halted with a structured `ZafiraError` specifying the violated condition and argument values.

---

## 7. Data Structures and Methods (`struct`, `impl`, `self`)

```zafira
struct BankAccount {
    account_no: String,
    balance: Float,
    is_active: Bool
}

impl BankAccount {
    fn deposit(self, amount: Float) {
        if amount > 0.0 {
            self.balance = self.balance + amount
        }
        return self.balance
    }

    fn summary(self) {
        return "Account: " + self.account_no + " | Balance: " + String(self.balance)
    }
}

let acc = BankAccount("UZB-001", 500000.0, true)
acc.deposit(150000.0)
print(acc.summary())
```

---

## 8. Control Flow

```zafira
// If-else branching:
if score >= 90 {
    print("Grade: A")
} else if score >= 80 {
    print("Grade: B")
} else {
    print("Grade: C")
}

// While loops:
let i = 0
while i < 5 {
    i = i + 1
}

// For-in iteration:
for item in [10, 20, 30] {
    print("Item: " + String(item))
}
```

---

## 9. Pattern Matching (`match =>`)

```zafira
let status_code = 404

let status_text = match status_code {
    200 => "OK",
    301..308 => "Redirect",
    400..499 => "Client Error",
    500..599 => "Server Error",
    _ => "Unknown Status"
}
```

---

## 10. Asynchronous Programming (`async`, `await`)

```zafira
async fn fetch_records(batch_id: Int) {
    datetime.sleep(0.02)
    return "Batch " + String(batch_id) + " processed"
}

let res = await fetch_records(1)
print(res)
```

---

## 11. Error Handling (`try`, `catch`, `throw`, `finally`)

```zafira
try {
    if denominator == 0 {
        throw "Division by zero is forbidden"
    }
    let res = numerator / denominator
} catch (err) {
    print("Handled: " + String(err))
} finally {
    print("Always runs.")
}
```

---

## 12. Silicon Hardware Directives (`run @gpu / @npu / @auto`)

```zafira
import std.ai

let a = ai.tensor([1.0, 2.0, 3.0])
let b = ai.tensor([4.0, 5.0, 6.0])

run @auto {
    let sim = ai.similarity(a, b)
    print("Similarity: " + String(sim))
}
```

---

## 13. Foreign Interop Bridge (`import py.*` and C FFI)

### Python Ecosystem Bridge:
```zafira
import py.numpy as np
import py.torch as torch

let matrix = np.zeros([4, 4])
print("Numpy shape: " + String(matrix.shape))
```

### C Foreign Function Interface:
```zafira
import std.ffi

let libc = ffi.load("msvcrt") // On Windows, or libc on Linux
libc.call("puts", ["Native C puts() executed!"], "int")
```

---

## 14. Standard Library (13 Batteries Included Modules)

1. `std.math` — High-precision mathematical functions (`sqrt`, `pow`, `abs`, `log`, `sin`, `cos`, `PI`, `E`).
2. `std.string` — Text manipulation (`upper`, `lower`, `split`, `join`, `replace`, `contains`, `reverse`).
3. `std.list` — Functional array utilities (`sort`, `filter`, `map`, `reduce`, `sum`, `max`, `min`).
4. `std.io` — Standard console I/O (`print`, `println`, `readline`).
5. `std.json` — Fast JSON serialization and deserialization (`parse`, `stringify`).
6. `std.net` — HTTP client and standalone embedded HTTP REST server (`get`, `post`, `listen`, `close`).
7. `std.fs` — Cross-platform filesystem operations (`read_text`, `write_text`, `append_text`, `exists`, `remove`).
8. `std.datetime` — Timestamp, formatting, and sleeping (`now`, `timestamp`, `format`, `sleep`).
9. `std.env` — Process environment, arguments, and platform inspection (`get`, `set`, `os`, `cwd`, `args`).
10. `std.crypto` — Cryptographic digests, HMAC, UUIDv4, and secure randomness (`sha256`, `sha512`, `uuid`, `random_hex`).
11. `std.regex` — Pattern matching and regular expressions (`test`, `find`, `find_all`, `replace`, `split`).
12. `std.ai` — Accelerated tensor primitives and vector similarity search (`tensor`, `zeros`, `ones`, `similarity`).
13. `std.ffi` — Dynamic native C symbol loading and direct function invocations.

---

## 15. ZPM Package Manager and CLI Suite

| Command | Action |
| :--- | :--- |
| `zafira run <file.zf>` | Run source file or directory project |
| `zafira init <name>` | Create new project with `zafira.json` manifest |
| `zafira test` | Run all automated test files in `tests/` |
| `zafira build` | Transpile project to optimized C99 source |
| `zafira pack` | Package project into single standalone `.exe` binary |
| `zafira playground` | Launch interactive local dark-mode studio on port 5000 |
