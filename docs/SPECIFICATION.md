# 🔷 Zafira Dasturlash Tili v1.0.0
# Rasmiy Til Spetsifikatsiyasi (Language Specification)

<p align="center">
  <strong>"Qattiq, tiniq, sinmas — xuddi sapfir toshi kabi mukammal"</strong><br>
  <em>Silicon-Native | Dual-Mode (Draft & Seal) | AI-First & Python-Interop Programming Language</em>
</p>

---

## 📑 Mundarija

1. [Kirish va Til Falsafasi](#1-kirish-va-til-falsafasi)
2. [Leksik Tuzilma (Lexical Grammar)](#2-leksik-tuzilma-lexical-grammar)
3. [Tiplar Tizimi (Type System)](#3-tiplar-tizimi-type-system)
4. [O'zgaruvchilar va O'zgarmaslar (`let`, `const`)](#4-ozgaruvchilar-va-ozgarmaslar-let-const)
5. [Funksiyalar va Dual-Mode Arxitekturasi (`fn`, `seal`, `draft`)](#5-funksiyalar-va-dual-mode-arxitekturasi-fn-seal-draft)
6. [Formal Invariantlar (`where` Shartlari)](#6-formal-invariantlar-where-shartlari)
7. [Ma'lumot Tuzilmalari va Metodlar (`struct`, `impl`, `self`)](#7-malumot-tuzilmalari-va-metodlar-struct-impl-self)
8. [Boshqaruv Oqimi (Control Flow)](#8-boshqaruv-oqimi-control-flow)
9. [Pattern Matching (`match =>`)](#9-pattern-matching-match-)
10. [Asinxron Dasturlash (`async`, `await`)](#10-asinxron-dasturlash-async-await)
11. [Xatoliklarni Boshqarish (`try`, `catch`, `throw`, `finally`)](#11-xatoliklarni-boshqarish-try-catch-throw-finally)
12. [Kremniy Direktivalari (`run @gpu / @npu / @auto`)](#12-kremniy-direktivalari-run-gpu--npu--auto)
13. [Tashqi Interop Ko'prigi (`import py.*` va C FFI)](#13-tashqi-interop-koprigi-import-py-va-c-ffi)
14. [Standart Kutubxona (`std.*` Barcha 13 ta Modul)](#14-standart-kutubxona-std-barcha-13-ta-modul)
15. [Paket Menejeri va CLI Buyruqlari](#15-paket-menejeri-va-cli-buyruqlari)

---

## 1. Kirish va Til Falsafasi

**Zafira** — sun'iy intellekt va kremniy hisoblash arxitekturalari (CPU, GPU, NPU) davri uchun yaratilgan yuqori unumdorlikdagi zamonaviy dasturlash tilidir.

### Asosiy Prinsiplar:
1. **Dual-Mode Paradigmasi**: G'oyani tezkor prototiplash uchun erkin dinamik rejim (`draft`), ishlab chiqarish va chip darajasidagi xavfsizlik uchun esa qat'iy tip va formal invariantlar bilan muhrlangan rejim (`seal`).
2. **Silicon-Native**: AI modellari va massivlarni bevosita kremniy chipida (`run @gpu`, `@npu`, `@auto`) parallel hisoblash.
3. **Zero-Overhead Python & C Interop**: Butun Python kutubxonalar ekotizimini (`import py.numpy`, `import py.torch`) va mahalliy C kutubxonalarni (`std.ffi`) wrapperlarsiz to'g'ridan-to'g'ri chaqirish.
4. **Matematik Invariant Kafolati**: `where` shartlari orqali funksiya kiruvchi qiymatlarining to'g'riligini statik darajada tekshirish va nosozliklarning oldini olish.

---

## 2. Leksik Tuzilma (Lexical Grammar)

### 2.1. Belgilar va Kodlash
* Zafira manba kodi **UTF-8** formatida saqlanadi.
* Fayl kengaytmasi: `.zf`.

### 2.2. Izohlar (Comments)
* Bir qatorli izohlar `//` belgisi bilan boshlanadi va qator oxirigacha davom etadi:
  ```zafira
  // Bu bir qatorli Zafira izohi
  let x = 10 // O'zgaruvchi qiymati
  ```

### 2.3. Identifikatorlar (Identifiers)
* Identifikatorlar lotin harflari (`a-z`, `A-Z`) yoki pastki chiziq (`_`) bilan boshlanishi kerak, davomida raqamlar (`0-9`) bo'lishi mumkin.
* Katta-kichik harflar farqlanadi (`ism` va `Ism` har xil identifikatorlar).

### 2.4. Kalit So'zlar (Keywords)
Zafira tilida 30 dan ortiq maxsus ajratilgan kalit so'zlar mavjud:
```
let       const     fn        return    if        else
while     for       in        struct    impl      import
as        true      false     null      match     seal
draft     where     run       async     await     and
or        not       try       catch     throw     finally
```

### 2.5. Literallar
* **Int**: Butun sonlar (`42`, `-10`, `0`).
* **Float**: Haqiqiy sonlar (`3.14`, `-0.05`, `1.0`).
* **String**: Qo'shtirnoq ichidagi matnlar (`"Salom, Dunyo!"`). `\n`, `\t`, `\"`, `\\` kabi escape ketma-ketliklarni qo'llab-quvvatlaydi.
* **Bool**: Mantiqiy qiymatlar: `true` va `false`.
* **Null**: Bo'sh qiymat: `null`.
* **List**: Kvadrat qavsli ro'yxatlar: `[1, 2, 3, "to'rt"]`.
* **Range**: Oraliq ifodalari: `0..10`, `boshlanish..tugash`.

### 2.6. Operatorlar va Ajratuvchilar
* **Arifmetik**: `+`, `-`, `*`, `/`, `%`, `**` (daraja).
* **Taqqoslash**: `==`, `!=`, `<`, `>`, `<=`, `>=`.
* **Mantiqiy**: `and`, `or`, `not`.
* **Belgilash**: `=`, `->` (return turi), `=>` (pattern matching fat-arrow).
* **Chegaralovchilar**: `(`, `)`, `{`, `}`, `[`, `]`, `,`, `:`, `;`, `.`.

---

## 3. Tiplar Tizimi (Type System)

Zafira statik va dinamik tiplashtirishni o'zaro uyg'unlashtirgan gibrid tiplar tizimiga ega.

### 3.1. Primitiv Tiplar
| Tip Nomi | Tavsifi | Misol |
| :--- | :--- | :--- |
| `Int` | 64-bitli butun son | `100`, `-5` |
| `Float` | 64-bitli suzuvchi nuqtali haqiqiy son | `3.14159`, `-0.5` |
| `String` | UTF-8 matn qatori | `"Zafira 2026"` |
| `Bool` | Mantiqiy qiymat | `true`, `false` |
| `Null` | Qiymat mavjud emasligi | `null` |
| `Any` | Har qanday turdagi dinamik qiymat | Dinamik ifodalar |

### 3.2. Murakkab va Kompozit Tiplar
* `List`: Bir jinsli yoki aralash ma'lumotlar massivi (`[1, 2, 3]`).
* `Struct`: Foydalanuvchi tomonidan e'lon qilingan maxsus ma'lumotlar tuzilmasi.
* `Task` / `Future`: Asinxron chaqiriq natijasini ifodalovchi asinxron obyekt.

### 3.3. Tiplarning Kengayishi (Numeric Widening)
Statik tekshiruvda `Int` tipi `Float` kutilgan joyda avtomatik ravishda qabul qilinadi (masalan, `Float` qaytaruvchi funksiyaga `Int` berilganda xatolik yuz bermaydi).

---

## 4. O'zgaruvchilar va O'zgarmaslar (`let`, `const`)

### 4.1. `let` — O'zgaruvchan Qiymatlar
`let` orqali e'lon qilingan o'zgaruvchilar qiymati keyinchalik qayta o'zgartirilishi mumkin:
```zafira
let hisoblagich = 0
hisoblagich = hisoblagich + 1
```

### 4.2. `const` — O'zgarmas Qiymatlar
`const` orqali e'lon qilingan identifikatorlar o'zgarmas hisoblanadi. Agar dasturchi ularga qayta qiymat berishga urinsa, Zafira statik tekshiruv bosqichida `TypeCheckError` tashlaydi:
```zafira
const MAKSIMAL_LIMIT = 500
// MAKSIMAL_LIMIT = 600  <-- STATIK XATOLIK: O'zgarmas qayta tayinlanmaydi!
```

---

## 5. Funksiyalar va Dual-Mode Arxitekturasi (`fn`, `seal`, `draft`)

Zafira funksiyalari loyihaning yetuklik darajasiga ko'ra ikkita rejimda yoziladi:

### 5.1. Draft / Oddiy Funksiyalar (`fn` yoki `draft fn`)
Dinamik tiplashtirilgan, prototiplash uchun qulay funksiyalar. Parametr va return turlarini belgilash ixtiyoriy:
```zafira
fn qosh(a, b) {
    return a + b
}

draft fn log_xabar(xabar) {
    print("[DRAFT]: " + xabar)
}
```

### 5.2. Muhrlangan Funksiyalar (`seal fn`)
Ishlab chiqarish (production) uchun tayyor, qat'iy tiplashtirilgan va statik tekshiriluvchi funksiyalar. Parametr tiplari va qaytish turi (`->`) majburiy:
```zafira
seal fn hisobla_maydon(kenglik: Float, boyi: Float) -> Float {
    return kenglik * boyi
}
```

---

## 6. Formal Invariantlar (`where` Shartlari)

Zafira tili funksiyalarning kirish kontraktlarini ta'minlash uchun `where` invariantlarini taqdim etadi. Ushbu shartlar funksiya bajarilishidan oldin tekshiriladi:

```zafira
seal fn xavfsiz_bolish(surat: Float, maxraj: Float) -> Float
    where maxraj != 0.0
{
    return surat / maxraj
}

seal fn foydalanuvchi_yoshi(yosh: Int) -> String
    where yosh >= 0 and yosh <= 150
{
    return "Tasdiqlangan yosh: " + String(yosh)
}
```

Agar statik hisoblashda yoki ijro vaqtida `where` sharti buzilsa, xatolik vujudga keladi va tizim nosoz holatga tushishdan himoyalanadi.

---

## 7. Ma'lumot Tuzilmalari va Metodlar (`struct`, `impl`, `self`)

Zafira tili zamonaviy ma'lumotlar inkapsulyatsiyasini `struct` va `impl` bloklari orqali amalga oshiradi.

### 7.1. Struct Ta'rifi
```zafira
struct Foydalanuvchi {
    id: Int,
    ism: String,
    balans: Int
}
```

### 7.2. Struct Konstruktori
Struct yangi nusxasini yaratish uchun struct nomi funksiya sifatida chaqiriladi:
```zafira
let jasper = Foydalanuvchi(1, "Jasper", 500000)
print(jasper.ism) // "Jasper"
```

### 7.3. Metodlarni Biriktirish (`impl`)
Metodlar `impl StructNomi` blokida e'lon qilinadi. Har bir metodning birinchi parametri `self` bo'lib, joriy obyekt maydonlariga to'g'ridan-to'g'ri murojaat qilish va ularni o'zgartirish imkonini beradi:
```zafira
impl Foydalanuvchi {
    fn salom(self) {
        return "Foydalanuvchi: " + self.ism + " (Balans: " + String(self.balans) + " UZS)"
    }

    fn tolov_qil(self, summa: Int) {
        if self.balans >= summa {
            self.balans = self.balans - summa
            return true
        }
        return false
    }

    fn toliq_hisobot(self) {
        return self.salom() + " -> Status: Faol"
    }
}

// Chaqirish:
let ok = jasper.tolov_qil(150000)
print(jasper.toliq_hisobot())
```

---

## 8. Boshqaruv Oqimi (Control Flow)

### 8.1. Shartli Ifodalar (`if`, `else`)
```zafira
if ball >= 90 {
    print("A'lo")
} else if ball >= 70 {
    print("Yaxshi")
} else {
    print("Qoniqarsiz")
}
```

### 8.2. `while` Sikli
```zafira
let i = 0
while i < 5 {
    print("Qadam: " + String(i))
    i = i + 1
}
```

### 8.3. `for .. in` Sikli
Range yoki ro'yxat bo'yicha takrorlash:
```zafira
// Oraliq (Range) bo'yicha:
for raqam in 1..5 {
    print("Son: " + String(raqam))
}

// Ro'yxat elementlari bo'yicha:
let shaharlar = ["Toshkent", "Samarqand", "Buxoro"]
for shahar in shaharlar {
    print("Shahar: " + shahar)
}
```

---

## 9. Pattern Matching (`match =>`)

Zafira qudratli `match` pattern matching operatori va ifodasiga ega. U qiymatlarni shoxobchalarga ajratishda `if/else` zanjirlarini qulay va xavfsiz almashtiradi.

### 9.1. Aniq Qiymatlar va Wildcard (`_`)
```zafira
let kod = 200
let status = match kod {
    200 => "Muvaffaqiyatli (OK)",
    404 => "Topilmadi (Not Found)",
    500 => "Server Xatosi (Internal Server Error)",
    _   => "Noma'lum status kodi"
}
```

### 9.2. Oraliqlar (Ranges) Bo'yicha Moslash
```zafira
let ball = 85
let baho = match ball {
    90..100 => "A",
    80..90  => "B",
    70..80  => "C",
    60..70  => "D",
    _       => "F"
}
```

### 9.3. O'zgaruvchi Bog'lash (Variable Binding)
```zafira
let kiruvchi = 42
let xabar = match kiruvchi {
    0 => "Nol",
    val => "Dinamik qabul qilindi: " + String(val)
}
```

---

## 10. Asinxron Dasturlash (`async`, `await`)

Zafira asinxron vazifalar va kiritish-chiqarish amallarini bloklamaydigan ichki asinxron dvigatelga ega.

### 10.1. `async fn` Ta'rifi
```zafira
async fn api_sorov(id) {
    sleep(0.05)
    return "Ma'lumot #" + String(id)
}
```

### 10.2. `await` bilan Kutib Olish
```zafira
let javob = await api_sorov(101)
print(javob)
```

### 10.3. Parallel Vazifalar (Non-Blocking Concurrency)
Bir vaqtning o'zida bir nechta vazifani `await` siz ishga tushirib, natijalarini keyin kutib olish:
```zafira
let t1 = api_sorov(1)
let t2 = api_sorov(2)
let t3 = api_sorov(3)

let r1 = await t1
let r2 = await t2
let r3 = await t3
```

### 10.4. Muhrlangan Asinxron Funksiyalar
```zafira
seal async fn hisobla_hash(matn: String) -> String {
    sleep(0.01)
    return crypto.sha256(matn)
}
```

---

## 11. Xatoliklarni Boshqarish (`try`, `catch`, `throw`, `finally`)

Zafira tili to'liq xatoliklarni ushlash va resurslarni tozalash mexanizmini qo'llab-quvvatlaydi.

```zafira
try {
    print("Resurs ochilmoqda...")
    if xato_holat == true {
        throw "Kutilmagan favqulodda holat yuz berdi!"
    }
} catch (e) {
    print("Xatolik ushlandi: " + e)
} finally {
    print("Resurslar xavfsiz yopildi va tozalandi.")
}
```
* `throw <ifoda>`: Istisno xatoligini tashlaydi.
* `catch (nom)` yoki `catch`: Xatoni ushlaydi.
* `finally`: Xato bo'lishi yoki bo'lmasligidan qat'i nazar **har doim** bajariladi.

---

## 12. Kremniy Direktivalari (`run @gpu / @npu / @auto`)

Zafira apparat bilan bevosita til darajasida gaplashadi:

```zafira
run @gpu {
    // Ushbu blok ichidagi amallar CUDA/GPU kontekstida bajariladi
    let v1 = ai.tensor([1.0, 2.0, 3.0])
    let v2 = ai.tensor([4.0, 5.0, 6.0])
    let natija = v1.dot(v2)
}

run @auto {
    // Platforma optimal qurilmani avtomatik tanlaydi (GPU bo'lsa GPU, aks holda CPU)
    let nollar = ai.zeros(4, 4)
}
```

---

## 13. Tashqi Interop Ko'prigi (`import py.*` va C FFI)

### 13.1. Python Zero-Overhead Interop
```zafira
import py.math
import py.json

let ildiz = math.sqrt(256.0) // 16.0
```

### 13.2. C FFI (`std.ffi`)
Dinamik C kutubxonalari (.dll / .so) bilan ishlash:
```zafira
import std.ffi

let libc = ffi.load("libc")
let modul = libc.call("abs", [-42], "int") // 42
```

---

## 14. Standart Kutubxona (`std.*` Barcha 13 ta Modul)

Zafira 13 ta o'rnatilgan boy standart modullarni taqdim etadi. Modulni chaqirish: `import std.<nom>` yoki `import std.<nom> as <taxallus>`.

---

### 14.1. `std.math` — Matematik Amallar
* `math.sqrt(x)`: Kvadrat ildiz.
* `math.pow(base, exp)`: Darajaga ko'tarish.
* `math.abs(x)`: Absolyut qiymat (modul).
* `math.floor(x)`: Pastga yaxlitlash.
* `math.ceil(x)`: Yuqoriga yaxlitlash.
* `math.round(x, [n])`: Eng yaqin butun yoki n ta raqamgacha yaxlitlash.
* `math.min(...)` / `math.max(...)`: Minimal va maksimal qiymat.
* `math.log(x, [base])`: Logarifm.
* `math.sin(x)`, `math.cos(x)`, `math.tan(x)`: Trigonometriya.
* O'zgarmaslar: `math.PI`, `math.E`, `math.INF`.

---

### 14.2. `std.string` — Matn bilan Ishlash
* `string.upper(s)` / `string.lower(s)`: Katta va kichik harflarga o'tkazish.
* `string.trim(s)`: Bo'sh joylarni tozalash.
* `string.split(s, [sep])`: Matnni qismlarga ajratish.
* `string.join(list, [sep])`: Ro'yxatni matnga birlashtirish.
* `string.replace(s, old, new, [count])`: Matn qismini almashtirish.
* `string.contains(s, sub)`: Ichida mavjudligini tekshirish (`true`/`false`).
* `string.starts_with(s, prefix)` / `string.ends_with(s, suffix)`.
* `string.repeat(s, n)`: Matnni takrorlash.
* `string.reverse(s)`: Matnni teskarisiga o'girish.

---

### 14.3. `std.list` — Ro'yxatlar Boshqaruvi
* `list.sort(lst, [key], [reverse])`: Ro'yxatni saralash.
* `list.reverse(lst)`: Ro'yxatni teskarisiga o'girish.
* `list.filter(lst, fn)`: Predikat bo'yicha filtrlash.
* `list.map(lst, fn)`: Elementlarni o'zgartirish.
* `list.reduce(lst, fn, [initial])`: Ro'yxatni bitta qiymatga keltirish.
* `list.find(lst, fn)`: Birinchi mos kelgan elementni topish.
* `list.contains(lst, item)`: Element mavjudligini tekshirish.
* `list.unique(lst)`: Takrorlanmas elementlarni ajratish.
* `list.flatten(lst)`: Ichma-ich ro'yxatlarni tekislash.
* `list.sum(lst)`, `list.max(lst)`, `list.min(lst)`.

---

### 14.4. `std.io` — Standart Kiritish va Chiqarish
* `io.print(...)`: Qator tashlamasdan chiqarish.
* `io.println(...)`: Qator tashlab chiqarish.
* `io.readline([prompt])`: Konsoldan ma'lumot o'qish.
* `io.write(text)`: To'g'ridan-to'g'ri oqimga yozish.

---

### 14.5. `std.ai` — Silikon Tenzor va AI Dvigateli
* `ai.tensor(data)`: N-o'lchamli tenzor yaratish (`shape`, `dot`, `sum`, `mean`, operatorlar).
* `ai.zeros(rows, cols)` / `ai.ones(rows, cols)`: Maxsus tenzorlar yaratish.
* `ai.similarity(t1, t2)`: Vektorlar kosinus o'xshashligini hisoblash.
* `ai.embedding_mock(text)`: Matn uchun semantik vektor hosil qilish.
* `ai.device()` / `ai.devices()`: Faol va mavjud apparat vositalarini aniqlash.

---

### 14.6. `std.json` — JSON Format Bilan Ishlash
* `json.parse(matn)`: JSON satrini ZafiraStruct yoki ZafiraList obyektiga aylantirish.
* `json.stringify(obj, [indent])`: Zafira obyektini JSON satriga aylantirish.
* `json.loads(...)`, `json.dumps(...)`: Sinonimlar.

---

### 14.7. `std.net` — Tarmoq va Web Xizmatlari
* `net.get(url, [headers])`: HTTP GET so'rovi (natija: `{ status, body, ok, headers }`).
* `net.post(url, [data], [json], [headers])`: HTTP POST so'rovi.
* `net.listen(port, handler_fn, [max_requests], [threaded])`: Yengil lokal HTTP server.
* `net.close(server)`: Serverni to'xtatish.

---

### 14.8. `std.fs` — Fayllar Tizimi
* `fs.read_text(path)`: Faylni matn sifatida o'qish.
* `fs.write_text(path, content)`: Faylga matn yozish.
* `fs.append_text(path, content)`: Fayl oxiriga qo'shish.
* `fs.exists(path)`: Mavjudligini tekshirish.
* `fs.is_file(path)` / `fs.is_dir(path)`.
* `fs.list_dir(path)`: Papka ichidagilarni ro'yxat qilish.
* `fs.make_dir(path, [recursive])`: Papka yaratish.
* `fs.remove(path)` / `fs.remove_dir(path, [recursive])`: O'chirish.
* `fs.file_size(path)`: Fayl hajmi (baytlarda).
* `fs.copy(src, dst)`: Nusxa olish.

---

### 14.9. `std.env` — Muhit O'zgaruvchilari va Tizim
* `env.get(key, [default])`: Muhit o'zgaruvchisi qiymatini olish.
* `env.set(key, val)`: Muhit o'zgaruvchisini o'rnatish.
* `env.has(key)`: Mavjudligini tekshirish.
* `env.remove(key)`: O'chirish.
* `env.args()`: CLI buyruq argumentlari ro'yxati.
* `env.os()`: Operatsion tizim nomi (`"windows"`, `"linux"`, `"darwin"`).
* `env.cwd()`: Joriy ishchi katalog yo'li.

---

### 14.10. `std.datetime` — Sana va Vaqt
* `datetime.now()`: Joriy sana va vaqt obyekti (`year`, `month`, `day`, `hour`, `minute`, `second`, `iso`).
* `datetime.timestamp()`: Unix timestamp (soniyalarda).
* `datetime.format([ts], [format])`: Sanani formatlash (masalan, `"%Y-%m-%d %H:%M:%S"`).
* `datetime.sleep(soniya)`: Kutish.
* `datetime.sleep_ms(millisoniya)`: Millisoniyalarda kutish.

---

### 14.11. `std.crypto` — Kriptografiya va Xavfsizlik
* `crypto.sha256(text)`: SHA-256 xesh (hex digest).
* `crypto.sha512(text)`: SHA-512 xesh.
* `crypto.md5(text)`: MD5 xesh.
* `crypto.hmac_sha256(key, message)`: HMAC-SHA256 xesh imzo.
* `crypto.base64_encode(text)`: Base64 kodlash.
* `crypto.base64_decode(text)`: Base64 dekodlash.
* `crypto.uuid()`: UUID v4 identifikatori.
* `crypto.random_bytes(n)`: Tasodifiy baytlar ro'yxati.
* `crypto.random_hex(n)`: 2*n belgili tasodifiy hex token.

---

### 14.12. `std.regex` — Muntazam Ifodalar (Regular Expressions)
* `regex.test(pattern, text)`: Mos kelishini tekshirish (`true`/`false`).
* `regex.find(pattern, text)`: Birinchi mos kelgan qismni olish.
* `regex.find_all(pattern, text)`: Barcha mos kelgan qismlar ro'yxati.
* `regex.replace(pattern, replacement, text)`: Birinchi moslikni almashtirish.
* `regex.replace_all(pattern, replacement, text)`: Barcha mosliklarni almashtirish.
* `regex.split(pattern, text)`: Matnni regex bo'yicha bo'lish.
* `regex.is_valid(pattern)`: Sintaktik to'g'riligini tekshirish.

---

### 14.13. `std.ffi` — C Foreign Function Interface
* `ffi.load(lib_name_or_path)`: Kutubxonani yuklash (`libc`, `msvcrt`, `.dll`, `.so`).
* `lib.call(func_name, [args], [return_type])`: C funksiyasini chaqirish.
* `lib.has_symbol(symbol_name)`: Simvol mavjudligini tekshirish.
* `ffi.c_int(val)`, `ffi.c_float(val)`, `ffi.c_double(val)`, `ffi.c_string(val)`, `ffi.c_bool(val)`: C turlariga o'rash.

---

## 15. Paket Menejeri va CLI Buyruqlari

Zafira tilini boshqarish va loyihalarni yuritish uchun CLI:

```bash
# 1. Yangi loyiha yaratish
python zafira.py init <loyiha_nomi>

# 2. Fayl yoki loyihani ishga tushirish
python zafira.py run <fayl.zf>
python zafira.py run .

# 3. C kodiga transpile qilish
python zafira.py transpile <fayl.zf>

# 4. Mustaqil binar dastur (.exe) ga kompilyatsiya qilish
python zafira.py compile <fayl.zf> -o <chiqish.exe>

# 5. Loyiha testlarini o'tkazish
python zafira.py test

# 6. Interaktiv REPL oynasi
python zafira.py repl

# 7. Web Interactive Playground (Online Studio)
python zafira.py playground --port 5000

# 8. Sintaktik daraxt va tokenlarni ko'rish (Debug)
python zafira.py tokens <fayl.zf>
python zafira.py ast <fayl.zf>
```

---

<p align="center">
  <sub>Zafira Language Specification v1.0.0 | Toshkent, O'zbekiston 🇺🇿 | 2026</sub>
</p>
