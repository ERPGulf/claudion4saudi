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
        // {
        //   name: "claudiontheme",
        //   label: "Claudion Theme",
        //   info: "Claudion Default Theme 2",
        // },
        // {
        //   name: "claudiondark",
        //   label: "Claudion Dark",
        //   info: "Claudion Theme 1",
        // },
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
        // {
        //   name: "automatic",
        //   label: "Automatic",
        //   info: "Uses system's theme to switch between light and dark mode",
        // },
        // {
        //   name: "blue",
        //   label: "Blue",
        //   info: "Blue Theme",
        // },
        // {
        //   name: "red",
        //   label: "Red",
        //   info: "Red Theme",
        // },
        // {
        //   name: "peachgrey",
        //   label: "Peach Grey",
        //   info: "Peach Grey Theme",
        // },
        {
          name: "purple",
          label: "Purple",
          info: "Purple Theme",
        },
        // {
        //   name: "claudionsimple",
        //   label: "Claudion Simple",
        //   info: "Claudion Default Theme 3",
        // },
        // {
        //   name: "claudionlight",
        //   label: "Claudion Light",
        //   info: "Claudion Default Theme 4",
        // },
        {
          name: "claudionday",
          label: "Claudion Day",
          info: "Claudion Default Theme 5",
        },
        {
          name: "claudionnight",
          label: "Claudion Night",
          info: "Claudion Default Theme 6",
        },
      ];
      resolve(this.themes);
    });
  }
};
