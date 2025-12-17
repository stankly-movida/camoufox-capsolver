import asyncio
import httpx

# NOTE: Replace "YOUR_API_KEY" with your actual CapSolver API key
CAPSOLVER_API_KEY = "YOUR_API_KEY"
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
