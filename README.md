# SmojSubmit

[![Package Control](https://img.shields.io/packagecontrol/dt/SmojSubmit?style=flat-square)](https://packagecontrol.io/packages/SmojSubmit)
[![GitHub](https://img.shields.io/github/license/YanWQ-monad/SmojSubmit?style=flat-square)](https://github.com/YanWQ-monad/SmojSubmit/blob/master/LICENSE)

SmojSubmit is a Sublime Text plugin, which can submit your code to Online Judge by one click,
and pull the result automatically.

English | [简体中文](https://github.com/YanWQ-monad/SmojSubmit/blob/master/README.zh.md)

---

![Introduction gif](https://raw.githubusercontent.com/YanWQ-monad/static/master/SmojSubmit/Introduction.gif)

## Install

Install SmojSubmit from [Package Control](https://packagecontrol.io/search/SmojSubmit).

Here are the detailed steps:

1. Press <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>P</kbd>, and select `Package Control: Install Package`;
2. Enter `SmojSubmit` and install.

## Configure

Select `Preferences` → `Package Settings` → `SMOJ Submit` → `Edit Settings`,
then enter your passwords to the configuration.

Note: `init_login` option is to toggle whether or not log in to the Online Judge when Sublime Text starts,
keep the default if you don't have special needs.

<details>
  <summary>A configuration example</summary>

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

## Usage

Right click on the Sublime Text editing area, select the target Online Judge in `Submit to...`.  
The `Submit` button is to submit to the latest submitted Online Judge.

## Contributing & Bugs report

Due to the use of unofficial API, there may be some bugs in the plugin.
If you have an issue, please report it in the [Issue Tracker](https://github.com/YanWQ-monad/SmojSubmit/issues).
Of course, features request is also accepted.

And welcome [PR](https://github.com/YanWQ-monad/SmojSubmit/pulls).

## License

[MIT](https://github.com/YanWQ-monad/SmojSubmit/blob/master/LICENSE)
