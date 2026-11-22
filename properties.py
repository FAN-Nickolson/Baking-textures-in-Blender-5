"""Настройки аддона. Сохраняются в .blend через Scene.bake_helper."""

import bpy
from bpy.props import (
    StringProperty, IntProperty, EnumProperty, FloatProperty, BoolProperty,
)


class BAKOT_PG_settings(bpy.types.PropertyGroup):
    high_name: StringProperty(name="High-poly объект")
    low_name:  StringProperty(name="Low-poly объект")

    bake_type: EnumProperty(
        name="Тип карты",
        items=[
            ('DIFFUSE',     "Base Color (Diffuse)", "Цвет материала high-poly"),
            ('NORMAL',      "Normal",      "Карта нормалей"),
            ('AO',          "AO",          "Ambient Occlusion"),
            ('ROUGHNESS',   "Roughness",   "Шероховатость"),
            ('METALLIC',    "Metallic",    "Металличность"),
            ('EMIT',        "Emission",    "Emission"),
            ('DISPLACEMENT', "Displacement", "Карта высот"),
        ],
        default='DIFFUSE',
    )
    resolution: IntProperty(name="Разрешение", default=2048, min=64, max=8192)
    cage_extrusion: FloatProperty(name="Cage Extrusion", default=0.5, min=0.0, max=100.0)
    margin: IntProperty(name="Margin (px)", default=4, min=0, max=64)
    margin_type: EnumProperty(
        name="Margin Type",
        items=[
            ('ADJACENT_FACES', "Adjacent Faces",
             "Пиксели с соседних граней через UV-швы (меньше кровотечения)"),
            ('EXTEND', "Extend",
             "Растягивать крайние пиксели наружу (старый метод)"),
        ],
        default='ADJACENT_FACES',
    )
    samples: IntProperty(name="Samples", default=8, min=1, max=1024)
    save_to_disk: BoolProperty(name="Сохранить PNG на диск", default=True)
    auto_fix_selection: BoolProperty(name="Автоисправление выделения", default=True)

    # --- Авто-UV ---
    auto_unwrap: BoolProperty(
        name="Авто-UV для low-poly",
        description="Если у low-poly нет UV-развёртки — создать автоматически перед запеканием",
        default=True,
    )
    unwrap_method: EnumProperty(
        name="Метод UV",
        items=[
            ('SMART_PROJECT', "Smart UV Project",
             "Умная проекция по углам (рекомендуется для быстрого теста)"),
            ('LIGHTMAP_PACK', "Lightmap Pack",
             "Каждая грань — отдельный остров (максимум швов, для запекания)"),
            ('UNWRAP', "Unwrap (Angle Based)",
             "Стандартная развёртка (без швов даст плоский результат)"),
        ],
        default='SMART_PROJECT',
    )
    unwrap_margin: FloatProperty(
        name="Отступ островов",
        description="Расстояние между UV-островами после упаковки (0.001–0.1)",
        default=0.02, min=0.0, max=0.5,
    )

    # --- Автопроверки ---
    auto_zero_metallic: BoolProperty(
        name="Автоматически обнулить Metallic",
        description="Временно ставит Metallic=0 у материалов high-poly",
        default=True,
    )
    auto_boost_cage: BoolProperty(
        name="Авто-подбор Cage Extrusion",
        description="Если cage=0 или слишком мал — увеличивает до безопасного значения",
        default=True,
    )
    auto_fix_normals: BoolProperty(
        name="Пересчитать нормали",
        description="Принудительно пересчитывает нормали наружу на high и low",
        default=True,
    )
    run_preflight: BoolProperty(
        name="Показать отчёт предпроверки перед запуском",
        default=True,
    )
    connect_after_bake: BoolProperty(
    name="Подключить текстуру к материалу",
    description="Автоматически подключать Image Texture к нужному входу "
                "Principled BSDF в зависимости от типа карты",
    default=True,
)
