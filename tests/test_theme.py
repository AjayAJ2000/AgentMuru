from pathlib import Path

from brickflowui.app import App
from brickflowui.theme import Theme


def test_theme_normalizes_branding_and_alias_keys():
    theme = Theme(
        {
            "branding": {
                "app_name": "Acme Portal",
                "logo": "/static/acme.svg",
                "favicon": "/static/acme.ico",
            },
            "colors": {
                "background": "#ffffff",
                "primary_hover": "#123456",
                "text_muted": "#666666",
            },
            "typography": {
                "font_family": "'IBM Plex Sans', sans-serif",
                "base_size": "15px",
            },
            "spacing": {
                "unit": "6px",
            },
            "borders": {
                "radius": "14px",
            },
            "surfaces": {
                "background": "#fafafa",
            },
            "shadows": {
                "medium": "0 8px 30px rgba(0,0,0,0.1)",
            },
            "motion": {
                "duration_normal": "260ms",
                "easing_standard": "ease-in-out",
            },
        }
    )

    assert theme.branding_value("title") == "Acme Portal"
    assert theme.branding_value("logo") == "/static/acme.svg"
    assert theme.config["colors"]["bg"] == "#ffffff"
    assert theme.config["colors"]["primary-hover"] == "#123456"
    assert theme.config["typography"]["sans"] == "'IBM Plex Sans', sans-serif"
    assert theme.config["spacing"]["base"] == "6px"
    assert theme.config["radius"]["md"] == "14px"
    assert theme.config["surfaces"]["canvas"] == "#fafafa"
    assert theme.config["shadows"]["md"] == "0 8px 30px rgba(0,0,0,0.1)"
    assert theme.config["motion"]["duration-normal"] == "260ms"


def test_theme_css_variables_include_surface_shadow_and_motion_tokens():
    theme = Theme(
        {
            "surfaces": {"overlay": "rgba(255,255,255,0.9)"},
            "shadows": {"large": "0 20px 50px rgba(0,0,0,0.12)"},
            "motion": {"duration_normal": "280ms", "easing_standard": "ease"},
        }
    )

    css = theme.to_css_variables()

    assert "--db-surface-overlay: rgba(255,255,255,0.9);" in css
    assert "--shadow-lg: 0 20px 50px rgba(0,0,0,0.12);" in css
    assert "--motion-duration-normal: 280ms;" in css
    assert "--transition: var(--transition-duration) var(--transition-easing);" in css


def test_theme_supports_light_and_dark_mode_overrides():
    theme = Theme(
        {
            "default_mode": "dark",
            "branding": {"brand_tagline": "Runtime confidence"},
            "light_mode": {
                "colors": {"background": "#ffffff", "text_muted": "#475569"},
            },
            "dark_mode": {
                "colors": {"background": "#010409", "text_muted": "#8b949e"},
            },
        }
    )

    css = theme.to_css_variables()

    assert theme.branding_value("tagline") == "Runtime confidence"
    assert theme.default_mode() == "dark"
    assert ":root[data-theme-mode='light']" in css
    assert "--db-bg: #010409;" in css
    assert "--db-bg: #ffffff;" in css


def test_theme_defaults_to_light_mode_when_not_explicitly_configured():
    theme = Theme()

    assert theme.default_mode() == "light"


def test_theme_supports_style_presets_and_light_dark_alias_sections():
    theme = Theme(
        {
            "preset": "executive",
            "light": {
                "colors": {"background": "#FEFEFD"},
            },
            "dark": {
                "colors": {"background": "#040712"},
            },
        }
    )

    css = theme.to_css_variables()

    assert theme.style_preset() == "executive"
    assert theme.config["shadows"]["md"] == "0 16px 36px rgba(15, 23, 42, 0.08)"
    assert "--db-bg: #FEFEFD;" in css
    assert "--db-bg: #040712;" in css


def test_app_uses_branding_from_theme_file_when_defaults_are_used():
    theme_path = Path(__file__).parent / "_branding_test.yaml"
    app = App(theme=theme_path)

    assert app.title == "Acme Control Center"
    assert app.logo == "/branding/acme.svg"
    assert app.favicon == "/branding/acme.ico"
