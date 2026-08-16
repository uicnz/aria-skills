# aria.yaml Fields

`agents/aria.yaml` contains Aria-specific interface metadata. It is machine-facing configuration rather than agent instructions.

## Complete Interface Example

```yaml
interface:
  displayName: "Skill Name"
  shortDescription: "Create and update specialized workflows"
  iconSmall: "./assets/skill-name.svg"
  iconLarge: "./assets/skill-name.png"
  brandColor: "#000000"
  defaultPrompt: "Use $skill-name to handle this task."
```

## Requirements

- Quote every string value and keep keys unquoted.
- Use camelCase field names.
- Keep `displayName` human-readable and concise; prefer two words when natural and unambiguous.
- Keep `shortDescription` between 25 and 64 characters.
- Set `iconSmall` to `./assets/<skill-name>.svg`.
- Set `iconLarge` to `./assets/<skill-name>.png`.
- Source the finished icon from `<skills-root>/_assets/svg/`, exclude filenames containing `legacy`, and record the approved source inside the SVG.
- Include the exact `$skill-name` invocation token in `defaultPrompt`.
- Include `brandColor` only when a deliberate brand color is established.

## Field Meanings

- `displayName`: Title shown in Aria's skill interface.
- `shortDescription`: Short UI summary for quick scanning.
- `iconSmall`: Relative path to the SVG icon.
- `iconLarge`: Relative path to the PNG icon.
- `brandColor`: Optional hexadecimal UI accent color.
- `defaultPrompt`: Short example prompt used to invoke the skill.

Regenerate this file after changing the skill name, display title, icon filenames, or default invocation prompt.
