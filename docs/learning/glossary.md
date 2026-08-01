# Glossary

## App

The `db.App` object that owns pages, routes, theme, state sessions, and runtime configuration.

## Component

A Python function that returns a VNode. Examples include `Text`, `Card`, `Table`, and `PipelineGraph`.

## VNode

The serializable representation of a UI node. BrickflowUI sends VNodes to the frontend.

## Page

A Python function decorated with `@app.page(...)`.

## State

Session-specific data created with `use_state`.

## Event

A browser interaction that calls a Python handler, such as button click, input change, table row click, or chat submit.

## Controlled Input

An input whose displayed value comes from state and whose changes update that state.

## Patch

A small UI update sent to the browser after state changes.

## Frontend Assets

The built React frontend served from [`brickflowui/frontend/dist`](https://github.com/AjayAJ2000/brickflowUI/tree/main/brickflowui/frontend/dist).

## MkDocs

The documentation tool used by this project.

## Databricks App

A hosted app runtime in Databricks that runs `app.py` using `app.yaml` and `requirements.txt`.

## Pipeline Graph

A visual flow of nodes and edges representing a data pipeline or DAG.

## Capstone

The final learning project that combines the major skills from the guide.
