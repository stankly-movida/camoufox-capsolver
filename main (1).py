import asyncio
from camoufox.async_api import AsyncCamoufox
from capsolver_api import solve_captcha # Import the utility function

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
    # --- Configuration ---
    target_url = "https://example.com/protected-page"
    turnstile_site_key = "0x4XXXXXXXXXXXXXXXXX"  # Replace with the actual site key
    # ---------------------

    print(f"Starting automation for: {target_url}")

    async with AsyncCamoufox(
        humanize=True,
        headless=False,
        os="windows"
    ) as browser:
        page = await browser.new_page()
        await page.goto(target_url)

        print("Browser navigated. Waiting for Turnstile...")
        # Wait for Turnstile to load
        try:
            await page.wait_for_selector('input[name="cf-turnstile-response"]', timeout=10000)
        except TimeoutError:
            print("Turnstile element not found within timeout. Proceeding...")
            return

        # Solve the CAPTCHA
        print("Turnstile detected. Solving CAPTCHA...")
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
        try:
            await page.click('button[type="submit"]')
            await page.wait_for_load_state("networkidle")
            print("Successfully bypassed Turnstile and submitted form!")
        except Exception as e:
            print(f"Could not submit form: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"An error occurred during the main execution: {e}")
