# 🔷 Zafira v1.0.0 — Dasturchilar Uchun Tezkor Ma'lumotnoma (Cheat Sheet)

> **"Qattiq, tiniq, sinmas — xuddi sapfir toshi kabi mukammal"**  
> *1 sahifalik ixcham qo'llanma: barcha sintaksis, modullar va CLI buyruqlari bir joyda.*

---

## ⚡ 1. CLI Buyruqlari (Quick CLI)

| Buyruq | Vazifasi | Misol |
| :--- | :--- | :--- |
| `run` | Dastur fayli yoki loyihani bajarish | `py -3 zafira.py run main.zf` |
| `repl` | Interaktiv buyruqlar satri (REPL) | `py -3 zafira.py repl` |
| `init` | Yangi Zafira loyihasi yaratish | `py -3 zafira.py init mening_loyiham` |
| `build` | Loyihani C kodiga transpile qilish | `py -3 zafira.py build .` |
| `compile` | Standalone binar `.exe` yaratish | `py -3 zafira.py compile main.zf -o ilova.exe` |
| `test` | Loyiha testlarini ishga tushirish | `py -3 zafira.py test` |
| `playground`| Veb-interaktiv studiyani ochish | `py -3 zafira.py playground --port 5000` |
| `tokens` | Leksik tokenlarni ko'rish (debug) | `py -3 zafira.py tokens app.zf` |
| `ast` | Pratt AST daraxtini ko'rish (debug) | `py -3 zafira.py ast app.zf` |

---

## 📌 2. O'zgaruvchilar va Tiplar

```zafira
let x = 10                // O'zgaruvchan qiymat (let)
const PI = 3.14159265     // O'zgarmas qiymat (const) — qayta tayinlash taqiqlanadi!

// Asosiy tiplar:
let butun: Int = 42
let haqiqiy: Float = 3.14
let matn: String = "Zafira"
let mantiq: Bool = true
let bosh: Null = null
let royxat: List = [1, 2, 3]
```

---

## 🛡️ 3. Dual-Mode Funksiyalar va `where` Invariantlari

```zafira
// 1. Draft rejim (dinamik, tezkor prototip):
fn qosh(a, b) {
    return a + b
}

// 2. Seal rejim (statik tekshiruvli, muhrlangan ishlab chiqarish kodi):
seal fn bolish(a: Float, b: Float) -> Float
    where b != 0.0  // Invariant shart: b nol bo'lsa kompilyatsiya/ijro to'xtatiladi!
{
    return a / b
}
```

---

## 🏛️ 4. Struct va Metodlar (`struct`, `impl`, `self`)

```zafira
struct Foydalanuvchi {
    ism: String,
    balans: Int
}

impl Foydalanuvchi {
    fn salom(self) {
        return "Foydalanuvchi: " + self.ism
    }

    fn tolov(self, summa: Int) {
        if self.balans >= summa {
            self.balans = self.balans - summa
            return true
        }
        return false
    }
}

let user = Foydalanuvchi("Jasper", 100000)
user.tolov(30000)
print(user.salom() + ", Qoldiq: " + String(user.balans))
```

---

## 🎯 5. Pattern Matching (`match =>`)

```zafira
let ball = 85

let baho = match ball {
    90..100 => "A'lo",
    70..90  => "Yaxshi",
    50..70  => "Qoniqarli",
    _       => "Qoniqarsiz (Wildcard)"
}

// Aniq qiymatlar va o'zgaruvchini bog'lash:
let buyruq = "start"
match buyruq {
    "start" => print("Tizim yondi"),
    "stop"  => print("Tizim o'chdi"),
    boshqa  => print("Noma'lum buyruq: " + boshqa)
}
```

---

## ⚡ 6. Asinxron Dasturlash (`async`, `await`)

```zafira
async fn malumot_yukla(id) {
    sleep(0.05)
    return "Yuklandi #" + String(id)
}

// Yagona kutish:
let res = await malumot_yukla(1)

// Parallel fon vazifalari (Non-blocking):
let t1 = malumot_yukla(10)
let t2 = malumot_yukla(20)

let javob1 = await t1
let javob2 = await t2
```

---

## 🚨 7. Xatoliklarni Boshqarish (`try`, `catch`, `finally`)

