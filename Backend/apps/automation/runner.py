"""The Playwright form filler.

Deliberately free of Django imports so it can be exercised against a local
HTML fixture without a database. ``services.py`` is the layer that turns a
Django ``AutomationRun`` into a :class:`FillPlan` and writes the result back.

The contract this module keeps, in one sentence: it types, it uploads, it
screenshots, and then it *stops* - the final Submit click only ever happens
when the caller passes ``allow_submit=True``, which the service layer grants
only for allowlisted sites with an official application API.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from .field_map import answer_for, choose_option, control_type_of, is_sensitive, match_field

logger = logging.getLogger(__name__)

# Walks the form and returns a serialisable description of every control,
# resolving each one's visible label the way a person would read it:
# <label for>, then a wrapping <label>, then aria-label, then the nearest
# preceding text in the same group.
COLLECT_CONTROLS_JS = """
() => {
  const visible = (el) => {
    const style = window.getComputedStyle(el);
    if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return false;
    const rect = el.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0;
  };

  const labelFor = (el) => {
    if (el.id) {
      const explicit = document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
      if (explicit && explicit.innerText.trim()) return explicit.innerText.trim();
    }
    const wrapper = el.closest('label');
    if (wrapper && wrapper.innerText.trim()) return wrapper.innerText.trim();
    const ariaRef = el.getAttribute('aria-labelledby');
    if (ariaRef) {
      const ref = document.getElementById(ariaRef);
      if (ref && ref.innerText.trim()) return ref.innerText.trim();
    }
    const group = el.closest('div, fieldset, li, td, p');
    if (group) {
      const text = Array.from(group.childNodes)
        .filter((n) => n.nodeType === Node.TEXT_NODE || (n.nodeType === 1 && !n.contains(el) && !['INPUT','SELECT','TEXTAREA'].includes(n.tagName)))
        .map((n) => (n.innerText || n.textContent || '').trim())
        .filter(Boolean)
        .join(' ');
      if (text) return text.slice(0, 200);
    }
    return '';
  };

  const out = [];
  document.querySelectorAll('input, select, textarea').forEach((el, index) => {
    const tag = el.tagName.toLowerCase();
    const type = (el.getAttribute('type') || (tag === 'input' ? 'text' : tag)).toLowerCase();
    if (['hidden', 'submit', 'button', 'reset', 'image'].includes(type)) return;
    if (!visible(el) && type !== 'file') return;

    if (!el.dataset.jadField) el.dataset.jadField = 'jad-' + index;

    out.push({
      handle: el.dataset.jadField,
      tag,
      type,
      name: el.getAttribute('name') || '',
      id: el.id || '',
      label: labelFor(el),
      placeholder: el.getAttribute('placeholder') || '',
      aria_label: el.getAttribute('aria-label') || '',
      required: el.required === true,
      disabled: el.disabled === true,
      readonly: el.readOnly === true,
      checked: el.checked === true,
      current_value: (el.value || '').slice(0, 120),
      options: tag === 'select' ? Array.from(el.options).map((o) => o.label || o.text || o.value) : [],
    });
  });
  return out;
}
"""

RESUME_HINTS = ("resume", "cv", "curriculum", "attach", "upload", "file")


@dataclass
class FillPlan:
    """Everything the runner needs for one attempt."""

    url: str
    values: dict[str, str]
    resume_path: str | None = None
    selector_overrides: dict[str, str] = field(default_factory=dict)
    allow_submit: bool = False
    headless: bool = False
    timeout_ms: int = 30_000
    review_timeout_ms: int = 15 * 60 * 1000
    screenshot_path: str | None = None


@dataclass
class FillResult:
    filled: dict[str, str] = field(default_factory=dict)
    skipped: list[dict] = field(default_factory=list)
    unanswered: list[str] = field(default_factory=list)
    resume_uploaded: bool = False
    submit_attempted: bool = False
    submitted: bool = False
    stop_reason: str = ""
    error: str = ""
    screenshot_path: str | None = None
    events: list[tuple[str, str, dict]] = field(default_factory=list)

    def event(self, level: str, message: str, **detail):
        self.events.append((level, message, detail))
        logger.log(getattr(logging, level.upper(), logging.INFO), message)


def _is_resume_input(control: dict) -> bool:
    if control.get("type") != "file":
        return False
    haystack = " ".join(
        str(control.get(k, "")) for k in ("label", "name", "id", "aria_label")
    ).lower()
    return any(hint in haystack for hint in RESUME_HINTS) or not haystack.strip()


def _selector(control: dict) -> str:
    return '[data-jad-field="' + control["handle"] + '"]'


def run_fill(plan: FillPlan) -> FillResult:
    """Open the page, fill what we confidently can, and stop.

    Never raises for page-level problems - failures land in ``result.error``
    so the caller can persist them against the run.
    """
    from playwright.sync_api import TimeoutError as PlaywrightTimeout
    from playwright.sync_api import sync_playwright

    result = FillResult()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=plan.headless)
        context = browser.new_context(accept_downloads=False)
        context.set_default_timeout(plan.timeout_ms)
        page = context.new_page()

        try:
            result.event("info", "Opening " + plan.url)
            page.goto(plan.url, wait_until="domcontentloaded", timeout=plan.timeout_ms)
            try:
                page.wait_for_load_state("networkidle", timeout=5_000)
            except PlaywrightTimeout:
                # Plenty of career sites keep a socket open forever; the DOM is
                # usually ready regardless, so carry on.
                result.event("debug", "Page kept loading; proceeding with the current DOM")

            controls = page.evaluate(COLLECT_CONTROLS_JS)
            result.event("info", f"Detected {len(controls)} form controls", count=len(controls))

            _fill_controls(page, plan, controls, result)
            _upload_resume(page, plan, controls, result)

            if plan.screenshot_path:
                Path(plan.screenshot_path).parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=plan.screenshot_path, full_page=True)
                result.screenshot_path = plan.screenshot_path
                result.event("info", "Captured a screenshot of the filled form")

            _finish(page, plan, result)

        except PlaywrightTimeout as exc:
            result.error = f"Timed out loading or interacting with the page: {exc}"
            result.event("error", result.error)
        except Exception as exc:  # noqa: BLE001 - surfaced to the user verbatim
            result.error = f"{type(exc).__name__}: {exc}"
            result.event("error", result.error)
        finally:
            context.close()
            browser.close()

    return result


def _fill_controls(page, plan: FillPlan, controls: list[dict], result: FillResult) -> None:
    for control in controls:
        if control["type"] == "file":
            continue

        label = control.get("label") or control.get("name") or control.get("id") or "(unlabelled)"

        if control["disabled"] or control["readonly"]:
            result.skipped.append({"label": label, "reason": "Field is not editable"})
            continue
        if is_sensitive(control):
            result.skipped.append(
                {"label": label, "reason": "Sensitive or demographic question - left for you"}
            )
            continue

        kind = control_type_of(control)
        already_filled = (
            control.get("checked", False)
            if kind in ("checkbox", "radio")
            else bool(control["current_value"])
        )
        if already_filled:
            result.skipped.append({"label": label, "reason": "Already has a value"})
            continue

        canonical = match_field(control)
        override = plan.selector_overrides.get(canonical) if canonical else None
        selector = override or _selector(control)
        value = answer_for(control, plan.values)

        if value is None:
            if control["required"]:
                result.unanswered.append(label)
            else:
                result.skipped.append({"label": label, "reason": "No saved answer"})
            continue

        try:
            if kind == "select":
                chosen = choose_option(control.get("options", []), value)
                if chosen is None:
                    result.unanswered.append(label)
                    result.event("warning", f"No matching option for '{label}'", wanted=value)
                    continue
                page.select_option(selector, label=chosen)
                value = chosen
            elif kind in ("checkbox", "radio"):
                # Only ever tick an affirmative, and never auto-accept terms -
                # which is why 'consent'/'agree' live in NEVER_FILL.
                if str(value).strip().lower() in ("yes", "true", "1"):
                    page.check(selector)
                else:
                    continue
            else:
                page.fill(selector, str(value))

            result.filled[canonical or label] = str(value)
            result.event("info", f"Filled '{label}'", field=canonical or label)
        except Exception as exc:  # noqa: BLE001
            result.skipped.append({"label": label, "reason": f"Could not fill: {exc}"})
            result.event("warning", f"Could not fill '{label}'", error=str(exc))


def _upload_resume(page, plan: FillPlan, controls: list[dict], result: FillResult) -> None:
    if not plan.resume_path:
        result.event("debug", "No resume selected for this run")
        return
    if not Path(plan.resume_path).exists():
        result.event("warning", "Selected resume file is missing on disk", path=plan.resume_path)
        return

    for control in controls:
        if not _is_resume_input(control):
            continue
        try:
            page.set_input_files(_selector(control), plan.resume_path)
            result.resume_uploaded = True
            result.event(
                "info",
                "Uploaded resume to '" + (control.get("label") or "file field") + "'",
                file=Path(plan.resume_path).name,
            )
            return
        except Exception as exc:  # noqa: BLE001
            result.event("warning", "Resume upload failed", error=str(exc))

    result.event("warning", "No resume upload field found on the page")


def _finish(page, plan: FillPlan, result: FillResult) -> None:
    """Either submit (allowlisted API sites only) or hand control back."""
    if not plan.allow_submit:
        result.stop_reason = (
            "Form filled and left open for your review. This site has no official "
            "application API, so the final Submit is yours to click."
        )
        result.event("info", result.stop_reason)
        if not plan.headless:
            result.event("info", "Waiting for you to finish in the browser window")
            try:
                page.wait_for_event("close", timeout=plan.review_timeout_ms)
                result.event("info", "Browser window closed - ending the run")
            except Exception:  # noqa: BLE001 - a timeout here is the normal path
                result.event("info", "Review window expired; closing the browser")
        return

    submit = page.locator(
        "button[type=submit], input[type=submit], "
        "button:has-text('Submit application'), button:has-text('Submit')"
    ).first
    result.submit_attempted = True
    try:
        submit.click(timeout=plan.timeout_ms)
        page.wait_for_load_state("networkidle", timeout=plan.timeout_ms)
        result.submitted = True
        result.stop_reason = "Submitted through the site's supported application flow."
        result.event("info", result.stop_reason)
    except Exception as exc:  # noqa: BLE001
        result.error = f"Submit click failed: {exc}"
        result.event("error", result.error)
