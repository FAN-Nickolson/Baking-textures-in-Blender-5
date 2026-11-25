"""Предполётные проверки."""

import mathutils
from .utils import ensure_uv_unwrap


def get_principled_bsdf(mat):
    if not mat or not mat.use_nodes:
        return None
    for node in mat.node_tree.nodes:
        if node.type == 'BSDF_PRINCIPLED':
            return node
    return None


def get_socket(node, *names):
    for n in names:
        if n in node.inputs:
            return node.inputs[n]
    return None


def preflight_check(high_obj, low_obj, s, context):
    warnings = []
    fixes = []
    undo = []

    # 0. Авто-UV
    if s.auto_unwrap and not low_obj.data.uv_layers:
        try:
            created, msg = ensure_uv_unwrap(low_obj, s.unwrap_method, s.unwrap_margin, context)
            if created:
                fixes.append(f"✔ UV для '{low_obj.name}' создан")
        except Exception as e:
            warnings.append(f"⚠️ Не удалось создать UV: {e}")

    if not low_obj.data.uv_layers:
        warnings.append("❌ LOW-POLY: нет UV-развёртки.")
        return warnings, fixes, undo

    # №4: Multi-UV
    if len(low_obj.data.uv_layers) > 1:
        warnings.append(f"⚠️ У '{low_obj.name}' {len(low_obj.data.uv_layers)} UV-слоёв. Будет использован первый: '{low_obj.data.uv_layers[0].name}'.")

    # №7: Проверка на нулевые координаты UV
    uv_data = low_obj.data.uv_layers[0].data
    is_empty = True
    for i in range(0, min(len(uv_data), 100)):
        if uv_data[i].uv[0] != 0.0 or uv_data[i].uv[1] != 0.0:
            is_empty = False
            break
    if is_empty:
        warnings.append("❌ UV-развёртка выглядит пустой (все координаты 0). Сделайте Unwrap.")

    # №3: Проверка модификаторов на High-poly
    active_mods = [m.name for m in high_obj.modifiers if m.show_viewport]
    if active_mods:
        warnings.append(f"⚠️ На High-poly активны модификаторы ({', '.join(active_mods)}). Запекание идёт по финальной геометрии.")

    # Металлы (Diffuse)
    if s.bake_type == 'DIFFUSE':
        for i, mat in enumerate(high_obj.data.materials):
            if not mat or not mat.use_nodes:
                continue
            bsdf = get_principled_bsdf(mat)
            if not bsdf:
                continue
            metallic_sock = get_socket(bsdf, "Metallic")
            if metallic_sock and not metallic_sock.is_linked and metallic_sock.default_value > 0.5:
                if s.auto_zero_metallic:
                    metallic_sock.default_value = 0.0
                    fixes.append(f"✔ Metallic '{mat.name}' обнулён")
                else:
                    warnings.append(f"⚠️ Metallic на '{mat.name}' > 0.5. Diffuse может быть тёмным.")

    # №2 и №9: Умный Cage и Margin
    try:
        l_bb = [low_obj.matrix_world @ mathutils.Vector(c) for c in low_obj.bound_box]
        l_min = [min(v[i] for v in l_bb) for i in range(3)]
        l_max = [max(v[i] for v in l_bb) for i in range(3)]
        size = max(l_max[i] - l_min[i] for i in range(3))

        if s.auto_boost_cage and (s.cage_extrusion <= 0.01 or s.cage_extrusion < size * 0.02):
            new_cage = max(0.01, size * 0.1)  # 10% от размера
            s.cage_extrusion = new_cage
            fixes.append(f"✔ Cage Extrusion авто-подобран: {new_cage:.3f}")

        if s.adaptive_margin:
            new_margin = max(2, int(s.resolution * 0.005))  # 0.5% от разрешения
            if s.margin != new_margin:
                s.margin = new_margin
                fixes.append(f"✔ Margin авто-подобран: {s.margin}px")
    except Exception:
        pass

    # Нормали
    if s.auto_fix_normals:
        try:
            import bmesh
            for obj in (high_obj, low_obj):
                bm = bmesh.new()
                bm.from_mesh(obj.data)
                bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
                bm.to_mesh(obj.data)
                bm.free()
                obj.data.update()
            fixes.append("✔ Нормали пересчитаны")
        except Exception:
            pass

    return warnings, fixes, undo
