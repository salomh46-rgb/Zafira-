# Zafira Language Support for Visual Studio Code

Official syntax highlighting and language configuration extension for the **Zafira Programming Language** (`.zf`).

## Features

- **Syntax Highlighting**:
  - Full keyword recognition (`let`, `const`, `fn`, `return`, `if`, `else`, `while`, `for`, `in`, `struct`, `import`, `seal`, `draft`, `where`, `run`, `and`, `or`, `not`)
  - Hardware directives (`@gpu`, `@npu`, `@auto`, `@cpu`)
  - Built-in types (`Int`, `Float`, `String`, `Bool`)
  - Built-in functions (`print`, `input`, `len`, `range`, `type`)
  - Function and struct declarations & calls
  - Strings, numbers, booleans, and comments (`//`, `/* */`)
  - Operators (`->`, `..`, arithmetic, logical, and comparison operators)
- **Language Configuration**:
  - Bracket matching & auto-closing pairs
  - Comment toggling (`Ctrl + /` for line comment, `Shift + Alt + A` for block comment)
  - Code folding support

## File Extension

- Files ending with `.zf` are automatically recognized as Zafira source code.

## Installation / Development

To install and test locally in VS Code:
1. Copy the `vscode-zafira` folder into your VS Code extensions folder:
   - Windows: `%USERPROFILE%\.vscode\extensions\zafira-lang`
   - Linux / macOS: `~/.vscode/extensions/zafira-lang`
2. Restart VS Code or run the `Developer: Reload Window` command.
