import bpy


# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================
def _unhide_object_recursive(obj):
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
        _unhide_object_recursive(o)
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


def _find_object(name, expected_role):
    obj = bpy.data.objects.get(name)
    if obj is None:
        for o in bpy.data.objects:
            if o.name.lower() == name.lower().strip():
                print(f"[BAKE] Точное имя не найдено, использую '{o.name}' вместо '{name}'")
                return o
        raise ValueError(f"{expected_role} объект '{name}' не найден в файле")
    return obj


def _get_principled_bsdf(mat):
    if not mat or not mat.use_nodes:
        return None
    for node in mat.node_tree.nodes:
        if node.type == 'BSDF_PRINCIPLED':
            return node
    return None


def _get_socket(node, *names):
    for n in names:
        if n in node.inputs:
            return node.inputs[n]
    return None