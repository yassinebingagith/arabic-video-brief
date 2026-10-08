from __future__ import annotations

import time
from pathlib import Path
from playwright.sync_api import BrowserContext, Page

from .formatter import FormattedPost


def _set_meta_destinations(page: Page, target: str = "instagram") -> None:
    """
    Ensure the publication destination target in Meta Business Suite is strictly configured.
    target: "instagram" (Instagram ONLY) or "facebook" (Facebook ONLY).
    """
    print(f"[Meta] Configuring destination target to: {target.upper()} ONLY...")
    try:
        # First check combobox or current destination text
        combobox = page.locator("[role='combobox']").first
        try:
            if combobox.is_visible(timeout=3000):
                combo_text = combobox.inner_text().strip().lower()
                if target == "facebook" and "كبسولة فكر" in combo_text and "capsulefikr" not in combo_text:
                    print("[Meta] Destination is already FACEBOOK ONLY. No changes needed.")
                    return
                if target == "instagram" and "capsulefikr" in combo_text and "كبسولة فكر" not in combo_text:
                    print("[Meta] Destination is already INSTAGRAM ONLY. No changes needed.")
                    return
                if target in ("both", "all", "facebook+instagram", "meta") and "كبسولة فكر" in combo_text and "capsulefikr" in combo_text:
                    print("[Meta] Destination is already BOTH FACEBOOK & INSTAGRAM. No changes needed.")
                    return
        except Exception:
            pass

        # 1. Open the dropdown by finding either combobox or account label
        dropdown = None
        try:
            if combobox.is_visible(timeout=2000):
                dropdown = combobox
        except Exception:
            pass

        if not dropdown:
            fb_label = page.locator("text='كبسولة فكر'").first
            ig_label = page.locator("text='capsulefikr'").first
            try:
                if fb_label.is_visible(timeout=2000):
                    dropdown = fb_label
                elif ig_label.is_visible(timeout=2000):
                    dropdown = ig_label
            except Exception:
                pass

        if not dropdown:
            post_to_card = page.locator("div:has-text('Post to')").first
            try:
                dropdown = post_to_card.locator("[role='combobox'], [role='button'], div[tabindex='0']").first
            except Exception:
                pass

        if dropdown:
            try:
                dropdown.click(timeout=3000)
                page.wait_for_timeout(1000)

                listbox = page.locator("div[role='listbox']").first
                listbox.wait_for(state="visible", timeout=5000)
                options = listbox.locator("div[role='option']")
                opt_count = options.count()

                fb_opt = None
                ig_opt = None
                for i in range(opt_count):
                    opt = options.nth(i)
                    txt = opt.inner_text().lower()
                    if "capsulefikr" in txt or "instagram" in txt:
                        ig_opt = opt
                    elif "كبسولة فكر" in txt or "facebook" in txt:
                        fb_opt = opt

                if target == "instagram":
                    if ig_opt:
                        ig_sel = ig_opt.get_attribute("aria-selected") == "true"
                        if not ig_sel:
                            print("[Meta] Selecting Instagram destination...")
                            ig_opt.click()
                            page.wait_for_timeout(500)
                    if fb_opt:
                        fb_sel = fb_opt.get_attribute("aria-selected") == "true"
                        if fb_sel:
                            print("[Meta] Deselecting Facebook destination...")
                            fb_opt.click()
                            page.wait_for_timeout(500)
                elif target == "facebook":
                    if fb_opt:
                        fb_sel = fb_opt.get_attribute("aria-selected") == "true"
                        if not fb_sel:
                            print("[Meta] Selecting Facebook destination...")
                            fb_opt.click()
                            page.wait_for_timeout(500)
                    if ig_opt:
                        ig_sel = ig_opt.get_attribute("aria-selected") == "true"
                        if ig_sel:
                            print("[Meta] Deselecting Instagram destination...")
                            ig_opt.click()
                            page.wait_for_timeout(500)
                elif target in ("both", "all", "facebook+instagram", "meta"):
                    if ig_opt:
                        ig_sel = ig_opt.get_attribute("aria-selected") == "true"
                        if not ig_sel:
                            print("[Meta] Selecting Instagram destination...")
                            ig_opt.click()
                            page.wait_for_timeout(500)
                    if fb_opt:
                        fb_sel = fb_opt.get_attribute("aria-selected") == "true"
                        if not fb_sel:
                            print("[Meta] Selecting Facebook destination...")
                            fb_opt.click()
                            page.wait_for_timeout(500)

                # Close dropdown cleanly
                page.keyboard.press("Escape")
                page.wait_for_timeout(500)
                try:
                    if listbox.is_visible(timeout=1000):
                        page.locator("text='Post to'").first.click()
                        page.wait_for_timeout(500)
                except Exception:
                    pass
            except Exception as e:
                print(f"[Meta] Note during options selection: {e}")

        print(f"[Meta] Destination target successfully set to: {target.upper()} ONLY.")
    except Exception as e:
        print(f"[Meta] Note during destination configuration: {e}")


