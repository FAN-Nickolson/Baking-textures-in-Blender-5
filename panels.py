"""Панель в N-сайдбаре и пункт в меню Object."""

import bpy
from .utils import t


class BAKOT_PT_panel(bpy.types.Panel):
    bl_label = "Bake Helper"
    bl_idname = "BAKOT_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake"

    def draw(self, context):
        layout = self.layout
        s = context.scene.bake_helper  # type: ignore[attr-defined]
        lang = s.language

        # --- Язык ---
        layout.prop(s, "language", text="")

        # --- Объекты ---
        box = layout.box()
        box.label(text=t(lang, "Объекты:", "Objects:"), icon='OBJECT_DATA')
        box.prop(s, "high_name", text=t(lang, "High-poly объект", "High-poly object"))
        box.prop(s, "low_name", text=t(lang, "Low-poly объект", "Low-poly object"))
        box.operator(
            "bake_helper.fill_from_selection",
            text=t(lang, "Взять из выделения", "Take from selection"),
            icon='RESTRICT_SELECT_OFF',
        )

        # --- UV ---
        box = layout.box()
        box.label(text=t(lang, "UV low-poly:", "UV low-poly:"), icon='UV')
        box.prop(s, "auto_unwrap", text=t(lang, "Авто-UV", "Auto-UV"))
        col = box.column(align=True)
        col.enabled = s.auto_unwrap
        col.prop(s, "unwrap_method", text=t(lang, "Метод UV", "UV Method"))
        col.prop(s, "unwrap_margin", text=t(lang, "Отступ островов", "Island margin"))
        row = box.row()
        row.enabled = bool(s.low_name)
        row.operator(
            "bake_helper.unwrap_low_only",
            text=t(lang, "Сделать UV сейчас", "Make UV now"),
            icon='MOD_UVPROJECT',
        )

        # --- Запекание ---
        box = layout.box()
        box.label(text=t(lang, "Запекание:", "Baking:"), icon='RENDER_STILL')
        box.prop(s, "bake_type", text=t(lang, "Тип карты", "Map type"))
        box.prop(s, "resolution", text=t(lang, "Разрешение", "Resolution"))
        box.prop(s, "cage_extrusion", text=t(lang, "Cage Extrusion", "Cage Extrusion"))

        col = box.column(align=True)
        col.label(text=t(lang, "Отступы (Margin):", "Margins:"))
        col.prop(s, "margin", text=t(lang, "Margin (px)", "Margin (px)"))
        col.prop(s, "margin_type", text=t(lang, "Margin Type", "Margin Type"))

        box.prop(s, "samples", text=t(lang, "Сэмплы (Samples)", "Samples"))
        box.prop(s, "connect_after_bake", text=t(lang, "Подключить текстуру", "Connect texture"))
        box.prop(s, "align_nodes_after_bake", text=t(lang, "Выровнять ноды", "Align nodes"))

        # --- Автопроверки ---
        box = layout.box()
        box.label(text=t(lang, "Автопроверки:", "Preflight checks:"), icon='CHECKMARK')
        col = box.column(align=True)
        col.prop(s, "auto_fix_selection", text=t(lang, "Исправлять выделение", "Fix selection"))
        col.prop(s, "auto_zero_metallic", text=t(lang, "Обнулять Metallic", "Zero Metallic"))
        col.prop(s, "auto_boost_cage", text=t(lang, "Подбирать Cage", "Boost Cage"))
        col.prop(s, "auto_fix_normals", text=t(lang, "Считать нормали", "Fix normals"))
        col.prop(s, "run_preflight", text=t(lang, "Показывать отчёт", "Show report"))

        # --- Сохранение ---
        layout.prop(s, "save_to_disk", text=t(lang, "Сохранить PNG на диск", "Save PNG to disk"))

        # --- Кнопка запуска ---
        layout.separator()
        row = layout.row()
        row.scale_y = 1.5
        row.operator(
            "bake_helper.bake_high_to_low",
            text=t(lang, "ЗАПЕЧЬ", "BAKE"),
            icon='RENDER_STILL',
        )


def menu_object_bake_helper(self, context):
    self.layout.separator()
    self.layout.operator(
        "bake_helper.bake_high_to_low",
        text="Bake High → Low (Bake Helper)",
        icon='RENDER_STILL',
    )
