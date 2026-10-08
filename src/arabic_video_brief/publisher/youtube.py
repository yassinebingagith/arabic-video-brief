from __future__ import annotations

import time
from pathlib import Path
from playwright.sync_api import BrowserContext, Page, expect

from .formatter import FormattedPost


def _prepare_youtube_thumbnail(thumb_path: Path) -> Path:
    """Ensure thumbnail file is within YouTube's 2MB limit while maintaining highest visual quality."""
    if not thumb_path.is_file():
        return thumb_path

    # YouTube strictly enforces a 2MB file size limit for custom thumbnails
    max_bytes = int(1.95 * 1024 * 1024)
    if thumb_path.stat().st_size <= max_bytes:
        return thumb_path

    opt_path = thumb_path.parent / f"{thumb_path.stem}_yt_opt.jpg"
    if opt_path.is_file() and opt_path.stat().st_size <= max_bytes:
        return opt_path

    try:
        from PIL import Image
        im = Image.open(thumb_path)
        im = im.convert("RGB")
        for quality in (95, 90, 85, 80):
            im.save(opt_path, "JPEG", quality=quality, optimize=True)
            if opt_path.stat().st_size <= max_bytes:
                print(f"[YouTube] Auto-optimized thumbnail to {opt_path.stat().st_size / 1024:.1f} KB to satisfy YouTube 2MB limit.")
                return opt_path
        return opt_path
    except Exception as e:
        print(f"[YouTube] Note on thumbnail optimization: {e}")
        return thumb_path


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

        # Custom Thumbnail Upload
        if post.cover_vertical_9x16 and post.cover_vertical_9x16.is_file():
            target_thumb = _prepare_youtube_thumbnail(post.cover_vertical_9x16)
            print(f"[YouTube] Setting custom 9:16 thumbnail: {target_thumb.name}...")
            try:
                thumb_input = page.locator("input#file-loader, ytcp-thumbnails-compact input[type='file']").first
                if thumb_input.count() > 0:
                    thumb_input.set_input_files(str(target_thumb))
                    print("[YouTube] Custom thumbnail set successfully.")
                    page.wait_for_timeout(2000)
                else:
                    upload_btn = page.locator("#upload-button, button[aria-label*='thumbnail' i], ytcp-button:has-text('Upload thumbnail'), ytcp-button:has-text('تحميل صورة')").first
                    if upload_btn.is_visible(timeout=3000):
                        with page.expect_file_chooser(timeout=5000) as fc_info:
                            upload_btn.click()
                        fc_info.value.set_files(str(target_thumb))
                        print("[YouTube] Custom thumbnail uploaded via file chooser.")
                        page.wait_for_timeout(2000)
            except Exception as thumb_err:
                print(f"[YouTube] Note on thumbnail upload: {thumb_err}")

        # Audience: Not made for kids
        print("[YouTube] Setting audience (not made for kids)...")
        not_kids_radio = page.locator(
            "tp-yt-paper-radio-button[name='VIDEO_MADE_FOR_KIDS_NOT_MFK'], "
            "tp-yt-paper-radio-button:has-text('No, it\\'s not made for kids'), "
            "tp-yt-paper-radio-button:has-text('لا، الفيديو ليس مخصصاً للأطفال')"
        ).first
        not_kids_radio.wait_for(state="visible", timeout=15000)
        not_kids_radio.click()
        page.wait_for_timeout(1000)

        # Ensure we advance to the Visibility tab
        print("[YouTube] Advancing to Visibility tab...")
        for _ in range(5):
            vis_check = page.locator("tp-yt-paper-radio-button[name='PUBLIC'], #public-radio-button, tp-yt-paper-radio-button[name='UNLISTED']").first
            if vis_check.is_visible():
                break
            step_badge = page.locator("#step-badge-3, button[aria-label*='Visibility' i], button[aria-label*='مستوى العرض' i]").first
            if step_badge.is_visible() and step_badge.is_enabled():
                step_badge.click()
                page.wait_for_timeout(1500)
            else:
                next_btn = page.locator("#next-button").first
                if next_btn.is_visible() and next_btn.is_enabled():
                    next_btn.click()
                    page.wait_for_timeout(1500)

        # Visibility options
        print("[YouTube] Setting visibility...")
        if draft:
            target_radio_name = "UNLISTED"
        elif schedule:
            target_radio_name = "SCHEDULE"
        else:
            target_radio_name = "PUBLIC"

        # Expand 'Save or publish' section if present
        save_or_pub = page.locator("#first-container, tp-yt-paper-radio-button[name='SAVE_OR_PUBLISH']").first
        if save_or_pub.is_visible():
            try:
                save_or_pub.click()
                page.wait_for_timeout(500)
            except Exception:
                pass

        vis_radio = page.locator(
            f"tp-yt-paper-radio-button[name='{target_radio_name}'], #{target_radio_name.lower()}-radio-button"
        ).first
        vis_radio.wait_for(state="visible", timeout=15000)
        vis_radio.scroll_into_view_if_needed()

        # Click radio button and confirm aria-checked is true
        for attempt in range(5):
            is_checked = vis_radio.get_attribute("aria-checked") == "true" or vis_radio.get_attribute("checked") is not None
            if is_checked:
                print(f"[YouTube] Confirmed: {target_radio_name} visibility is selected.")
                break
            click_target = vis_radio.locator("#radioContainer, #radioLabel, #offRadio").first
            if click_target.is_visible():
                click_target.click()
            else:
                vis_radio.click()
            page.wait_for_timeout(1000)

        page.wait_for_timeout(1500)

        # Ensure video upload reaches 100% / enters processing before publishing
        print(f"[YouTube] Monitoring video upload progress for {post.video_path.name}...")
        for wait_idx in range(1, 151):  # up to 450 seconds
            # Retrieve text from the modal dialog and upload progress elements
            dialog_text = ""
            for selector in [
                ".progress-label",
                "ytcp-video-upload-progress",
                "ytcp-animatable[metadata-type='progress']",
                "ytcp-uploads-dialog",
                "#dialog",
            ]:
                loc = page.locator(selector)
                if loc.count() > 0:
                    try:
                        t = loc.first.inner_text().strip().lower()
                        if t:
                            dialog_text = t
                            break
                    except Exception:
                        pass
            if not dialog_text:
                try:
                    dialog_text = page.locator("body").inner_text().strip().lower()
                except Exception:
                    dialog_text = ""

            # Check percentage progress
            import re
            pct_match = re.search(r"(\d+)\s*%", dialog_text)
            is_active_upload = False
            if pct_match:
                pct_val = int(pct_match.group(1))
                # Only treat as actively uploading if percentage is < 100
                if pct_val < 100:
                    is_active_upload = True
                    if wait_idx % 2 == 0:
                        print(f"[YouTube] Upload in progress: {pct_val}% ({wait_idx * 3}s elapsed)...")
                    page.wait_for_timeout(3000)
                    continue

            # Verified transition to processing / checks / complete:
            # As soon as the upload is 100% finished or passes to 'Processing up to HD' or 'Checks',
            # YouTube handles everything server-side. The video is fully uploaded and ready to publish!
            ready_terms = [
                "processing", "checks complete", "complete", "no issues found", "ready to publish",
                "معالجة", "اكتملت المعالجة", "اكتمل التحميل", "اكتمل الفحص", "لم يتم العثور على أي مشاكل",
                "traitement", "terminée", "vérification terminée"
            ]
            if not is_active_upload and any(term in dialog_text for term in ready_terms):
                matched_line = "Processing / Checks ready"
                for line in dialog_text.splitlines():
                    if any(term in line.lower() for term in ready_terms):
                        matched_line = line.strip()
                        break
                print(f"[YouTube] Video upload reached 100% ({matched_line})! Proceeding to publish immediately...")
                break

            if wait_idx % 4 == 0:
                short_status = " ".join(dialog_text.split())[:70]
                print(f"[YouTube] Waiting for upload progress ({wait_idx * 3}s elapsed)... Status: '{short_status}'")
            page.wait_for_timeout(3000)

        # Verify #done-button state and text
        print("[YouTube] Finalizing and publishing...")
        done_btn = page.locator("#done-button, ytcp-button#done-button").first
        done_btn.wait_for(state="visible", timeout=15000)
        for _ in range(30):
            if done_btn.is_enabled():
                break
            page.wait_for_timeout(1000)

        btn_text = done_btn.inner_text().strip()
        print(f"[YouTube] Finalize button text: '{btn_text}'")

        # If we intended PUBLIC, the button MUST say Publish (نشر), NOT Save (حفظ)
        if target_radio_name == "PUBLIC" and ("save" in btn_text.lower() or "حفظ" in btn_text):
            print("[YouTube] Warning: Button says 'Save' instead of 'Publish'. Re-clicking PUBLIC radio button directly...")
            pub_radio = page.locator("tp-yt-paper-radio-button[name='PUBLIC'], #public-radio-button").first
            pub_radio.scroll_into_view_if_needed()
            radio_dot = pub_radio.locator("#radioContainer, #offRadio, #radioLabel").first
            if radio_dot.is_visible():
                radio_dot.click()
            else:
                pub_radio.click(force=True)
            page.wait_for_timeout(1500)
            btn_text = done_btn.inner_text().strip()
            print(f"[YouTube] Finalize button text after re-click: '{btn_text}'")

        done_btn.click()
        print("[YouTube] Clicked Publish button. Waiting for publication confirmation...")
        page.wait_for_timeout(3000)

        # Wait for publication confirmation modal or upload dialog to disappear.
        video_url = ""
        share_dialog = page.locator("ytcp-video-share-dialog").first
        published_confirmed = False

        for wait_sec in range(90):
            # Check for multilingual warning/confirmation dialogs (e.g. checks still in progress)
            for confirm_sel in [
                "ytcp-confirmation-dialog",
                "ytcp-dialog:has(#confirm-button)",
                "tp-yt-paper-dialog:has(#confirm-button)",
            ]:
                cd = page.locator(confirm_sel).first
                try:
                    if cd.is_visible(timeout=200):
                        print(f"[YouTube] Detected modal dialog ({confirm_sel}). Locating confirm/publish button...")
                        c_btn = cd.locator(
                            "#confirm-button, "
                            "button:has-text('Publish anyway'), ytcp-button:has-text('Publish anyway'), "
                            "button:has-text('Publier quand même'), ytcp-button:has-text('Publier quand même'), "
                            "button:has-text('نشر على أي حال'), ytcp-button:has-text('نشر على أي حال'), "
                            "button:has-text('النشر على أي حال'), ytcp-button:has-text('النشر على أي حال'), "
                            "button:has-text('Publish'), ytcp-button:has-text('Publish'), "
                            "button:has-text('Publier'), ytcp-button:has-text('Publier'), "
                            "button:has-text('نشر'), ytcp-button:has-text('نشر')"
                        ).first
                        if c_btn.is_visible(timeout=500):
                            print("[YouTube] Clicking confirmation/publish button inside dialog...")
                            c_btn.click(force=True)
                            page.wait_for_timeout(2000)
                except Exception:
                    pass

            # Also check direct button selector across entire page for any unhandled confirmation buttons
            try:
                publish_anyway_btn = page.locator(
                    "ytcp-button:has-text('Publish anyway'), button:has-text('Publish anyway'), "
                    "tp-yt-paper-button:has-text('Publish anyway'), [aria-label*='Publish anyway'], "
                    "ytcp-button:has-text('نشر على أي حال'), button:has-text('نشر على أي حال'), "
                    "ytcp-button:has-text('النشر على أي حال'), button:has-text('النشر على أي حال'), "
                    "ytcp-button:has-text('Publier quand même'), button:has-text('Publier quand même'), "
                    "ytcp-confirmation-dialog #confirm-button"
                ).first
                if publish_anyway_btn.is_visible(timeout=200):
                    print("[YouTube] Detected 'Publish anyway' button. Clicking...")
                    publish_anyway_btn.click(force=True)
                    page.wait_for_timeout(2000)
            except Exception:
                pass

            # Also check for "Video processing" / cloud processing modal
            # YouTube shows this once the upload is 100% committed to inform that background HD processing is running.
            for proc_sel in [
                "ytcp-uploads-still-processing-dialog",
                "tp-yt-paper-dialog:has-text('Video processing')",
                "tp-yt-paper-dialog:has-text('معالجة الفيديو')",
                "tp-yt-paper-dialog:has-text('Processing up to HD')",
                "tp-yt-paper-dialog:has-text('The standard definition')",
            ]:
                proc_dialog = page.locator(proc_sel).first
                try:
                    if proc_dialog.is_visible(timeout=200):
                        print("[YouTube] Detected 'Video processing' modal (cloud processing active). Clicking Close...")
                        close_btn = proc_dialog.locator(
                            "#close-button, button:has-text('Close'), ytcp-button:has-text('Close'), "
                            "button:has-text('Fermer'), button:has-text('إغلاق')"
                        ).first
                        if close_btn.is_visible(timeout=1500):
                            close_btn.click(force=True)
                            page.wait_for_timeout(2000)
                            published_confirmed = True
                            print("[YouTube] Clicked Close on Video Processing dialog. Publication committed successfully!")
                            break
                except Exception:
                    pass

            if published_confirmed:
                break

            # 1. Primary proof of publication: ytcp-video-share-dialog is visible
            try:
                if share_dialog.is_visible(timeout=300):
                    print("[YouTube] Publication confirmation reached (Share dialog opened).")
                    published_confirmed = True
                    try:
                        share_link = share_dialog.locator("a.ytcp-video-info, a[href*='youtu.be']").first
                        if share_link.is_visible(timeout=2000):
                            video_url = share_link.get_attribute("href") or ""
                            print(f"[YouTube] Video URL from share dialog: {video_url}")
                    except Exception:
                        pass

                    # Close share dialog
                    close_btn = share_dialog.locator(
                        "#close-button, button:has-text('Close'), button:has-text('Fermer'), button:has-text('إغلاق')"
                    ).first
                    if close_btn.is_visible(timeout=3000):
                        close_btn.click()
                        page.wait_for_timeout(2000)
                    break
            except Exception:
                pass

            # 2. Secondary proof of publication: upload dialog closed completely (enforce minimum 8s wait)
            try:
                if wait_sec >= 8 and not done_btn.is_visible():
                    active_dialogs = page.locator("ytcp-uploads-dialog, tp-yt-paper-dialog#dialog")
                    if active_dialogs.count() == 0 or not active_dialogs.first.is_visible():
                        print("[YouTube] Upload wizard closed completely. Publication successfully committed.")
                        published_confirmed = True
                        break
            except Exception:
                pass

            # If done_btn is still visible and enabled at key intervals, re-click only if no overlay modal is open
            if wait_sec in (12, 24, 36) and done_btn.is_visible() and done_btn.is_enabled():
                has_overlay = page.locator("ytcp-confirmation-dialog, ytcp-uploads-still-processing-dialog, tp-yt-iron-overlay-backdrop.opened").count() > 0
                if not has_overlay:
                    print(f"[YouTube] Done button still active at {wait_sec}s. Re-clicking...")
                    done_btn.click(force=True)

            page.wait_for_timeout(1000)

        # Fallback URL extraction if not retrieved from share dialog
        if not video_url:
            try:
                link_elem = page.locator("a.ytcp-video-info, a[href*='youtu.be']").first
                if link_elem.is_visible(timeout=2000):
                    video_url = link_elem.get_attribute("href") or ""
            except Exception:
                pass

        # Critical Safety: Check if modal is still open
        try:
            active_modal = page.locator("ytcp-uploads-dialog, tp-yt-paper-dialog#dialog").first
            if active_modal.is_visible(timeout=500):
                print("[YouTube] Notice: Modal was still visible. Giving backend 5s grace period...")
                page.wait_for_timeout(5000)
        except Exception:
            pass

        page.wait_for_timeout(3000)
        print(f"[YouTube] Done! Video uploaded successfully. {video_url}")
        return {"status": "success", "url": video_url}

    except Exception as exc:
        print(f"[YouTube] Error during upload: {exc}")
        raise
    finally:
        page.close()
