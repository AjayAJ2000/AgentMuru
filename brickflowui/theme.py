import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Union


DEFAULT_THEME = {
    "style_preset": "modern",
    "default_mode": "light",
    "branding": {
        "title": "BrickflowUI App",
        "tagline": "React components. Python syntax.",
        "logo": None,
        "favicon": None,
        "show_theme_toggle": True,
    },
    "loading": {
        "title": "BrickflowUI",
        "message": "Connecting to runtime...",
        "subtitle": "Preparing the workspace runtime.",
        "animation": "spinner",
        "light": {},
        "dark": {},
    },
    "colors": {
        "primary": "#4361EE",
        "primary-hover": "#3650D8",
        "primary-light": "rgba(67, 97, 238, 0.12)",
        "bg": "#F8FAFC",
        "surface": "#FFFFFF",
        "surface-2": "#F1F5F9",
        "text": "#0F172A",
        "text-muted": "#475569",
        "text-subtle": "#94A3B8",
        "border": "#E2E8F0",
        "border-strong": "#CBD5E1",
        "success": "#15803D",
        "warning": "#B45309",
        "error": "#BE123C",
        "info": "#1D4ED8",
        "link": "#4361EE",
    },
    "surfaces": {
        "canvas": "#F8FAFC",
        "muted": "#F1F5F9",
        "overlay": "rgba(255, 255, 255, 0.84)",
        "card": "#F1F5F9",
        "hover": "#E2E8F0",
    },
    "typography": {
        "sans": "'Inter', 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        "heading": "'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        "mono": "'JetBrains Mono', 'Fira Code', Menlo, Monaco, monospace",
        "base-size": "15px",
    },
    "spacing": {
        "base": "4px",
    },
    "radius": {
        "sm": "4px",
        "md": "6px",
        "lg": "8px",
        "xl": "12px",
        "full": "9999px",
    },
    "shadows": {
        "sm": "0 1px 2px rgba(15, 23, 42, 0.05)",
        "md": "0 8px 24px rgba(15, 23, 42, 0.08)",
        "lg": "0 24px 48px rgba(15, 23, 42, 0.12)",
    },
    "motion": {
        "duration-fast": "140ms",
        "duration-normal": "220ms",
        "duration-slow": "360ms",
        "easing-standard": "cubic-bezier(0.2, 0.8, 0.2, 1)",
        "stagger-step": "40ms",
    },
    "modes": {
        "light": {},
        "dark": {
            "colors": {
                "primary": "#4361EE",
                "primary-hover": "#3650D8",
                "primary-light": "rgba(67, 97, 238, 0.18)",
                "bg": "#0A0F1E",
                "surface": "#0F172A",
                "surface-2": "#1E293B",
                "text": "#F1F5F9",
                "text-muted": "#94A3B8",
                "text-subtle": "#64748B",
                "border": "#1E293B",
                "border-strong": "#334155",
                "success": "#22C55E",
                "warning": "#F59E0B",
                "error": "#F43F5E",
                "info": "#3B82F6",
                "link": "#4361EE",
            },
            "surfaces": {
                "canvas": "#0A0F1E",
                "muted": "#111B2E",
                "overlay": "rgba(10, 15, 30, 0.84)",
                "card": "#1E293B",
                "hover": "#334155",
            },
            "shadows": {
                "sm": "0 0 0 1px rgba(51, 65, 85, 0.48)",
                "md": "0 0 0 1px rgba(51, 65, 85, 0.72)",
                "lg": "0 0 0 1px rgba(67, 97, 238, 0.12), 0 24px 48px rgba(2, 6, 23, 0.48)",
            },
        },
    },
}


