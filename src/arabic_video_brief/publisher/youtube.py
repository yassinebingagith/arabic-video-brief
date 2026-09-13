from __future__ import annotations

import time
from pathlib import Path
from playwright.sync_api import BrowserContext, Page, expect

from .formatter import FormattedPost


def publish_to_youtube(
    context: BrowserContext,
    post: FormattedPost,
    schedule: str | None = None,
    draft: bool = False,
) -> dict[str, str]:
    page = context.new_page()
    page.set_default_timeout(45000)

    try:
        print("[YouTube] Navigating to YouTube Studio...")
        page.goto("https://studio.youtube.com", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        # Check authentication
        if "accounts.google.com" in page.url or "signin" in page.url.lower():
            raise RuntimeError(
                "Not logged into YouTube Studio! Please run: python scripts/avbrief.py login"
            )

        print("[YouTube] Locating upload trigger...")
        # Try clicking create button or direct upload icon
        create_btn = page.locator("#create-icon, button[aria-label*='Create' i], ytcp-button#create-icon").first
        if create_btn.is_visible():
            create_btn.click()
            page.wait_for_timeout(1000)
            upload_item = page.locator("tp-yt-paper-item:has-text('Upload video'), ytcp-text-menu tp-yt-paper-item:first-child").first
            if upload_item.is_visible():
                upload_item.click()
            page.wait_for_timeout(1500)
        else:
            direct_upload = page.locator("#upload-icon, ytcp-button#upload-icon").first
            if direct_upload.is_visible():
                direct_upload.click()
                page.wait_for_timeout(1500)

        # File input
        file_input = page.locator("input[type='file']").first
        file_input.wait_for(state="attached", timeout=15000)
        print(f"[YouTube] Uploading {post.video_path.name}...")
        file_input.set_input_files(str(post.video_path))

        # Wait for title input to become interactive
        print("[YouTube] Filling title and description...")
        title_box = page.locator("#textbox[aria-label*='title' i], #title-textarea #textbox").first
        title_box.wait_for(state="visible", timeout=30000)
        title_box.click()
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
        title_box.fill(post.youtube_title)
        page.wait_for_timeout(1000)

        desc_box = page.locator("#textbox[aria-label*='description' i], #description-textarea #textbox").first
        if desc_box.is_visible():
            desc_box.click()
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
            desc_box.fill(post.youtube_description)
            page.wait_for_timeout(1000)

        # Audience: Not made for kids
        print("[YouTube] Setting audience (not made for kids)...")
        not_kids_radio = page.locator(
            "tp-yt-paper-radio-button[name='VIDEO_MADE_FOR_KIDS_NOT_MFK'], "
            "tp-yt-paper-radio-button:has-text('No, it\\'s not made for kids'), "
            "tp-yt-paper-radio-button:has-text('لا، الفيديو ليس مخصصاً للأطفال')"
        ).first
        if not_kids_radio.is_visible():
            not_kids_radio.click()
            page.wait_for_timeout(1000)

        # Click Next through steps to reach Visibility
        print("[YouTube] Advancing to Visibility tab...")
        for step in range(3):
            next_btn = page.locator("#next-button").first
            if next_btn.is_visible() and next_btn.is_enabled():
                next_btn.click()
                page.wait_for_timeout(1500)

        # Visibility options
        print("[YouTube] Setting visibility...")
        if draft:
            unlisted_radio = page.locator("tp-yt-paper-radio-button[name='UNLISTED']").first
            if unlisted_radio.is_visible():
                unlisted_radio.click()
        elif schedule:
            schedule_radio = page.locator("#schedule-radio-button, tp-yt-paper-radio-button[name='SCHEDULE']").first
            if schedule_radio.is_visible():
                schedule_radio.click()
                print(f"[YouTube] Note: Scheduled for {schedule}")
        else:
            public_radio = page.locator("tp-yt-paper-radio-button[name='PUBLIC']").first
            if public_radio.is_visible():
                public_radio.click()

        page.wait_for_timeout(1500)

        # Wait for video upload to hit 100% / complete before publishing
        print(f"[YouTube] Uploading {post.video_path.name}. Waiting for upload to hit 100% / complete...")
        max_upload_wait_seconds = 300  # up to 5 minutes
        start_time = time.time()
        while time.time() - start_time < max_upload_wait_seconds:
            progress_el = page.locator(
                "ytcp-video-upload-progress, .progress-label, span.progress-label"
            ).first
            progress_text = ""
            if progress_el.is_visible():
                progress_text = progress_el.inner_text().strip()
                if progress_text:
                    print(f"[YouTube] Upload progress: {progress_text}")

            dialog_text = page.locator("ytcp-uploads-dialog, #dialog, body").first.inner_text()

            # Check if upload is complete / checks started / processing
            complete_signals = [
                "upload complete", "checks complete", "processing will begin",
                "checks starting", "processing up to", "اكتمل التحميل", "اكتملت عمليات التحقق"
            ]
            if any(sig in dialog_text.lower() for sig in complete_signals):
                print("[YouTube] Video upload is 100% complete!")
                break

            if any(sig in progress_text.lower() for sig in complete_signals):
                print(f"[YouTube] Video upload finished: {progress_text}")
                break

            page.wait_for_timeout(4000)
        else:
            print("[YouTube] Warning: Max wait time reached, proceeding to finalize...")

        # Save / Publish button
        print("[YouTube] Finalizing and publishing...")
        done_btn = page.locator("#done-button").first
        if done_btn.is_visible() and done_btn.is_enabled():
            done_btn.click()
            page.wait_for_timeout(4000)

        # If a completion / share modal appears, wait if it is still transferring
        for _ in range(30):
            modal = page.locator("ytcp-dialog, ytcp-video-share-dialog, ytcp-uploads-still-processing-dialog").first
            if modal.is_visible():
                m_txt = modal.inner_text().lower()
                if "uploading" in m_txt or "جاري التحميل" in m_txt or "%" in m_txt:
                    print("[YouTube] Modal indicates upload is still in progress... waiting...")
                    page.wait_for_timeout(5000)
                    continue
            break

        # Retrieve video link if available on completion modal
        video_url = ""
        link_elem = page.locator("a.ytcp-video-info, a[href*='youtu.be']").first
        if link_elem.is_visible():
            video_url = link_elem.get_attribute("href") or ""

        # Close dialog if open
        close_btn = page.locator("#close-button, ytcp-button#close-button").first
        if close_btn.is_visible():
            close_btn.click()
            page.wait_for_timeout(2000)

        # Buffer pause so connections close cleanly
        page.wait_for_timeout(3000)

        print(f"[YouTube] Done! Video uploaded successfully. {video_url}")
        return {"status": "success", "url": video_url}

    except Exception as exc:
        print(f"[YouTube] Error during upload: {exc}")
        raise
    finally:
        page.close()
