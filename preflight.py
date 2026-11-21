"""Предполётные проверки: UV, Metallic, Base Color, bounding box, нормали, margin."""

import bpy
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

    # ---------- 0. Авто-UV ----------
    if s.auto_unwrap and not low_obj.data.uv_layers:
        try:
            created, msg = ensure_uv_unwrap(
                low_obj, s.unwrap_method, s.unwrap_margin, context
            )
            if created:
                fixes.append(f"✔ UV для '{low_obj.name}' создан ({s.unwrap_method})")
            else:
                print(f"[PREFLIGHT] UV: {msg}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            warnings.append(
                f"⚠️ Не удалось создать UV автоматически: {e}. "
                f"Сделайте UV вручную (Edit Mode → U)."
            )

    # ---------- 1. UV на low ----------
    if not low_obj.data.uv_layers:
        warnings.append("❌ LOW-POLY: нет UV-развёртки. Запекание невозможно.")
        return warnings, fixes, undo
    if low_obj.data.uv_layers.active is None:
        warnings.append("⚠️ LOW-POLY: нет активного UV-слоя (UV Map).")

    # ---------- 2. Материалы high ----------
    if not high_obj.data.materials:
        warnings.append("❌ HIGH-POLY: нет материалов. Diffuse запечётся чёрным.")
    else:
        for i, mat in enumerate(high_obj.data.materials):
            if mat is None:
                warnings.append(f"⚠️ HIGH-POLY: пустой слот материала #{i}.")
                continue
            bsdf = get_principled_bsdf(mat)
            if bsdf is None:
                warnings.append(
                    f"⚠️ HIGH-POLY: материал '{mat.name}' без Principled BSDF — "
                    f"Diffuse может запечься чёрным."
                )
                continue

            metallic_sock = get_socket(bsdf, "Metallic")
            if metallic_sock is not None:
                if not metallic_sock.is_linked:
                    if metallic_sock.default_value > 0.5:
                        msg = (
                            f"❌ HIGH-POLY: материал '{mat.name}': "
                            f"Metallic = {metallic_sock.default_value:.2f} → "
                            f"Diffuse запечётся ЧЁРНЫМ."
                        )
                        if s.auto_zero_metallic:
                            old = metallic_sock.default_value
                            metallic_sock.default_value = 0.0
                            fixes.append(f"✔ Metallic '{mat.name}': {old:.2f} → 0.0")
                            undo.append(
                                lambda sock=metallic_sock, val=old:
                                    setattr(sock, "default_value", val)
                            )
                        else:
                            warnings.append(msg)
                else:
                    warnings.append(
                        f"⚠️ HIGH-POLY: материал '{mat.name}': Metallic подключён "
                        f"к узлу — если 1.0, Diffuse будет чёрным."
                    )

            base_sock = get_socket(bsdf, "Base Color")
            if base_sock is not None and not base_sock.is_linked:
                v = base_sock.default_value
                if v[0] < 0.02 and v[1] < 0.02 and v[2] < 0.02:
                    warnings.append(
                        f"❌ HIGH-POLY: материал '{mat.name}': "
                        f"Base Color = чёрный → результат будет чёрным."
                    )

            alpha_sock = get_socket(bsdf, "Alpha")
            if alpha_sock is not None and not alpha_sock.is_linked:
                if alpha_sock.default_value < 0.01:
                    warnings.append(
                        f"⚠️ HIGH-POLY: материал '{mat.name}': Alpha = 0 — "
                        f"объект может быть невидим для лучей."
                    )

    # ---------- 3. Bounding box ----------
    try:
        import mathutils
        h_bb = [high_obj.matrix_world @ mathutils.Vector(c) for c in high_obj.bound_box]
        l_bb = [low_obj.matrix_world @ mathutils.Vector(c) for c in low_obj.bound_box]
        h_min = [min(v[i] for v in h_bb) for i in range(3)]
        h_max = [max(v[i] for v in h_bb) for i in range(3)]
        l_min = [min(v[i] for v in l_bb) for i in range(3)]
        l_max = [max(v[i] for v in l_bb) for i in range(3)]

        overlap = all(
            h_min[i] <= l_max[i] and l_min[i] <= h_max[i]
            for i in range(3)
        )
        if not overlap:
            warnings.append(
                "❌ HIGH и LOW объекты НЕ ПЕРЕСЕКАЮТСЯ в пространстве. "
                "Совместите их (Origin → To Geometry)."
            )

        size = max(h_max[i] - h_min[i] for i in range(3))
        if size > 0 and s.cage_extrusion < size * 0.01:
            msg = (
                f"⚠️ Cage Extrusion = {s.cage_extrusion:.3f} слишком мал "
                f"для объекта размером {size:.2f}."
            )
            if s.auto_boost_cage:
                new_val = max(size * 0.05, 0.5)
                old_val = s.cage_extrusion
                s.cage_extrusion = new_val
                fixes.append(f"✔ Cage Extrusion: {old_val:.3f} → {new_val:.3f}")
                undo.append(
                    lambda prop=s, val=old_val:
                        setattr(prop, "cage_extrusion", val)
                )
            else:
                warnings.append(msg)
    except Exception as e:
        warnings.append(f"⚠️ Не удалось проверить bounding box: {e}")

    # ---------- 4. Cage Extrusion = 0 ----------
    if s.cage_extrusion <= 0.0001:
        msg = "❌ Cage Extrusion = 0."
        if s.auto_boost_cage:
            s.cage_extrusion = 0.5
            fixes.append("✔ Cage Extrusion: 0 → 0.5")
            undo.append(lambda prop=s: setattr(prop, "cage_extrusion", 0.0))
        else:
            warnings.append(msg)

    # ---------- 5. Нормали ----------
    if s.auto_fix_normals:
        try:
            import bmesh
            for obj in (high_obj, low_obj):
                if len(obj.data.polygons) == 0:
                    warnings.append(f"❌ '{obj.name}' не содержит полигонов.")
                    continue
                bm = bmesh.new()
                bm.from_mesh(obj.data)
                bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
                bm.to_mesh(obj.data)
                bm.free()
                obj.data.update()
                fixes.append(f"✔ Нормали '{obj.name}' пересчитаны наружу")
        except Exception as e:
            warnings.append(f"⚠️ Не удалось пересчитать нормали: {e}")

    # ---------- 6. Principled BSDF для Diffuse ----------
    if s.bake_type == 'DIFFUSE':
        if not high_obj.data.materials:
            warnings.append("❌ HIGH-POLY без материала — Diffuse будет чёрным.")
        else:
            has_bsdf = any(
                get_principled_bsdf(m) for m in high_obj.data.materials if m
            )
            if not has_bsdf:
                warnings.append("❌ У HIGH-POLY нет ни одного Principled BSDF.")

    # ---------- 7. Кровотечение ----------
    if s.margin > 8:
        warnings.append(
            f"⚠️ Margin = {s.margin}px может «наползать» на соседние UV-острова. "
            f"Рекомендуется 2–4px."
        )

    return warnings, fixes, undo