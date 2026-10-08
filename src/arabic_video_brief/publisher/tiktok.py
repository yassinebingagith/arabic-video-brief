from __future__ import annotations

import time
from pathlib import Path
from playwright.sync_api import BrowserContext

from .formatter import FormattedPost


def publish_to_tiktok(
    context: BrowserContext,
    post: FormattedPost,
    schedule: str | None = None,
    draft: bool = False,
) -> dict[str, str]:
    page = context.new_page()
    page.set_default_timeout(120000)

    try:
        print("[TikTok] Navigating to TikTok Studio Upload...")
        page.goto("https://www.tiktok.com/tiktokstudio/upload", wait_until="domcontentloaded")
        page.wait_for_timeout(5000)

        # Dismiss any exit confirmation modal if present from previous attempt
        cancel_btn = page.locator("button:has-text('Cancel'), button:has-text('إلغاء')").first
        if cancel_btn.is_visible():
            cancel_btn.click()
            page.wait_for_timeout(1000)

        # Dismiss onboarding tour overlays
        try:
            page.evaluate("""() => {
                const portal = document.getElementById('react-joyride-portal');
                if (portal) portal.remove();
                const overlays = document.querySelectorAll('.react-joyride__overlay, .react-joyride__spotlight');
                overlays.forEach(el => el.remove());
            }""")
        except Exception:
            pass

        print("[TikTok] Uploading video file...")
        file_input = page.locator("input[type='file']").first
        if file_input.count() == 0:
            for frame in page.frames:
                frame_input = frame.locator("input[type='file']").first
                if frame_input.count() > 0:
                    file_input = frame_input
                    break

        file_input.wait_for(state="attached", timeout=20000)
        file_input.set_input_files(str(post.video_path))
        print(f"[TikTok] Uploading {post.video_path.name}. Waiting for upload to hit 100%...")

        # Wait for video upload to hit 100% (takes 30-50s for 40MB)
        for _ in range(30):
            page.wait_for_timeout(4000)
            txt = page.locator("body").inner_text()
            if "Uploaded" in txt or "100%" in txt:
                print("[TikTok] Upload reached 100%!")
                break
        else:
            print("[TikTok] Upload wait finished, proceeding with form...")

        print("[TikTok] Entering caption...")
        caption_box = page.locator("div[contenteditable='true'], div[data-placeholder*='caption' i]").first
        if not caption_box.is_visible():
            for frame in page.frames:
                frame_box = frame.locator("div[contenteditable='true']").first
                if frame_box.is_visible():
                    caption_box = frame_box
                    break

        caption_box.wait_for(state="visible", timeout=30000)
        caption_box.click(force=True)
        page.wait_for_timeout(500)

        # TikTok auto-populates the caption with the video filename stem (e.g. 'brief').
        # Clear it using native keyboard events to ensure Draft.js / React editor state resets completely.
        page.keyboard.press("Control+A")
        page.wait_for_timeout(200)
        page.keyboard.press("Backspace")
        page.wait_for_timeout(300)
        page.keyboard.press("Delete")
        page.wait_for_timeout(300)

        # Additional execCommand wipe to guarantee no residual DOM text or editor nodes remain
        page.evaluate("""() => {
            const el = document.querySelector("div[contenteditable='true'], div[data-placeholder*='caption' i]");
            if (el) {
                el.focus();
                document.execCommand('selectAll', false, null);
                document.execCommand('delete', false, null);
            }
        }""")
        page.wait_for_timeout(500)

        # Verification check: if any residual text like 'brief' persists, clear once more
        current_txt = caption_box.inner_text().strip()
        if current_txt:
            caption_box.click(force=True)
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
            page.wait_for_timeout(300)

        caption_box.fill(post.tiktok_caption)
        page.wait_for_timeout(2000)

        # Unfocus caption cleanly without pressing Escape
        page.locator("h2, .title, body").first.click(position={"x": 10, "y": 10})
        page.wait_for_timeout(1000)

        # Custom Cover Upload (if cover_vertical_9x16 is present)
        if post.cover_vertical_9x16 and post.cover_vertical_9x16.is_file():
            print(f"[TikTok] Setting custom 9:16 cover: {post.cover_vertical_9x16.name}...")
            try:
                # 1. Look for 'Edit cover' button or clickable cover preview
                edit_cover_btn = page.locator(
                    "button:has-text('Edit cover'), button:has-text('تعديل الغلاف'), "
                    "[data-e2e='edit-cover-btn'], .cover-image, .cover-container, "
                    "div[class*='cover'] button, div[class*='cover-edit']"
                ).first

                if not edit_cover_btn.is_visible():
                    edit_cover_btn = page.locator(".tiktok-cover, [class*='cover-preview'], [class*='coverContainer']").first

                if edit_cover_btn.is_visible():
                    edit_cover_btn.scroll_into_view_if_needed()
                    edit_cover_btn.click()
                    page.wait_for_timeout(2000)

                    # 2. Check for 'Upload cover' / 'Upload photo' tab in modal
                    upload_tab = page.locator(
                        "div:has-text('Upload cover'), button:has-text('Upload cover'), "
                        "div:has-text('Upload photo'), button:has-text('Upload photo'), "
                        "div:has-text('تحميل غلاف'), button:has-text('تحميل غلاف'), "
                        "div:has-text('تحميل صورة'), button:has-text('تحميل صورة'), "
                        "[class*='tab']:has-text('Upload'), [class*='tab']:has-text('تحميل')"
                    ).first
                    if upload_tab.is_visible():
                        upload_tab.click()
                        page.wait_for_timeout(1000)

                    # 3. Locate file input for image upload
                    cover_input = page.locator(
                        "input[type='file'][accept*='image'], div[role='dialog'] input[type='file'], .modal input[type='file']"
                    ).first

                    if cover_input.count() > 0:
                        cover_input.set_input_files(str(post.cover_vertical_9x16))
                        print("[TikTok] Custom cover image uploaded successfully!")
                        page.wait_for_timeout(2500)
                    else:
                        upload_area = page.locator(
                            "div[role='dialog'] [class*='upload'], div[role='dialog'] button:has-text('Upload'), "
                            "div[role='dialog'] div:has-text('Upload')"
                        ).first
                        if upload_area.is_visible():
                            try:
                                with page.expect_file_chooser(timeout=3000) as fc_info:
                                    upload_area.click()
                                fc_info.value.set_files(str(post.cover_vertical_9x16))
                                print("[TikTok] Custom cover image uploaded via file chooser!")
                                page.wait_for_timeout(2500)
                            except Exception:
                                print("[TikTok] Note: Cover file chooser not triggered.")

                    # 4. Click Save/Confirm/Done strictly inside the cover modal
                    cover_dialog = page.locator("div[role='dialog'], [class*='modal']").first
                    confirm_btn = cover_dialog.locator(
                        "button:has-text('Save'), button:has-text('Confirm'), button:has-text('Done'), "
                        "button:has-text('حفظ'), button:has-text('تأكيد'), button:has-text('تم')"
                    ).first
                    if confirm_btn.is_visible():
                        confirm_btn.click()
                        page.wait_for_timeout(2000)
                        print("[TikTok] Cover modal saved and closed.")
                    else:
                        close_btn = cover_dialog.locator("button[aria-label*='close' i], .modal-close, button:has-text('Cancel')").first
                        if close_btn.is_visible():
                            close_btn.click()

                    try:
                        cover_dialog.wait_for(state="hidden", timeout=5000)
                    except Exception:
                        pass
                else:
                    print("[TikTok] Note: 'Edit cover' button not found on upload page.")
            except Exception as cover_err:
                print(f"[TikTok] Note on cover setting: {cover_err}")

        # Ensure no accidental exit modal blocks the page
        exit_dialog_cancel = page.locator("div[role='dialog']:has-text('exit') button:has-text('Cancel'), div[role='dialog']:has-text('خروج') button:has-text('إلغاء')").first
        if exit_dialog_cancel.is_visible():
            exit_dialog_cancel.click()
            page.wait_for_timeout(1000)

        if draft:
            print("[TikTok] Saving as Draft...")
            save_draft = page.get_by_role("button", name="Save draft", exact=True)
            if not save_draft.is_visible():
                save_draft = page.locator("button:has-text('Save draft'), button:has-text('حفظ كمسودة')").first
            save_draft.scroll_into_view_if_needed()
            save_draft.click()
            page.wait_for_timeout(5000)
            return {"status": "success", "mode": "draft"}

        print("[TikTok] Locating Post button...")
        post_btn = page.get_by_role("button", name="Post", exact=True)
        if not post_btn.is_visible():
            post_btn = page.get_by_role("button", name="نشر", exact=True)
        if not post_btn.is_visible():
            post_btn = page.locator("button.Button__root:has-text('Post'):not([disabled]), button:has-text('Post'):not([disabled])").first

        post_btn.scroll_into_view_if_needed()
        page.wait_for_timeout(1000)
        print("[TikTok] Clicking Post...")
        post_btn.click()
        page.wait_for_timeout(3000)

        # Wait for success confirmation (redirection to /content or published modal)
        print("[TikTok] Waiting for publication confirmation...")
        confirmed = False
        for i in range(30):  # up to 90 seconds
            page.wait_for_timeout(3000)

            # CRITICAL: Handle secondary "Continue to post?" / "Post now" confirmation modal if it appears
            modal_post_btn = page.locator(
                "div[role='dialog'] button:has-text('Post now'), "
                "button:has-text('Post now'), "
                "button:has-text('نشر الآن'), "
                "button:has-text('Post anyway'), "
                "button:has-text('Proceed'), "
                "div[role='dialog'] button:has-text('Post'), "
                "div[role='dialog'] button:has-text('نشر'), "
                ".Button__root:has-text('Post now'), "
                "div[class*='modal'] button:has-text('Post')"
            ).first

            if modal_post_btn.is_visible():
                print(f"[TikTok] Detected 'Continue to post?' dialog at check {i+1}. Clicking 'Post now'...")
                try:
                    modal_post_btn.click(force=True)
                    page.wait_for_timeout(3000)
                except Exception as m_err:
                    print(f"[TikTok] Note on modal click: {m_err}")

            if "content" in page.url:
                confirmed = True
                break
            txt = page.locator("body").inner_text()
            if "Manage your posts" in txt or "Your video has been published" in txt or "uploaded successfully" in txt.lower():
                confirmed = True
                break

        if not confirmed:
            page.screenshot(path="outputs/tt_unconfirmed.png")
            raise RuntimeError("TikTok post submission was not confirmed by the platform. Screenshot saved.")

        print("[TikTok] SUCCESS: Video is officially published to TikTok!")
        return {"status": "success"}

    except Exception as exc:
        print(f"[TikTok] Error during upload: {exc}")
        raise
    finally:
        page.close()