THEME_PRESETS = {
    "modern": {},
    "executive": {
        "colors": {
            "primary": "#1D4ED8",
            "primary-hover": "#1E40AF",
            "primary-light": "rgba(29, 78, 216, 0.12)",
            "info": "#0F766E",
        },
        "surfaces": {
            "card": "#EEF2FF",
            "hover": "#DBEAFE",
        },
        "radius": {
            "lg": "16px",
            "xl": "22px",
        },
        "shadows": {
            "md": "0 16px 36px rgba(15, 23, 42, 0.08)",
            "lg": "0 28px 64px rgba(15, 23, 42, 0.12)",
        },
    },
    "bento": {
        "colors": {
            "primary": "#7C3AED",
            "primary-hover": "#6D28D9",
            "primary-light": "rgba(124, 58, 237, 0.14)",
            "info": "#0891B2",
        },
        "surfaces": {
            "card": "#F8FAFC",
            "hover": "#F1F5F9",
        },
        "radius": {
            "lg": "20px",
            "xl": "28px",
        },
        "shadows": {
            "md": "0 18px 40px rgba(15, 23, 42, 0.08)",
            "lg": "0 32px 72px rgba(15, 23, 42, 0.12)",
        },
    },
    "cyberpunk": {
        "colors": {
            "primary": "#22D3EE",
            "primary-hover": "#06B6D4",
            "primary-light": "rgba(34, 211, 238, 0.16)",
            "bg": "#050816",
            "surface": "#0B1223",
            "surface-2": "#111B33",
            "text": "#E0F2FE",
            "text-muted": "#7DD3FC",
            "border": "#1D4ED8",
            "warning": "#F59E0B",
            "error": "#F43F5E",
            "info": "#A855F7",
        },
        "surfaces": {
            "canvas": "#050816",
            "muted": "#091224",
            "overlay": "rgba(5, 8, 22, 0.88)",
            "card": "#0B1223",
            "hover": "#13213D",
        },
        "radius": {
            "md": "12px",
            "lg": "18px",
            "xl": "24px",
        },
        "shadows": {
            "sm": "0 0 0 1px rgba(34, 211, 238, 0.14)",
            "md": "0 0 0 1px rgba(34, 211, 238, 0.18), 0 18px 40px rgba(2, 6, 23, 0.45)",
            "lg": "0 0 0 1px rgba(168, 85, 247, 0.16), 0 28px 70px rgba(2, 6, 23, 0.58)",
        },
        "motion": {
            "duration-fast": "120ms",
            "duration-normal": "180ms",
            "duration-slow": "300ms",
        },
    },
    "minimal": {
        "colors": {
            "primary": "#111827",
            "primary-hover": "#030712",
            "primary-light": "rgba(17, 24, 39, 0.08)",
            "info": "#2563EB",
        },
        "surfaces": {
            "card": "#FFFFFF",
            "hover": "#F8FAFC",
        },
        "radius": {
            "md": "10px",
            "lg": "14px",
            "xl": "18px",
        },
        "shadows": {
            "sm": "0 1px 2px rgba(15, 23, 42, 0.04)",
            "md": "0 10px 20px rgba(15, 23, 42, 0.06)",
            "lg": "0 20px 40px rgba(15, 23, 42, 0.08)",
        },
    },
}


_SECTION_ALIASES: Dict[str, str] = {
    "brand": "branding",
    "branding": "branding",
    "colors": "colors",
    "loading": "loading",
    "typography": "typography",
    "spacing": "spacing",
    "radius": "radius",
    "borders": "radius",
    "surfaces": "surfaces",
    "shadows": "shadows",
    "motion": "motion",
    "modes": "modes",
    "light_mode": "light_mode",
    "dark_mode": "dark_mode",
    "light": "light_mode",
    "dark": "dark_mode",
    "style_preset": "style_preset",
    "preset": "style_preset",
}

_KEY_ALIASES: Dict[str, Dict[str, str]] = {
    "branding": {
        "app_name": "title",
        "brand_name": "title",
        "name": "title",
        "brand_tagline": "tagline",
        "subtitle": "tagline",
        "theme_toggle": "show_theme_toggle",
    },
    "colors": {
        "primary_hover": "primary-hover",
        "primary_light": "primary-light",
        "background": "bg",
        "text_muted": "text-muted",
        "text_subtle": "text-subtle",
        "border_strong": "border-strong",
    },
    "typography": {
        "font_family": "sans",
        "font_heading": "heading",
        "font_mono": "mono",
        "base_size": "base-size",
    },
    "spacing": {
        "unit": "base",
    },
    "radius": {
        "radius": "md",
    },
    "surfaces": {
        "background": "canvas",
        "surface": "muted",
    },
    "shadows": {
        "small": "sm",
        "medium": "md",
        "large": "lg",
    },
    "motion": {
        "duration_fast": "duration-fast",
        "duration_normal": "duration-normal",
        "duration_slow": "duration-slow",
        "easing_standard": "easing-standard",
        "stagger_step": "stagger-step",
    },
}


def _canonical_section_name(value: object) -> str:
    section = str(value)
    return _SECTION_ALIASES.get(section, section)


def _deep_merge(base: Dict[str, Any], override: Mapping[str, Any]) -> Dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, Mapping) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


