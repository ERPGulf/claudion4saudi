"""Claudion desk themes: Claudion Day, Claudion Night and ERPGulf are the only themes offered."""

import frappe
from frappe import _

CLAUDION_THEMES = ("ClaudionDay", "ClaudionNight", "ERPGulf")
DEFAULT_THEME = "ClaudionDay"


def _resolve(theme: str | None) -> str | None:
    key = (theme or "").replace(" ", "").lower()
    return next((t for t in CLAUDION_THEMES if t.lower() == key), None)


@frappe.whitelist()
def switch_theme(theme: str):
    """Replaces frappe.core.doctype.user.user.switch_theme, which only saves Light/Dark/Automatic."""
    resolved = _resolve(theme)
    if not resolved:
        frappe.throw(_("Theme {0} is not available").format(theme))
    frappe.db.set_value("User", frappe.session.user, "desk_theme", resolved)


def enforce_claudion_themes():
    """Move users on any other theme (or none) to Claudion Day. A user's own choice of theme is kept."""
    User = frappe.qb.DocType("User")
    (
        frappe.qb.update(User)
        .set(User.desk_theme, DEFAULT_THEME)
        .where(User.desk_theme.isnull() | User.desk_theme.notin(CLAUDION_THEMES))
    ).run()
