# 💎 SapphireKV — In-Memory Cache & Key-Value Store

<p align="center">
  <img src="https://raw.githubusercontent.com/salomh46-rgb/Zafira-/main/vscode-zafira/icon.png" width="128" alt="Zafira SapphireKV"/>
</p>

<p align="center">
  <b>100% Zafira v1.0.0 dasturlash tilida yozilgan ultra-tezkor In-Memory kesh va doimiy ombor dvigateli.</b><br/>
  <i>Redis va Memcached'ning yengil, xavfsiz va kristalldek tiniq analogi.</i>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Language-Zafira_1.0.0-0ea5e9?style=for-the-badge&logo=crystal" alt="Zafira"/>
  <img src="https://img.shields.io/badge/Architecture-REST_&_In--Memory-10b981?style=for-the-badge" alt="In-Memory"/>
  <img src="https://img.shields.io/badge/Persistence-AOF_Engine-f59e0b?style=for-the-badge" alt="Persistence"/>
  <img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="MIT License"/>
</p>

---

## 🌟 Nega SapphireKV?

**SapphireKV** — bu **Zafira dasturlash tili** faqat nazariy til emas, balki real ishlab chiqarish (production) muhitida yuqori yuklamali server va kesh tizimlarini qura olishini isbotlovchi **Flagman Dogfooding Loyihasi**dir.

U hech qanday tashqi C/Python kutubxonalariga ehtiyoj sezmasdan, to'liq Zafira sintaksisi (`struct`, `impl`, `try/catch`, `std.net`, `std.json`, `std.fs`, `std.datetime`) imkoniyatlaridan foydalanib yozilgan.

---

## ✨ Asosiy Imkoniyatlar

1. ⚡ **In-Memory Tezkorlik**: Barcha kalit-qiymat ma'lumotlari to'g'ridan-to'g'ri RAM xotirada mikrosoniyalarda qayta ishlanadi.
2. ⏱️ **TTL & Lazy Expiration**: Har bir kesh kaliti uchun soniyalarda yashash muddati (TTL) belgilanadi. Muddati o'tgan kalitlar xotirani bo'shatish uchun avtomatik tozalanadi.
3. 💾 **AOF Persistence (Append-Only File)**: Server qayta yuklanganda ma'lumotlar yo'qolib ketmasligi uchun har bir operatsiya fonda `sapphire_store.aof` fayliga saqlanadi va startda xotiraga tiklanadi.
4. 🌐 **O'rnatilgan HTTP REST API**: Istalgan dastur (Python, Node.js, Go, PHP, cURL) orqali HTTP orqali ulanish imkoniyati (Port: `6380`).
5. 📊 **Haqiqiy Vaqt Statistikasi**: Jami amallar, Kesh Topilmalari (Hits) va Topilmaganlar (Misses) hisobi.
6. 📦 **1-Buyruqda Binar Kompilyatsiya**: `zafira pack` yordamida mustaqil `.exe` binar faylga aylanadi.

---

## 🚀 Tezkor Boshlash (Quick Start)

### 1. Zafira tili orqali ishga tushirish
```bash
# Loyiha papkasiga o'ting
cd sapphire_kv

# Serverni ishga tushiring
zafira run .
```

### 2. Standalone Binar (.exe) qilish
```bash
zafira pack . -o dist/sapphire_kv.exe
./dist/sapphire_kv.exe
```

### 3. Avtomatlashtirilgan Testlarni bajarish
```bash
zafira test .
```
Natija:
```
[Zafira Test] Jami 2 ta test topildi...
  ✅ [PASSED] test_main.zf
  ✅ [PASSED] test_store.zf
  🧪 Natijalar: Jami: 2 | O'tdi: 2 | Yiqildi: 0
```

---

## 📡 REST API Qo'llanmasi

Server sukut bo'yicha `http://127.0.0.1:6380` portida ishlaydi.

### 1. Sog'liqni tekshirish (PING)
```bash
curl http://127.0.0.1:6380/ping
# Javob: PONG
```

### 2. Qiymatni yozish (SET)
```bash
curl -X POST http://127.0.0.1:6380/set \
  -H "Content-Type: application/json" \
  -d '{"key": "user:1", "val": "Jasper", "ttl": 60.0}'
# Javob: {"status": "OK", "saved": true}
```

### 3. Qiymatni o'qish (GET)
```bash
curl http://127.0.0.1:6380/get?key=user:1
# Javob: {"found": true, "key": "user:1", "val": "Jasper"}
```

### 4. Kalitni o'chirish (DEL)
```bash
curl http://127.0.0.1:6380/del?key=user:1
# Javob: {"deleted": true}
```

### 5. Dvigatel Statistikasi (STATS)
```bash
curl http://127.0.0.1:6380/stats
# Javob: {"total_operations": 42, "hits": 38, "misses": 4, "engine": "Zafira In-Memory KV"}
```

---

## 🏗️ Arxitektura va Kod Tuzilishi

```
sapphire_kv/
├── zafira.json           # ZPM Loyiha manifesti
├── README.md             # Loyiha hujjati
├── src/
│   ├── store.zf          # Asosiy Store dvigateli (SET, GET, DEL, TTL, AOF)
│   └── main.zf           # REST Server shlyuzi va Entrypoint
├── tests/
│   ├── test_main.zf      # Boshlang'ich yaxlitlik testi
│   └── test_store.zf     # To'liq xotira va persistence unit testlari
└── dist/
    └── sapphire_kv.exe   # Standalone kompilyatsiya qilingan binar
```

### Koddan Namuna (`src/store.zf`):
```zafira
struct Store {
    items: JsonObject,
    total_ops: Int,
    hits: Int,
    misses: Int,
    aof_path: String
}

impl Store {
    fn set(self, key: String, val: String, ttl_seconds: Float) {
        let now = datetime.timestamp()
        let exp = 0.0
        if ttl_seconds > 0.0 {
            exp = now + ttl_seconds
        }
        let item = json.parse("{}")
        item["key"] = key
        item["val"] = val
        item["exp"] = exp
        self.items[key] = item
        self.persist()
        return true
    }
}
```

---

## 👨‍💻 Muallif
- **Javohirbek Asqarov (Jasper)** — Zafira tili va SapphireKV yaratuvchisi.
- Loyiha: [Zafira Programming Language](https://github.com/salomh46-rgb/Zafira-)
