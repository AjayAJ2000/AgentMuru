from __future__ import annotations

from pathlib import Path

import brickflowui as db


ROOT = Path(__file__).resolve().parents[2]
LOGO = ROOT / "docs" / "assets" / "brickflowui-mark.svg"


app = db.App(
    title="BrickflowUI Local Playground",
    theme={
        "branding": {
            "title": "BrickflowUI Local Playground",
            "tagline": "Stress-test controls, loading, themes, and layouts locally.",
            "logo": str(LOGO) if LOGO.exists() else None,
            "favicon": str(LOGO) if LOGO.exists() else None,
        },
        "default_mode": "light",
        "dark_mode": {
            "colors": {
                "background": "#08111F",
                "surface": "#0F172A",
                "surface-2": "#152238",
                "text": "#E2E8F0",
                "text_muted": "#94A3B8",
                "border": "#1E293B",
            }
        },
        "loading": {
            "title": "BrickflowUI Local Playground",
            "subtitle": "Booting the local validation workspace",
            "asset": str(LOGO) if LOGO.exists() else None,
            "animation": "pulse",
        },
    },
)


RUNS = [
    {"day": "Mon", "runs": 24, "failures": 2},
    {"day": "Tue", "runs": 18, "failures": 1},
    {"day": "Wed", "runs": 31, "failures": 3},
    {"day": "Thu", "runs": 27, "failures": 0},
]

OPTIONS = [
    {"label": "Bronze", "value": "bronze"},
    {"label": "Silver", "value": "silver"},
    {"label": "Gold", "value": "gold"},
]


@app.page("/", title="Playground", icon="Sparkles")
def playground():
    search, set_search = db.use_state("")
    layers, set_layers = db.use_state(["bronze"])
    window, set_window = db.use_state({"start": "2026-05-01", "end": "2026-05-07"})
    auto_refresh, set_auto_refresh = db.use_state(True)
    loading_demo, set_loading_demo = db.use_state(False)

    def toggle_loading_demo():
        set_loading_demo(not loading_demo)

    return db.Column(
        [
            db.Hero(
                "Local validation playground",
                subtitle="Use this app to test responsiveness, theme switching, media, and state-heavy inputs before shipping a bigger portal.",
                image=str(LOGO) if LOGO.exists() else None,
                tagline="Designed for fast iteration and regression checks.",
                badges=[db.Badge("0.1.13", color="orange"), db.Badge("Playground", color="blue")],
                actions=[
                    db.Button("Stop loading" if loading_demo else "Simulate loading", on_click=toggle_loading_demo, loading=loading_demo),
                    db.ThemeToggle(),
                ],
            ),
            db.Grid(
                [
                    db.Card(
                        [
                            db.SectionHeader("Fast input controls", subtitle="Typing should stay smooth even when state is Python-controlled."),
                            db.Input(
                                name="search",
                                label="Search",
                                placeholder="Type quickly here...",
                                value=search,
                                on_change=set_search,
                                debounce_ms=200,
                            ),
                            db.MultiSelect(
                                name="layers",
                                label="Layers",
                                options=OPTIONS,
                                values=layers,
                                on_change=set_layers,
                            ),
                            db.DateRangePicker(
                                name="window",
                                label="Window",
                                start=window["start"],
                                end=window["end"],
                                on_change=set_window,
                            ),
                            db.Toggle(name="auto_refresh", label="Auto refresh", checked=auto_refresh, on_change=set_auto_refresh),
                        ],
                        bordered=True,
                        elevated=True,
                    ),
                    db.Card(
                        [
                            db.SectionHeader("Live state output", subtitle="This mirrors the current Python state so you can verify interaction flow."),
                            db.Code(
                                "\n".join(
                                    [
                                        f"search = {search!r}",
                                        f"layers = {layers!r}",
                                        f"window = {window!r}",
                                        f"auto_refresh = {auto_refresh!r}",
                                    ]
                                )
                            ),
                        ],
                        bordered=True,
                        elevated=True,
                    ),
                ],
                cols=2,
                gap=4,
            ),
            db.Grid(
                [
                    db.Card(
                        [
                            db.BarChart(
                                data=RUNS,
                                x_key="day",
                                y_keys=["runs", "failures"],
                                title="Run volume vs failures",
                            )
                        ],
                        bordered=True,
                        elevated=True,
                    ),
                    db.Card(
                        [
                            db.Table(
                                data=RUNS,
                                columns=[
                                    {"key": "day", "label": "Day"},
                                    {"key": "runs", "label": "Runs"},
                                    {"key": "failures", "label": "Failures", "format": "metric"},
                                ],
                                pagination=4,
                                exportable=True,
                            )
                        ],
                        bordered=True,
                        elevated=True,
                    ),
                ],
                cols=2,
                gap=4,
            ),
        ],
        gap=5,
        padding=6,
    )


if __name__ == "__main__":
    app.run()

