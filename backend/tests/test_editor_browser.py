"""Real browser acceptance; RUN_EDITOR_BROWSER=1 pytest tests/test_editor_browser.py."""

import os
import socket
import threading
import time

import pytest
from tests.test_editor import editorial, database, SECRET  # noqa: F401

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_EDITOR_BROWSER") != "1", reason="Opt-in Chromium acceptance"
)


def test_private_editor_browser_review_maps_bulk_and_mobile(editorial):  # noqa: F811
    import uvicorn
    from playwright.sync_api import expect, sync_playwright
    from app.main import app

    _, assignments = editorial
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    server = uvicorn.Server(
        uvicorn.Config(app, log_level="error", proxy_headers=False, loop="asyncio")
    )
    thread = threading.Thread(target=lambda: server.run(sockets=[sock]), daemon=True)
    thread.start()
    try:
        deadline = time.monotonic() + 15
        while not server.started and time.monotonic() < deadline:
            time.sleep(0.05)
        assert server.started
        base = f"http://127.0.0.1:{port}"
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(base + "/editor")
            expect(
                page.get_by_role("heading", name="Review the evidence.")
            ).to_be_visible()
            page.get_by_label("Reviewer label").fill("browser:editor")
            page.get_by_label("Editorial key").fill(SECRET)
            page.get_by_role("button", name="Sign in", exact=True).click()
            expect(
                page.get_by_role("heading", name="Review queue", exact=True)
            ).to_be_visible()
            page.get_by_label("Search", exact=True).fill("Editor proposed")
            page.get_by_role("button", name="Apply filters").click()
            page.get_by_role("link", name="Editor proposed boundary").click()
            expect(
                page.get_by_role("heading", name="Editor proposed boundary", exact=True)
            ).to_be_visible()
            expect(page.locator("#proposed-map path.boundary")).to_have_count(1)
            if page.get_by_label("Published primary", exact=True).is_visible():
                page.get_by_label("Published primary", exact=True).select_option(
                    "editor-primary"
                )
            expect(page.locator("#primary-map path.boundary")).to_have_count(1)
            expect(page.locator("#sources")).to_contain_text(
                "Synthetic integration evidence"
            )
            assert page.locator('#sources a[href^="javascript:"]').count() == 0
            page.get_by_role("button", name="Zoom in on both maps").click()
            page.get_by_role("button", name="Fit both maps").click()
            # Private data remains private until a human confirms an action.
            assert (
                "editor-proposed"
                not in page.request.get(base + "/api/v1/world/117").text()
            )
            page.get_by_label("Decision", exact=True).select_option("dispute")
            page.get_by_label("Rationale", exact=True).fill(
                "Conflicting source dates; needs a closer reading."
            )
            page.get_by_role("checkbox").check()
            page.get_by_role("button", name="Record decision").click()
            expect(page.locator("#history")).to_contain_text("browser:editor · dispute")
            expect(page.locator("#record-heading")).to_contain_text("disputed")
            assert (
                "editor-proposed"
                not in page.request.get(base + "/api/v1/world/117").text()
            )
            page.get_by_label("Decision", exact=True).select_option("approve")
            page.get_by_label("Rationale", exact=True).fill(
                "Synthetic geometry and source checked for this test only."
            )
            page.get_by_role("checkbox").check()
            page.get_by_role("button", name="Record decision").click()
            expect(page.locator("#record-heading")).to_contain_text("reviewed")
            expect(page.locator("#history")).to_contain_text("browser:editor · approve")
            assert (
                "editor-proposed" in page.request.get(base + "/api/v1/world/117").text()
            )
            page.goto(base + "/editor?q=Editor+proposed&status=reviewed")
            expect(
                page.get_by_role("link", name="Editor proposed boundary")
            ).to_be_visible()
            page.goto(base + "/editor?q=Editor+citation&confidence=high")
            page.get_by_label("Select Editor citation a", exact=True).check()
            page.get_by_label("Select Editor citation b", exact=True).check()
            page.get_by_label("Shared rationale").fill(
                "Checked both synthetic citations; no historical approval implied."
            )
            page.get_by_role(
                "checkbox",
                name="I checked every selected citation. Approving makes these records public.",
            ).check()
            page.get_by_role("button", name="Approve 2 selected records").click()
            expect(page.get_by_role("status")).to_contain_text(
                "Citation batch approved"
            )
            page.goto(base + "/editor/reviews/" + assignments["editor-proposed"])
            page.set_viewport_size({"width": 390, "height": 844})
            expect(page.locator("#proposed-map path.boundary")).to_have_count(1)
            assert page.evaluate(
                "document.documentElement.scrollWidth <= window.innerWidth"
            )
            if os.environ.get("EDITOR_SCREENSHOT"):
                page.screenshot(path=os.environ["EDITOR_SCREENSHOT"], full_page=True)
            # Reload gets a new view, but never persists the editorial API key.
            assert page.evaluate("JSON.stringify({...localStorage})").find(SECRET) == -1
            assert (
                page.evaluate("JSON.stringify({...sessionStorage})").find(SECRET) == -1
            )
            page.reload()
            expect(page.locator("#history")).to_contain_text("browser:editor · approve")
            # Large original source geometries must not hit JavaScript argument limits.
            import math

            def large_geometry(route):
                data = route.fetch().json()
                ring = [
                    [
                        12 + math.cos(i * math.tau / 130000),
                        41 + math.sin(i * math.tau / 130000),
                    ]
                    for i in range(130000)
                ]
                ring.append(ring[0])
                data["target"]["geometry_json"] = {
                    "type": "Polygon",
                    "coordinates": [ring],
                }
                route.fulfill(json=data)

            page.route(
                "**/editor/api/reviews/" + assignments["editor-proposed"],
                large_geometry,
            )
            page.reload()
            expect(page.locator("#proposed-map path.boundary")).to_have_count(
                1, timeout=15000
            )
            page.get_by_role("button", name="Sign out").click()
            expect(
                page.get_by_role("heading", name="Review the evidence.")
            ).to_be_visible()
            assert page.request.get(base + "/editor/api/queue").status == 401
            assert not errors
            browser.close()
    finally:
        server.should_exit = True
        thread.join(timeout=10)
        sock.close()
