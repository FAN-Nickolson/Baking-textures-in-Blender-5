"""Панель в N-сайдбаре и пункт в меню Object."""

import bpy


class BAKOT_PT_panel(bpy.types.Panel):
    bl_label = "Bake Helper"
    bl_idname = "BAKOT_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake"

    def draw(self, context):
        layout = self.layout
        s = context.scene.bake_helper  # type: ignore[attr-defined]

        # --- Объекты ---
        box = layout.box()
        box.label(text="Объекты:", icon='OBJECT_DATA')
        box.prop(s, "high_name", text="High")
        box.prop(s, "low_name", text="Low")
        box.operator(
            "bake_helper.fill_from_selection",
            text="Взять из выделения",
            icon='RESTRICT_SELECT_OFF',
        )

        # --- UV ---
        box = layout.box()
        box.label(text="UV low-poly:", icon='UV')
        box.prop(s, "auto_unwrap")
        col = box.column(align=True)
        col.enabled = s.auto_unwrap
        col.prop(s, "unwrap_method")
        col.prop(s, "unwrap_margin")
        row = box.row()
        row.enabled = bool(s.low_name)
        row.operator(
            "bake_helper.unwrap_low_only",
            text="Сделать UV сейчас",
            icon='MOD_UVPROJECT',
        )

        # --- Запекание ---
        box = layout.box()
        box.label(text="Запекание:", icon='RENDER_STILL')
        box.prop(s, "bake_type")
        box.prop(s, "resolution")
        box.prop(s, "cage_extrusion")

        col = box.column(align=True)
        col.label(text="Отступы (Margin):")
        col.prop(s, "margin")
        col.prop(s, "margin_type")

        box.prop(s, "samples")
        box.prop(s, "connect_after_bake")

        # --- Автопроверки ---
        box = layout.box()
        box.label(text="Автопроверки:", icon='CHECKMARK')
        col = box.column(align=True)
        col.prop(s, "auto_fix_selection")
        col.prop(s, "auto_zero_metallic")
        col.prop(s, "auto_boost_cage")
        col.prop(s, "auto_fix_normals")
        col.prop(s, "run_preflight")

        # --- Сохранение ---
        layout.prop(s, "save_to_disk")

        # --- Кнопка запуска ---
        layout.separator()
        row = layout.row()
        row.scale_y = 1.5
        row.operator(
            "bake_helper.bake_high_to_low",
            text="ЗАПЕЧЬ",
            icon='RENDER_STILL',
        )


def menu_object_bake_helper(self, context):
    self.layout.separator()
    self.layout.operator(
        "bake_helper.bake_high_to_low",
        text="Запечь High → Low (Bake Helper)",
        icon='RENDER_STILL',
    )
