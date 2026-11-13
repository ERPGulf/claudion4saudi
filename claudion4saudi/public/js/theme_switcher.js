frappe.provide("frappe.ui");

// name  = the value of <html data-theme-mode>, and what the theme's CSS is keyed on
// value = the User.desk_theme option saved on the server
// base  = the Frappe theme it runs on top of (<html data-theme>). Claudion Night runs on
//         Frappe's own dark theme, so every screen and script that checks for "dark" follows it.
const CLAUDION_THEMES = [
  { name: "claudionday", value: "ClaudionDay", label: "Claudion Day", info: "Claudion light theme" },
  { name: "claudionnight", value: "ClaudionNight", label: "Claudion Night", info: "Claudion dark theme", base: "dark" },
  { name: "erpgulf", value: "ERPGulf", label: "ERPGulf", info: "ERPGulf theme" },
];

const claudion_base_theme = (mode) => {
  const theme = CLAUDION_THEMES.find((t) => t.name === mode);
  return (theme && theme.base) || mode;
};

frappe.ui.set_theme = (theme) => {
  const root = document.documentElement;
  const theme_mode = root.getAttribute("data-theme-mode");
  if (!theme && theme_mode === "automatic") {
    theme = frappe.ui.dark_theme_media_query.matches ? "dark" : "light";
  }
  root.setAttribute("data-theme", claudion_base_theme(theme || theme_mode));
};

// Apply straight away, before the desk finishes starting up.
frappe.ui.set_theme();

frappe.ui.ThemeSwitcher = class ClaudionThemeSwitcher extends frappe.ui.ThemeSwitcher {
  fetch_themes() {
    this.themes = CLAUDION_THEMES.map((theme) => ({
      ...theme,
      label: __(theme.label),
      info: __(theme.info),
    }));
    return Promise.resolve(this.themes);
  }

  render() {
    super.render();
    // Preview cards are drawn with data-theme=<name>; point each at its base theme and
    // carry the mode alongside, so a card previews exactly what the theme will look like.
    this.themes.forEach((theme) => {
      theme.$html
        .find(`[data-theme="${theme.name}"]`)
        .addBack(`[data-theme="${theme.name}"]`)
        .attr("data-theme-mode", theme.name)
        .attr("data-theme", claudion_base_theme(theme.name));
    });
  }

  toggle_theme(theme_name) {
    const theme = CLAUDION_THEMES.find((t) => t.name === theme_name);
    if (!theme) return;

    this.current_theme = theme.name;
    document.documentElement.setAttribute("data-theme-mode", theme.name);
    frappe.ui.set_theme();
    frappe.show_alert(__("Theme Changed"), 3);

    frappe.xcall("frappe.core.doctype.user.user.switch_theme", { theme: theme.value });
  }
};
