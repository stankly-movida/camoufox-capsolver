# Camoufox + CapSolver: Unstoppable Web Automation

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Status: Active](https://img.shields.io/badge/Status-Active-brightgreen.svg)]()

> **TL;DR**: Use **Camoufox** to evade browser fingerprinting and **CapSolver** to automatically solve CAPTCHAs like Cloudflare Turnstile and reCAPTCHA v2/v3. Together, they enable stable, human-like web automation at scale with minimal detection and high success rates.

---

## 🚀 Overview

Modern web automation faces two primary hurdles: sophisticated **anti-bot fingerprinting** and persistent **CAPTCHA challenges**. This repository provides a robust, production-ready solution by integrating two powerful tools:

1.  **Camoufox**: An open-source, anti-detect Firefox build that spoofs browser fingerprints at the native C++ level.
2.  **CapSolver**: An AI-powered CAPTCHA solving service that handles virtually all modern challenges, including Turnstile and reCAPTCHA.

This integration ensures your automation scripts appear as legitimate human users, both in terms of browser identity and interaction behavior.

![Integration Diagram](https://assets.capsolver.com/prod/posts/camoufox-capsolver/BHTvecwsomf8-10fb15c77258a991b0028080a64fb42d.png)

## ✨ Key Features

| Feature | Camoufox Contribution | CapSolver Contribution |
| :--- | :--- | :--- |
| **Anti-Detection** | Native C++ fingerprint spoofing (WebGL, Canvas, Fonts, etc.) | N/A |
| **CAPTCHA Bypass** | N/A | Solves Turnstile, reCAPTCHA v2/v3, hCaptcha, etc. |
| **Human-Like Behavior** | Built-in mouse movement humanization | Fast, reliable, and consistent solving |
| **Geo-Location** | Automatic timezone/locale calculation based on proxy IP | N/A |

## 🛠️ Setup and Installation

### 1. Prerequisites

You will need a CapSolver API key. You can sign up and get your key here:
👉 **[Get Your CapSolver API Key](https://dashboard.capsolver.com/dashboard/overview/?utm_source=github&utm_medium=repo&utm_campaign=camoufox-capsolver-integration)**

> **Bonus:** Use code **`CAMOUFOX`** when registering to receive bonus credits!

### 2. Installation

Install the Camoufox Python package and the `httpx` library for asynchronous API calls.

```bash
# Install Camoufox with GeoIP support
pip install -U camoufox[geoip]

# Install the necessary HTTP client
pip install httpx

# Download the Camoufox browser binary
camoufox fetch
```

## 💻 Core Integration Logic (API Method)

The recommended approach is to use the CapSolver API directly for maximum control and flexibility.

### `capsolver_api.py`

This module contains the asynchronous functions to interact with the CapSolver API.

```python
import asyncio
import httpx

CAPSOLVER_API_KEY = "YOUR_API_KEY"  # Replace with your actual key
CAPSOLVER_API = "https://api.capsolver.com"


async def create_task(task_payload: dict) -> str:
    """Create a CAPTCHA solving task and return the task ID."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{CAPSOLVER_API}/createTask",
            json={
                "clientKey": CAPSOLVER_API_KEY,
                "task": task_payload
            }
        )
        result = response.json()
        if result.get("errorId") != 0:
            raise Exception(f"CapSolver error: {result.get('errorDescription')}")
        return result["taskId"]


async def get_task_result(task_id: str, max_attempts: int = 120) -> dict:
    """Poll for task result until solved or timeout."""
    async with httpx.AsyncClient() as client:
        for _ in range(max_attempts):
            response = await client.post(
                f"{CAPSOLVER_API}/getTaskResult",
                json={
                    "clientKey": CAPSOLVER_API_KEY,
                    "taskId": task_id
                }
            )
            result = response.json()

            if result.get("status") == "ready":
                return result["solution"]
            elif result.get("status") == "failed":
                raise Exception(f"Task failed: {result.get('errorDescription')}")

            await asyncio.sleep(1)

    raise TimeoutError("CAPTCHA solving timed out")


async def solve_captcha(task_payload: dict) -> dict:
    """Complete CAPTCHA solving workflow."""
    task_id = await create_task(task_payload)
    return await get_task_result(task_id)
```

## 💡 Usage Examples

### Example 1: Solving Cloudflare Turnstile

This example demonstrates how to use the `solve_captcha` function to get a Turnstile token and inject it into the Camoufox-controlled page.

```python
import asyncio
from camoufox.async_api import AsyncCamoufox
from capsolver_api import solve_captcha # Assuming the above code is saved as capsolver_api.py

async def solve_turnstile(site_key: str, page_url: str) -> str:
    """Solve Cloudflare Turnstile and return the token."""
    task_payload = {
        "type": "AntiTurnstileTaskProxyLess",
        "websiteURL": page_url,
        "websiteKey": site_key,
    }
    solution = await solve_captcha(task_payload)
    return solution["token"]


async def main():
    target_url = "https://example.com/protected-page"
    turnstile_site_key = "0x4XXXXXXXXXXXXXXXXX"  # Find this in page source

    async with AsyncCamoufox(
        humanize=True,
        headless=False,
        os="windows"
    ) as browser:
        page = await browser.new_page()
        await page.goto(target_url)

        # Wait for Turnstile to load
        await page.wait_for_selector('input[name="cf-turnstile-response"]', timeout=10000)

        # Solve the CAPTCHA
        token = await solve_turnstile(turnstile_site_key, target_url)
        print(f"Got Turnstile token: {token[:50]}...")

        # Inject the token and trigger the form submission
        await page.evaluate(f'''
            document.querySelector('input[name="cf-turnstile-response"]').value = "{token}";

            // Optional: Call the hidden callback if present
            const callback = document.querySelector('[data-callback]');
            if (callback) {{
                const callbackName = callback.getAttribute('data-callback');
                if (window[callbackName]) {{
                    window[callbackName]('{token}');
                }}
            }}
        ''')

        # Submit the form (adjust selector as needed)
        await page.click('button[type="submit"]')
        await page.wait_for_load_state("networkidle")

        print("Successfully bypassed Turnstile!")


if __name__ == "__main__":
    asyncio.run(main())
```

### Example 2: Solving reCAPTCHA v2

This example shows the payload structure for solving a standard reCAPTCHA v2 challenge.

```python
import asyncio
from camoufox.async_api import AsyncCamoufox
from capsolver_api import solve_captcha # Assuming the above code is saved as capsolver_api.py

async def solve_recaptcha_v2(site_key: str, page_url: str) -> str:
    """Solve reCAPTCHA v2 and return the token."""
    task_payload = {
        "type": "ReCaptchaV2TaskProxyLess",
        "websiteURL": page_url,
        "websiteKey": site_key,
    }
    solution = await solve_captcha(task_payload)
    return solution["gRecaptchaResponse"]


async def main():
    target_url = "https://example.com/recaptcha-page"
    recaptcha_site_key = "6LXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"

    async with AsyncCamoufox(humanize=True) as browser:
        page = await browser.new_page()
        await page.goto(target_url)

        # Solve the CAPTCHA
        token = await solve_recaptcha_v2(recaptcha_site_key, target_url)
        print(f"Got reCAPTCHA token: {token[:50]}...")

        # Inject the token into the hidden textarea
        await page.evaluate(f'''
            document.getElementById('g-recaptcha-response').value = "{token}";
        ''')

        # Submit the form
        await page.click('button[type="submit"]')
        await page.wait_for_load_state("networkidle")

        print("Successfully bypassed reCAPTCHA v2!")


if __name__ == "__main__":
    asyncio.run(main())
```

## 🔗 Alternative: Browser Extension Method

For simpler use cases, you can load the CapSolver browser extension directly into Camoufox.

1.  Download the CapSolver extension from [CapSolver Extension Page](https://www.capsolver.com/en/extension?utm_source=github&utm_medium=repo&utm_campaign=camoufox-capsolver-integration).
2.  Load it during Camoufox initialization:

```python
from camoufox.sync_api import Camoufox

with Camoufox(
    addons=["/path/to/capsolver-extension"],
    headless=False  # Extensions typically require headed mode
) as browser:
    page = browser.new_page()
    # The extension will automatically detect and solve CAPTCHAs
```

## 🤝 Contributing

Contributions are welcome! If you have suggestions for improving the integration, please open an issue or submit a pull request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
