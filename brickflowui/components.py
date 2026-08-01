"""
BrickflowUI primitive components.

Each function returns a VNode. Think of these as your JSX — but pure Python.
Usage:
    from brickflowui import components as ui
    node = ui.Column([ui.Text("Hello!"), ui.Button("Click me", on_click=handler)])
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Callable, Dict, Iterator, List, Optional, Literal

from .vdom import VNode, EventHandler

# ── Type aliases ────────────────────────────────────────────────────────────

ButtonVariant = Literal["primary", "secondary", "danger", "ghost", "outline"]
AlertType = Literal["info", "success", "warning", "error"]
TextVariant = Literal["h1", "h2", "h3", "h4", "body", "caption", "code", "label"]
InputType = Literal["text", "password", "email", "number", "url", "search", "date", "textarea"]
BadgeColor = Literal["blue", "green", "yellow", "red", "purple", "gray", "orange"]


# ── Layout ───────────────────────────────────────────────────────────────────


def Column(
    children: List[VNode],
    gap: int = 2,
    padding: int = 0,
    align: Literal["start", "center", "end", "stretch"] = "stretch",
    **kwargs,
) -> VNode:
    """Vertical stack of children."""
    props = {"gap": gap, "padding": padding, "align": align, **kwargs}
    return VNode(
        type="Column",
        props=props,
        children=children,
    )


def Row(
    children: List[VNode],
    gap: int = 2,
    wrap: bool = False,
    align: Literal["start", "center", "end", "stretch"] = "center",
    justify: Literal["start", "center", "end", "between", "around"] = "start",
    **kwargs,
) -> VNode:
    """Horizontal row of children."""
    return VNode(
        type="Row",
        props={"gap": gap, "wrap": wrap, "align": align, "justify": justify, **kwargs},
        children=children,
    )


def Card(
    children: List[VNode],
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
    bordered: bool = True,
    padding: int = 4,
    hover: bool = False,
    elevated: bool = False,
    animated: bool = False,
    animation: Optional[str] = None,
    animation_delay: Optional[float] = None,
    **kwargs,
) -> VNode:
    """A surface card container."""
    return VNode(
        type="Card",
        props={
            "title": title,
            "subtitle": subtitle,
            "bordered": bordered,
            "padding": padding,
            "hover": hover,
            "elevated": elevated,
            "animated": animated,
            "animation": animation,
            "animationDelay": animation_delay,
            **kwargs,
        },
        children=children,
    )


def Grid(
    children: List[VNode],
    cols: int = 2,
    gap: int = 4,
) -> VNode:
    """Responsive grid layout."""
    return VNode(
        type="Grid",
        props={"cols": cols, "gap": gap, "style": {"--cols": str(cols)}},
        children=children,
    )


def Divider(label: Optional[str] = None) -> VNode:
    """Horizontal rule, optionally with a label."""
    return VNode(type="Divider", props={"label": label})


def Spacer(size: int = 4) -> VNode:
    """Blank vertical spacer."""
    return VNode(type="Spacer", props={"size": size})


# ── Typography ────────────────────────────────────────────────────────────────


def Text(
    value: str,
    variant: TextVariant = "body",
    color: Optional[str] = None,
    bold: bool = False,
    italic: bool = False,
    muted: bool = False,
    style: Optional[Dict[str, Any]] = None,
    class_name: Optional[str] = None,
) -> VNode:
    """A text/heading element."""
    return VNode(
        type="Text",
        props={
            "value": value,
            "variant": variant,
            "color": color,
            "bold": bold,
            "italic": italic,
            "muted": muted,
            "style": style,
            "className": class_name,
        },
    )


def Code(value: str, language: str = "python") -> VNode:
    """Syntax-highlighted code block."""
    return VNode(type="Code", props={"value": value, "language": language})


# ── Interactive Controls ───────────────────────────────────────────────────


def Button(
    label: str,
    on_click: Optional[EventHandler] = None,
    variant: ButtonVariant = "primary",
    icon: Optional[str] = None,
    disabled: bool = False,
    loading: bool = False,
    animated: bool = False,
    animation: Optional[str] = None,
    animation_delay: Optional[float] = None,
    html_type: Literal["button", "submit", "reset"] = "button",
    **kwargs,
) -> VNode:
    handlers: Dict[str, EventHandler] = {}
    if on_click:
        handlers["click"] = on_click
    return VNode(
        type="Button",
        props={
            "label": label,
            "variant": variant,
            "icon": icon,
            "disabled": disabled,
            "loading": loading,
            "animated": animated,
            "animation": animation,
            "animationDelay": animation_delay,
            "htmlType": html_type,
            **kwargs,
        },
        event_handlers=handlers,
    )


def Input(
    name: str,
    label: Optional[str] = None,
    type: InputType = "text",
    placeholder: str = "",
    value: str = "",
    on_change: Optional[Callable[[str], None]] = None,
    disabled: bool = False,
    required: bool = False,
    error: Optional[str] = None,
    loading: bool = False,
    debounce_ms: int = 180,
    change_strategy: Literal["debounce", "immediate", "blur"] = "debounce",
    sync_on_blur: bool = True,
) -> VNode:
    """Controlled text-like input with opt-in sync behavior for backend-driven apps.

    By default, BrickflowUI debounces text updates so typing stays local and fast
    while still syncing state back to Python.
    """
    handlers: Dict[str, EventHandler] = {}
    if on_change:
        handlers["change"] = on_change
    return VNode(
        type="Input",
        props={"name": name, "label": label, "inputType": type, "placeholder": placeholder,
               "value": value, "disabled": disabled, "required": required, "error": error,
               "loading": loading, "debounceMs": debounce_ms, "changeStrategy": change_strategy,
               "syncOnBlur": sync_on_blur},
        event_handlers=handlers,
    )


def Select(
    name: str,
    options: List[Dict[str, str]],
    label: Optional[str] = None,
    value: Optional[str] = None,
    placeholder: str = "Select an option",
    on_change: Optional[Callable[[str], None]] = None,
    disabled: bool = False,
    loading: bool = False,
    animated: bool = False,
    animation: Optional[str] = None,
    animation_delay: Optional[float] = None,
) -> VNode:
    """Dropdown select. options = [{"label": "...", "value": "..."}]"""
    handlers: Dict[str, EventHandler] = {}
    if on_change:
        handlers["change"] = on_change
    return VNode(
        type="Select",
        props={"name": name, "options": options, "label": label, "value": value,
               "placeholder": placeholder, "disabled": disabled, "loading": loading,
               "animated": animated, "animation": animation, "animationDelay": animation_delay},
        event_handlers=handlers,
    )


def Checkbox(
    name: str,
    label: str,
    checked: bool = False,
    on_change: Optional[Callable[[bool], None]] = None,
    disabled: bool = False,
    loading: bool = False,
    animated: bool = False,
    animation: Optional[str] = None,
    animation_delay: Optional[float] = None,
) -> VNode:
    handlers: Dict[str, EventHandler] = {}
    if on_change:
        handlers["change"] = on_change
    return VNode(
        type="Checkbox",
        props={"name": name, "label": label, "checked": checked, "disabled": disabled,
               "loading": loading, "animated": animated, "animation": animation, "animationDelay": animation_delay},
        event_handlers=handlers,
    )


def Toggle(
    name: str,
    label: str,
    checked: bool = False,
    on_change: Optional[Callable[[bool], None]] = None,
    disabled: bool = False,
    loading: bool = False,
    animated: bool = False,
    animation: Optional[str] = None,
    animation_delay: Optional[float] = None,
) -> VNode:
    handlers: Dict[str, EventHandler] = {}
    if on_change:
        handlers["change"] = on_change
    return VNode(
        type="Toggle",
        props={"name": name, "label": label, "checked": checked, "disabled": disabled,
               "loading": loading, "animated": animated, "animation": animation, "animationDelay": animation_delay},
        event_handlers=handlers,
    )


def Slider(
    name: str,
    label: Optional[str] = None,
    min: float = 0,
    max: float = 100,
    step: float = 1,
    value: float = 0,
    on_change: Optional[Callable[[float], None]] = None,
    disabled: bool = False,
    loading: bool = False,
    animated: bool = False,
    animation: Optional[str] = None,
    animation_delay: Optional[float] = None,
) -> VNode:
    handlers: Dict[str, EventHandler] = {}
    if on_change:
        handlers["change"] = on_change
    return VNode(
        type="Slider",
        props={"name": name, "label": label, "min": min, "max": max, "step": step, "value": value,
               "disabled": disabled, "loading": loading, "animated": animated,
               "animation": animation, "animationDelay": animation_delay},
        event_handlers=handlers,
    )


# ── Data Display ───────────────────────────────────────────────────────────


def Table(
    data: List[Dict[str, Any]],
    columns: Optional[List[Dict[str, Any]]] = None,
    pagination: int = 20,
    on_row_click: Optional[Callable[[Dict[str, Any]], None]] = None,
    editable: bool = False,
    loading: bool = False,
    empty_message: str = "No data available",
    error_message: Optional[str] = None,
    exportable: bool = False,
) -> VNode:
    """
    Data table. columns = [{"key": "col", "label": "Column", "sortable": True}]
    If columns is None, keys are auto-inferred from data[0].
    """
    if columns is None and data:
        columns = [{"key": k, "label": k.replace("_", " ").title(), "sortable": True} for k in data[0].keys()]
    handlers: Dict[str, EventHandler] = {}
    if on_row_click:
        handlers["rowClick"] = on_row_click
    return VNode(
        type="Table",
        props={"data": data, "columns": columns or [], "pagination": pagination,
               "editable": editable, "loading": loading, "emptyMessage": empty_message,
               "errorMessage": error_message, "exportable": exportable},
        event_handlers=handlers,
    )


def Badge(
    label: str,
    color: BadgeColor = "blue",
    style: Optional[Dict[str, Any]] = None,
    class_name: Optional[str] = None,
) -> VNode:
    """Compact highlighted label for tags, states, or short metadata."""
    return VNode(type="Badge", props={"label": label, "color": color, "style": style, "className": class_name})


def Alert(
    message: str,
    type: AlertType = "info",
    title: Optional[str] = None,
    dismissible: bool = False,
) -> VNode:
    return VNode(
        type="Alert",
        props={"message": message, "alertType": type, "title": title, "dismissible": dismissible},
    )


def Spinner(size: Literal["sm", "md", "lg"] = "md") -> VNode:
    return VNode(type="Spinner", props={"size": size})


def Progress(value: float, max: float = 100, label: Optional[str] = None, color: str = "blue") -> VNode:
    """Progress bar. value and max are numbers."""
    return VNode(type="Progress", props={"value": value, "max": max, "label": label, "color": color, "animated": True})


def Stat(
    label: str,
    value: str,
    delta: Optional[str] = None,
    delta_type: Literal["increase", "decrease", "neutral"] = "neutral",
    icon: Optional[str] = None,
    animated: bool = False,
    animation: Optional[str] = None,
    animation_delay: Optional[float] = None,
) -> VNode:
    """KPI stat card (number + label + optional delta)."""
    return VNode(
        type="Stat",
        props={
            "label": label,
            "value": value,
            "delta": delta,
            "deltaType": delta_type,
            "icon": icon,
            "animated": animated,
            "animation": animation,
            "animationDelay": animation_delay,
        },
    )


# ── Navigation & Structure ─────────────────────────────────────────────────


def Tabs(
    items: List[VNode],
    default_active: int = 0,
    on_change: Optional[Callable[[int], None]] = None,
    animated: bool = False,
    animation: Optional[str] = None,
    animation_delay: Optional[float] = None,
) -> VNode:
    """Tab container. Children should be TabItem nodes."""
    handlers: Dict[str, EventHandler] = {}
    if on_change:
        handlers["change"] = on_change
    return VNode(
        type="Tabs",
        props={"defaultActive": default_active, "animated": animated, "animation": animation, "animationDelay": animation_delay},
        children=items,
        event_handlers=handlers,
    )


def TabItem(label: str, children: List[VNode], icon: Optional[str] = None) -> VNode:
    return VNode(type="TabItem", props={"label": label, "icon": icon}, children=children)


def Sidebar(
    items: List[VNode],
    logo: Optional[str] = None,
    brand_name: str = "BrickflowUI",
    tagline: Optional[str] = None,
    collapsed: bool = False,
    show_theme_toggle: bool = False,
    sticky: bool = True,
    **kwargs,
) -> VNode:
    return VNode(
        type="Sidebar",
        props={"logo": logo, "brandName": brand_name, "tagline": tagline, "collapsed": collapsed,
               "showThemeToggle": show_theme_toggle, "sticky": sticky, **kwargs},
        children=items,
    )


def TopNav(
    items: List[VNode],
    logo: Optional[str] = None,
    brand_name: str = "BrickflowUI",
    tagline: Optional[str] = None,
    actions: Optional[List[VNode]] = None,
    sticky: bool = True,
    show_theme_toggle: bool = False,
    **kwargs,
) -> VNode:
    return VNode(
        type="TopNav",
        props={
            "logo": logo,
            "brandName": brand_name,
            "tagline": tagline,
            "actions": actions or [],
            "sticky": sticky,
            "showThemeToggle": show_theme_toggle,
            **kwargs,
        },
        children=items,
    )


def ThemeToggle(
    label: str = "Theme",
    light_label: str = "Light",
    dark_label: str = "Dark",
) -> VNode:
    return VNode(
        type="ThemeToggle",
        props={"label": label, "lightLabel": light_label, "darkLabel": dark_label},
    )


def NavItem(
    label: str,
    path: str,
    icon: Optional[str] = None,
    badge: Optional[str] = None,
) -> VNode:
    return VNode(type="NavItem", props={"label": label, "path": path, "icon": icon, "badge": badge})


def Modal(
    visible: bool,
    title: str,
    children: List[VNode],
    on_close: Optional[EventHandler] = None,
    size: Literal["sm", "md", "lg", "xl"] = "md",
    animated: bool = True,
    animation: Optional[str] = "fade-up",
    animation_delay: Optional[float] = None,
) -> VNode:
    handlers: Dict[str, EventHandler] = {}
    if on_close:
        handlers["close"] = on_close
    return VNode(
        type="Modal",
        props={"visible": visible, "title": title, "size": size, "animated": animated, "animation": animation, "animationDelay": animation_delay},
        children=children,
        event_handlers=handlers,
    )


def Drawer(
    visible: bool,
    title: str,
    children: List[VNode],
    on_close: Optional[EventHandler] = None,
    side: Literal["left", "right"] = "right",
    width: str = "420px",
    animated: bool = True,
    animation: Optional[str] = "fade-up",
    animation_delay: Optional[float] = None,
) -> VNode:
    handlers: Dict[str, EventHandler] = {}
    if on_close:
        handlers["close"] = on_close
    return VNode(
        type="Drawer",
        props={"visible": visible, "title": title, "side": side, "width": width, "animated": animated, "animation": animation, "animationDelay": animation_delay},
        children=children,
        event_handlers=handlers,
    )


def Popup(
    visible: bool,
    title: str,
    children: List[VNode],
    on_close: Optional[EventHandler] = None,
    size: Literal["sm", "md", "lg"] = "sm",
    backdrop: bool = True,
    placement: Literal["center"] = "center",
    animated: bool = True,
    animation: Optional[str] = "fade-up",
    animation_delay: Optional[float] = None,
) -> VNode:
    handlers: Dict[str, EventHandler] = {}
    if on_close:
        handlers["close"] = on_close
    return VNode(
        type="Popup",
        props={"visible": visible, "title": title, "size": size, "backdrop": backdrop, "placement": placement, "animated": animated, "animation": animation, "animationDelay": animation_delay},
        children=children,
        event_handlers=handlers,
    )


def Accordion(
    items: List[VNode],
    default_open: Optional[List[int]] = None,
    allow_multiple: bool = False,
) -> VNode:
    return VNode(
        type="Accordion",
        props={"defaultOpen": default_open or [], "allowMultiple": allow_multiple},
        children=items,
    )


def AccordionItem(
    title: str,
    children: List[VNode],
    subtitle: Optional[str] = None,
    icon: Optional[str] = None,
) -> VNode:
    return VNode(type="AccordionItem", props={"title": title, "subtitle": subtitle, "icon": icon}, children=children)


def EmptyState(
    title: str,
    message: str,
    icon: Optional[str] = None,
    actions: Optional[List[VNode]] = None,
    animated: bool = False,
    animation: Optional[str] = None,
    animation_delay: Optional[float] = None,
) -> VNode:
    return VNode(type="EmptyState", props={"title": title, "message": message, "icon": icon, "actions": actions or [], "animated": animated, "animation": animation, "animationDelay": animation_delay})


def Breadcrumbs(items: List[Dict[str, Any]]) -> VNode:
    return VNode(type="Breadcrumbs", props={"items": items})


def DateRangePicker(
    name: str,
    label: Optional[str] = None,
    start: str = "",
    end: str = "",
    on_change: Optional[Callable[[Dict[str, str]], None]] = None,
    disabled: bool = False,
    loading: bool = False,
    animated: bool = False,
    animation: Optional[str] = None,
    animation_delay: Optional[float] = None,
) -> VNode:
    handlers: Dict[str, EventHandler] = {}
    if on_change:
        handlers["change"] = on_change
    return VNode(
        type="DateRangePicker",
        props={"name": name, "label": label, "start": start, "end": end, "disabled": disabled, "loading": loading,
               "animated": animated, "animation": animation, "animationDelay": animation_delay},
        event_handlers=handlers,
    )


def MultiSelect(
    name: str,
    options: List[Dict[str, str]],
    label: Optional[str] = None,
    values: Optional[List[str]] = None,
    on_change: Optional[Callable[[List[str]], None]] = None,
    disabled: bool = False,
    loading: bool = False,
    placeholder: Optional[str] = None,
    animated: bool = False,
    animation: Optional[str] = None,
    animation_delay: Optional[float] = None,
) -> VNode:
    """Controlled multi-value selector for filters, scopes, or tags."""
    handlers: Dict[str, EventHandler] = {}
    if on_change:
        handlers["change"] = on_change
    return VNode(
        type="MultiSelect",
        props={"name": name, "options": options, "label": label, "values": values or [], "disabled": disabled, "loading": loading,
               "placeholder": placeholder, "animated": animated, "animation": animation, "animationDelay": animation_delay},
        event_handlers=handlers,
    )


def Toast(
    message: str,
    title: Optional[str] = None,
    type: AlertType = "info",
    visible: bool = True,
    icon: Optional[str] = None,
    on_close: Optional[EventHandler] = None,
    dismissible: bool = True,
    auto_hide_ms: Optional[int] = None,
    animated: bool = True,
    animation: Optional[str] = "fade-up",
    animation_delay: Optional[float] = None,
) -> VNode:
    handlers: Dict[str, EventHandler] = {}
    if on_close:
        handlers["close"] = on_close
    return VNode(
        type="Toast",
        props={
            "message": message,
            "title": title,
            "alertType": type,
            "visible": visible,
            "icon": icon,
            "dismissible": dismissible,
            "autoHideMs": auto_hide_ms,
            "animated": animated,
            "animation": animation,
            "animationDelay": animation_delay,
        },
        event_handlers=handlers,
    )


def Timeline(
    items: List[Dict[str, Any]],
    title: Optional[str] = None,
    animated: bool = False,
    animation: Optional[str] = None,
    animation_delay: Optional[float] = None,
) -> VNode:
    return VNode(type="Timeline", props={"items": items, "title": title, "animated": animated, "animation": animation, "animationDelay": animation_delay})


def Image(
    src: str,
    alt: str = "",
    width: str = "100%",
    height: str = "auto",
    fit: Literal["cover", "contain", "fill", "none", "scale-down"] = "cover",
    caption: Optional[str] = None,
    radius: str = "var(--radius-lg)",
    loading: Literal["lazy", "eager"] = "lazy",
    variant: Literal["content", "inline", "avatar"] = "content",
    inline: bool = False,
    animated: bool = False,
    animation: Optional[str] = None,
    animation_delay: Optional[float] = None,
) -> VNode:
    return VNode(
        type="Image",
        props={
            "src": src,
            "alt": alt,
            "width": width,
            "height": height,
            "fit": fit,
            "caption": caption,
            "radius": radius,
            "loadingMode": loading,
            "variant": "inline" if inline else variant,
            "animated": animated,
            "animation": animation,
            "animationDelay": animation_delay,
        },
    )


def Video(
    src: str,
    poster: Optional[str] = None,
    width: str = "100%",
    height: str = "auto",
    caption: Optional[str] = None,
    radius: str = "var(--radius-lg)",
    controls: bool = True,
    autoplay: bool = False,
    loop: bool = False,
    muted: bool = False,
    animated: bool = False,
    animation: Optional[str] = None,
    animation_delay: Optional[float] = None,
) -> VNode:
    return VNode(
        type="Video",
        props={
            "src": src,
            "poster": poster,
            "width": width,
            "height": height,
            "caption": caption,
            "radius": radius,
            "controls": controls,
            "autoplay": autoplay,
            "loop": loop,
            "muted": muted,
            "animated": animated,
            "animation": animation,
            "animationDelay": animation_delay,
        },
    )


def SparklineStat(
    label: str,
    value: str,
    data: List[Dict[str, Any]],
    x_key: str,
    y_key: str,
    delta: Optional[str] = None,
    delta_type: Literal["increase", "decrease", "neutral"] = "neutral",
    color: Optional[str] = None,
) -> VNode:
    return VNode(
        type="SparklineStat",
        props={
            "label": label,
            "value": value,
            "data": data,
            "xKey": x_key,
            "yKey": y_key,
            "delta": delta,
            "deltaType": delta_type,
            "color": color,
        },
    )


def Hero(
    title: str,
    subtitle: Optional[str] = None,
    eyebrow: Optional[str] = None,
    tagline: Optional[str] = None,
    image: Optional[str] = None,
    image_alt: str = "",
    actions: Optional[List[VNode]] = None,
    badges: Optional[List[VNode]] = None,
    visual: Optional[VNode] = None,
    animated: bool = True,
    animation: Optional[str] = "fade-up",
    animation_delay: Optional[float] = None,
) -> VNode:
    """Premium landing/dashboard hero section."""
    return VNode(
        type="Hero",
        props={
            "title": title,
            "subtitle": subtitle,
            "eyebrow": eyebrow,
            "tagline": tagline,
            "image": image,
            "imageAlt": image_alt,
            "actions": actions or [],
            "badges": badges or [],
            "animated": animated,
            "animation": animation,
            "animationDelay": animation_delay,
        },
        children=[visual] if visual else [],
    )


def Embed(
    src: str,
    title: str = "Embedded content",
    height: str = "420px",
    allow_fullscreen: bool = True,
    loading: Literal["lazy", "eager"] = "lazy",
    sandbox: Optional[str] = None,
    radius: str = "var(--radius-lg)",
    animated: bool = False,
    animation: Optional[str] = None,
    animation_delay: Optional[float] = None,
) -> VNode:
    return VNode(
        type="Embed",
        props={
            "src": src,
            "title": title,
            "height": height,
            "allowFullscreen": allow_fullscreen,
            "loadingMode": loading,
            "sandbox": sandbox,
            "radius": radius,
            "animated": animated,
            "animation": animation,
            "animationDelay": animation_delay,
        },
    )


def SectionHeader(
    title: str,
    subtitle: Optional[str] = None,
    actions: Optional[List[VNode]] = None,
    eyebrow: Optional[str] = None,
    animated: bool = False,
    animation: Optional[str] = None,
    animation_delay: Optional[float] = None,
) -> VNode:
    """Reusable section title with optional actions."""
    return VNode(
        type="SectionHeader",
        props={"title": title, "subtitle": subtitle, "actions": actions or [], "eyebrow": eyebrow, "animated": animated, "animation": animation, "animationDelay": animation_delay},
    )


def StatusStrip(
    items: List[Dict[str, Any]],
    title: Optional[str] = None,
    columns: int = 4,
    animated: bool = False,
    animation: Optional[str] = None,
    animation_delay: Optional[float] = None,
) -> VNode:
    """Compact signal cards for health, freshness, latency, SLA, and cost."""
    return VNode(type="StatusStrip", props={"items": items, "title": title, "columns": columns, "animated": animated, "animation": animation, "animationDelay": animation_delay})


def Stepper(
    steps: List[Dict[str, Any]],
    active: int = 0,
    orientation: Literal["horizontal", "vertical"] = "horizontal",
    animated: bool = False,
    animation: Optional[str] = None,
    animation_delay: Optional[float] = None,
) -> VNode:
    """Process stepper for setup, deployments, releases, and approvals."""
    return VNode(type="Stepper", props={"steps": steps, "active": active, "orientation": orientation, "animated": animated, "animation": animation, "animationDelay": animation_delay})


def KanbanBoard(
    columns: List[Dict[str, Any]],
    on_card_click: Optional[Callable[[Dict[str, Any]], None]] = None,
    animated: bool = False,
    animation: Optional[str] = None,
    animation_delay: Optional[float] = None,
) -> VNode:
    """Kanban board for work queues, triage boards, or pipeline issues."""
    handlers: Dict[str, EventHandler] = {}
    if on_card_click:
        handlers["cardClick"] = on_card_click
    return VNode(type="KanbanBoard", props={"columns": columns, "animated": animated, "animation": animation, "animationDelay": animation_delay}, event_handlers=handlers)


def ChatMessage(
    role: Literal["user", "assistant", "system", "tool"],
    content: str,
    name: Optional[str] = None,
    timestamp: Optional[str] = None,
    avatar: Optional[str] = None,
    tone: Literal["default", "success", "warning", "error", "info"] = "default",
    animated: bool = False,
    animation: Optional[str] = None,
    animation_delay: Optional[float] = None,
) -> VNode:
    """Single chat transcript message for assistant/copilot style apps."""
    return VNode(
        type="ChatMessage",
        props={
            "role": role,
            "content": content,
            "name": name,
            "timestamp": timestamp,
            "avatar": avatar,
            "tone": tone,
            "animated": animated,
            "animation": animation,
            "animationDelay": animation_delay,
        },
    )


def ChatInput(
    name: str = "message",
    value: str = "",
    placeholder: str = "Ask a question",
    on_change: Optional[Callable[[str], None]] = None,
    on_submit: Optional[Callable[[str], None]] = None,
    disabled: bool = False,
    loading: bool = False,
    submit_label: str = "Send",
    debounce_ms: int = 180,
    change_strategy: Literal["debounce", "immediate", "blur"] = "debounce",
    animated: bool = False,
    animation: Optional[str] = None,
    animation_delay: Optional[float] = None,
) -> VNode:
    """Controlled chat input with change and submit callbacks."""
    handlers: Dict[str, EventHandler] = {}
    if on_change:
        handlers["change"] = on_change
    if on_submit:
        handlers["submit"] = on_submit
    return VNode(
        type="ChatInput",
        props={
            "name": name,
            "value": value,
            "placeholder": placeholder,
            "disabled": disabled,
            "loading": loading,
            "submitLabel": submit_label,
            "debounceMs": debounce_ms,
            "changeStrategy": change_strategy,
            "animated": animated,
            "animation": animation,
            "animationDelay": animation_delay,
        },
        event_handlers=handlers,
    )


# ── Data Visualization ──────────────────────────────────────────────────────


def Plot(figure: Dict[str, Any]) -> VNode:
    """Renders a Plotly figure dict. Pass the result of plotly.graph_objects.Figure."""
    # Support both dict and plotly Figure objects
    if hasattr(figure, "to_json"):
        import json
        figure = json.loads(figure.to_json())  # type: ignore
    return VNode(type="Plot", props={"figure": figure})


def AreaChart(
    data: List[Dict[str, Any]],
    x_key: str,
    y_keys: List[str],
    title: Optional[str] = None,
    colors: Optional[List[str]] = None,
    height: int = 300,
    loading: bool = False,
    empty_message: str = "No chart data available",
    on_click: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> VNode:
    handlers: Dict[str, EventHandler] = {}
    if on_click:
        handlers["click"] = on_click
    return VNode(type="AreaChart", props={"data": data, "xKey": x_key, "yKeys": y_keys, "title": title, "colors": colors, "height": height, "loading": loading, "emptyMessage": empty_message}, event_handlers=handlers)


def BarChart(
    data: List[Dict[str, Any]],
    x_key: str,
    y_keys: List[str],
    title: Optional[str] = None,
    colors: Optional[List[str]] = None,
    horizontal: bool = False,
    height: int = 300,
    loading: bool = False,
    empty_message: str = "No chart data available",
    on_click: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> VNode:
    handlers: Dict[str, EventHandler] = {}
    if on_click:
        handlers["click"] = on_click
    return VNode(type="BarChart", props={"data": data, "xKey": x_key, "yKeys": y_keys, "title": title, "colors": colors, "horizontal": horizontal, "height": height, "loading": loading, "emptyMessage": empty_message}, event_handlers=handlers)


def LineChart(
    data: List[Dict[str, Any]],
    x_key: str,
    y_keys: List[str],
    title: Optional[str] = None,
    colors: Optional[List[str]] = None,
    height: int = 300,
    loading: bool = False,
    empty_message: str = "No chart data available",
    on_click: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> VNode:
    handlers: Dict[str, EventHandler] = {}
    if on_click:
        handlers["click"] = on_click
    return VNode(type="LineChart", props={"data": data, "xKey": x_key, "yKeys": y_keys, "title": title, "colors": colors, "height": height, "loading": loading, "emptyMessage": empty_message}, event_handlers=handlers)


def DonutChart(
    data: List[Dict[str, str | float]],
    value_key: str = "value",
    label_key: str = "label",
    title: Optional[str] = None,
    height: int = 300,
    loading: bool = False,
    empty_message: str = "No chart data available",
    on_click: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> VNode:
    handlers: Dict[str, EventHandler] = {}
    if on_click:
        handlers["click"] = on_click
    return VNode(type="DonutChart", props={"data": data, "valueKey": value_key, "labelKey": label_key, "title": title, "height": height, "loading": loading, "emptyMessage": empty_message}, event_handlers=handlers)


def ScatterChart(
    data: List[Dict[str, Any]],
    x_key: str,
    y_key: str,
    title: Optional[str] = None,
    group_key: Optional[str] = None,
    color: Optional[str] = None,
    height: int = 300,
    loading: bool = False,
    empty_message: str = "No chart data available",
    on_click: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> VNode:
    """Scatter plot for correlation, anomaly, and cluster views."""
    handlers: Dict[str, EventHandler] = {}
    if on_click:
        handlers["click"] = on_click
    return VNode(
        type="ScatterChart",
        props={
            "data": data,
            "xKey": x_key,
            "yKey": y_key,
            "groupKey": group_key,
            "title": title,
            "color": color,
            "height": height,
            "loading": loading,
            "emptyMessage": empty_message,
        },
        event_handlers=handlers,
    )


def ComposedChart(
    data: List[Dict[str, Any]],
    x_key: str,
    bar_keys: Optional[List[str]] = None,
    line_keys: Optional[List[str]] = None,
    area_keys: Optional[List[str]] = None,
    title: Optional[str] = None,
    colors: Optional[List[str]] = None,
    height: int = 320,
    loading: bool = False,
    empty_message: str = "No chart data available",
    on_click: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> VNode:
    """Mixed bar/line/area chart for throughput vs SLA, cost vs volume, etc."""
    handlers: Dict[str, EventHandler] = {}
    if on_click:
        handlers["click"] = on_click
    return VNode(
        type="ComposedChart",
        props={
            "data": data,
            "xKey": x_key,
            "barKeys": bar_keys or [],
            "lineKeys": line_keys or [],
            "areaKeys": area_keys or [],
            "title": title,
            "colors": colors,
            "height": height,
            "loading": loading,
            "emptyMessage": empty_message,
        },
        event_handlers=handlers,
    )


def GaugeChart(
    value: float,
    min: float = 0,
    max: float = 100,
    title: Optional[str] = None,
    label: Optional[str] = None,
    color: Optional[str] = None,
    height: int = 220,
) -> VNode:
    """Gauge for freshness, SLA, quality score, or reliability indicators."""
    return VNode(
        type="GaugeChart",
        props={"value": value, "min": min, "max": max, "title": title, "label": label, "color": color, "height": height},
    )


def RadarChart(
    data: List[Dict[str, Any]],
    angle_key: str,
    value_keys: List[str],
    title: Optional[str] = None,
    colors: Optional[List[str]] = None,
    height: int = 320,
    loading: bool = False,
    empty_message: str = "No chart data available",
) -> VNode:
    """Radar chart for scorecards and capability comparisons."""
    return VNode(
        type="RadarChart",
        props={
            "data": data,
            "angleKey": angle_key,
            "valueKeys": value_keys,
            "title": title,
            "colors": colors,
            "height": height,
            "loading": loading,
            "emptyMessage": empty_message,
        },
    )


def Heatmap(
    data: List[Dict[str, Any]],
    x_key: str,
    y_key: str,
    value_key: str,
    title: Optional[str] = None,
    color: Optional[str] = None,
    empty_message: str = "No heatmap data available",
    on_click: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> VNode:
    """Grid heatmap for freshness, failures, latency, and utilization."""
    handlers: Dict[str, EventHandler] = {}
    if on_click:
        handlers["click"] = on_click
    return VNode(
        type="Heatmap",
        props={
            "data": data,
            "xKey": x_key,
            "yKey": y_key,
            "valueKey": value_key,
            "title": title,
            "color": color,
            "emptyMessage": empty_message,
        },
        event_handlers=handlers,
    )


def FunnelChart(
    data: List[Dict[str, Any]],
    value_key: str = "value",
    label_key: str = "label",
    title: Optional[str] = None,
    colors: Optional[List[str]] = None,
    height: int = 300,
    loading: bool = False,
    empty_message: str = "No chart data available",
    on_click: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> VNode:
    """Funnel chart for conversion, quality gates, or pipeline stage drop-off."""
    handlers: Dict[str, EventHandler] = {}
    if on_click:
        handlers["click"] = on_click
    return VNode(
        type="FunnelChart",
        props={"data": data, "valueKey": value_key, "labelKey": label_key, "title": title, "colors": colors, "height": height, "loading": loading, "emptyMessage": empty_message},
        event_handlers=handlers,
    )


def TreeMap(
    data: List[Dict[str, Any]],
    value_key: str = "value",
    name_key: str = "name",
    title: Optional[str] = None,
    colors: Optional[List[str]] = None,
    height: int = 300,
    loading: bool = False,
    empty_message: str = "No chart data available",
    on_click: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> VNode:
    """Treemap for cost, storage, workload, or ownership breakdowns."""
    handlers: Dict[str, EventHandler] = {}
    if on_click:
        handlers["click"] = on_click
    return VNode(
        type="TreeMap",
        props={"data": data, "valueKey": value_key, "nameKey": name_key, "title": title, "colors": colors, "height": height, "loading": loading, "emptyMessage": empty_message},
        event_handlers=handlers,
    )


def PipelineGraph(
    nodes: List[Dict[str, Any]],
    edges: List[Dict[str, Any]],
    title: Optional[str] = None,
    layout: Literal["left-to-right", "top-to-bottom"] = "left-to-right",
    animated: bool = True,
    empty_message: str = "No pipeline nodes available",
    on_node_click: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> VNode:
    """
    Visual pipeline/DAG graph.

    nodes = [{"id": "bronze", "label": "Bronze", "status": "success", "layer": "bronze"}]
    edges = [{"from": "bronze", "to": "silver"}]
    """
    handlers: Dict[str, EventHandler] = {}
    if on_node_click:
        handlers["nodeClick"] = on_node_click
    return VNode(
        type="PipelineGraph",
        props={
            "nodes": nodes,
            "edges": edges,
            "title": title,
            "layout": layout,
            "animated": animated,
            "emptyMessage": empty_message,
        },
        event_handlers=handlers,
    )


# ── Forms ────────────────────────────────────────────────────────────────────


@contextmanager
def form(
    action: str,
    method: str = "POST",
    success_redirect: Optional[str] = None,
) -> Iterator[List[VNode]]:
    """
    Context manager that collects children and returns a Form VNode.

    Usage:
        with db.form("/api/submit", success_redirect="/dashboard") as f:
            f.append(db.Input(name="username", label="Username"))
            f.append(db.Button("Submit", html_type="submit"))
    """
    children: List[VNode] = []
    yield children
    # After context exits, return a Form VNode — but since we can't 'return' from a
    # context manager in Python, the form() must be assigned like a regular function.
    # Users should call form_node() below for more natural usage.


def Form(
    children: List[VNode],
    action: str,
    method: str = "POST",
    success_redirect: Optional[str] = None,
    reload_on_success: bool = False,
) -> VNode:
    """
    Wraps children in a form that posts JSON to `action`.
    Input/Select/Checkbox/Toggle components with `name` prop are serialized.
    """
    return VNode(
        type="Form",
        props={
            "action": action,
            "method": method,
            "successRedirect": success_redirect,
            "reloadOnSuccess": reload_on_success,
        },
        children=children,
    )


# ── Databricks-specific components ────────────────────────────────────────


def CatalogBrowser(
    on_select: Optional[Callable[[Dict[str, str]], None]] = None,
    selected: Optional[Dict[str, str]] = None,
    catalogs: Optional[List[Dict[str, Any]]] = None,
    loading: bool = False,
    error: Optional[str] = None,
    empty_message: str = "No catalogs available",
    disabled: bool = False,
) -> VNode:
    """
    Server-driven catalog/schema/table browser.

    Pass records returned by ``brickflowui.databricks.catalog_tree``. Selection
    callbacks receive a normalized record containing catalog, schema, and table.
    """
    handlers: Dict[str, EventHandler] = {}
    if on_select:
        handlers["select"] = on_select
    return VNode(
        type="CatalogBrowser",
        props={
            "catalogs": catalogs or [],
            "selected": selected or {},
            "loading": loading,
            "error": error,
            "emptyMessage": empty_message,
            "disabled": disabled,
        },
        event_handlers=handlers,
    )


def WarehouseSelector(
    on_select: Optional[Callable[[str], None]] = None,
    selected_id: Optional[str] = None,
    label: str = "SQL Warehouse",
    warehouses: Optional[List[Dict[str, Any]]] = None,
    loading: bool = False,
    error: Optional[str] = None,
    empty_message: str = "No warehouses available",
    disabled: bool = False,
) -> VNode:
    """Select from server-provided warehouses visible to the current principal."""
    handlers: Dict[str, EventHandler] = {}
    if on_select:
        handlers["select"] = on_select
    return VNode(
        type="WarehouseSelector",
        props={
            "warehouses": warehouses or [],
            "selectedId": selected_id,
            "label": label,
            "loading": loading,
            "error": error,
            "emptyMessage": empty_message,
            "disabled": disabled,
        },
        event_handlers=handlers,
    )


def JobTrigger(
    job_id: str,
    label: str = "Run Job",
    on_complete: Optional[Callable[[Dict[str, Any]], None]] = None,
    on_trigger: Optional[Callable[[Dict[str, Any]], None]] = None,
    status: Optional[str] = None,
    run_id: Optional[str] = None,
    loading: bool = False,
    error: Optional[str] = None,
    disabled: bool = False,
) -> VNode:
    """Server-driven Databricks job action with explicit run state."""
    handlers: Dict[str, EventHandler] = {}
    if on_trigger:
        handlers["trigger"] = on_trigger
    if on_complete:
        handlers["complete"] = on_complete
    return VNode(
        type="JobTrigger",
        props={
            "jobId": job_id,
            "label": label,
            "status": status,
            "runId": run_id,
            "loading": loading,
            "error": error,
            "disabled": disabled,
        },
        event_handlers=handlers,
    )
