# SmojSubmit

[![Package Control](https://img.shields.io/packagecontrol/dt/SmojSubmit?style=flat-square)](https://packagecontrol.io/packages/SmojSubmit)
[![GitHub](https://img.shields.io/github/license/YanWQ-monad/SmojSubmit?style=flat-square)](https://github.com/YanWQ-monad/SmojSubmit/blob/master/LICENSE)

SmojSubmit 是一个 Sublime Text 插件，它可以一键提交你的代码到指定 OJ，并自动抓取评测结果。

[English](https://github.com/YanWQ-monad/SmojSubmit/blob/master/README.md) | 简体中文

---

![演示 gif](https://raw.githubusercontent.com/YanWQ-monad/static/master/SmojSubmit/Introduction.gif)

## 安装

1. 按下 <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>P</kbd>，选择 `Package Control: Install Package`；
2. 输入并搜索 `SmojSubmit`，然后选择并安装。

> 如果在第一步没有发现 `Package Control: Install Package`，你需要先执行以下步骤：  
> 按下 <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>P</kbd>，选择 `Install Package Control` 以安装 Package Control。

## 配置

从菜单栏依次选择 `Preferences` → `Package Settings` → `SMOJ Submit` → `Edit Settings`，然后在弹出的窗口的配置中输入你 OJ 的密码。

**注 1：窗口的左半边为模板，右边才是写配置的地方，请依照左边的模板依样画葫芦**  
注 2：`init_login` 选项为是否在启动 Sublime Text 的时候就登录到该 OJ，无特殊情况不建议修改。

<details>
  <summary>一个配置好的例子</summary>

``` json
{
    "oj": {
        "bzoj": {
            "username": "Monad",
            "password": "******",
            "init_login": false
        },
        "luogu": {
            "username": "Monad",
            "password": "******",
            "init_login": false
        },
        "codeforces": {
            "username": "YanWQmonad",
            "password": "******",
            "init_login": false
        }
    }
}
```
</details>

## 使用

在 Sublime Text 编辑区内右键，在右键菜单中 `Submit to...` 内选择目标 OJ 即可。  
`Submit` 按钮为提交至最近提交过的 OJ。

## 问题报告

由于使用了非官方的 API，插件可能存在一些 bug。如果你遇到了 bug，请在 [Issue](https://github.com/YanWQ-monad/SmojSubmit/issues) 页面中提出。

同时欢迎 [PR](https://github.com/YanWQ-monad/SmojSubmit/pulls)。
