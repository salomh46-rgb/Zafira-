# 🔷 Zafira v1.0.0 — Developer Cheatsheet (1-Page Reference)

> **"Rigid, crystal-clear, unbreakable — as flawless as a sapphire"**  
> *A high-density 1-page reference covering syntax, standard modules, and CLI toolchain commands.*

---

## ⚡ 1. CLI Commands & Toolchain

| Command | Description | Example |
| :--- | :--- | :--- |
| `run` | Execute source file or project package | `python zafira.py run main.zf` |
| `repl` | Interactive terminal read-eval-print loop | `python zafira.py repl` |
| `init` | Scaffold a new Zafira project structure | `python zafira.py init my_app` |
| `build` | Transpile project into optimized C99 source | `python zafira.py build .` |
| `compile` | Compile directly to native standalone `.exe` binary | `python zafira.py compile main.zf -o app.exe` |
| `pack` | Self-contained single-translation-unit packager | `python zafira.py pack . -o dist/app.exe` |
| `test` | Discover and run all automated project tests | `python zafira.py test` |
| `playground`| Launch browser interactive obsidian studio | `python zafira.py playground --port 5000` |
| `tokens` | Inspect lexical token stream (debug) | `python zafira.py tokens app.zf` |
| `ast` | Inspect Pratt AST syntax tree (debug) | `python zafira.py ast app.zf` |

---

## 📌 2. Variables, Constants, and Types

```zafira
let x = 10                // Mutable variable
const PI = 3.14159265     // Immutable constant (compile-time & runtime protected)

// Core static types:
let count: Int = 42
let ratio: Float = 3.14
let name: String = "Zafira"
let active: Bool = true
let empty: Null = null
let items: List = [1, 2, 3]
let data: JsonObject = json.parse("{}")
```

---

## 🛡️ 3. Dual-Mode Functions & `where` Invariants

```zafira
// 1. Draft Mode (Dynamic, rapid prototyping without annotations):
fn add(a, b) {
    return a + b
}

// 2. Seal Mode (Strict static types with mathematical contract invariants):
seal fn divide(a: Float, b: Float) -> Float
    where b != 0.0  // Invariant condition: halts with proof error if b == 0.0
{
    return a / b
}
```

---

## 🏛️ 4. Structs & OOP Methods (`struct`, `impl`, `self`)

```zafira
struct User {
    id: Int,
    name: String,
    score: Float
}

impl User {
    fn greet(self) {
        return "Hello, I am " + self.name
    }

    fn add_score(self, points: Float) {
        self.score = self.score + points
        return self.score
    }
}

let u = User(101, "Jasper", 98.5)
print(u.greet())
u.add_score(1.5)
```

---

## 🎯 5. Pattern Matching (`match =>`)

```zafira
let score = 92

let grade = match score {
    90..100 => "A+ Elite",
    80..89  => "B Good",
    70..79  => "C Satisfactory",
    0..69   => "Retake Required",
    _       => "Invalid Score"
}
```

---

## ⚡ 6. Native Async / Await

```zafira
async fn fetch_user(id: Int) {
    datetime.sleep(0.05)
    return "User:" + String(id)
}

let task = await fetch_user(42)
print("Result: " + task)
```

---

## 🔒 7. Error Handling (`try / catch / throw / finally`)

```zafira
fn withdraw(amount: Float) {
    if amount <= 0.0 {
        throw "Invalid withdrawal amount"
    }
    return true
}

try {
    withdraw(-50.0)
} catch (err) {
    print("Caught error: " + String(err))
} finally {
    print("Cleanup executed unconditionally.")
}
```

---

## 🧠 8. AI & Silicon Tensors (`run @gpu / @npu`)

```zafira
import std.ai

let v1 = ai.tensor([1.0, 2.0, 3.0])
let v2 = ai.tensor([4.0, 5.0, 6.0])

// Hardware directive block:
run @auto {
    let similarity = ai.similarity(v1, v2)
    print("Cosine Similarity: " + String(similarity))
}
```

---

## 🌐 9. Standard Library (13 Batteries Included Modules)

### `std.math`
```zafira
import std.math
math.sqrt(16.0)     // 4.0
math.pow(2.0, 10.0) // 1024.0
math.abs(-5)        // 5
```

### `std.string`
```zafira
import std.string
string.upper("zafira")              // "ZAFIRA"
string.split("a,b,c", ",")          // ["a", "b", "c"]
string.join(["x", "y"], "-")        // "x-y"
```

### `std.list`
```zafira
import std.list
list.sort([3, 1, 4])                // [1, 3, 4]
list.sum([10, 20, 30])              // 60
list.filter([1, 2, 3], fn(x) { return x > 1 })
```

### `std.json`
```zafira
import std.json
let obj = json.parse("{\"status\": \"OK\"}")
let raw = json.stringify(obj)
```

### `std.crypto`
```zafira
import std.crypto
crypto.sha256("password")
crypto.uuid()                       // "c9bf9e57-1685-4c89-bafb-ff5af830be8a"
crypto.hmac_sha256("secret", "msg")
```

### `std.regex`
```zafira
import std.regex
regex.test("^[a-z]+$", "zafira")    // true
regex.find_all("\\d+", "ID 101, 202")
```

### `std.fs`
```zafira
import std.fs
fs.write_text("data.txt", "Hello Zafira")
let txt = fs.read_text("data.txt")
fs.remove("data.txt")
```

### `std.net`
```zafira
import std.net
let res = net.get("https://api.github.com")
let srv = net.listen(8080, fn(req) { return "OK" })
```

### `std.datetime`
```zafira
import std.datetime
let t = datetime.now()
datetime.sleep(0.1)
```

### `std.env`
```zafira
import std.env
let p = env.get("PATH")
let os_name = env.os()              // "windows" | "linux" | "darwin"
```

### `std.ffi` (C Foreign Function Interface)
```zafira
import std.ffi
let lib = ffi.load("msvcrt")        // or libc on Linux
lib.call("puts", ["Hello from C!"], "int")
```

---

## 🐍 10. Zero-Overhead Python Interop

```zafira
import py.numpy as np
import py.math as p_math

let arr = np.array([1, 2, 3, 4])
print("Mean: " + String(arr.mean()))
```
