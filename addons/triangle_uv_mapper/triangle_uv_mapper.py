bl_info = {
    "name": "Triangle UV Mapper (3-point assign, capture & auto-rotate)",
    "author": "ChatGPT × Greg Madison",
    "version": (1, 2, 0),
    "blender": (4, 2, 0),
    "location": "UV Editor > N-panel > Triangle UV Mapper",
    "description": "Capture UVs from a selected triangle, assign 3 UV coordinates with auto-rotating mappings (1..6).",
    "category": "UV",
}

import bpy
import bmesh
from bpy.props import (
    FloatVectorProperty,
    IntProperty,
)
from bpy.types import (
    Operator,
    Panel,
    PropertyGroup,
)


# -----------------------------
# Properties
# -----------------------------
class TRIUV_Props(PropertyGroup):
    # Three UV coordinate slots (defaults form an equilateral triangle)
    uv1: FloatVectorProperty(
        name="UV 1",
        description="UV coordinates for point 1",
        size=2,
        default=(0.0, 0.0),
        subtype='XYZ'
    )
    uv2: FloatVectorProperty(
        name="UV 2",
        description="UV coordinates for point 2",
        size=2,
        default=(0.5, 0.866),
        subtype='XYZ'
    )
    uv3: FloatVectorProperty(
        name="UV 3",
        description="UV coordinates for point 3",
        size=2,
        default=(1.0, 0.0),
        subtype='XYZ'
    )

    # Mapping index 1..6
    mapping_index: IntProperty(
        name="Mapping",
        description="Current mapping (1..6)",
        default=1,
        min=1,
        max=6
    )


# -----------------------------
# Core utilities
# -----------------------------
def get_edit_bmesh(context):
    """Get the active object's BMesh while in Edit Mode."""
    ob = context.object
    if not ob or ob.type != 'MESH':
        return None, None
    me = ob.data
    bm = bmesh.from_edit_mesh(me)
    return bm, me


def find_single_selected_triangle(bm):
    """Return the active or single selected triangular face, or None."""
    face = bm.faces.active
    if face and len(face.verts) == 3 and face.select:
        return face

    selected_tris = [f for f in bm.faces if f.select and len(f.verts) == 3]
    if len(selected_tris) == 1:
        return selected_tris[0]
    return None


def mapping_to_permutation(mapping_index):
    """Map 1..6 to permutations of (0,1,2) for UV1,UV2,UV3 -> A,B,C."""
    table = [
        (0, 1, 2),  # 1 - 1A, 2B, 3C
        (2, 0, 1),  # 2 - 1C, 2A, 3B
        (1, 2, 0),  # 3 - 1B, 2C, 3A
        (2, 1, 0),  # 4 - 1C, 2B, 3A
        (0, 2, 1),  # 5 - 1A, 2C, 3B
        (1, 0, 2),  # 6 - 1B, 2A, 3C
    ]
    idx = max(1, min(6, mapping_index)) - 1
    return table[idx]


# -----------------------------
# Operators
# -----------------------------
class TRIUV_OT_CaptureFromTriangle(Operator):
    """Capture UVs from the selected triangle (A,B,C loops) into UV1, UV2, UV3"""
    bl_idname = "triuv.capture_from_triangle"
    bl_label = "Capture From Selected Triangle"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.triuv_props
        bm, me = get_edit_bmesh(context)
        if bm is None:
            self.report({'ERROR'}, "No mesh object in Edit Mode.")
            return {'CANCELLED'}

        # Ensure UV layer exists
        uv_layer = bm.loops.layers.uv.active
        if uv_layer is None:
            uv_layer = bm.loops.layers.uv.verify()
            bmesh.update_edit_mesh(me, False, False)

        face = find_single_selected_triangle(bm)
        if face is None:
            self.report({'ERROR'}, "Select exactly one triangular face.")
            return {'CANCELLED'}

        if len(face.loops) != 3:
            self.report({'ERROR'}, "Selected face is not a triangle.")
            return {'CANCELLED'}

        # Read A,B, C (loops[0], loops[1], loops[2]) into UV1, UV2, UV3
        luvA = face.loops[0][uv_layer].uv
        luvB = face.loops[1][uv_layer].uv
        luvC = face.loops[2][uv_layer].uv

        props.uv1 = (float(luvA.x), float(luvA.y))
        props.uv2 = (float(luvB.x), float(luvB.y))
        props.uv3 = (float(luvC.x), float(luvC.y))

        # No need to update edit mesh (we only changed Scene props)
        self.report({'INFO'}, "Captured UVs into slots 1, 2, 3 (A→1, B→2, C→3).")
        return {'FINISHED'}


