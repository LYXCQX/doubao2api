"""Automated slider captcha solver with humanized mouse trajectory simulation.

Designed for ByteDance SecSDK slider captchas on Doubao web runtime.
Supports:
1. Captcha DOM & iframe detection.
2. Gap distance calculation via edge/shadow/template matching.
3. Humanized non-linear mouse trajectory generation (acceleration, deceleration,
   overshoot, micro-jitter, non-uniform delays).
4. Playwright mouse execution and post-solve verification.
"""

from __future__ import annotations

import asyncio
import io
import logging
import math
import random
from typing import Any, List, Optional, Tuple

log = logging.getLogger("doubao2api.captcha_solver")


def generate_human_trajectory(
    start_x: float,
    start_y: float,
    distance: float,
    total_time: Optional[float] = None,
) -> List[Tuple[float, float, float]]:
    """Generate a realistic human-like mouse movement trajectory.

    Features:
    - Phase 1 (Acceleration): Rapid acceleration covering ~70-80% of distance.
    - Phase 2 (Deceleration): Gradual slowing down as approaching the target.
    - Phase 3 (Overshoot & Backtrack): Slight overshoot (+2~5px) and fine adjustment.
    - Y-axis micro-jitter (natural hand tremor +-1~2px).
    - Variable non-uniform time intervals between frames.

    Returns:
        List of (x, y, delay_seconds) tuples.
    """
    if total_time is None:
        # Human slider drag typically takes 0.6s to 1.2s depending on distance
        total_time = random.uniform(0.65, 1.15)

    steps: List[Tuple[float, float, float]] = []

    # Decide overshoot amount (1.5px to 4.5px)
    overshoot = random.uniform(1.5, 4.5) if distance > 40 else 0.0
    effective_distance = distance + overshoot

    # Number of movement sample points (30 - 55 steps)
    num_steps = random.randint(32, 52)
    step_duration = total_time / num_steps

    curr_x = start_x
    curr_y = start_y
    accum_dist = 0.0

    # Phase 1 & 2: Movement to overshoot point
    for i in range(1, num_steps + 1):
        t = i / num_steps  # Progress 0.0 -> 1.0

        # Non-linear easing: easeOutQuart or cubic bezier-like
        # Rapid start, gentle stop: 1 - (1 - t)^3
        progress = 1.0 - math.pow(1.0 - t, 3.2)
        target_dist = effective_distance * progress
        dx = target_dist - accum_dist
        accum_dist = target_dist

        curr_x += dx

        # Y-axis random hand tremor (sinusoidal + noise)
        y_noise = random.uniform(-0.8, 0.8) + 0.5 * math.sin(t * math.pi * 3)
        actual_y = curr_y + y_noise

        # Non-uniform delay between frames (10ms - 30ms)
        delay = step_duration * random.uniform(0.7, 1.3)
        steps.append((round(curr_x, 2), round(actual_y, 2), round(delay, 4)))

    # Phase 3: Overshoot correction (re-centering to exact target)
    if overshoot > 0:
        back_steps = random.randint(4, 7)
        for j in range(1, back_steps + 1):
            bt = j / back_steps
            dx = -(overshoot / back_steps) * (1.0 + random.uniform(-0.2, 0.2))
            curr_x += dx
            actual_y = curr_y + random.uniform(-0.5, 0.5)
            delay = random.uniform(0.02, 0.045)
            steps.append((round(curr_x, 2), round(actual_y, 2), round(delay, 4)))

    return steps


def calculate_gap_offset(
    bg_bytes: bytes,
    piece_bytes: Optional[bytes] = None,
) -> Optional[int]:
    """Calculate the horizontal gap offset in the slider background image.

    Uses PIL / edge-difference analysis to locate the cutout notch.
    """
    try:
        from PIL import Image, ImageFilter
    except ImportError:
        log.warning("Pillow not installed; unable to perform image-based gap analysis")
        return None

    try:
        bg_img = Image.open(io.BytesIO(bg_bytes)).convert("L")
        width, height = bg_img.size

        if width < 50 or height < 30:
            return None

        # Apply edge enhancement
        edges = bg_img.filter(ImageFilter.FIND_EDGES)
        edge_data = edges.load()

        # Search for high edge-density vertical band in the valid range [40, width - 40]
        # Most ByteDance sliders have the gap between 15% and 85% of the width
        min_x = int(width * 0.15)
        max_x = int(width * 0.88)

        col_scores = []
        for x in range(min_x, max_x):
            score = 0
            # Sample middle 60% of height where the slider puzzle resides
            for y in range(int(height * 0.2), int(height * 0.8)):
                score += edge_data[x, y]
            col_scores.append((score, x))

        if not col_scores:
            return None

        # Find column with peak edge transition
        col_scores.sort(key=lambda s: s[0], reverse=True)
        best_x = col_scores[0][1]

        log.info("Calculated slider gap offset: x=%d (img width=%d)", best_x, width)
        return best_x
    except Exception as e:
        log.warning("Failed to calculate gap offset from image: %s", e)
        return None


