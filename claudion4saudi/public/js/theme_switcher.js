frappe.provide("frappe.ui");

frappe.ui.ThemeSwitcher = class CustomThemeSwitcher extends (
  frappe.ui.ThemeSwitcher
) {
  constructor() {
    super();
  }

  // `name` is the value core writes to <html data-theme-mode> and, after
  // toTitle(), the value it persists to User.desk_theme. It must stay lowercase
  // and single-word: toTitle() only upper-cases the first character of each
  // space-separated word, so "claudionday" round-trips as "Claudionday", which
  // is exactly what the User.desk_theme Property Setter now lists and what the
  // CSS bundles key on ([data-theme="claudionday"]).
  fetch_themes() {
    return new Promise((resolve) => {
      this.themes = [
        {
          name: "light",
          label: __("Frappe Light"),
          info: __("Light Theme"),
        },
        {
          name: "dark",
          label: __("Timeless Night"),
          info: __("Dark Theme"),
        },
        {
          name: "automatic",
          label: __("Automatic"),
          info: __("Uses system's theme to switch between light and dark mode"),
        },
        {
          name: "purple",
          label: __("Purple"),
          info: __("Purple Theme"),
        },
        {
          name: "claudionday",
          label: __("Claudion Day"),
          info: __("Claudion Day Theme"),
        },
        {
          name: "claudionnight",
          label: __("Claudion Night"),
          info: __("Claudion Night Theme"),
        },
      ];
      resolve(this.themes);
    });
  }
};