class Theme:
    def __init__(self, theme_config: Union[str, Path, Dict[str, Any], None] = None):
        self.config: Dict[str, Any] = deepcopy(DEFAULT_THEME)
        if theme_config:
            self.load(theme_config)

    def load(self, theme_config: Union[str, Path, Dict[str, Any]]):
        if isinstance(theme_config, (str, Path)):
            path = Path(theme_config)
            if not path.exists():
                raise FileNotFoundError(f"Theme file not found: {path}")

            ext = path.suffix.lower()
            with open(path, "r", encoding="utf-8") as f:
                if ext == ".json":
                    content = json.load(f)
                elif ext in (".yaml", ".yml"):
                    try:
                        import yaml  # type: ignore[import-untyped]
                    except ImportError as exc:
                        raise ImportError(
                            "PyYAML is required to load YAML themes. "
                            "Install it with: pip install PyYAML"
                        ) from exc
                    content = yaml.safe_load(f)
                else:
                    raise ValueError(f"Unsupported theme format: {ext}")
            self._merge(self._normalize_theme(content))
        elif isinstance(theme_config, dict):
            self._merge(self._normalize_theme(theme_config))

    def default_mode(self) -> str:
        mode = str(self.config.get("default_mode", "light")).lower()
        return mode if mode in {"light", "dark"} else "light"

    def style_preset(self) -> str:
        preset = str(self.config.get("style_preset", "modern")).lower()
        return preset if preset in THEME_PRESETS else "modern"

    def branding_value(self, key: str, default: Any = None) -> Any:
        return self.config.get("branding", {}).get(key, default)

    def _merge(self, new_config: Dict[str, Any]):
        self.config = _deep_merge(self.config, new_config)

    def _normalize_section_values(self, section: str, raw_values: Any) -> Any:
        if not isinstance(raw_values, dict):
            return raw_values

        section_aliases = _KEY_ALIASES.get(section, {})
        values = {
            section_aliases.get(raw_key, raw_key): raw_value
            for raw_key, raw_value in raw_values.items()
        }

        if section == "radius" and "md" in values and "lg" not in values:
            values = {**values, "lg": values["md"]}
        return values

    def _normalize_modes(self, raw_modes: Mapping[str, Any]) -> Dict[str, Any]:
        normalized_modes: Dict[str, Any] = {}
        for mode_name, mode_values in raw_modes.items():
            if not isinstance(mode_values, Mapping):
                continue
            normalized_mode: Dict[str, Any] = {}
            for section_name, section_values in mode_values.items():
                section = _canonical_section_name(section_name)
                normalized_mode[section] = self._normalize_section_values(section, section_values)
            normalized_modes[str(mode_name).lower()] = normalized_mode
        return normalized_modes

    def _normalize_theme(self, raw_config: Mapping[str, Any]) -> Dict[str, Any]:
        normalized: Dict[str, Any] = {}
        preset_name = raw_config.get("style_preset") or raw_config.get("preset")
        if isinstance(preset_name, str):
            preset = THEME_PRESETS.get(preset_name.strip().lower())
            if preset:
                normalized = _deep_merge(normalized, deepcopy(preset))
        for raw_section, raw_values in raw_config.items():
            section = _canonical_section_name(raw_section)

            if section == "modes" and isinstance(raw_values, Mapping):
                normalized["modes"] = self._normalize_modes(raw_values)
                continue

            if section in {"light_mode", "dark_mode"} and isinstance(raw_values, Mapping):
                modes = normalized.setdefault("modes", {})
                mode_name = "light" if section == "light_mode" else "dark"
                modes[mode_name] = {
                    _canonical_section_name(mode_section): self._normalize_section_values(
                        _canonical_section_name(mode_section),
                        mode_values,
                    )
                    for mode_section, mode_values in raw_values.items()
                }
                continue

            values = self._normalize_section_values(section, raw_values)

            if section in normalized and isinstance(normalized[section], dict) and isinstance(values, dict):
                normalized[section].update(values)
            else:
                normalized[section] = values
        return normalized

    def _resolved_mode_config(self, mode: Optional[str] = None) -> Dict[str, Any]:
        selected_mode = (mode or self.default_mode()).lower()
        mode_overrides = self.config.get("modes", {}).get(selected_mode, {})
        merged = deepcopy(self.config)
        merged.pop("modes", None)
        merged.pop("default_mode", None)
        return _deep_merge(merged, mode_overrides)

    def _css_block(self, selector: str, config: Mapping[str, Any]) -> str:
        lines = [f"{selector} {{"]

        for key, val in config.get("colors", {}).items():
            lines.append(f"  --db-{key}: {val};")

        for key, val in config.get("surfaces", {}).items():
            lines.append(f"  --db-surface-{key}: {val};")

        for key, val in config.get("typography", {}).items():
            lines.append(f"  --font-{key}: {val};")

        base_spacing = config.get("spacing", {}).get("base", "4px")
        lines.append(f"  --space-unit: {base_spacing};")
        for i in range(1, 13):
            lines.append(f"  --space-{i}: calc(var(--space-unit) * {i});")

        for key, val in config.get("radius", {}).items():
            lines.append(f"  --radius-{key}: {val};")

        for key, val in config.get("shadows", {}).items():
            lines.append(f"  --shadow-{key}: {val};")

        motion = config.get("motion", {})
        for key, val in motion.items():
            lines.append(f"  --motion-{key}: {val};")

        if "duration-normal" in motion:
            lines.append(f"  --transition-duration: {motion['duration-normal']};")
        if "easing-standard" in motion:
            lines.append(f"  --transition-easing: {motion['easing-standard']};")
        if "duration-normal" in motion and "easing-standard" in motion:
            lines.append("  --transition: var(--transition-duration) var(--transition-easing);")

        lines.append("}")
        return "\n".join(lines)

    def to_css_variables(self) -> str:
        default_mode = self.default_mode()
        blocks = [self._css_block(":root", self._resolved_mode_config(default_mode))]
        for mode_name in ("dark", "light"):
            if mode_name == default_mode:
                continue
            blocks.append(
                self._css_block(
                    f":root[data-theme-mode='{mode_name}']",
                    self._resolved_mode_config(mode_name),
                )
            )
        return "\n\n".join(blocks)
