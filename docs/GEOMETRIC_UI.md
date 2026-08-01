# Design-Forward UI

BrickflowUI can build branded product surfaces without maintaining a separate frontend. Keep the design grounded in the supported component API and shared theme tokens so the result remains responsive and maintainable.

## Start From Maintained References

Run the [Component Studio](./EXAMPLES.md#component-studio) to inspect the maintained layout, media, motion, loading, modal, and responsive patterns:

```bash
python examples/component_studio/app.py
```

Use [Theming](./THEMING.md) for the current color, typography, spacing, radius, shadow, branding, and light/dark-mode token model. Those tokens are the stable basis for design-forward applications.

## Recommended Composition

Build the surface in this order:

1. Choose a coherent token palette and typography scale.
2. Establish the app shell and responsive navigation.
3. Give each page one clear visual hierarchy and primary action.
4. Compose with `Row`, `Column`, `Grid`, `Card`, `Hero`, and media components.
5. Add motion and custom `style` values selectively after the layout works at wide and narrow viewports.

Prefer reusable theme tokens over repeated inline values. Use `style` for the small number of art-directed details that are genuinely unique to a surface.

## Supported Product Patterns

The maintained components cover:

- rounded application shells and card surfaces
- image-led hero sections and local assets
- top navigation, sidebars, tabs, and action rows
- responsive grids and horizontally safe data regions
- branded loading states and light/dark themes
- interactive galleries, filters, and modal workflows through normal state hooks

For an end-to-end data product, follow the [Data Pipeline Command Center](./EXAMPLES.md#data-pipeline-command-center). For component-level exploration and visual QA, stay with the [Component Studio](./EXAMPLES.md#component-studio).
