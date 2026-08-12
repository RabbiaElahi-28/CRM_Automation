from datetime import datetime
from pathlib import Path


def take_screenshot(page, name):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = Path(f"reports/screenshots/{name}_{timestamp}.png")
    path.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(path))
    return str(path)