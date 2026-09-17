"""Heuristics that map a form control on an unknown page to a profile field.

Application forms vary wildly, but the *labels* converge: almost everyone asks
for "First name", "Phone", "LinkedIn". So the filler scores each control
against a table of keyword patterns rather than shipping per-site selectors,
and per-site overrides (SupportedSite.selector_overrides) handle the rest.

Each entry is (canonical_field, patterns, input_types). Order matters: the
first match wins, so the most specific patterns are listed first.
"""
from __future__ import annotations

import re

TEXTUAL = ("text", "email", "tel", "url", "search", "number", "textarea")

#: Canonical field -> keyword patterns matched against a control's label,
#: name, id, placeholder and aria-label (all lowercased and joined).
FIELD_PATTERNS: list[tuple[str, tuple[str, ...], tuple[str, ...]]] = [
    # Specific before generic: "first name" must beat bare "name".
    ("first_name", ("first name", "firstname", "given name", "fname"), TEXTUAL),
    ("last_name", ("last name", "lastname", "surname", "family name", "lname"), TEXTUAL),
    ("full_name", ("full name", "your name", "candidate name", "applicant name", "name"), TEXTUAL),
    ("email", ("email", "e-mail"), TEXTUAL),
    ("phone", ("phone", "mobile", "contact number", "telephone", "cell"), TEXTUAL),
    ("linkedin_url", ("linkedin",), TEXTUAL),
    ("github_url", ("github", "git hub"), TEXTUAL),
    ("portfolio_url", ("portfolio", "website", "personal site", "blog"), TEXTUAL),
    ("address_city", ("city", "town"), TEXTUAL),
    ("address_state", ("state", "province", "region"), TEXTUAL),
    ("address_country", ("country",), TEXTUAL),
    ("location", ("location", "current location", "address"), TEXTUAL),
    ("current_company", ("current company", "current employer", "company", "employer"), TEXTUAL),
    ("current_title", ("current title", "current role", "job title", "position", "designation"), TEXTUAL),
    ("years_experience", ("years of experience", "total experience", "experience in years", "yoe"), TEXTUAL),
    ("expected_salary", ("expected salary", "salary expectation", "desired salary", "expected ctc", "compensation"), TEXTUAL),
    ("notice_period_days", ("notice period", "availability", "when can you start", "start date"), TEXTUAL),
    ("skills", ("skills", "technologies", "tech stack"), TEXTUAL),
    ("summary", ("summary", "about you", "tell us about", "cover letter", "why do you want"), ("textarea",)),
    ("work_authorization", ("work authorization", "authorized to work", "work status", "visa status"), TEXTUAL + ("select", "radio")),
    ("requires_sponsorship", ("sponsorship", "require visa", "need sponsorship"), TEXTUAL + ("select", "radio")),
    ("willing_to_relocate", ("relocate", "relocation", "willing to move"), TEXTUAL + ("select", "radio")),
]

#: Controls matching these are never touched automatically. Getting one of
#: these wrong is far worse than leaving it for the user.
NEVER_FILL = (
    "password", "ssn", "social security", "national id", "aadhaar", "passport",
    "date of birth", "dob", "gender", "race", "ethnicity", "disability",
    "veteran", "sexual orientation", "salary history", "current ctc",
    "bank", "account number", "routing", "card number", "cvv",
    "captcha", "otp", "verification code", "signature", "consent", "agree",
)

#: Keywords broad enough to fire on unrelated text - "name" inside an email
#: placeholder, "company" inside a boilerplate sentence. They are matched only
#: after every specific keyword in the table has been tried, so a placeholder
#: of "your.name@company.com" on an Email field still resolves to email.
LOOSE_KEYWORDS = frozenset({
    "name", "company", "employer", "position", "location", "address",
    "city", "town", "state", "province", "region", "country", "website",
    "blog", "skills", "summary", "availability", "compensation",
})

_PATTERN_CACHE: dict[str, re.Pattern] = {}


def _pattern(keyword: str) -> re.Pattern:
    """Whole-word match so 'name' does not fire inside 'username'."""
    if keyword not in _PATTERN_CACHE:
        body = re.escape(keyword).replace(r"\ ", r"[\s_\-]*")
        _PATTERN_CACHE[keyword] = re.compile(
            r"(?<![a-z0-9])" + body + r"(?![a-z0-9])"
        )
    return _PATTERN_CACHE[keyword]


def describe(control: dict) -> str:
    """Join every scrap of text describing a control into one haystack."""
    parts = [
        control.get("label", ""),
        control.get("name", ""),
        control.get("id", ""),
        control.get("placeholder", ""),
        control.get("aria_label", ""),
    ]
    return " ".join(p for p in parts if p).lower()


def is_sensitive(control: dict) -> bool:
    """True for anything in NEVER_FILL - demographic, financial or security
    questions the user must answer themselves."""
    haystack = describe(control)
    if (control.get("type") or "").lower() == "password":
        return True
    return any(term in haystack for term in NEVER_FILL)


def control_type_of(control: dict) -> str:
    tag = (control.get("tag") or "input").lower()
    if tag in ("textarea", "select"):
        return tag
    return (control.get("type") or "text").lower()


def match_field(control: dict) -> str | None:
    """Return the canonical profile field for a control, or None.

    ``control`` is the dict the Playwright runner builds per input:
    ``{tag, type, name, id, label, placeholder, aria_label, required}``.
    """
    if is_sensitive(control):
        return None

    control_type = control_type_of(control)

    # The input type is a stronger signal than any label text.
    if control_type == "email":
        return "email"
    if control_type == "tel":
        return "phone"

    haystack = describe(control)
    if not haystack.strip():
        return None

    # Two passes so specificity beats table order: every precise keyword is
    # tried against every field before any loose keyword is tried at all.
    for loose_pass in (False, True):
        for canonical, keywords, allowed_types in FIELD_PATTERNS:
            if control_type not in allowed_types:
                continue
            candidates = [
                kw for kw in keywords if (kw in LOOSE_KEYWORDS) is loose_pass
            ]
            if any(_pattern(kw).search(haystack) for kw in candidates):
                return canonical
    return None


def answer_for(control: dict, values: dict) -> str | None:
    """Resolve the value to type into a control, or None to leave it alone."""
    canonical = match_field(control)
    if canonical:
        value = values.get(canonical)
        return value if value not in (None, "") else None

    # No structural match - fall back to the user's saved custom answers,
    # keyed by the question text itself.
    if is_sensitive(control):
        return None
    haystack = describe(control)
    for question, saved in values.items():
        if len(question) > 12 and question.lower() in haystack:
            return str(saved)
    return None


def choose_option(options: list[str], desired: str) -> str | None:
    """Pick the closest <select> option for a desired value.

    Exact match, then containment either way. Refuses to guess beyond that -
    a wrong dropdown answer on a screening question is a silent failure.
    """
    if not desired:
        return None
    desired_norm = desired.strip().lower()
    for option in options:
        if option.strip().lower() == desired_norm:
            return option
    for option in options:
        option_norm = option.strip().lower()
        if option_norm and (option_norm in desired_norm or desired_norm in option_norm):
            return option
    return None
