from __future__ import annotations

from pathlib import Path

import brickflowui as db


APP_DIR = Path(__file__).resolve().parent
ASSETS = APP_DIR / "assets"

BRAND_MARK = ASSETS / "collab-mark.svg"
HERO_ART = ASSETS / "hero-innovation.svg"
WORK_MODULAR = ASSETS / "work-modular.svg"
WORK_INTERFACE = ASSETS / "work-ai-interface.svg"
LIGHT_LOADER = ASSETS / "loader-light.svg"
DARK_LOADER = ASSETS / "loader-dark.svg"


THEME = {
    "style_preset": "bento",
    "default_mode": "light",
    "branding": {
        "title": "Geometric Signal Lab",
        "tagline": "Glassmorphism and geometric product surfaces in pure Python.",
        "logo": str(BRAND_MARK) if BRAND_MARK.exists() else None,
        "favicon": str(BRAND_MARK) if BRAND_MARK.exists() else None,
        "show_theme_toggle": False,
    },
    "loading": {
        "title": "Geometric Signal Lab",
        "subtitle": "Building precision layout, layered gradients, and branded loading in pure Python.",
        "message": "Loading the geometry showcase...",
        "animation": "float",
        "light": {"asset": str(LIGHT_LOADER) if LIGHT_LOADER.exists() else None},
        "dark": {
            "asset": str(DARK_LOADER) if DARK_LOADER.exists() else None,
            "subtitle": "Dark-mode glass layer active.",
        },
    },
    "typography": {
        "font_family": "'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        "font_heading": "'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    },
    "colors": {
        "primary": "#6D74FF",
        "primary_hover": "#5760EB",
        "background": "#AAB9E8",
        "surface": "#FDFDFF",
        "surface_2": "#EEF2FF",
        "text": "#101828",
        "text_muted": "#516079",
        "border": "#D4DDF1",
        "info": "#4F46E5",
        "success": "#0EA5E9",
        "warning": "#8B5CF6",
    },
    "surfaces": {
        "canvas": "#AAB9E8",
        "muted": "#EEF2FF",
        "overlay": "rgba(255, 255, 255, 0.82)",
        "card": "#FFFFFF",
        "hover": "#EEF2FF",
    },
    "radius": {"lg": "26px", "xl": "36px"},
    "shadows": {
        "sm": "0 8px 22px rgba(78, 97, 157, 0.08)",
        "md": "0 24px 54px rgba(92, 104, 171, 0.12)",
        "lg": "0 36px 84px rgba(88, 102, 177, 0.18)",
    },
    "dark_mode": {
        "colors": {
            "background": "#0E1730",
            "surface": "#121B37",
            "surface_2": "#182449",
            "text": "#F8FAFF",
            "text_muted": "#B8C2E2",
            "border": "#2C3A66",
            "info": "#9FB5FF",
            "success": "#8BE9FF",
            "warning": "#C4A0FF",
        },
        "surfaces": {
            "canvas": "#0E1730",
            "muted": "#182449",
            "overlay": "rgba(18, 27, 55, 0.88)",
            "card": "#121B37",
            "hover": "#22305B",
        },
    },
}


NAV_ITEMS = ["Home", "Works", "About", "Contact"]

WORKS = [
    {
        "pill": "3D Concept",
        "pill_color": "purple",
        "title": "Modular Product System",
        "description": "A scalable 3D system built for modern digital products and design-forward internal tools.",
        "link": "View Case",
        "image": str(WORK_MODULAR),
    },
    {
        "pill": "Visual Exploration",
        "pill_color": "green",
        "title": "AI Interface Concept",
        "description": "Exploring intelligent UI through dimensional composition, translucent layers, and calm operator UX.",
        "link": "View Case",
        "image": str(WORK_INTERFACE),
    },
    {
        "pill": "Launch Surface",
        "pill_color": "blue",
        "title": "Branded Product Entry",
        "description": "High-confidence launch pages with precise hierarchy, motion restraint, and image-led storytelling.",
        "link": "View Case",
        "image": str(HERO_ART),
    },
    {
        "pill": "Platform Ops",
        "pill_color": "orange",
        "title": "Glass Control Room",
        "description": "Premium internal tooling concepts that feel more like products than stitched admin dashboards.",
        "link": "View Case",
        "image": str(HERO_ART),
    },
]


app = db.App(theme=THEME)


def nav_button(label: str, active_nav: str, set_active_nav) -> db.VNode:
    """Render the rounded navigation pills used in the geometric shell."""
    active = label == active_nav
    return db.Button(
        label,
        on_click=lambda: set_active_nav(label),
        variant="ghost",
        style={
            "borderRadius": "999px",
            "padding": "12px 22px",
            "background": "rgba(109, 116, 255, 0.12)" if active else "transparent",
            "border": "1px solid rgba(109, 116, 255, 0.14)" if active else "1px solid transparent",
            "color": "var(--db-primary)" if active else "var(--db-text)",
            "fontWeight": "600",
            "boxShadow": "0 10px 24px rgba(109, 116, 255, 0.12)" if active else "none",
        },
    )


def icon_button(icon: str) -> db.VNode:
    """Render small circular icon controls for the nav shell."""
    return db.Button(
        "",
        icon=icon,
        variant="ghost",
        style={
            "width": "42px",
            "height": "42px",
            "borderRadius": "999px",
            "border": "1px solid rgba(16, 24, 40, 0.08)",
            "background": "rgba(255, 255, 255, 0.76)",
            "backdropFilter": "blur(14px)",
            "boxShadow": "0 12px 28px rgba(72, 88, 146, 0.08)",
        },
    )


def primary_cta(label: str, on_click) -> db.VNode:
    """Create the filled CTA style used in the hero section."""
    return db.Button(
        label,
        on_click=on_click,
        icon="ArrowRight",
        variant="primary",
        style={
            "borderRadius": "999px",
            "padding": "18px 28px",
            "minWidth": "198px",
            "justifyContent": "space-between",
            "boxShadow": "0 20px 44px rgba(109, 116, 255, 0.26)",
        },
    )


def secondary_cta(label: str, on_click) -> db.VNode:
    """Create the outlined CTA style used in the hero section."""
    return db.Button(
        label,
        on_click=on_click,
        variant="outline",
        style={
            "borderRadius": "999px",
            "padding": "18px 28px",
            "minWidth": "164px",
            "border": "1.5px solid rgba(82, 98, 170, 0.44)",
            "background": "rgba(255, 255, 255, 0.72)",
            "backdropFilter": "blur(10px)",
        },
    )


def work_card(work: dict) -> db.VNode:
    """Render one wide recent-work card closer to the desktop reference layout."""
    return db.Card(
        [
            db.Row(
                [
                    db.Column(
                        [
                            db.Badge(
                                work["pill"],
                                color=work["pill_color"],
                                style={
                                    "padding": "10px 16px",
                                    "borderRadius": "999px",
                                    "fontWeight": "600",
                                    "display": "inline-flex",
                                    "width": "fit-content",
                                },
                            ),
                            db.Spacer(2),
                            db.Text(
                                work["title"],
                                variant="h4",
                                style={
                                    "fontSize": "clamp(34px, 2.8vw, 46px)",
                                    "lineHeight": "1.08",
                                    "letterSpacing": "-0.03em",
                                },
                            ),
                            db.Spacer(2),
                            db.Text(
                                work["description"],
                                variant="body",
                                style={
                                    "fontSize": "20px",
                                    "lineHeight": "1.55",
                                    "maxWidth": "420px",
                                },
                                muted=True,
                            ),
                            db.Spacer(3),
                            db.Button(
                                work["link"],
                                icon="ArrowRight",
                                variant="ghost",
                                style={
                                    "padding": "0",
                                    "fontSize": "19px",
                                    "fontWeight": "600",
                                    "color": "var(--db-primary)",
                                    "background": "transparent",
                                    "justifyContent": "flex-start",
                                },
                            ),
                        ],
                        gap=0,
                        style={"flex": "0 0 46%", "minWidth": "280px"},
                    ),
                    db.Card(
                        [
                            db.Image(
                                work["image"],
                                alt=work["title"],
                                fit="contain",
                                width="100%",
                                height="250px",
                                radius="30px",
                            )
                        ],
                        bordered=False,
                        padding=2,
                        style={
                            "flex": "1",
                            "background": "rgba(255, 255, 255, 0.56)",
                            "border": "1px solid rgba(212, 221, 241, 0.9)",
                            "boxShadow": "inset 0 1px 0 rgba(255, 255, 255, 0.74)",
                            "minHeight": "280px",
                        },
                    ),
                ],
                gap=4,
                wrap=True,
                align="center",
            )
        ],
        bordered=True,
        padding=5,
        style={
            "borderRadius": "34px",
            "background": "rgba(255, 255, 255, 0.84)",
            "backdropFilter": "blur(14px)",
            "border": "1px solid rgba(212, 221, 241, 0.95)",
            "boxShadow": "0 24px 54px rgba(72, 88, 146, 0.08)",
            "minHeight": "356px",
        },
    )


def visible_works(start_index: int) -> list[dict]:
    """Return two rotating cards without ever leaving the showcase empty."""
    total = len(WORKS)
    return [WORKS[(start_index + offset) % total] for offset in range(2)]


@app.page("/", title="Geometry UI", icon="Sparkles")
def geometry_lab():
    """Replicate a geometric, glassmorphism-heavy desktop product layout using current BrickflowUI primitives."""
    active_nav, set_active_nav = db.use_state("Home")
    work_index, set_work_index = db.use_state(0)
    show_brief, set_show_brief = db.use_state(False)

    headline_by_nav = {
        "Home": "Playground for",
        "Works": "Showcase for",
        "About": "Studio for",
        "Contact": "Launchpad for",
    }
    subtitle_by_nav = {
        "Home": "A collaborative visual experiment crafted through precision, geometry, and 3D glass aesthetics.",
        "Works": "A portfolio-grade product surface proving BrickflowUI can express calm, premium, geometric UI compositions.",
        "About": "A design systems concept built to test whether Python-first apps can feel editorial, dimensional, and polished.",
        "Contact": "A friendly handoff surface for teams who want product-like portals without leaving Python.",
    }

    displayed_works = visible_works(work_index)

    return db.Column(
        [
            db.Card(
                [
                    db.Row(
                        [
                            db.Row(
                                [
                                    db.Image(str(BRAND_MARK), alt="Collab", width="52px", height="52px", fit="contain", variant="inline"),
                                    db.Text("COLLAB", variant="h4", style={"letterSpacing": "0.08em", "color": "var(--db-primary)"}),
                                ],
                                gap=3,
                                align="center",
                                style={"flex": "0 0 188px"},
                            ),
                            db.Row(
                                [nav_button(label, active_nav, set_active_nav) for label in NAV_ITEMS],
                                gap=1,
                                align="center",
                                justify="end",
                                style={"flex": "1"},
                            ),
                            db.Row(
                                [
                                    icon_button("Heart"),
                                    icon_button("UserRound"),
                                    icon_button("Menu"),
                                ],
                                gap=1,
                                align="center",
                            ),
                        ],
                        gap=2,
                        justify="between",
                        align="center",
                        wrap=False,
                        style={
                            "padding": "14px 18px",
                            "borderRadius": "999px",
                            "background": "rgba(255, 255, 255, 0.86)",
                            "border": "1px solid rgba(255, 255, 255, 0.92)",
                            "backdropFilter": "blur(18px)",
                            "boxShadow": "0 18px 42px rgba(79, 96, 159, 0.12)",
                        },
                    ),
                    db.Spacer(6),
                    db.Row(
                        [
                            db.Column(
                                [
                                    db.Text(
                                        headline_by_nav[active_nav],
                                        variant="h1",
                                        style={
                                            "fontSize": "clamp(66px, 6.7vw, 94px)",
                                            "lineHeight": "0.96",
                                            "letterSpacing": "-0.055em",
                                            "maxWidth": "520px",
                                        },
                                    ),
                                    db.Spacer(2),
                                    db.Card(
                                        [
                                            db.Text(
                                                "Digital Innovation",
                                                variant="h1",
                                                style={
                                                    "fontSize": "clamp(64px, 6vw, 92px)",
                                                    "lineHeight": "1",
                                                    "letterSpacing": "-0.055em",
                                                },
                                            )
                                        ],
                                        bordered=True,
                                        padding=4,
                                        style={
                                            "width": "fit-content",
                                            "borderRadius": "28px",
                                            "background": "linear-gradient(135deg, rgba(247, 221, 255, 0.82), rgba(226, 210, 255, 0.72))",
                                            "border": "2px solid rgba(31, 41, 77, 0.74)",
                                            "boxShadow": "0 18px 36px rgba(109, 116, 255, 0.12)",
                                        },
                                    ),
                                    db.Spacer(4),
                                    db.Text(
                                        subtitle_by_nav[active_nav],
                                        variant="body",
                                        style={
                                            "fontSize": "clamp(22px, 1.9vw, 28px)",
                                            "lineHeight": "1.5",
                                            "maxWidth": "580px",
                                        },
                                        muted=True,
                                    ),
                                    db.Spacer(5),
                                    db.Row(
                                        [
                                            primary_cta("Start a Project", lambda: set_show_brief(True)),
                                            secondary_cta("View Works", lambda: set_active_nav("Works")),
                                        ],
                                        gap=3,
                                        wrap=True,
                                        align="center",
                                    ),
                                ],
                                gap=0,
                                style={"flex": "0 0 43%", "minWidth": "360px"},
                            ),
                            db.Column(
                                [
                                    db.Card(
                                        [
                                            db.Image(
                                                str(HERO_ART),
                                                alt="Glassmorphism hero composition",
                                                fit="contain",
                                                width="100%",
                                                height="560px",
                                                radius="0px",
                                            )
                                        ],
                                        bordered=False,
                                        padding=0,
                                        style={
                                            "background": "radial-gradient(circle at 22% 30%, rgba(243, 223, 255, 0.55), transparent 26%), radial-gradient(circle at 74% 14%, rgba(160, 198, 255, 0.42), transparent 24%), radial-gradient(circle at 68% 72%, rgba(133, 165, 255, 0.2), transparent 22%), transparent",
                                            "borderRadius": "0px",
                                            "boxShadow": "none",
                                        },
                                    )
                                ],
                                style={
                                    "flex": "1",
                                    "minWidth": "520px",
                                    "alignItems": "stretch",
                                    "justifyContent": "center",
                                },
                            ),
                        ],
                        gap=5,
                        wrap=True,
                        align="center",
                    ),
                    db.Spacer(5),
                    db.Row(
                        [
                            db.Text("Recent Works", variant="h3", style={"fontSize": "32px"}),
                            db.Row(
                                [
                                    db.Button(
                                        "",
                                        icon="ArrowLeft",
                                        on_click=lambda: set_work_index((work_index - 1) % len(WORKS)),
                                        variant="outline",
                                        style={
                                            "width": "56px",
                                            "height": "56px",
                                            "borderRadius": "999px",
                                            "background": "rgba(255, 255, 255, 0.74)",
                                        },
                                    ),
                                    db.Button(
                                        "",
                                        icon="ArrowRight",
                                        on_click=lambda: set_work_index((work_index + 1) % len(WORKS)),
                                        variant="outline",
                                        style={
                                            "width": "56px",
                                            "height": "56px",
                                            "borderRadius": "999px",
                                            "background": "rgba(255, 255, 255, 0.74)",
                                        },
                                    ),
                                ],
                                gap=2,
                            ),
                        ],
                        justify="between",
                        align="center",
                        wrap=True,
                    ),
                    db.Spacer(3),
                    db.Row(
                        [work_card(work) for work in displayed_works],
                        gap=4,
                        wrap=True,
                        align="stretch",
                    ),
                ],
                bordered=False,
                padding=6,
                style={
                    "minHeight": "100vh",
                    "maxWidth": "1460px",
                    "margin": "0 auto",
                    "borderRadius": "42px",
                    "background": "radial-gradient(circle at 8% 22%, rgba(105, 181, 255, 0.34), transparent 22%), radial-gradient(circle at 78% 10%, rgba(179, 171, 255, 0.28), transparent 26%), linear-gradient(180deg, #B6C3EF 0%, #AFBDEB 100%)",
                    "boxShadow": "0 40px 96px rgba(80, 96, 160, 0.18)",
                },
            ),
            db.Popup(
                visible=show_brief,
                title="Geometry UI brief",
                on_close=lambda: set_show_brief(False),
                size="lg",
                children=[
                    db.Column(
                        [
                            db.Text("This example is the BrickflowUI answer to highly geometric, glass-heavy product surfaces.", variant="h4"),
                            db.Spacer(2),
                            db.Text(
                                "It proves that the current library can express rounded shells, pill navigation, image-led hero layouts, recent-work cards, and branded loading directly from Python. The remaining gap to pixel-perfect clones is not layout viability, but richer first-class primitives like absolute stack layers, aspect-ratio frames, and tokenized glass surfaces.",
                                variant="body",
                                style={"lineHeight": "1.7"},
                            ),
                        ],
                        gap=1,
                    )
                ],
            ),
        ],
        padding=6,
        gap=0,
        style={"minHeight": "100vh", "background": "linear-gradient(180deg, #AAB9E8 0%, #B9C5EA 100%)"},
    )


if __name__ == "__main__":
    app.run()
