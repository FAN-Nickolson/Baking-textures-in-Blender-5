import bpy


# ============================================================
# ПАНЕЛЬ В N-SIDEBAR (3D Viewport)
# ============================================================
class BAKOT_PT_main_panel(bpy.types.Panel):
    """Главная панель аддона в боковой панели 3D Viewport."""
    bl_label = "Baking Textures"
    bl_idname = "BAKOT_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Baking"        # ← имя вкладки в Sidebar (N)

    def draw(self, context):
        layout = self.layout
        s = context.scene.bake_helper

        # --- Быстрый старт ---
        box = layout.box()
        box.label(text="Быстрый старт", icon='PLAY')
        col = box.column(align=True)
        col.operator(
            "bake_helper.quick",
            text="Запечь по выделению",
            icon='RESTRICT_SELECT_OFF',
        )
        col.operator(
            "bake_helper.settings",
            text="Открыть настройки…",
            icon='PREFERENCES',
        )

        # --- Текущие имена объектов ---
        layout.separator()
        col = layout.column(align=True)
        col.label(text="Объекты:")
        col.prop(s, "high_name", text="High")
        col.prop(s, "low_name",  text="Low")

        # --- Быстрые настройки ---
        layout.separator()
        col = layout.column(align=True)
        col.label(text="Параметры:")
        col.prop(s, "bake_type", text="")
        col.prop(s, "resolution")