import bpy
from bpy.props import StringProperty, IntProperty, EnumProperty, FloatProperty, BoolProperty


# ============================================================
# ХРАНИЛИЩЕ НАСТРОЕК
# ============================================================
class BakeSettings(bpy.types.PropertyGroup):
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
            ('DISPLACEMENT',"Displacement","Карта высот"),
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

    # --- автопроверки ---
    auto_zero_metallic: BoolProperty(
        name="Автоматически обнулить Metallic",
        description="Временно ставит Metallic=0 у материалов high-poly (причина №1 чёрной текстуры)",
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
        description="Если включено — после проверки откроется окно с найденными проблемами",
        default=True,
    )