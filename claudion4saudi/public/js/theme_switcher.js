frappe.provide("frappe.ui");

frappe.ui.ThemeSwitcher = class CustomThemeSwitcher extends frappe.ui.ThemeSwitcher {
  constructor() {
    super()
  }

  fetch_themes() {

    return new Promise((resolve) => {
      this.themes = [
        {
          name: "claudiontheme2",
          label: "Claudion Theme 2",
          info: "Claudion Default Theme 2",
        },
        {
          name: "themei",
          label: "Theme I",
          info: "Claudion Theme 1",
        },
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
          name: "peachgrey",
          label: "Peach Grey",
          info: "Peach Grey Theme",
        },
        {
          name: "purple",
          label: "Purple",
          info: "Purple Theme",
        },
        {
          name: "claudiontheme3",
          label: "Claudion Theme 3",
          info: "Claudion Default Theme 3",
        },
        {
          name: "claudiontheme4",
          label: "Claudion Theme 4",
          info: "Claudion Default Theme 4",
        },
      ];
      resolve(this.themes);
    });
  }
};
