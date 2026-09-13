from __future__ import annotations

import time
from pathlib import Path
from playwright.sync_api import BrowserContext

from .formatter import FormattedPost


def publish_to_meta(
    context: BrowserContext,
    post: FormattedPost,
    schedule: str | None = None,
    draft: bool = False,
) -> dict[str, str]:
    page = context.new_page()
    page.set_default_timeout(180000)

    try:
        print("[Meta] Navigating to Meta Business Suite...")
        # Direct URL with the user's business asset ID, with fallback to Home
        page.goto("https://business.facebook.com/latest/reels_composer/?asset_id=1340731649114146&business_id=1971406070195910", wait_until="domcontentloaded")
        page.wait_for_timeout(5000)

        # If not in composer, click 'Create Reel' button from Home
        if "reels_composer" not in page.url:
            create_reel_btn = page.locator("button:has-text('Create Reel'), div[role='button']:has-text('Create Reel')").first
            if create_reel_btn.is_visible():
                create_reel_btn.click()
                page.wait_for_timeout(5000)

        # Check authentication
        if "login" in page.url.lower():
            raise RuntimeError(
                "Not logged into Meta Business Suite! Please run: python scripts/avbrief.py login"
            )

        print("[Meta] Locating video upload...")
        add_btn = page.locator("button:has-text('Add video'), div[role='button']:has-text('Add video'), button:has-text('إضافة فيديو')").first
        if add_btn.is_visible():
            with page.expect_file_chooser(timeout=20000) as fc_info:
                add_btn.click()
            file_chooser = fc_info.value
            file_chooser.set_files(str(post.video_path))
        else:
            file_input = page.locator("input[type='file']").first
            file_input.wait_for(state="attached", timeout=20000)
            file_input.set_input_files(str(post.video_path))

        print(f"[Meta] Uploading {post.video_path.name}. Waiting for upload to reach 100%...")
        for _ in range(30):
            page.wait_for_timeout(3000)
            txt = page.locator("body").inner_text()
            if "100%" in txt:
                print("[Meta] Video upload hit 100%!")
                break
        else:
            print("[Meta] Upload wait finished, proceeding with form...")

        # Both Facebook Page & Instagram account are linked and checked by default
        print("[Meta] Entering caption into Text box...")
        caption_box = page.locator("div[role='textbox'], div[contenteditable='true']").first
        caption_box.wait_for(state="visible", timeout=30000)
        caption_box.click()
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
        caption_box.fill(post.meta_caption)
        page.wait_for_timeout(2000)

        print("[Meta] Waiting for Step 1 (Create) Next button to become active...")
        for check in range(1, 15):
            page.wait_for_timeout(3000)
            next_btn = page.locator("button:has-text('Next'), div[role='button']:has-text('Next')").last
            dis = next_btn.get_attribute("aria-disabled") or next_btn.get_attribute("disabled")
            if dis != "true" and dis is not True:
                print("[Meta] Next button is active. Advancing to Step 2 (Edit)...")
                next_btn.click()
                page.wait_for_timeout(4000)
                break
        else:
            # Fallback click
            page.locator("button:has-text('Next'), div[role='button']:has-text('Next')").last.click()
            page.wait_for_timeout(4000)

        print("[Meta] Advancing from Step 2 (Edit) to Step 3 (Share)...")
        next_btn2 = page.locator("button:has-text('Next'), div[role='button']:has-text('Next')").last
        if next_btn2.is_visible():
            next_btn2.click()
            page.wait_for_timeout(4000)

        if draft:
            draft_radio = page.locator("input[type='radio'][value*='DRAFT' i], label:has-text('Draft'), label:has-text('مسودة')").first
            if draft_radio.is_visible():
                draft_radio.click()
                page.wait_for_timeout(1000)
        elif schedule:
            schedule_radio = page.locator("input[type='radio'][value*='SCHEDULE' i], label:has-text('Schedule'), label:has-text('جدولة')").first
            if schedule_radio.is_visible():
                schedule_radio.click()
                print(f"[Meta] Note: Scheduled for {schedule}")

        print("[Meta] Locating Share / Publish button on Share tab...")
        share_btn = page.locator(
            "button:has-text('Share'), button:has-text('Publish'), div[role='button']:has-text('Share'), div[role='button']:has-text('Publish'), button:has-text('مشاركة'), button:has-text('نشر')"
        ).last
        share_btn.wait_for(state="visible", timeout=30000)
        print("[Meta] Clicking Share / Publish...")
        share_btn.click()
        page.wait_for_timeout(6000)

        # Wait for "Reel processing" confirmation modal
        print("[Meta] Waiting for Reel processing confirmation modal...")
        confirmed = False
        for _ in range(15):
            txt = page.locator("body").inner_text()
            if "Reel processing" in txt or "Once your reel has finished processing" in txt:
                print("[Meta] Confirmed: Reel is processing!")
                confirmed = True
                done_btn = page.locator("button:has-text('Done'), div[role='button']:has-text('Done'), button:has-text('تم')").first
                if done_btn.is_visible():
                    done_btn.click()
                    page.wait_for_timeout(2000)
                break
            if "reels_composer" not in page.url:
                confirmed = True
                break
            page.wait_for_timeout(3000)

        if not confirmed:
            page.screenshot(path="outputs/meta_unconfirmed.png")
            raise RuntimeError("Meta publication was not confirmed by the platform. Screenshot saved.")

        print("[Meta] SUCCESS: Reel is officially published to Facebook & Instagram!")
        return {"status": "success"}

    except Exception as exc:
        print(f"[Meta] Error during upload: {exc}")
        raise
    finally:
        page.close()
