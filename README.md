# Camoufox + CapSolver: 网页自动化解决方案

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Status: Active](https://img.shields.io/badge/Status-Active-brightgreen.svg)]()

> **简介**: 本项目提供了一个将 **Camoufox**（反检测浏览器）与 **CapSolver**（验证码识别服务）集成的方案。通过结合浏览器指纹伪装和自动验证码解决，实现稳定、高效的网页自动化和数据采集。

---

## 🚀 项目背景

在进行网页自动化或数据采集时，我们经常会遇到两大挑战：复杂的**浏览器指纹检测**和各种**验证码**。本集成方案旨在解决这些问题：

1.  **Camoufox**: 一个基于 Firefox 的开源反检测浏览器，通过在底层 C++ 层面伪装浏览器指纹，帮助脚本绕过反爬虫系统的检测。
2.  **CapSolver**: 一个 AI 驱动的验证码解决服务，支持 Cloudflare Turnstile、reCAPTCHA 等主流验证码类型。

通过这种方式，您的自动化脚本能够模拟真实用户的行为和环境，大大提高成功率。

![集成示意图](https://assets.capsolver.com/prod/posts/camoufox-capsolver/BHTvecwsomf8-10fb15c77258a991b0028080a64fb42d.png)

## ✨ 核心功能

| 功能点 | Camoufox 作用 | CapSolver 作用 |
| :--- | :--- | :--- |
| **反检测** | 原生 C++ 级别指纹伪装（如 WebGL、Canvas、字体等） | 无 |
| **验证码处理** | 无 | 解决 Turnstile、reCAPTCHA v2/v3、hCaptcha 等 |
| **行为模拟** | 内置鼠标移动拟人化算法，模拟真实用户操作 | 提供快速、可靠的验证码结果 |
| **地理位置** | 根据代理 IP 自动设置时区和区域 | 无 |

## 🛠️ 环境准备

### 1. 准备 CapSolver API 密钥

您需要一个 CapSolver API 密钥来使用验证码解决服务。
👉 **[获取您的 CapSolver API 密钥](https://dashboard.capsolver.com/dashboard/overview/?utm_source=github&utm_medium=repo&utm_campaign=camoufox-capsolver-integration)**

> **提示**：注册时使用代码 **`CAMOUFOX`** 可获得额外奖励额度。

### 2. 安装依赖

安装 Camoufox Python 库和用于 API 调用的 `httpx` 库。

```bash
# 安装 Camoufox (推荐带 GeoIP 支持)
pip install -U camoufox[geoip]

# 安装 HTTP 客户端
pip install httpx

# 下载 Camoufox 浏览器核心文件
camoufox fetch
```

## 💻 核心代码逻辑（API 方式）

推荐使用 API 方式进行集成，以获得对验证码解决流程的完全控制。

### `capsolver_api.py`

此文件封装了与 CapSolver API 交互的异步函数，包括创建任务和轮询结果。

## 💡 使用示例

### 示例 1: 解决 Cloudflare Turnstile

此示例展示了如何获取 Turnstile 令牌并将其注入到 Camoufox 页面中。

```python
import asyncio
from camoufox.async_api import AsyncCamoufox
from capsolver_api import solve_captcha # 假设 capsolver_api.py 已保存

async def solve_turnstile(site_key: str, page_url: str) -> str:
    """解决 Cloudflare Turnstile 并返回令牌。"""
    task_payload = {
        "type": "AntiTurnstileTaskProxyLess",
        "websiteURL": page_url,
        "websiteKey": site_key,
    }
    solution = await solve_captcha(task_payload)
    return solution["token"]


async def main():
    target_url = "https://example.com/protected-page"
    turnstile_site_key = "0x4XXXXXXXXXXXXXXXXX"  # 替换为实际的站点密钥

    async with AsyncCamoufox(
        humanize=True,
        headless=False,
        os="windows"
    ) as browser:
        page = await browser.new_page()
        await page.goto(target_url)

        # 等待 Turnstile 元素加载
        await page.wait_for_selector('input[name="cf-turnstile-response"]', timeout=10000)

        # 解决验证码
        token = await solve_turnstile(turnstile_site_key, target_url)
        print(f"获取到 Turnstile 令牌: {token[:50]}...")

        # 注入令牌并尝试触发表单提交
        await page.evaluate(f'''
            document.querySelector('input[name="cf-turnstile-response"]').value = "{token}";

            // 可选：调用隐藏的回调函数
            const callback = document.querySelector('[data-callback]');
            if (callback) {{
                const callbackName = callback.getAttribute('data-callback');
                if (window[callbackName]) {{
                    window[callbackName]('{token}');
                }}
            }}
        ''')

        # 提交表单（请根据实际页面调整选择器）
        await page.click('button[type="submit"]')
        await page.wait_for_load_state("networkidle")

        print("成功绕过 Turnstile 并提交表单！")


if __name__ == "__main__":
    asyncio.run(main())
```

## 🔗 替代方案：浏览器扩展集成

对于不需要精细控制的场景，可以直接将 CapSolver 浏览器扩展加载到 Camoufox 中。

1.  从 [CapSolver 扩展页面](https://www.capsolver.com/en/extension?utm_source=github&utm_medium=repo&utm_campaign=camoufox-capsolver-integration) 下载扩展。
2.  在 Camoufox 初始化时加载：

```python
from camoufox.sync_api import Camoufox

with Camoufox(
    addons=["/path/to/capsolver-extension"],
    headless=False  # 扩展通常需要在有头模式下运行
) as browser:
    page = browser.new_page()
    # 扩展将自动检测并解决验证码
```

## 🤝 贡献

欢迎提交 Issue 或 Pull Request 来改进此集成方案。

## 📄 许可证

本项目采用 MIT 许可证授权。
