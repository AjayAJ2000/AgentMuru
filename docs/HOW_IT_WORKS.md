# How It Works

This page explains the runtime model behind BrickflowUI so you can reason about performance, state, routing, and deployment.

If you only want to build an app quickly, start with [Quick Start](./GETTING_STARTED.md). If you want to understand why the framework behaves the way it does, read this page.

For the full production architecture, packaging expectations, and deployment-critical paths, also read [Architecture](./ARCHITECTURE.md).

## Mental model

BrickflowUI is a Python runtime plus a prebuilt frontend.

Your Python code does not generate static HTML files directly. Instead:

1. your page function returns a tree of `VNode` objects
2. the server serializes that tree
3. the browser receives the UI model over WebSocket
4. the frontend renders it and sends interaction events back to Python

That gives you a Python-first authoring model with an interactive browser experience.

## Runtime flow

```text
Python page function
    -> VNode tree
    -> server session render
    -> JSON payload / patches over WebSocket
    -> frontend renders components
    -> user clicks / types / submits
    -> event sent back to Python
    -> state updates
    -> page re-renders
```

## Pages and routing

Each `@app.page(...)` registers a render function for a path.

Important detail:

- if you register more than one page, BrickflowUI wraps page content in an app shell automatically
- if you only register one page, the page renders directly

## Session state

Hooks such as `use_state` are scoped to the current browser session.

That means:

- each connected user gets independent state
- one user changing a filter does not affect another user
- navigating to another page resets the rendered component tree for that page session

## Forms and API routes

BrickflowUI supports both interactive event handlers and explicit HTTP routes.

Use component callbacks when:

- you want lightweight in-session UI updates
- the interaction belongs to the current page state

Use `@app.route(...)` when:

- you want a real API endpoint
- you want to handle form submission
- you need auth-protected HTTP access

## Auth and access control

BrickflowUI separates page registration from access enforcement.

You can declare access requirements on both pages and routes.

This matters because:

- UI navigation can stay simple
- access logic is explicit at the page/route boundary
- user identity and app identity can both be supported

## The frontend bundle

The frontend is prebuilt and shipped inside the Python package under:

- [`brickflowui/frontend/dist/`](https://github.com/AjayAJ2000/brickflowUI/tree/main/brickflowui/frontend/dist)

This is important for Databricks Apps because:

- the app cannot rely on a separate frontend build step at runtime
- the server needs those built assets present inside the installed package
- stricter CSP environments work better when the app serves local bundled assets instead of inline scripts or third-party font/CDN dependencies

## Why Databricks Apps matter

BrickflowUI is designed to run especially well as a Databricks App.

In that environment:

- the platform provides the port through `DATABRICKS_APP_PORT`
- your `app.yaml` should run `python app.py`
- your Python package and frontend assets need to be fully bundled before deployment

## What is efficient about this model?

The main efficiency wins are:

- page authors stay in Python
- state is per session instead of global by default
- the frontend is already built and does not need a live JS toolchain in production
- updates happen through a runtime channel instead of full page reloads

## What should app authors be careful about?

- avoid slow blocking work directly in frequently-triggered event handlers
- treat page functions like render functions, not one-time setup blocks
- use helpers and reusable UI functions once a page gets large
- protect routes and pages explicitly when auth matters
- keep third-party frontend dependencies minimal for Databricks deployment
