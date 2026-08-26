import frappe

# Themes this app adds on top of core's Light / Dark / Automatic.
#
# These strings are not arbitrary. frappe.ui.ThemeSwitcher.toggle_theme() posts
# toTitle(theme.name) to this endpoint, and toTitle() (datatype.js) upper-cases
# only the first character of each space-separated word. So the switcher entry
# named "claudionday" arrives here as "Claudionday" - not "ClaudionDay" - and
# that is what has to be stored in User.desk_theme, because frappe/www/desk.html
# renders data-theme="{{ desk_theme.lower() }}" and the CSS bundles key on
# [data-theme="claudionday"].
APP_THEMES = ("Claudionday", "Claudionnight", "Purple")
CORE_THEMES = ("Light", "Dark", "Automatic")


def _allowed_themes() -> set:
	"""Valid desk_theme values, taken from the field itself where possible.

	The User.desk_theme options are widened by this app's Property Setter, so the
	field is the single source of truth and stays in step with the fixture. Falls
	back to the known set if meta is unavailable (e.g. very early in a migrate).
	"""
	try:
		options = frappe.get_meta("User").get_field("desk_theme").options or ""
		found = {o.strip() for o in options.split("\n") if o.strip()}
		if found:
			return found
	except Exception:
		pass
	return set(CORE_THEMES) | set(APP_THEMES)


@frappe.whitelist()
def switch_theme(theme: str):
	"""Persist a desk theme, including this app's custom ones.

	Overrides frappe.core.doctype.user.user.switch_theme, which hard-codes
	`if theme in ["Dark", "Light", "Automatic"]` and silently discards anything
	else - so ClaudionDay/ClaudionNight/Purple applied to the DOM and then
	vanished on reload, with no error to explain why.

	Unlike core, an unrecognised theme raises instead of being dropped on the
	floor: a silent no-op here is exactly what made the original bug so hard to
	see.
	"""
	allowed = _allowed_themes()
	if theme not in allowed:
		frappe.throw(
			frappe._("{0} is not a valid desk theme. Valid themes: {1}").format(
				frappe.bold(theme), ", ".join(sorted(allowed))
			),
			title=frappe._("Invalid Theme"),
		)

	frappe.db.set_value("User", frappe.session.user, "desk_theme", theme)
	return theme