class TRIUV_OT_Apply(Operator):
    """Apply current mapping (UV1/2/3 -> A/B/C) and auto-rotate to next mapping"""
    bl_idname = "triuv.apply"
    bl_label = "Apply Mapping"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.triuv_props
        bm, me = get_edit_bmesh(context)
        if bm is None:
            self.report({'ERROR'}, "No mesh object in Edit Mode.")
            return {'CANCELLED'}

        uv_layer = bm.loops.layers.uv.active
        if uv_layer is None:
            uv_layer = bm.loops.layers.uv.verify()
            bmesh.update_edit_mesh(me, False, False)

        face = find_single_selected_triangle(bm)
        if face is None:
            self.report({'ERROR'}, "Select exactly one triangular face.")
            return {'CANCELLED'}

        if len(face.loops) != 3:
            self.report({'ERROR'}, "Selected face is not a triangle.")
            return {'CANCELLED'}

        uv_points = [props.uv1, props.uv2, props.uv3]
        perm = mapping_to_permutation(props.mapping_index)

        # Assign UVs to loops A,B,C according to current mapping
        for loop_idx, uv_src_idx in enumerate(perm):
            loop = face.loops[loop_idx]
            luv = loop[uv_layer]
            uv_src = uv_points[uv_src_idx]
            luv.uv.x = float(uv_src[0])
            luv.uv.y = float(uv_src[1])

        bmesh.update_edit_mesh(me, loop_triangles=False, destructive=False)

        # Auto-rotate mapping 1..6
        old = props.mapping_index
        props.mapping_index = 1 if props.mapping_index >= 6 else props.mapping_index + 1

        self.report({'INFO'}, f"Applied mapping #{old} and rotated to {props.mapping_index}.")
        return {'FINISHED'}


# -----------------------------
# UI Panel (UV Editor)
# -----------------------------
class TRIUV_PT_Panel(Panel):
    bl_label = "Triangle UV Mapper"
    bl_category = "Triangle UV Mapper"
    bl_space_type = 'IMAGE_EDITOR'    # UV/Image Editor
    bl_region_type = 'UI'             # N-panel
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        props = context.scene.triuv_props

        # --- New: capture button at the very top ---
        layout.operator("triuv.capture_from_triangle", icon="EYEDROPPER")

        layout.separator()

        # UV slots
        col = layout.column(align=True)
        col.label(text="UV Coordinates (1, 2, 3):")
        col.prop(props, "uv1", text="1")
        col.prop(props, "uv2", text="2")
        col.prop(props, "uv3", text="3")

        layout.separator()
        layout.label(text=f"Current Mapping: {props.mapping_index}")
        layout.operator("triuv.apply", icon="UV")


# -----------------------------
# Registration
# -----------------------------
classes = (
    TRIUV_Props,
    TRIUV_OT_CaptureFromTriangle,
    TRIUV_OT_Apply,
    TRIUV_PT_Panel,
)

def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.triuv_props = bpy.props.PointerProperty(type=TRIUV_Props)

def unregister():
    del bpy.types.Scene.triuv_props
    for c in reversed(classes):
        bpy.utils.unregister_class(c)

if __name__ == "__main__":
    register()