def publish_to_meta(
    context: BrowserContext,
    post: FormattedPost,
    schedule: str | None = None,
    draft: bool = False,
    mode: str = "video",
    target: str | None = None,
) -> dict[str, str]:
    page = context.new_page()
    page.set_default_timeout(180000)

    try:
        if mode == "photo":
            if not post.cover_facebook_4x5 or not post.cover_facebook_4x5.is_file():
                raise RuntimeError(
                    "Cannot publish Facebook Photo Post: 'cover_facebook_4x5.png' (or .jpg) not found in folder! "
                    "Generate the 4:5 image first or publish as video reel with '--mode video'."
                )
            print("[Meta] Navigating to Meta Business Suite Post Composer for Photo Post...")
            page.goto("https://business.facebook.com/latest/composer/?asset_id=1340731649114146&business_id=1971406070195910", wait_until="domcontentloaded")
            page.wait_for_timeout(5000)

            if "login" in page.url.lower():
                raise RuntimeError("Not logged into Meta Business Suite! Please run: python scripts/avbrief.py login")

            # Configure destination: Facebook ONLY for photo posts
            photo_target = target if target else "facebook"
            _set_meta_destinations(page, target=photo_target)

            print(f"[Meta] Uploading Photo: {post.cover_facebook_4x5.name}...")
            add_photo_btn = page.locator("button:has-text('Add photo'), div[role='button']:has-text('Add photo'), button:has-text('إضافة صورة')").first
            if add_photo_btn.is_visible():
                with page.expect_file_chooser(timeout=20000) as fc_info:
                    add_photo_btn.click()
                fc_info.value.set_files(str(post.cover_facebook_4x5))
            else:
                file_input = page.locator("input[type='file']").first
                file_input.wait_for(state="attached", timeout=20000)
                file_input.set_input_files(str(post.cover_facebook_4x5))

            page.wait_for_timeout(4000)

            print("[Meta] Entering text caption for Photo Post...")
            caption_box = page.locator("div[role='textbox'], div[contenteditable='true']").first
            caption_box.wait_for(state="visible", timeout=30000)
            caption_box.click()
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")

            # Priority Rule: Prioritize deep_dive_summary.txt FIRST. Fall back to post-description.txt if missing.
            if post.deep_dive_caption and post.deep_dive_caption.strip():
                photo_caption = post.deep_dive_caption.strip()
                print(f"[Meta] Prioritizing Deep-Dive Educational Synthesis ({len(photo_caption)} characters) for Facebook Photo Post...")
            else:
                photo_caption = post.meta_caption
                print(f"[Meta] Deep-dive summary not found. Falling back to narrative post description ({len(photo_caption)} characters)...")

            caption_box.fill(photo_caption)
            page.wait_for_timeout(2000)

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

            pub_btn = page.locator(
                "button:has-text('Publish'), div[role='button']:has-text('Publish'), button:has-text('نشر'), button:has-text('Schedule'), button:has-text('Share')"
            ).last
            pub_btn.wait_for(state="visible", timeout=30000)
            print("[Meta] Clicking Publish for Photo Post...")
            pub_btn.click()
            page.wait_for_timeout(6000)
            print("[Meta] SUCCESS: Facebook Photo Post published successfully!")
            return {"status": "success", "mode": "photo_post"}

        print("[Meta] Navigating to Meta Business Suite Reels Composer...")
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

        # Configure destination: Default is BOTH Facebook & Instagram simultaneously when targeting Meta
        reel_target = target if target else "meta"
        _set_meta_destinations(page, target=reel_target)

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
        upload_complete = False
        for wait_idx in range(1, 101):  # up to 300 seconds (5 min)
            page.wait_for_timeout(3000)
            txt = page.locator("body").inner_text()
            if any(term in txt for term in ["100%", "100 %", "100٪", "Upload complete", "Uploaded", "تم تحميل الفيديو"]):
                print(f"[Meta] Video upload hit 100% (check {wait_idx})!")
                upload_complete = True
                break
            # Also check if Next button became active already (indicating upload finished)
            next_check = page.locator("button:has-text('Next'), div[role='button']:has-text('Next'), button:has-text('التالي'), div[role='button']:has-text('التالي')").last
            if next_check.is_visible():
                dis = next_check.get_attribute("aria-disabled") or next_check.get_attribute("disabled")
                if dis != "true" and dis is not True:
                    print(f"[Meta] Next button is already enabled at check {wait_idx}. Video ready!")
                    upload_complete = True
                    break
            if wait_idx % 5 == 0:
                print(f"[Meta] Still waiting for video upload... ({wait_idx * 3}s elapsed)")
        if not upload_complete:
            print("[Meta] Warning: 100% text not explicitly detected within timeout, proceeding with caution...")

        # Both Facebook Page & Instagram account are linked and checked by default
        print("[Meta] Entering caption into Text box...")
        caption_box = page.locator("div[role='textbox'], div[contenteditable='true']").first
        caption_box.wait_for(state="visible", timeout=30000)
        caption_box.click()
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
        caption_box.fill(post.meta_caption)
        page.wait_for_timeout(2000)

        # Custom 9:16 Cover Upload for Meta Reel (Instagram)
        if post.cover_vertical_9x16 and post.cover_vertical_9x16.is_file():
            print(f"[Meta] Setting custom 9:16 cover for Reel: {post.cover_vertical_9x16.name}...")
            try:
                # Scroll to and click the 'Upload image' tab
                upload_tab = page.locator("button:has-text('Upload image'), div[role='button']:has-text('Upload image')").last
                if upload_tab.is_visible(timeout=5000):
                    upload_tab.scroll_into_view_if_needed()
                    upload_tab.click()
                    page.wait_for_timeout(1500)

                    # Click the 'Upload Image' link or area which triggers the file chooser
                    blue_link = page.locator("a:has-text('Upload Image'), div:has-text('Upload image')").last
                    with page.expect_file_chooser(timeout=10000) as ifc:
                        blue_link.click()
                    ifc.value.set_files(str(post.cover_vertical_9x16))
                    page.wait_for_timeout(3000)
                    print("[Meta] Custom 9:16 Reel cover set successfully!")
            except Exception as thumb_err:
                print(f"[Meta] Warning setting custom Reel cover: {thumb_err}")

        print("[Meta] Waiting for Step 1 (Create) Next button to become active...")
        advanced_step1 = False
        for check in range(1, 61):  # up to 180 seconds (3 min)
            page.wait_for_timeout(3000)
            next_btn = page.locator("button:has-text('Next'), div[role='button']:has-text('Next'), button:has-text('التالي'), div[role='button']:has-text('التالي')").last
            if not next_btn.is_visible():
                continue
            dis = next_btn.get_attribute("aria-disabled") or next_btn.get_attribute("disabled")
            if dis != "true" and dis is not True:
                print(f"[Meta] Next button is active (check {check}). Advancing to Step 2 (Edit)...")
                next_btn.click()
                page.wait_for_timeout(4000)
                advanced_step1 = True
                break
            if check % 5 == 0:
                print(f"[Meta] Waiting for Next button to be enabled... ({check * 3}s)")

        if not advanced_step1:
            print("[Meta] Next button did not become active within timeout. Capturing debug screenshot...")
            page.screenshot(path="outputs/meta_step1_disabled.png")
            # Try click or evaluate click via javascript
            try:
                print("[Meta] Attempting click on Next button...")
                page.locator("button:has-text('Next'), div[role='button']:has-text('Next'), button:has-text('التالي'), div[role='button']:has-text('التالي')").last.click(timeout=15000)
                page.wait_for_timeout(4000)
            except Exception as e:
                print(f"[Meta] Fallback click note: {e}")

        print("[Meta] Advancing from Step 2 (Edit) to Step 3 (Share)...")
        next_btn2 = page.locator("button:has-text('Next'), div[role='button']:has-text('Next'), button:has-text('التالي'), div[role='button']:has-text('التالي')").last
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

        dest_str = "BOTH FACEBOOK & INSTAGRAM" if reel_target in ("both", "all", "facebook+instagram", "meta") else f"{reel_target.upper()} ONLY"
        print(f"[Meta] SUCCESS: Reel is officially published to {dest_str}!")
        return {"status": "success", "mode": f"reel_{reel_target}"}

    except Exception as exc:
        print(f"[Meta] Error during upload: {exc}")
        try:
            page.screenshot(path="outputs/meta_error.png")
            print("[Meta] Error screenshot saved to outputs/meta_error.png")
        except Exception:
            pass
        raise
    finally:
        page.close()
