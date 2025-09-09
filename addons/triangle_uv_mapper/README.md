# Triangle UV Mapper

Assign three UV coordinates (1:xy, 2:xy, 3:xy) to the vertices of a selected triangle (vertex A, vertex B, vertex C) and auto-rotate through 6 mappings.

<img width="2892" height="1834" alt="image" src="https://github.com/user-attachments/assets/c1f3c2fe-fc24-400d-a72f-27028fab2fe3" />

## Features
- Capture UVs from the selected triangle (A→1, B→2, C→3)
- Apply mapping and auto-advance (1→2→…→6→1)
- Minimal UI in the UV Editor (N-panel)

## Compatibility
- Blender: 4.2+
- Platforms: Windows, macOS, Linux
- Dependencies: none

## Quick Start
1. **Edit Mode**, select exactly one triangular face.
2. UV Editor → **N** → *Triangle UV Mapper*.
3. **Capture From Selected Triangle** to fill UV1/2/3.
4. **Apply Mapping** to assign and auto-rotate the mapping.

## Known Limitations
- Requires exactly one triangle selected.
- Uses the **active** UV map (creates one if missing).

## Authors
- ChatGPT × Greg Madison
