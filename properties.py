"""Настройки аддона."""

import bpy
from bpy.props import (
    StringProperty, IntProperty, EnumProperty, FloatProperty, BoolProperty,
)


def update_lang(self, context):
    """Обновляет подсказки у кнопок (операторов)."""
    from .utils import t
    from . import operators
    lang = self.language

    operators.BAKOT_OT_fill_from_selection.bl_description = t(lang, "Активный = Low, второй выделенный = High", "Active = Low, second selected = High")
    operators.BAKOT_OT_unwrap_low_only.bl_description = t(lang, "Создаёт UV-развёртку для low-poly без запекания", "Creates UV unwrap for low-poly without baking")
    operators.BAKOT_OT_bake_high_to_low.bl_description = t(lang, "Запекает выбранную карту с high-poly на low-poly", "Bakes the selected map from high-poly to low-poly")

    if context and hasattr(context, "window_manager"):
        context.window_manager.tag_redraw()
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                area.tag_redraw()


class BAKOT_PG_settings(bpy.types.PropertyGroup):
    language: EnumProperty(
        name="Language",
        items=[
            ('EN', "English", "English language"),
            ('RU', "Русский", "Русский язык"),
        ],
        default='EN',
        update=update_lang,
    )

    high_name: StringProperty(name="High-poly", description="High-poly object | Объект High-poly")
    low_name: StringProperty(name="Low-poly", description="Low-poly object | Объект Low-poly")

    bake_type: EnumProperty(
        name="Map type",
        items=[
            ('DIFFUSE',     "Base Color (Diffuse)", "Base color"),
            ('NORMAL',      "Normal",      "Normal map"),
            ('AO',          "AO",          "Ambient Occlusion"),
            ('ROUGHNESS',   "Roughness",   "Roughness map"),
            ('METALLIC',    "Metallic",    "Metallic map"),
            ('EMIT',        "Height / Displacement (Emit)", "Height map via Emission"),
        ],
        default='DIFFUSE',
    )
    resolution: IntProperty(name="Resolution", default=2048, min=64, max=8192)

    use_gpu: BoolProperty(name="Use GPU", default=True, description="Use GPU (OptiX/CUDA) if available | Использовать GPU, если доступно")
    cage_extrusion: FloatProperty(name="Cage Extrusion", default=0.5, min=0.0, max=100.0, description="Cage extrusion distance | Расстояние вытягивания клетки")

    adaptive_margin: BoolProperty(name="Adaptive Margin", default=True, description="Auto-calculate margin based on resolution | Авто-подбор отступа по разрешению")
    margin: IntProperty(name="Margin (px)", default=4, min=0, max=64, description="Margin around UV islands | Отступ вокруг UV-островов")
    margin_type: EnumProperty(
        name="Margin Type",
        items=[('ADJACENT_FACES', "Adjacent Faces", ""), ('EXTEND', "Extend", "")],
        default='ADJACENT_FACES',
    )

    samples: IntProperty(name="Samples", default=8, min=1, max=1024, description="Render samples | Количество сэмплов")
    save_to_disk: BoolProperty(name="Save PNG to disk", default=True, description="Save baked image to disk | Сохранить текстуру на диск")
    use_clear: BoolProperty(name="Clear image before bake", default=True, description="Clear image before baking | Очищать изображение перед запеканием")
    auto_fix_selection: BoolProperty(name="Auto-fix selection", default=True, description="Fix object visibility | Автоисправление видимости")

    # --- Auto-UV ---
    auto_unwrap: BoolProperty(name="Auto-UV", default=True, description="Create UV automatically | Создать UV автоматически")
    unwrap_method: EnumProperty(
        name="UV Method",
        items=[('SMART_PROJECT', "Smart UV Project", ""), ('LIGHTMAP_PACK', "Lightmap Pack", ""), ('UNWRAP', "Unwrap", "")],
        default='SMART_PROJECT',
    )
    unwrap_margin: FloatProperty(name="Island margin", default=0.02, min=0.0, max=0.5, description="Island distance | Расстояние между островами")

    # --- Preflight checks ---
    auto_zero_metallic: BoolProperty(name="Auto-zero Metallic", default=True, description="Set Metallic=0 on high-poly | Обнулить Metallic у High-poly")
    auto_boost_cage: BoolProperty(name="Auto-boost Cage", default=True, description="Increase cage if too small | Увеличить Cage, если он слишком мал")
    auto_fix_normals: BoolProperty(name="Recalculate normals", default=True, description="Fix normals | Пересчитать нормали")
    run_preflight: BoolProperty(name="Show preflight report", default=True, description="Show warnings before baking | Показывать отчёт перед запуском")

    # --- Post-processing ---
    connect_after_bake: BoolProperty(name="Connect texture", default=True, description="Auto-connect to Principled BSDF | Автоподключение к нодам")
    align_nodes_after_bake: BoolProperty(name="Align nodes", default=True, description="Align shader nodes | Выровнять ноды")
