import os
import random
import time
from datetime import datetime
import brickflowui as db

# Initialize App
theme_path = os.path.join(os.path.dirname(__file__), "theme.yaml")
app = db.App(title="BrickflowUI Master Showcase", theme=theme_path)

# --- Helper Logic ---
def get_mock_data():
    return [
        {"id": i, "name": f"Project {chr(65+i)}", "status": random.choice(["Active", "Pending", "Completed"]), 
         "progress": random.randint(10, 100), "revenue": random.randint(1000, 5000)}
        for i in range(15)
    ]

# --- Pages ---

@app.page("/", title="Executive Dashboard", icon="LayoutDashboard")
def dashboard():
    revenue, set_revenue = db.use_state(45230)
    users, set_users = db.use_state(1240)
    
    # Update revenue simulation
    db.use_effect(lambda: set_revenue(lambda current: current + random.randint(-50, 200)), [time.time() // 5])

    chart_data = [
        {"name": "Jan", "value": 400, "users": 200},
        {"name": "Feb", "value": 300, "users": 250},
        {"name": "Mar", "value": 600, "users": 400},
        {"name": "Apr", "value": 800, "users": 380},
        {"name": "May", "value": 500, "users": 450},
        {"name": "Jun", "value": 900, "users": 600},
    ]

    return db.Column([
        db.Row([
            db.Text("Operational Overview", variant="h1"),
            db.Badge("Live Updates", color="green")
        ], justify="between"),
        
        db.Grid([
            db.Card([
                db.Stat("Total Revenue", f"${revenue:,}", delta="+12.5%", delta_type="increase", icon="Activity")
            ]),
            db.Card([
                db.Stat("Active Users", f"{users:,}", delta="+5.2%", delta_type="increase", icon="Clock")
            ]),
            db.Card([
                db.Stat("System Health", "99.9%", delta="Stable", delta_type="neutral", icon="Server")
            ]),
            db.Card([
                db.Stat("Open Issues", "4", delta="-2", delta_type="decrease", icon="AlertTriangle")
            ]),
        ], cols=4),
        
        db.Grid([
            db.Card([
                db.AreaChart(chart_data, x_key="name", y_keys=["value"], title="Revenue Growth"),
            ]),
            db.Card([
                db.BarChart(chart_data, x_key="name", y_keys=["users"], title="User Engagement", colors=["#00aed1"]),
            ]),
        ], cols=2),
        
        db.Card([
            db.Text("Quick Actions", variant="h3"),
            db.Row([
                db.Button("Generate Report", icon="GitBranch"),
                db.Button("Sync Data", variant="secondary", icon="Database"),
                db.Button("Archive All", variant="danger", icon="XCircle"),
            ])
        ])
    ], gap=6)


@app.page("/data", title="Data Explorer", icon="Database")
def data_explorer():
    selected_table, set_table = db.use_state({"catalog": "main", "schema": "default", "table": "users"})
    is_loading, set_loading = db.use_state(False)
    
    data = db.use_memo(get_mock_data, [])

    return db.Column([
        db.Text("Data Management", variant="h1"),
        
        db.Grid([
            db.Card([
                db.Text("Unity Catalog Browser", variant="h4"),
                db.CatalogBrowser(on_select=set_table, selected=selected_table),
            ]),
            db.Column([
                db.Card([
                    db.WarehouseSelector(label="Select SQL Warehouse", selected_id="wh-123"),
                    db.Spacer(2),
                    db.Button("Refresh Data", on_click=lambda: set_loading(True), loading=is_loading, width="100%"),
                ]),
                db.Card([
                    db.Stat("Inspected Table", f"{selected_table.get('table', 'None')}"),
                    db.Text(f"Path: {selected_table.get('catalog')}.{selected_table.get('schema')}", variant="caption")
                ])
            ])
        ], cols=2),
        
        db.Card([
            db.Table(
                data=data,
                columns=[
                    {"key": "name", "label": "Project Name", "sortable": True},
                    {"key": "status", "label": "Status"},
                    {"key": "progress", "label": "Progress %", "sortable": True},
                    {"key": "revenue", "label": "Budget", "sortable": True},
                ],
                pagination=5,
                on_row_click=lambda r: print(f"Clicked {r['row']['name']}")
            )
        ], title="Project Inventory")
    ], gap=6)


@app.page("/components", title="Component Gallery", icon="FlaskConical")
def component_gallery():
    slider_val, set_slider = db.use_state(50)
    toggle_val, set_toggle = db.use_state(True)
    modal_open, set_modal = db.use_state(False)
    
    return db.Column([
        db.Text("Component Gallery", variant="h1"),
        
        db.Tabs([
            db.TabItem("Interactivity", [
                db.Grid([
                    db.Card([
                        db.Text("Standard Inputs", variant="h4"),
                        db.Input(name="username", label="Username", placeholder="Enter name..."),
                        db.Select(name="role", label="User Role", options=[
                            {"label": "Admin", "value": "admin"},
                            {"label": "Editor", "value": "editor"}
                        ]),
                        db.Slider(name="priority", label=f"Priority: {slider_val}", value=slider_val, on_change=set_slider),
                        db.Checkbox(name="agree", label="I accept terms"),
                        db.Toggle(name="notif", label="Enable Notifications", checked=toggle_val, on_change=set_toggle),
                    ]),
                    db.Card([
                        db.Text("Action Triggers", variant="h4"),
                        db.Button("Open Modal", on_click=lambda: set_modal(True)),
                        db.Spacer(4),
                        db.Text("Feedback Elements", variant="h4"),
                        db.Row([
                            db.Badge("Critical", color="red"),
                            db.Badge("Beta", color="purple"),
                            db.Badge("New", color="orange"),
                        ]),
                        db.Spacer(2),
                        db.Alert("Your changes have been saved successfully.", type="success", title="Update Complete"),
                        db.Spacer(2),
                        db.Progress(value=slider_val, label="Task Completion"),
                        db.Spacer(2),
                        db.Row([db.Spinner("sm"), db.Text("Processing...", variant="caption")]),
                    ])
                ], cols=2)
            ]),
            db.TabItem("Typography", [
                db.Card([
                    db.Text("Heading 1", variant="h1"),
                    db.Text("Heading 2", variant="h2"),
                    db.Text("Heading 3", variant="h3"),
                    db.Text("Heading 4", variant="h4"),
                    db.Text("Standard body text for readable paragraphs."),
                    db.Text("Caption text for small notes", variant="caption"),
                    db.Text("db.Stat('Label', '100')", variant="code"),
                    db.Text("UPPERCASE LABEL", variant="label"),
                    db.Divider("Syntax Highlighted Code"),
                    db.Code("def hello():\n    print('Hello World')", language="python")
                ])
            ])
        ]),
        
        db.Modal(
            visible=modal_open,
            title="Interactive Modal",
            on_close=lambda: set_modal(False),
            children=[
                db.Text("This is a context-managed modal dialog."),
                db.Text("Modals can contain any BrickflowUI component.", variant="caption"),
                db.Spacer(4),
                db.Row([
                    db.Button("Cancel", variant="secondary", on_click=lambda: set_modal(False)),
                    db.Button("Confirm Action", on_click=lambda: set_modal(False)),
                ], justify="end")
            ]
        )
    ], gap=6)

@app.page("/advanced", title="Advanced Settings", icon="Settings")
def advanced_tools():
    return db.Column([
        db.Text("Advanced Integration", variant="h1"),
        
        db.Grid([
            db.Card([
                db.Text("Databricks Job Trigger", variant="h4"),
                db.Text("Directly trigger and monitor workspace jobs.", variant="caption"),
                db.Spacer(4),
                db.JobTrigger(job_id="job-888", label="Run ETL Pipeline", on_complete=lambda r: print("Job Done!")),
            ]),
            db.Card([
                db.Text("Custom Plotly Visualization", variant="h4"),
                db.Plot({
                    "data": [{"x": [1, 2, 3], "y": [10, 15, 13], "type": "scatter"}],
                    "layout": {"title": "Raw Plotly Graph", "paper_bgcolor": "rgba(0,0,0,0)", "plot_bgcolor": "rgba(0,0,0,0)"}
                })
            ])
        ], cols=2),
        
        db.Card([
            db.Text("Form Serialization Demo", variant="h3"),
            db.Form(
                [
                    db.Input(name="api_key", label="Secrets Key", type="password"),
                    db.Row([
                        db.Checkbox(name="opt_a", label="Opt-in Alpha"),
                        db.Checkbox(name="opt_b", label="Opt-in Beta"),
                    ]),
                    db.Button("Save Configuration", html_type="submit", width="100%")
                ],
                action="/api/submit",
                success_redirect="/",
            )
        ])
    ], gap=6)

@app.route("/api/submit", methods=["POST"])
async def handle_submit(request):
    data = await request.json()
    print(f"Received form data: {data}")
    return {"status": "success"}

if __name__ == "__main__":
    app.run()