class SliderCaptchaSolver:
    """Automated solver for ByteDance SecSDK slider captchas."""

    def __init__(self):
        self.max_attempts = 2

    async def detect_and_solve(self, page: Any, timeout: float = 8.0) -> bool:
        """Detect if a slider captcha is visible and attempt humanized auto-solve.

        Args:
            page: Playwright Page instance.
            timeout: Maximum time to spend on solving.

        Returns:
            True if captcha was successfully solved and dismissed, False otherwise.
        """
        if not page:
            return False

        try:
            # 1. Search for captcha in main page or any child iframe
            target_context = None
            container = None

            # Check iframes first (SecSDK often embeds in verify iframe)
            for frame in page.frames:
                try:
                    for sel in [
                        '#captcha_container',
                        '.captcha_verify_container',
                        '.secsdk-captcha-wrapper',
                        '[class*="captcha-modal"]',
                        '[class*="captcha_verify"]',
                    ]:
                        loc = frame.locator(sel)
                        if await loc.count() > 0 and await loc.first.is_visible():
                            target_context = frame
                            container = loc.first
                            break
                except Exception:
                    continue
                if target_context:
                    break

            # Fallback to main page context
            if not target_context:
                for sel in [
                    '#captcha_container',
                    '.captcha_verify_container',
                    '.secsdk-captcha-wrapper',
                    '[class*="captcha-modal"]',
                    '[class*="captcha_verify"]',
                ]:
                    loc = page.locator(sel)
                    if await loc.count() > 0 and await loc.first.is_visible():
                        target_context = page
                        container = loc.first
                        break

            if not target_context or not container:
                log.debug("No visible slider captcha container found")
                return False

            log.info("Slider captcha detected. Attempting automated solve...")

            # 2. Locate drag handle
            handle = None
            for handle_sel in [
                '.secsdk-captcha-drag-icon',
                '.captcha_drag_icon',
                '.sec-captcha-drag-icon',
                '[class*="drag-icon"]',
                '[class*="drag_button"]',
                '[class*="secsdk-captcha-drag"]',
            ]:
                loc = target_context.locator(handle_sel)
                if await loc.count() > 0 and await loc.first.is_visible():
                    handle = loc.first
                    break

            if not handle:
                log.warning("Captcha container found but drag handle element not found")
                return False

            handle_box = await handle.bounding_box()
            if not handle_box:
                log.warning("Could not get bounding box of captcha drag handle")
                return False

            # 3. Locate background image to calculate distance
            bg_elem = None
            for bg_sel in [
                '#captcha-verify-image',
                '.captcha_verify_img_slide',
                'img[src*="captcha"]',
                'img[src*="verify"]',
                'canvas[class*="captcha"]',
            ]:
                loc = target_context.locator(bg_sel)
                if await loc.count() > 0 and await loc.first.is_visible():
                    bg_elem = loc.first
                    break

            distance = None
            if bg_elem:
                bg_box = await bg_elem.bounding_box()
                try:
                    # Attempt screenshot of background element for edge analysis
                    bg_bytes = await bg_elem.screenshot()
                    gap_x = calculate_gap_offset(bg_bytes)
                    if gap_x is not None and bg_box:
                        # Scale if natural width differs from displayed width
                        distance = gap_x * (bg_box["width"] / 340.0) if bg_box["width"] > 0 else gap_x
                except Exception as e:
                    log.warning("Failed to screenshot background image: %s", e)

            # If image analysis didn't get distance, estimate from standard SecSDK dimensions
            if distance is None:
                # SecSDK typical slider distance is between 120px and 220px
                distance = random.uniform(140.0, 190.0)
                log.info("Using estimated slider distance: %.1fpx", distance)

            # 4. Perform humanized drag
            start_x = handle_box["x"] + handle_box["width"] / 2
            start_y = handle_box["y"] + handle_box["height"] / 2

            trajectory = generate_human_trajectory(start_x, start_y, distance)

            log.info("Executing humanized slider drag: start=(%.1f, %.1f), distance=%.1f, steps=%d",
                     start_x, start_y, distance, len(trajectory))

            # Initial pause before dragging (human reaction time)
            await asyncio.sleep(random.uniform(0.15, 0.35))

            await page.mouse.move(start_x, start_y)
            await asyncio.sleep(0.05)
            await page.mouse.down()

            for px, py, delay in trajectory:
                await page.mouse.move(px, py)
                if delay > 0:
                    await asyncio.sleep(delay)

            # Hold at the end slightly before release (human verification)
            await asyncio.sleep(random.uniform(0.08, 0.18))
            await page.mouse.up()

            # 5. Wait and verify if solved
            await asyncio.sleep(1.5)

            is_still_visible = False
            try:
                is_still_visible = await container.is_visible()
            except Exception:
                is_still_visible = False

            if not is_still_visible:
                log.info("Successfully solved slider captcha! Container is dismissed.")
                return True
            else:
                log.warning("Slider captcha still visible after drag attempt.")
                return False

        except Exception as exc:
            log.warning("Exception during automated captcha solving: %s", exc)
            return False
