# 🔷 Zafira VS Code Extension O'rnatish Yo'riqnomasi

Zafira (`.zf`) dasturlash tili uchun Visual Studio Code kengaytmasini o'rnatishning 3 xil oson usuli mavjud:

---

## 🚀 Usul 1: VSIX Fayli Orqali (Tavsiya etiladi)

Tayyor paketlangan `.vsix` faylini to'g'ridan-to'g'ri VS Code ga o'rnatish:

1. VS Code dasturini oching.
2. `Ctrl + Shift + P` (macOS da `Cmd + Shift + P`) tugmalarini bosing.
3. Qidiruv qatoriga quyidagini yozing va tanlang:
   ```text
   Extensions: Install from VSIX...
   ```
4. `D:\ALLProjects\zafira-lang\vscode-zafira\zafira-lang-0.1.0.vsix` faylini tanlang va **Install** tugmasini bosing.
5. VS Code ni qayta ishga tushiring yoki oynani yangilang (`Developer: Reload Window`).

---

## 🛠️ Usul 2: Extension Development Rejimi (F5)

Kengaytmani sinash yoki yangi sintaksis qoidalarini ishlab chiqish uchun:

1. `vscode-zafira/` papkasini VS Code dasturida oching:
   ```powershell
   code D:\ALLProjects\zafira-lang\vscode-zafira
   ```
2. Klaviaturada `F5` tugmasini bosing.
3. Yangi ochilgan **Extension Development Host** oynasida har qanday `.zf` faylini oching (masalan, `examples/hello.zf`).
4. To'liq sintaksis ranglash va kod yig'ish (folding) bir zumda ishlaydi!

---

## 📂 Usul 3: To'g'ridan-to'g'ri Extensions Papkasiga Nusxalash

Agar VSIX vositasi bo'lmasa, papkani to'g'ridan-to'g'ri VS Code kengaytmalar papkasiga nusxalashingiz mumkin:

### Windows:
```powershell
Copy-Item -Recurse "D:\ALLProjects\zafira-lang\vscode-zafira" "$env:USERPROFILE\.vscode\extensions\zafira-lang"
```

### Linux / macOS:
```bash
cp -r D:/ALLProjects/zafira-lang/vscode-zafira ~/.vscode/extensions/zafira-lang
```

Nusxalangach, VS Code oynasini qayta yuklang (`Ctrl+Shift+P` -> `Developer: Reload Window`).

---

## ✨ Imkoniyatlar

- 🎨 **To'liq sintaksis ranglash**: `let`, `const`, `fn`, `seal`, `draft`, `where`, `run`, `struct`, `import`, `for`, `while`
- ⚡ **Hardware direktivalar**: `@gpu`, `@npu`, `@auto`, `@cpu`
- 🛡️ **O'rnatilgan turlar**: `Int`, `Float`, `String`, `Bool`
- 💬 **Avtomatik izohlar**: `Ctrl + /` (bitta qator) va `Shift + Alt + A` (blokli izoh)
- 🧩 **Qavslarni avto-yopish** va bloklarni yig'ish (code folding)
