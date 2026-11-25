"""Bake Helper: запекание текстур с high-poly на low-poly."""

bl_info = {
    "name": "Bake Helper: High → Low",
    "author": "Custom",
    "version": (1, 3, 0),
    "blender": (5, 0, 0),
    "location": "View3D > Sidebar > Bake | Object menu",
    "description": "Запекание текстур с high-poly на low-poly + авто-UV",
    "category": "Object",
}

import bpy  # noqa: E402
from bpy.app.handlers import persistent  # noqa: E402

from .properties import BAKOT_PG_settings, update_lang  # noqa: E402
from .operators import (  # noqa: E402
    BAKOT_OT_preflight_report,
    BAKOT_OT_bake_high_to_low,
    BAKOT_OT_unwrap_low_only,
    BAKOT_OT_fill_from_selection,
)
from .panels import BAKOT_PT_panel, menu_object_bake_helper  # noqa: E402


classes = (
    BAKOT_PG_settings,
    BAKOT_OT_preflight_report,
    BAKOT_OT_bake_high_to_low,
    BAKOT_OT_unwrap_low_only,
    BAKOT_OT_fill_from_selection,
    BAKOT_PT_panel,
)


@persistent
def load_bake_helper_lang(dummy):
    """Обновляет подсказки при загрузке .blend файла."""
    for scene in bpy.data.scenes:
        if hasattr(scene, "bake_helper"):
            update_lang(scene.bake_helper, bpy.context)


def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.bake_helper = bpy.props.PointerProperty(type=BAKOT_PG_settings)
    bpy.types.VIEW3D_MT_object.append(menu_object_bake_helper)

    # Добавляем обработчик для обновления подсказок при загрузке
    bpy.app.handlers.load_post.append(load_bake_helper_lang)

    # Первичная инициализация подсказок (при старте Blender)
    if bpy.context.scene and hasattr(bpy.context.scene, "bake_helper"):
        update_lang(bpy.context.scene.bake_helper, bpy.context)


def unregister():
    if load_bake_helper_lang in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(load_bake_helper_lang)

    bpy.types.VIEW3D_MT_object.remove(menu_object_bake_helper)
    if hasattr(bpy.types.Scene, "bake_helper"):
        del bpy.types.Scene.bake_helper
    for c in reversed(classes):
        try:
            bpy.utils.unregister_class(c)
        except Exception:
            pass


if __name__ == "__main__":
    register()
