# Local Development

This page is the practical guide for developing BrickflowUI apps locally before you move them into Databricks Apps or any shared environment.

## What Local Development Should Cover

A solid local workflow should answer these questions clearly:

- How do I run the app?
- How do I work with auth locally?
- How do I use local logos, images, GIFs, or videos?
- How do I debug loading, WebSocket state, and route handlers?
- How do I test dark mode, light mode, and responsive navigation?

Use these examples as your default local validation loop:

- [`examples/local_playground/app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/local_playground/app.py) for fast interaction, theme, media, and responsiveness checks
- [`examples/component_studio/app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/component_studio/app.py) when you want a broader component tour
- [`examples/acme_analytics_command_center/app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/acme_analytics_command_center/app.py) when you want to test a more product-style shell

## Run A Local App

```python
import brickflowui as db

app = db.App(title="Local Studio")

@app.page("/")
def home():
    return db.Text("Local runtime is healthy.", variant="h2")

if __name__ == "__main__":
    app.run()
```

Then start it with:

```bash
python app.py
```

## Recommended Local Loop

1. Start the app with `python app.py`
2. Open it in the browser
3. Keep browser devtools open
4. Watch the WebSocket connection at `/events`
5. Trigger controls and confirm you see state patches come back

## Recommended Testing Playground

Start with [`examples/local_playground/app.py`](https://github.com/AjayAJ2000/brickflowUI/blob/main/examples/local_playground/app.py) whenever you change framework code.

That app is intended to validate:

- input smoothness
- loading transitions
- theme switching
- local asset serving
- responsive shell collapse
- chart and table rendering
- auth-aware routes and forms when you extend it locally

## Local Auth Patterns

BrickflowUI supports application identity and user identity patterns. For local development, the most practical path is header-based testing.

```python
import brickflowui as db
from brickflowui.auth import HeaderAuthProvider

app = db.App(
    auth_mode="user",
    auth_provider=HeaderAuthProvider(),
    allow_anonymous=False,
)
```

Then send a local request header such as:

```text
x-brickflow-user-id: alice
```

This is useful for:

- testing route protection
- testing page-level access control
- validating role-gated flows
- building secure internal tools before identity is wired to the real platform

For the broader auth model, pair this page with [Auth And Security](./AUTH_AND_SECURITY.md).

## Local Images, GIFs, Videos, And Logos

You can now point media components and loading assets to local files directly from Python:

```python
app = db.App(
    loading={
        "title": "Acme Workspace",
        "subtitle": "Preparing your runtime",
        "asset": "assets/loader.gif",
    }
)

hero = db.Hero(
    "Command center",
    tagline="Built with BrickflowUI",
    image="assets/logo.svg",
)

preview = db.Image("assets/screenshot.png", alt="Preview", variant="content")
avatar = db.Image("assets/operator.png", alt="Operator", variant="avatar", width="40px")
demo = db.Video("assets/demo.mp4", poster="assets/poster.png")
```

The runtime serves those files automatically through a safe asset route, so you do not need to mount a separate static server just to get branding or demos on screen.

## Responsive Development

When testing local responsiveness, verify these behaviors:

- `Sidebar` should collapse behind a mobile menu button
- `TopNav` should collapse into a mobile menu automatically
- tables should remain scrollable without breaking the page shell
- cards and grids should stack instead of overflowing horizontally
- forms should stay usable inside drawers, popups, and modals

## Default Backend Loading Behavior

BrickflowUI now tracks backend event lifecycles automatically for common interactive controls.

That means when the user:

- clicks a button
- changes a select
- toggles a checkbox or switch
- adjusts a slider
- submits a chat prompt
- updates a multi-select or date range

the component can show loading while the backend handler is running and clear that state when the runtime finishes processing.

This is especially useful when:

- you query a warehouse
- you call a model endpoint
- you load heavy dashboard state
- you need to prevent repeated clicks while the backend is still working

For text-oriented controls such as `Input` and `ChatInput`, the framework now keeps typing local-first by default and syncs changes back to Python with a debounce. That avoids a full round-trip on every character while preserving controlled state.

On top of that, frontend tree updates are now applied on the next animation frame and treated as non-urgent work in React. That means the UI is more resilient when the backend is chatty or a page has several interactive regions updating at once.

## Useful Debug Checks

If something looks stuck, check these in order:

1. Confirm the browser shows a successful WebSocket connection.
2. Confirm the event handler actually updates state or completes cleanly.
3. Confirm the packaged frontend assets exist in [`brickflowui/frontend/dist`](https://github.com/AjayAJ2000/brickflowUI/tree/main/brickflowui/frontend/dist).
4. Confirm local asset paths point to real files.
5. Confirm the browser is not serving an older cached bundle.
6. Confirm your POST route is receiving the CSRF header if you are testing forms or protected JSON endpoints from a browser session.

## Theme Modes During Local Development

If your app defines both modes, you can test them right away:

```python
app = db.App(
    theme={
        "default_mode": "light",
        "dark_mode": {
            "colors": {"background": "#0A0F1E", "surface": "#0F172A", "text": "#F1F5F9"}
        },
    }
)
```

Then surface a toggle with:

```python
db.ThemeToggle()
```

or let `Sidebar` / `TopNav` show it automatically.

If you omit `dark_mode`, BrickflowUI stays in light mode by default. That is the safe baseline for older examples and new YAML theme files.
