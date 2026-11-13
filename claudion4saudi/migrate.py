from claudion4saudi.theme import enforce_claudion_themes


def after_migrate():
    enforce_claudion_themes()
