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
          label: "Light",
          info: "Light Theme",
        },
        {
          name: "dark",
          label: "Dark",
          info: "Dark Theme",
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
          info: "Peach Grey Theme",
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
