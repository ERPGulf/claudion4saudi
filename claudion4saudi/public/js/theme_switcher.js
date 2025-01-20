frappe.provide("frappe.ui");

frappe.ui.ThemeSwitcher = class CustomThemeSwitcher extends (
  frappe.ui.ThemeSwitcher
) {
  constructor() {
    super();
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
          info: "Peach Grey - Default Theme",
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
};
