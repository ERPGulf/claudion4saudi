frappe.provide("frappe.ui");

frappe.ui.ThemeSwitcher = class CustomThemeSwitcher extends (
  frappe.ui.ThemeSwitcher
) {
  constructor() {
    super();
    this.default_theme = "peach_grey";
  }

  fetch_themes() {
    return new Promise((resolve) => {
      this.themes = [
        {
          name: "light",
          label: "Frappe Light",
          info: "Light Theme",
        },
        {
          name: "dark",
          label: "Timeless Night",
          info: "Dark Theme",
        },
        {
          name: "automatic",
          label: "Automatic",
          info: "Uses system's theme to switch between light and dark mode",
        },
        {
          name: "blue",
          label: "Blue",
          info: "Blue Theme",
        },
        {
          name: "red",
          label: "Red",
          info: "Red Theme",
        },
        {
          name: "peach_grey",
          label: "Peach Grey",
          info: "Peach Grey Theme (Default)",
        },
        {
          name: "purple",
          label: "Purple",
          info: "Purple Theme",
        },
      ];

      resolve(this.themes);
    });
  }

  set_default_theme() {
    frappe.db.get_value("User", frappe.session.user, "desk_theme", (r) => {
      if (!r || !r.desk_theme) {
        frappe.db.set_value(
          "User",
          frappe.session.user,
          "desk_theme",
          this.default_theme
        );
        frappe.show_alert({
          message: `Default theme set to ${this.default_theme.replace(
            "_",
            " "
          )}`,
          indicator: "green",
        });
      }
    });
  }
};
