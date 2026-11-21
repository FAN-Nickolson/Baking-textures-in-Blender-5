"""Вспомогательные функции: поиск объектов, принудительное выделение, авто-UV."""

import bpy


def find_object(name, expected_role):
    """Ищет объект по имени, при неудаче — без учёта регистра и пробелов."""
    obj = bpy.data.objects.get(name)
    if obj is None:
        for o in bpy.data.objects:
            if o.name.lower() == name.lower().strip():
                print(f"[BAKE] Точное имя не найдено, использую '{o.name}' вместо '{name}'")
                return o
        raise ValueError(f"{expected_role} объект '{name}' не найден в файле")
    return obj


def unhide_object_recursive(obj):
    """Снимает скрытость с объекта и всех его родительских коллекций."""
    obj.hide_viewport = False
    obj.hide_set(False)
    obj.hide_select = False
    for coll in obj.users_collection:
        coll.hide_viewport = False
        coll.hide_select = False

    def walk_layer(layer_coll):
        for child in layer_coll.children:
            if obj.name in child.collection.objects:
                child.exclude = False
                child.hide_viewport = False
            walk_layer(child)

    walk_layer(bpy.context.view_layer.layer_collection)


def force_select(high_obj, low_obj, context):
    """Гарантированно выделяет high + low (low активный)."""
    vl = context.view_layer
    for o in (high_obj, low_obj):
        unhide_object_recursive(o)
        if o.name not in vl.objects:
            try:
                vl.link(o)
            except Exception:
                pass

    for o in vl.objects:
        o.select_set(False)
    vl.objects.active = None
    vl.update()

    high_obj.select_set(True)
    low_obj.select_set(True)
    vl.objects.active = low_obj

    selected = [o.name for o in context.selected_objects]
    active = vl.objects.active.name if vl.objects.active else None
    print(f"[BAKE] Выделено: {selected}  |  Активный: {active}")

    if high_obj.name not in selected:
        raise RuntimeError(f"Не удалось выделить high-poly '{high_obj.name}'")
    if low_obj.name not in selected:
        raise RuntimeError(f"Не удалось выделить low-poly '{low_obj.name}'")
    if active != low_obj.name:
        raise RuntimeError(f"Активным стал не low-poly, а '{active}'")
    return high_obj, low_obj


def ensure_uv_unwrap(obj, method='SMART_PROJECT', island_margin=0.02, context=None):
    """Создаёт UV-развёртку, если её нет. Возвращает (created: bool, message: str)."""
    if context is None:
        context = bpy.context

    if obj.data.uv_layers and len(obj.data.uv_layers) > 0:
        return (False, "UV уже существует")

    prev_active = context.view_layer.objects.active
    prev_selected = list(context.selected_objects)

    try:
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        context.view_layer.objects.active = obj

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')

        if method == 'SMART_PROJECT':
            bpy.ops.uv.smart_project(
                angle_limit=1.15192,
                island_margin=island_margin,
                area_weight=0.0,
                correct_aspect=True,
                scale_to_bounds=False,
            )
        elif method == 'LIGHTMAP_PACK':
            bpy.ops.uv.lightmap_pack(
                PREF_CONTEXT='ALL_FACES',
                PREF_MARGIN_DIV=island_margin,
            )
        elif method == 'UNWRAP':
            bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=island_margin)
        else:
            raise ValueError(f"Неизвестный метод: {method}")

        bpy.ops.uv.pack_islands(margin=island_margin)
        return (True, f"UV создан методом {method}")

    finally:
        try:
            if obj.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
        except Exception:
            pass
        try:
            bpy.ops.object.select_all(action='DESELECT')
            for o in prev_selected:
                if o.name in context.view_layer.objects:
                    o.select_set(True)
            if prev_active and prev_active.name in context.view_layer.objects:
                context.view_layer.objects.active = prev_active
        except Exception:
            pass