```zafira
try {
    if xato_bor {
        throw "Xatolik yuz berdi!"
    }
    let hisob = 100 / 0
} catch (e) {
    print("Xato ushlandi: " + e)
} finally {
    print("Doim bajariluvchi tozalash bloki")
}
```

---

## 🚀 8. Apparat Direktivalari (`run @gpu / @npu / @auto`)

```zafira
run @gpu {
    let t1 = ai.tensor([1.0, 2.0, 3.0])
    let t2 = ai.tensor([4.0, 5.0, 6.0])
    let dot = t1.dot(t2)
}

run @auto {
    // Optimal chip (CPU yoki NPU) avtomatik belgilanadi
    let nollar = ai.zeros(2, 4)
}
```

---

## 🐍 9. Python Zero-Overhead Interop

```zafira
import py.math
import py.random

let ildiz = math.sqrt(144.0)          // 12.0
let tasodif = random.randint(1, 100)  // Tasodifiy son
```

---

## 📦 10. Standart Kutubxona Shpargalkasi (`std.*`)

| Modul | Asosiy Funksiyalari | Namunasi |
| :--- | :--- | :--- |
| **`std.math`** | `sqrt`, `pow`, `abs`, `floor`, `ceil`, `round`, `min`, `max`, `log`, `sin`, `cos`, `tan`, `PI` | `math.sqrt(64.0)` |
| **`std.string`** | `upper`, `lower`, `trim`, `split`, `join`, `replace`, `contains`, `starts_with`, `reverse` | `string.upper("salom")` |
| **`std.list`** | `sort`, `reverse`, `filter`, `map`, `reduce`, `find`, `contains`, `unique`, `sum`, `max`, `min` | `list.map([1,2], fn(x){ return x*2 })` |
| **`std.io`** | `print`, `println`, `readline`, `write` | `io.println("Salom")` |
| **`std.ai`** | `tensor`, `zeros`, `ones`, `similarity`, `embedding_mock`, `device` | `let t = ai.tensor([1,2,3])` |
| **`std.json`** | `parse`, `stringify`, `loads`, `dumps` | `let obj = json.parse("{\"a\": 1}")` |
| **`std.net`** | `get(url)`, `post(url, data)`, `listen(port, handler)`, `close(srv)` | `let r = net.get("https://api.xyz")` |
| **`std.fs`** | `read_text`, `write_text`, `append_text`, `exists`, `is_file`, `is_dir`, `copy`, `remove` | `fs.write_text("f.txt", "matn")` |
| **`std.env`** | `get(key, def)`, `set(key, val)`, `has(key)`, `os()`, `cwd()`, `args()` | `let os = env.os()` |
| **`std.datetime`**| `now()`, `timestamp()`, `format(ts, fmt)`, `sleep(s)`, `sleep_ms(ms)` | `let sana = datetime.now().iso` |
| **`std.crypto`** | `sha256`, `sha512`, `md5`, `hmac_sha256`, `base64_encode`, `base64_decode`, `uuid` | `let id = crypto.uuid()` |
| **`std.regex`** | `test(pat, text)`, `find`, `find_all`, `replace`, `replace_all`, `split`, `is_valid` | `regex.test("^\\d+$", "123")` |
| **`std.ffi`** | `load(nom)`, `call(fn, args, tur)`, `has_symbol(nom)`, `c_int`, `c_string` | `let c = ffi.load("libc")` |

---

## 💡 11. Oltin Qoidalar & Maslahatlar
1. **Har doim `import std.<modul>` bilan modullarni chaqiring**: Masalan, `import std.crypto`, `import std.fs`.
2. **String konvertatsiyasi**: Raqam va matnni birlashtirishda `String(son)` dan foydalaning: `"Qiymat: " + String(x)`.
3. **Statik xavfsizlik**: Muhim biznes logikasi va to'lov/hisob-kitoblarni har doim `seal fn` va `where` invariantlari bilan himoyalang.
4. **Resurs tozaligi**: Fayllar va tarmoq ulanishlarini `try ... finally` bloklarida yopishni odat qiling.

---
<sub>Zafira Language Cheatsheet v1.0.0 | 2026</sub>
