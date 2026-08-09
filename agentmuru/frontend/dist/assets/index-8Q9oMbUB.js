import { r as reactExports, j as jsxRuntimeExports, R as ReactDOM, a as React } from "./vendor-CNrsWy0A.js";
(function polyfill() {
  const relList = document.createElement("link").relList;
  if (relList && relList.supports && relList.supports("modulepreload")) return;
  for (const link of document.querySelectorAll('link[rel="modulepreload"]')) processPreload(link);
  new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      if (mutation.type !== "childList") continue;
      for (const node of mutation.addedNodes) if (node.tagName === "LINK" && node.rel === "modulepreload") processPreload(node);
    }
  }).observe(document, {
    childList: true,
    subtree: true
  });
  function getFetchOpts(link) {
    const fetchOpts = {};
    if (link.integrity) fetchOpts.integrity = link.integrity;
    if (link.referrerPolicy) fetchOpts.referrerPolicy = link.referrerPolicy;
    if (link.crossOrigin === "use-credentials") fetchOpts.credentials = "include";
    else if (link.crossOrigin === "anonymous") fetchOpts.credentials = "omit";
    else fetchOpts.credentials = "same-origin";
    return fetchOpts;
  }
  function processPreload(link) {
    if (link.ep) return;
    link.ep = true;
    const fetchOpts = getFetchOpts(link);
    fetch(link.href, fetchOpts);
  }
})();
const PROTOCOL_VERSION = 1;
class RuntimeClient {
  socket = null;
  reconnectTimer = null;
  closed = false;
  async json(url, init) {
    const response = await fetch(url, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers ?? {} }
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.detail ?? `Runtime request failed with ${response.status}`);
    }
    return response.json();
  }
  app() {
    return this.json("/api/v1/app");
  }
  async sessions() {
    const value = await this.json("/api/v1/sessions");
    return value.sessions.map((session) => ({
      id: session.id,
      title: session.title,
      updatedAt: session.updated_at,
      eventSequence: session.event_sequence
    }));
  }
  createSession(title) {
    return this.json("/api/v1/sessions", { method: "POST", body: JSON.stringify({ title }) });
  }
  session(id) {
    return this.json(`/api/v1/sessions/${encodeURIComponent(id)}`);
  }
  submit(sessionId, content) {
    return this.json(`/api/v1/sessions/${encodeURIComponent(sessionId)}/messages`, {
      method: "POST",
      body: JSON.stringify({ content, idempotency_key: crypto.randomUUID() })
    });
  }
  cancel(runId) {
    return this.json(`/api/v1/runs/${encodeURIComponent(runId)}/cancel`, { method: "POST" });
  }
  decide(approvalId, decision, reason) {
    return this.json(`/api/v1/approvals/${encodeURIComponent(approvalId)}`, {
      method: "PATCH",
      body: JSON.stringify({ decision, reason })
    });
  }
  connect(sessionId, after, onEvent, onState, onError) {
    this.disconnect();
    this.closed = false;
    let lastSequence = after;
    let attempts = 0;
    const open = () => {
      onState(attempts === 0 ? "connecting" : "reconnecting");
      const scheme = window.location.protocol === "https:" ? "wss" : "ws";
      const socket = new WebSocket(
        `${scheme}://${window.location.host}/api/v1/sessions/${encodeURIComponent(sessionId)}/stream?after=${lastSequence}`
      );
      this.socket = socket;
      socket.onopen = () => {
        attempts = 0;
        onState("connected");
      };
      socket.onmessage = (message) => {
        try {
          const envelope = JSON.parse(String(message.data));
          if (envelope.protocol_version !== PROTOCOL_VERSION) throw new Error("Unsupported runtime protocol");
          if (envelope.kind === "event") {
            const event = envelope.data;
            lastSequence = Math.max(lastSequence, event.sequence);
            onEvent(event);
          } else if (envelope.kind === "error") {
            onError(String(envelope.data.code ?? "Runtime stream error"));
          }
        } catch (error) {
          onError(error instanceof Error ? error.message : "Invalid runtime event");
        }
      };
      socket.onerror = () => socket.close();
      socket.onclose = () => {
        if (this.closed) return;
        attempts += 1;
        onState("reconnecting");
        const delay = Math.min(500 * 2 ** Math.min(attempts, 5), 1e4);
        this.reconnectTimer = window.setTimeout(open, delay);
      };
    };
    open();
    return () => this.disconnect();
  }
  disconnect() {
    this.closed = true;
    if (this.reconnectTimer !== null) window.clearTimeout(this.reconnectTimer);
    this.reconnectTimer = null;
    this.socket?.close();
    this.socket = null;
  }
}
function initialWorkspaceState(sessionId) {
  return {
    sessionId,
    title: null,
    messages: [],
    runs: {},
    activities: [],
    approvals: [],
    artifacts: [],
    spans: [],
    usage: { inputTokens: 0, outputTokens: 0, totalTokens: 0, cost: 0 },
    lastSequence: 0,
    protocolError: null
  };
}
function hydrateWorkspace(snapshot) {
  const state = initialWorkspaceState(snapshot.id);
  state.title = snapshot.title;
  state.lastSequence = snapshot.event_sequence;
  state.messages = snapshot.messages.map((message) => ({
    id: message.id,
    role: message.role,
    content: message.content,
    runId: null,
    name: message.name
  }));
  state.runs = Object.fromEntries(snapshot.runs.map((run) => [
    run.id,
    { id: run.id, agent: run.agent_name, status: run.status, errorCode: run.error_code }
  ]));
  state.artifacts = snapshot.artifacts.map((artifact) => ({
    id: artifact.id,
    runId: artifact.run_id,
    kind: artifact.kind,
    name: artifact.name,
    mimeType: artifact.mime_type,
    creator: artifact.creator
  }));
  state.approvals = snapshot.approvals.map((approval) => ({
    id: approval.id,
    runId: approval.run_id,
    toolCallId: "",
    toolName: approval.tool_name,
    arguments: approval.arguments,
    permission: approval.permission,
    risk: approval.risk,
    status: approval.status,
    reason: approval.reason
  }));
  return state;
}
function stringValue(value, fallback = "") {
  return typeof value === "string" ? value : fallback;
}
function numberValue(value) {
  return typeof value === "number" && Number.isFinite(value) ? value : 0;
}
function objectValue(value) {
  return value && typeof value === "object" && !Array.isArray(value) ? value : {};
}
function updateActivity(activities, id, update) {
  const index = activities.findIndex((activity) => activity.id === id);
  if (index === -1) {
    return [...activities, {
      id,
      runId: null,
      name: stringValue(update.name, "tool"),
      status: update.status ?? "requested",
      arguments: update.arguments ?? {},
      ...update
    }];
  }
  return activities.map((activity, position) => position === index ? { ...activity, ...update } : activity);
}
function reduceWorkspace(state, event) {
  if (event.session_id !== state.sessionId || event.sequence <= state.lastSequence) return state;
  const expected = state.lastSequence + 1;
  if (event.sequence !== expected) {
    return { ...state, protocolError: `Expected event sequence ${expected}, received ${event.sequence}` };
  }
  const next = { ...state, lastSequence: event.sequence, protocolError: null };
  const payload = event.payload;
  const runId = event.run_id;
  switch (event.type) {
    case "session.started":
      return { ...next, title: stringValue(payload.title) || state.title };
    case "user.message.received":
      return {
        ...next,
        messages: [...state.messages, {
          id: stringValue(payload.message_id, event.id),
          role: "user",
          content: stringValue(payload.content),
          runId
        }]
      };
    case "agent.started": {
      if (!runId) return next;
      return {
        ...next,
        runs: {
          ...state.runs,
          [runId]: { id: runId, agent: stringValue(payload.agent, "agent"), status: "running" }
        }
      };
    }
    case "model.token.delta": {
      if (!runId) return next;
      const draftId = `assistant-${runId}`;
      const existing = state.messages.find((message) => message.id === draftId);
      const messages = existing ? state.messages.map((message) => message.id === draftId ? { ...message, content: message.content + stringValue(payload.delta), streaming: true } : message) : [...state.messages, {
        id: draftId,
        role: "assistant",
        content: stringValue(payload.delta),
        runId,
        streaming: true
      }];
      return { ...next, messages };
    }
    case "assistant.message.completed": {
      const draftId = runId ? `assistant-${runId}` : "";
      const finalMessage = {
        id: stringValue(payload.message_id, event.id),
        role: "assistant",
        content: stringValue(payload.content),
        runId,
        streaming: false
      };
      const hasDraft = state.messages.some((message) => message.id === draftId);
      return {
        ...next,
        messages: hasDraft ? state.messages.map((message) => message.id === draftId ? finalMessage : message) : [...state.messages, finalMessage]
      };
    }
    case "tool.call.requested": {
      const id = stringValue(payload.tool_call_id, event.id);
      return {
        ...next,
        activities: updateActivity(state.activities, id, {
          id,
          runId,
          name: stringValue(payload.tool_name, "tool"),
          status: "requested",
          arguments: objectValue(payload.arguments)
        })
      };
    }
    case "tool.call.started":
    case "tool.call.completed":
    case "tool.call.failed": {
      const id = stringValue(payload.tool_call_id, event.id);
      const status = event.type.endsWith("started") ? "running" : event.type.endsWith("completed") ? "completed" : "failed";
      return {
        ...next,
        activities: updateActivity(state.activities, id, {
          runId,
          name: stringValue(payload.tool_name, "tool"),
          status,
          result: payload.result,
          errorCode: stringValue(payload.code) || void 0
        })
      };
    }
    case "approval.requested":
      return {
        ...next,
        approvals: [...state.approvals, {
          id: stringValue(payload.approval_id, event.id),
          runId: runId ?? "",
          toolCallId: stringValue(payload.tool_call_id),
          toolName: stringValue(payload.tool_name, "tool"),
          arguments: objectValue(payload.arguments),
          permission: stringValue(payload.permission) || null,
          risk: stringValue(payload.risk, "unknown"),
          status: "pending"
        }]
      };
    case "approval.granted":
    case "approval.rejected":
    case "approval.expired": {
      const approvalId = stringValue(payload.approval_id);
      const status = event.type.endsWith("granted") ? "approved" : event.type.endsWith("expired") ? "expired" : "rejected";
      return {
        ...next,
        approvals: state.approvals.map((approval) => approval.id === approvalId ? { ...approval, status, actor: stringValue(payload.actor), reason: stringValue(payload.reason) || null } : approval)
      };
    }
    case "artifact.created":
      return {
        ...next,
        artifacts: [...state.artifacts, {
          id: stringValue(payload.artifact_id, event.id),
          runId,
          kind: stringValue(payload.kind, "file"),
          name: stringValue(payload.name, "Artifact"),
          mimeType: stringValue(payload.mime_type, "application/octet-stream"),
          creator: stringValue(payload.creator, "agent")
        }]
      };
    case "trace.span.started":
      return {
        ...next,
        spans: [...state.spans, {
          id: stringValue(payload.span_id, event.id),
          parentId: event.parent_id,
          name: stringValue(payload.name, "span"),
          kind: stringValue(payload.kind, "runtime"),
          status: "running"
        }]
      };
    case "trace.span.completed": {
      const spanId = stringValue(payload.span_id);
      return {
        ...next,
        spans: state.spans.map((span) => span.id === spanId ? { ...span, status: stringValue(payload.status, "completed"), durationMs: numberValue(payload.duration_ms) } : span)
      };
    }
    case "usage.recorded":
      return {
        ...next,
        usage: {
          inputTokens: state.usage.inputTokens + numberValue(payload.input_tokens),
          outputTokens: state.usage.outputTokens + numberValue(payload.output_tokens),
          totalTokens: state.usage.totalTokens + numberValue(payload.total_tokens),
          cost: state.usage.cost + numberValue(payload.cost)
        }
      };
    case "run.completed":
    case "run.failed":
    case "run.cancelled": {
      if (!runId) return next;
      const status = event.type === "run.completed" ? "completed" : event.type === "run.failed" ? "failed" : "cancelled";
      return {
        ...next,
        runs: {
          ...state.runs,
          [runId]: {
            ...state.runs[runId] ?? { id: runId, agent: "agent" },
            status,
            errorCode: stringValue(payload.code) || void 0
          }
        }
      };
    }
    default:
      return next;
  }
}
const toKebabCase = (string) => string.replace(/([a-z0-9])([A-Z])/g, "$1-$2").toLowerCase();
const mergeClasses = (...classes) => classes.filter((className, index, array) => {
  return Boolean(className) && array.indexOf(className) === index;
}).join(" ");
var defaultAttributes = {
  xmlns: "http://www.w3.org/2000/svg",
  width: 24,
  height: 24,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 2,
  strokeLinecap: "round",
  strokeLinejoin: "round"
};
const Icon = reactExports.forwardRef(
  ({
    color = "currentColor",
    size = 24,
    strokeWidth = 2,
    absoluteStrokeWidth,
    className = "",
    children,
    iconNode,
    ...rest
  }, ref) => {
    return reactExports.createElement(
      "svg",
      {
        ref,
        ...defaultAttributes,
        width: size,
        height: size,
        stroke: color,
        strokeWidth: absoluteStrokeWidth ? Number(strokeWidth) * 24 / Number(size) : strokeWidth,
        className: mergeClasses("lucide", className),
        ...rest
      },
      [
        ...iconNode.map(([tag, attrs]) => reactExports.createElement(tag, attrs)),
        ...Array.isArray(children) ? children : [children]
      ]
    );
  }
);
const createLucideIcon = (iconName, iconNode) => {
  const Component = reactExports.forwardRef(
    ({ className, ...props }, ref) => reactExports.createElement(Icon, {
      ref,
      iconNode,
      className: mergeClasses(`lucide-${toKebabCase(iconName)}`, className),
      ...props
    })
  );
  Component.displayName = `${iconName}`;
  return Component;
};
const Activity = createLucideIcon("Activity", [
  [
    "path",
    {
      d: "M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2",
      key: "169zse"
    }
  ]
]);
const Archive = createLucideIcon("Archive", [
  ["rect", { width: "20", height: "5", x: "2", y: "3", rx: "1", key: "1wp1u1" }],
  ["path", { d: "M4 8v11a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8", key: "1s80jp" }],
  ["path", { d: "M10 12h4", key: "a56b0p" }]
]);
const Bot = createLucideIcon("Bot", [
  ["path", { d: "M12 8V4H8", key: "hb8ula" }],
  ["rect", { width: "16", height: "12", x: "4", y: "8", rx: "2", key: "enze0r" }],
  ["path", { d: "M2 14h2", key: "vft8re" }],
  ["path", { d: "M20 14h2", key: "4cs60a" }],
  ["path", { d: "M15 13v2", key: "1xurst" }],
  ["path", { d: "M9 13v2", key: "rq6x2g" }]
]);
const Braces = createLucideIcon("Braces", [
  [
    "path",
    { d: "M8 3H7a2 2 0 0 0-2 2v5a2 2 0 0 1-2 2 2 2 0 0 1 2 2v5c0 1.1.9 2 2 2h1", key: "ezmyqa" }
  ],
  [
    "path",
    {
      d: "M16 21h1a2 2 0 0 0 2-2v-5c0-1.1.9-2 2-2a2 2 0 0 1-2-2V5a2 2 0 0 0-2-2h-1",
      key: "e1hn23"
    }
  ]
]);
const Check = createLucideIcon("Check", [["path", { d: "M20 6 9 17l-5-5", key: "1gmf2c" }]]);
const CircleAlert = createLucideIcon("CircleAlert", [
  ["circle", { cx: "12", cy: "12", r: "10", key: "1mglay" }],
  ["line", { x1: "12", x2: "12", y1: "8", y2: "12", key: "1pkeuh" }],
  ["line", { x1: "12", x2: "12.01", y1: "16", y2: "16", key: "4dfq90" }]
]);
const CornerDownRight = createLucideIcon("CornerDownRight", [
  ["polyline", { points: "15 10 20 15 15 20", key: "1q7qjw" }],
  ["path", { d: "M4 4v7a4 4 0 0 0 4 4h12", key: "z08zvw" }]
]);
const FileCode2 = createLucideIcon("FileCode2", [
  ["path", { d: "M4 22h14a2 2 0 0 0 2-2V7l-5-5H6a2 2 0 0 0-2 2v4", key: "1pf5j1" }],
  ["path", { d: "M14 2v4a2 2 0 0 0 2 2h4", key: "tnqrlb" }],
  ["path", { d: "m5 12-3 3 3 3", key: "oke12k" }],
  ["path", { d: "m9 18 3-3-3-3", key: "112psh" }]
]);
const FileText = createLucideIcon("FileText", [
  ["path", { d: "M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z", key: "1rqfz7" }],
  ["path", { d: "M14 2v4a2 2 0 0 0 2 2h4", key: "tnqrlb" }],
  ["path", { d: "M10 9H8", key: "b1mrlr" }],
  ["path", { d: "M16 13H8", key: "t4e002" }],
  ["path", { d: "M16 17H8", key: "z1uh3a" }]
]);
const LoaderCircle = createLucideIcon("LoaderCircle", [
  ["path", { d: "M21 12a9 9 0 1 1-6.219-8.56", key: "13zald" }]
]);
const OctagonAlert = createLucideIcon("OctagonAlert", [
  ["path", { d: "M12 16h.01", key: "1drbdi" }],
  ["path", { d: "M12 8v4", key: "1got3b" }],
  [
    "path",
    {
      d: "M15.312 2a2 2 0 0 1 1.414.586l4.688 4.688A2 2 0 0 1 22 8.688v6.624a2 2 0 0 1-.586 1.414l-4.688 4.688a2 2 0 0 1-1.414.586H8.688a2 2 0 0 1-1.414-.586l-4.688-4.688A2 2 0 0 1 2 15.312V8.688a2 2 0 0 1 .586-1.414l4.688-4.688A2 2 0 0 1 8.688 2z",
      key: "1fd625"
    }
  ]
]);
const PlugZap = createLucideIcon("PlugZap", [
  [
    "path",
    { d: "M6.3 20.3a2.4 2.4 0 0 0 3.4 0L12 18l-6-6-2.3 2.3a2.4 2.4 0 0 0 0 3.4Z", key: "goz73y" }
  ],
  ["path", { d: "m2 22 3-3", key: "19mgm9" }],
  ["path", { d: "M7.5 13.5 10 11", key: "7xgeeb" }],
  ["path", { d: "M10.5 16.5 13 14", key: "10btkg" }],
  ["path", { d: "m18 3-4 4h6l-4 4", key: "16psg9" }]
]);
const Plus = createLucideIcon("Plus", [
  ["path", { d: "M5 12h14", key: "1ays0h" }],
  ["path", { d: "M12 5v14", key: "s699le" }]
]);
const Radio = createLucideIcon("Radio", [
  ["path", { d: "M4.9 19.1C1 15.2 1 8.8 4.9 4.9", key: "1vaf9d" }],
  ["path", { d: "M7.8 16.2c-2.3-2.3-2.3-6.1 0-8.5", key: "u1ii0m" }],
  ["circle", { cx: "12", cy: "12", r: "2", key: "1c9p78" }],
  ["path", { d: "M16.2 7.8c2.3 2.3 2.3 6.1 0 8.5", key: "1j5fej" }],
  ["path", { d: "M19.1 4.9C23 8.8 23 15.1 19.1 19", key: "10b0cb" }]
]);
const RotateCw = createLucideIcon("RotateCw", [
  ["path", { d: "M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8", key: "1p45f6" }],
  ["path", { d: "M21 3v5h-5", key: "1q7to0" }]
]);
const Send = createLucideIcon("Send", [
  [
    "path",
    {
      d: "M14.536 21.686a.5.5 0 0 0 .937-.024l6.5-19a.496.496 0 0 0-.635-.635l-19 6.5a.5.5 0 0 0-.024.937l7.93 3.18a2 2 0 0 1 1.112 1.11z",
      key: "1ffxy3"
    }
  ],
  ["path", { d: "m21.854 2.147-10.94 10.939", key: "12cjpa" }]
]);
const ShieldCheck = createLucideIcon("ShieldCheck", [
  [
    "path",
    {
      d: "M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z",
      key: "oel41y"
    }
  ],
  ["path", { d: "m9 12 2 2 4-4", key: "dzmm74" }]
]);
const Square = createLucideIcon("Square", [
  ["rect", { width: "18", height: "18", x: "3", y: "3", rx: "2", key: "afitv7" }]
]);
const Table2 = createLucideIcon("Table2", [
  [
    "path",
    {
      d: "M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2V9M9 21H5a2 2 0 0 1-2-2V9m0 0h18",
      key: "gugj83"
    }
  ]
]);
const UserRound = createLucideIcon("UserRound", [
  ["circle", { cx: "12", cy: "8", r: "5", key: "1hypcn" }],
  ["path", { d: "M20 21a8 8 0 0 0-16 0", key: "rfgkzh" }]
]);
const Wrench = createLucideIcon("Wrench", [
  [
    "path",
    {
      d: "M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z",
      key: "cbrjhi"
    }
  ]
]);
const X = createLucideIcon("X", [
  ["path", { d: "M18 6 6 18", key: "1bl5f8" }],
  ["path", { d: "m6 6 12 12", key: "d8bk6v" }]
]);
function ActivityCard({ activity }) {
  const Icon2 = activity.status === "completed" ? Check : activity.status === "failed" ? CircleAlert : activity.status === "running" ? LoaderCircle : Wrench;
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("article", { className: `muru-activity is-${activity.status}`, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "muru-activity-icon", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Icon2, { size: 15, "aria-hidden": "true" }) }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "muru-activity-body", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "muru-activity-heading", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: activity.name }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: activity.status })
      ] }),
      Object.keys(activity.arguments).length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsx("pre", { children: JSON.stringify(activity.arguments, null, 2) }),
      activity.errorCode && /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: "muru-inline-error", children: [
        "Error: ",
        activity.errorCode
      ] })
    ] })
  ] });
}
const icons = { json: Braces, code: FileCode2, table: Table2, markdown: FileText, report: FileText };
function ArtifactPanel({ artifacts }) {
  if (artifacts.length === 0) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "muru-panel-empty", children: "Artifacts created by agents will be collected here." });
  }
  return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "muru-artifact-list", children: artifacts.map((artifact) => {
    const Icon2 = icons[artifact.kind] ?? FileText;
    return /* @__PURE__ */ jsxRuntimeExports.jsxs("a", { href: `/api/v1/artifacts/${encodeURIComponent(artifact.id)}`, target: "_blank", rel: "noreferrer", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Icon2, { size: 16, "aria-hidden": "true" }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: artifact.name }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("small", { children: [
          artifact.kind,
          " by ",
          artifact.creator
        ] })
      ] })
    ] }, artifact.id);
  }) });
}
function ApprovalCard({ approval, onDecision }) {
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("article", { className: `muru-approval is-${approval.status}`, "aria-label": `Approval for ${approval.toolName}`, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("header", { children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "muru-approval-icon", children: /* @__PURE__ */ jsxRuntimeExports.jsx(OctagonAlert, { size: 17, "aria-hidden": "true" }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: "Human approval required" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("small", { children: approval.toolName })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: "muru-risk", children: [
        approval.risk,
        " risk"
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("dl", { children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("dt", { children: "Permission" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("dd", { children: approval.permission || "No permission declared" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("dt", { children: "Arguments" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("dd", { children: /* @__PURE__ */ jsxRuntimeExports.jsx("pre", { children: JSON.stringify(approval.arguments, null, 2) }) })
      ] })
    ] }),
    approval.status === "pending" ? /* @__PURE__ */ jsxRuntimeExports.jsxs("footer", { children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("button", { className: "muru-reject", type: "button", onClick: () => onDecision(approval.id, "reject"), children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(X, { size: 15 }),
        " Reject"
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("button", { className: "muru-approve", type: "button", onClick: () => onDecision(approval.id, "approve"), children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(ShieldCheck, { size: 15 }),
        " Approve once"
      ] })
    ] }) : /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: "muru-decision", children: [
      "Decision: ",
      approval.status
    ] })
  ] });
}
function Conversation({ messages, approvals, onApproval }) {
  if (messages.length === 0 && approvals.length === 0) {
    return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "muru-conversation-empty", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Bot, { size: 22, "aria-hidden": "true" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: "Ready for an objective" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: "Messages, tool activity, approvals, and artifacts will appear as the runtime emits them." })
    ] });
  }
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "muru-conversation", "aria-live": "polite", children: [
    messages.filter((message) => message.role !== "tool").map((message) => {
      const Icon2 = message.role === "user" ? UserRound : Bot;
      return /* @__PURE__ */ jsxRuntimeExports.jsxs("article", { className: `muru-message is-${message.role}`, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "muru-message-avatar", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Icon2, { size: 16, "aria-hidden": "true" }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("header", { children: [
            message.role === "user" ? "You" : "AgentMuru",
            message.streaming && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Streaming" })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: message.content })
        ] })
      ] }, message.id);
    }),
    approvals.map((approval) => /* @__PURE__ */ jsxRuntimeExports.jsx(ApprovalCard, { approval, onDecision: onApproval }, approval.id))
  ] });
}
function RunComposer({ disabled, running, onSubmit, onCancel }) {
  const [content, setContent] = reactExports.useState("");
  const submit = (event) => {
    event.preventDefault();
    const value = content.trim();
    if (!value || disabled) return;
    onSubmit(value);
    setContent("");
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("form", { className: "muru-composer", onSubmit: submit, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "muru-objective", children: "Give the agent an objective" }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        "textarea",
        {
          id: "muru-objective",
          value: content,
          onChange: (event) => setContent(event.target.value),
          placeholder: "Investigate the failed pipeline and prepare a remediation plan",
          rows: 2,
          disabled
        }
      ),
      running ? /* @__PURE__ */ jsxRuntimeExports.jsxs("button", { className: "muru-cancel", type: "button", onClick: onCancel, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Square, { size: 15 }),
        " Cancel run"
      ] }) : /* @__PURE__ */ jsxRuntimeExports.jsxs("button", { className: "muru-send", type: "submit", disabled: disabled || !content.trim(), children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Send, { size: 15 }),
        " Run"
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("small", { children: "Tool calls are visible. Risky actions pause for approval." })
  ] });
}
function SessionRail({ appName, sessions, selectedId, onCreate, onSelect }) {
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("aside", { className: "muru-session-rail", "aria-label": "Agent sessions", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("header", { className: "muru-brand", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "muru-brand-mark", "aria-hidden": "true", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Bot, { size: 18 }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: appName }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("small", { children: "Muru Workspace" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("button", { className: "muru-mobile-new", type: "button", onClick: onCreate, "aria-label": "New session", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Plus, { size: 17 }) })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("button", { className: "muru-primary-action", type: "button", onClick: onCreate, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Plus, { size: 16 }),
      " New session"
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("nav", { className: "muru-session-list", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "muru-section-label", children: "Sessions" }),
      sessions.length === 0 ? /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "muru-rail-empty", children: "No sessions yet. Start one when you are ready." }) : sessions.map((session) => /* @__PURE__ */ jsxRuntimeExports.jsxs(
        "button",
        {
          className: `muru-session-item ${selectedId === session.id ? "is-active" : ""}`,
          type: "button",
          onClick: () => onSelect(session.id),
          children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(Radio, { size: 14, "aria-hidden": "true" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: session.title || "Untitled session" })
          ]
        },
        session.id
      ))
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("footer", { className: "muru-rail-footer", children: "Runtime events are authoritative. Workspace state can be replayed." })
  ] });
}
function TracePanel({ spans, usage }) {
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "muru-trace-panel", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "muru-usage-grid", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("small", { children: "Input" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: usage.inputTokens })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("small", { children: "Output" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: usage.outputTokens })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("small", { children: "Total" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: usage.totalTokens })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("small", { children: "Cost" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: usage.cost ? `$${usage.cost.toFixed(4)}` : "n/a" })
      ] })
    ] }),
    spans.length === 0 ? /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "muru-panel-empty", children: "Trace spans become available as model and tool work executes." }) : /* @__PURE__ */ jsxRuntimeExports.jsx("ol", { className: "muru-span-list", children: spans.map((span) => /* @__PURE__ */ jsxRuntimeExports.jsxs("li", { children: [
      span.parentId ? /* @__PURE__ */ jsxRuntimeExports.jsx(CornerDownRight, { size: 14 }) : /* @__PURE__ */ jsxRuntimeExports.jsx(Activity, { size: 14 }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: span.name }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("small", { children: [
          span.kind,
          " · ",
          span.status
        ] })
      ] }),
      span.durationMs !== void 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("time", { children: [
        span.durationMs.toFixed(0),
        " ms"
      ] })
    ] }, span.id)) })
  ] });
}
function Workspace(props) {
  const [panel, setPanel] = reactExports.useState("artifacts");
  const activeRun = props.state ? Object.values(props.state.runs).find((run) => ["queued", "running", "waiting_approval"].includes(run.status)) : void 0;
  const interruptedRun = props.state ? Object.values(props.state.runs).find((run) => run.errorCode === "process_interrupted") : void 0;
  const connectionLabel = props.connection === "connected" ? "Runtime connected" : props.connection === "reconnecting" ? "Reconnecting" : props.connection;
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("main", { className: "muru-workspace", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx(
      SessionRail,
      {
        appName: props.appName,
        sessions: props.sessions,
        selectedId: props.state?.sessionId,
        onCreate: props.onCreateSession,
        onSelect: props.onSelectSession
      }
    ),
    !props.state ? /* @__PURE__ */ jsxRuntimeExports.jsxs("section", { className: "muru-empty-workspace", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "muru-empty-mark", children: /* @__PURE__ */ jsxRuntimeExports.jsx(PlugZap, { size: 24 }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("h1", { children: "Start an agent session" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: "Run an objective with streaming, governed tools, artifacts, and a replayable trace." }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("button", { className: "muru-primary-action", type: "button", onClick: props.onCreateSession, children: "New session" })
    ] }) : /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("section", { className: "muru-run-column", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("header", { className: "muru-run-header", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: `muru-connection is-${props.connection}`, children: [
              props.connection === "reconnecting" && /* @__PURE__ */ jsxRuntimeExports.jsx(RotateCw, { size: 12 }),
              connectionLabel
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("h1", { children: props.state.title || "Untitled session" })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "muru-run-state", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("small", { children: "Active run" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: activeRun ? `${activeRun.agent} · ${activeRun.status.replace("_", " ")}` : "Idle" })
          ] })
        ] }),
        (props.error || props.state.protocolError) && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "muru-error-banner", role: "alert", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(CircleAlert, { size: 16 }),
          props.error || props.state.protocolError
        ] }),
        interruptedRun && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "muru-recovery-banner", role: "status", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(CircleAlert, { size: 16 }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: "Previous process was interrupted." }),
            " Durable history is intact."
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "button",
            {
              type: "button",
              onClick: () => document.getElementById("muru-objective")?.focus(),
              children: "Start a new run"
            }
          )
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "muru-run-scroll", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            Conversation,
            {
              messages: props.state.messages,
              approvals: props.state.approvals,
              onApproval: props.onApproval
            }
          ),
          props.state.activities.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("section", { className: "muru-activity-section", "aria-label": "Tool activity", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { children: "Runtime activity" }),
            props.state.activities.map((activity) => /* @__PURE__ */ jsxRuntimeExports.jsx(ActivityCard, { activity }, activity.id))
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          RunComposer,
          {
            disabled: props.connection !== "connected",
            running: Boolean(activeRun),
            onSubmit: props.onSubmit,
            onCancel: () => activeRun && props.onCancel(activeRun.id)
          }
        )
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("aside", { className: "muru-context-panel", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "muru-panel-tabs", role: "tablist", "aria-label": "Run context", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("button", { type: "button", role: "tab", "aria-selected": panel === "artifacts", onClick: () => setPanel("artifacts"), children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(Archive, { size: 14 }),
            " Artifacts ",
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: props.state.artifacts.length })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("button", { type: "button", role: "tab", "aria-selected": panel === "trace", onClick: () => setPanel("trace"), children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(Activity, { size: 14 }),
            " Trace"
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "muru-panel-content", children: panel === "artifacts" ? /* @__PURE__ */ jsxRuntimeExports.jsx(ArtifactPanel, { artifacts: props.state.artifacts }) : /* @__PURE__ */ jsxRuntimeExports.jsx(TracePanel, { spans: props.state.spans, usage: props.state.usage }) })
      ] })
    ] })
  ] });
}
function App() {
  const clientRef = reactExports.useRef(null);
  if (clientRef.current === null) clientRef.current = new RuntimeClient();
  const client = clientRef.current;
  const [metadata, setMetadata] = reactExports.useState(null);
  const [sessions, setSessions] = reactExports.useState([]);
  const [selectedId, setSelectedId] = reactExports.useState(null);
  const [workspace, setWorkspace] = reactExports.useState(null);
  const [connection, setConnection] = reactExports.useState("offline");
  const [error, setError] = reactExports.useState(null);
  reactExports.useEffect(() => {
    let active = true;
    Promise.all([client.app(), client.sessions()]).then(([app, availableSessions]) => {
      if (!active) return;
      setMetadata(app);
      setSessions(availableSessions);
      if (availableSessions[0]) setSelectedId(availableSessions[0].id);
    }).catch((reason) => {
      if (!active) return;
      setConnection("error");
      setError(reason instanceof Error ? reason.message : "Unable to load AgentMuru");
    });
    return () => {
      active = false;
      client.disconnect();
    };
  }, [client]);
  reactExports.useEffect(() => {
    if (!selectedId) {
      setWorkspace(null);
      setConnection("offline");
      return;
    }
    let active = true;
    let disconnect = () => void 0;
    setConnection("connecting");
    setError(null);
    client.session(selectedId).then((snapshot) => {
      if (!active) return;
      const hydrated = hydrateWorkspace(snapshot);
      setWorkspace(hydrated);
      disconnect = client.connect(
        selectedId,
        hydrated.lastSequence,
        (event) => {
          setWorkspace((current) => current ? reduceWorkspace(current, event) : current);
          setSessions((current) => current.map((session) => session.id === event.session_id ? { ...session, eventSequence: event.sequence } : session));
        },
        setConnection,
        setError
      );
    }).catch((reason) => {
      if (!active) return;
      setConnection("error");
      setError(reason instanceof Error ? reason.message : "Unable to load session");
    });
    return () => {
      active = false;
      disconnect();
    };
  }, [client, selectedId]);
  const createSession = reactExports.useCallback(() => {
    setError(null);
    client.createSession(`Session ${sessions.length + 1}`).then((session) => {
      const summary = {
        id: session.id,
        title: session.title,
        updatedAt: session.updated_at,
        eventSequence: session.event_sequence
      };
      setSessions((current) => [summary, ...current]);
      setSelectedId(session.id);
    }).catch((reason) => setError(reason instanceof Error ? reason.message : "Unable to create session"));
  }, [client, sessions.length]);
  const submit = reactExports.useCallback((content) => {
    if (!selectedId) return;
    client.submit(selectedId, content).catch((reason) => setError(reason instanceof Error ? reason.message : "Unable to start run"));
  }, [client, selectedId]);
  const cancel = reactExports.useCallback((runId) => {
    client.cancel(runId).catch((reason) => setError(reason instanceof Error ? reason.message : "Unable to cancel run"));
  }, [client]);
  const decide = reactExports.useCallback((approvalId, decision) => {
    client.decide(approvalId, decision).catch((reason) => setError(reason instanceof Error ? reason.message : "Unable to record approval"));
  }, [client]);
  return /* @__PURE__ */ jsxRuntimeExports.jsx(
    Workspace,
    {
      appName: metadata?.title || "AgentMuru",
      sessions,
      state: workspace,
      connection,
      error,
      onCreateSession: createSession,
      onSelectSession: setSelectedId,
      onSubmit: submit,
      onCancel: cancel,
      onApproval: decide
    }
  );
}
ReactDOM.createRoot(document.getElementById("root")).render(
  /* @__PURE__ */ jsxRuntimeExports.jsx(React.StrictMode, { children: /* @__PURE__ */ jsxRuntimeExports.jsx(App, {}) })
);
//# sourceMappingURL=index-8Q9oMbUB.js.map
