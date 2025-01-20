app_name = "claudion4saudi"
app_title = "Claudion4Saudi"
app_publisher = "Claudion"
app_description = "Claudion4Saudi"
app_email = "support@ERPGulf.com"
app_license = "mit"


from frappe import _
from . import __version__ as app_version
# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "claudion4saudi",
# 		"logo": "/assets/claudion4saudi/logo.png",
# 		"title": "Claudion4Saudi",
# 		"route": "/claudion4saudi",
# 		"has_permission": "claudion4saudi.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/claudion4saudi/css/claudion4saudi.css"
# app_include_js = "/assets/claudion4saudi/js/claudion4saudi.js"
app_include_css = "claudion4saudi.bundle.css"
app_include_js = ["claudion4saudi.bundle.js"]

# include js, css files in header of web template
# web_include_css = "/assets/claudion4saudi/css/claudion4saudi.css"
# web_include_js = "/assets/claudion4saudi/js/claudion4saudi.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "claudion4saudi/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    # "Item": "claudion4saudi/custom/js/item.js",
    "Quotation": "claudion4saudi/custom/js/quotation.js", 
    "Sales Order": "public/js/custom_sales_order.js",  
    "Sales Invoice": "public/js/custom_sales_invoice.js",  
}
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "claudion4saudi/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "claudion4saudi.utils.jinja_methods",
# 	"filters": "claudion4saudi.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "claudion4saudi.install.before_install"
after_install = "claudion4saudi.install.set_default_theme"

# Uninstallation
# ------------

# before_uninstall = "claudion4saudi.uninstall.before_uninstall"
# after_uninstall = "claudion4saudi.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "claudion4saudi.utils.before_app_install"
# after_app_install = "claudion4saudi.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "claudion4saudi.utils.before_app_uninstall"
# after_app_uninstall = "claudion4saudi.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "claudion4saudi.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"claudion4saudi.tasks.all"
# 	],
# 	"daily": [
# 		"claudion4saudi.tasks.daily"
# 	],
# 	"hourly": [
# 		"claudion4saudi.tasks.hourly"
# 	],
# 	"weekly": [
# 		"claudion4saudi.tasks.weekly"
# 	],
# 	"monthly": [
# 		"claudion4saudi.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "claudion4saudi.install.before_tests"

# Overriding Methods
# ------------------------------

override_whitelisted_methods = {
	"frappe.core.doctype.user.user.switch_theme": "claudion4saudi.override.switch_theme"
}

#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "claudion4saudi.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "claudion4saudi.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["claudion4saudi.utils.before_request"]
# after_request = ["claudion4saudi.utils.after_request"]

# Job Events
# ----------
# before_job = ["claudion4saudi.utils.before_job"]
# after_job = ["claudion4saudi.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"claudion4saudi.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }
fixtures = [
    {"dt": "Custom Field", "filters": {"module": "Claudion4Saudi"}},
    {"dt": "DocType", "filters": {"module": "Claudion4Saudi"}},
    {"dt": "Property Setter", "filters": {"module": "Claudion4Saudi"}}
]

