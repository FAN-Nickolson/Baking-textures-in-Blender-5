"""Сам процесс запекания и сохранение результата на диск."""

import bpy
from .utils import force_select


def bake_texture(high_obj, low_obj, s, context):
    scene = context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = s.samples

    # --- Изображение ---
    img_name = f"{low_obj.name}_{s.bake_type}_Baked"
    if img_name in bpy.data.images:
        bpy.data.images.remove(bpy.data.images[img_name])
    img = bpy.data.images.new(img_name, width=s.resolution, height=s.resolution)
    if s.bake_type in {'NORMAL', 'AO', 'ROUGHNESS', 'METALLIC', 'DISPLACEMENT'}:
        img.colorspace_settings.name = 'Non-Color'  # type: ignore[assignment]
    else:
        img.colorspace_settings.name = 'sRGB'  # type: ignore[assignment]

    # --- Материал-приёмник ---
    mat = bpy.data.materials.new(name=f"{low_obj.name}_BakeMat")
    mat.use_nodes = True
    if mat.node_tree is None:
        raise RuntimeError(f"Не удалось создать node tree для '{mat.name}'")
    nodes = mat.node_tree.nodes
    tex_node = nodes.new('ShaderNodeTexImage')
    tex_node.image = img  # type: ignore[attr-defined]
    nodes.active = tex_node
    tex_node.select = True

    if low_obj.data.materials:
        low_obj.data.materials[0] = mat
    else:
        low_obj.data.materials.append(mat)

    # --- Выделение ---
    if s.auto_fix_selection:
        force_select(high_obj, low_obj, context)
    else:
        bpy.ops.object.select_all(action='DESELECT')
        high_obj.select_set(True)
        low_obj.select_set(True)
        context.view_layer.objects.active = low_obj

    # --- Параметры ---
    bake_settings = scene.render.bake
    bake_settings.use_selected_to_active = True
    bake_settings.cage_extrusion = s.cage_extrusion
    bake_settings.margin = s.margin
    bake_settings.margin_type = s.margin_type
    bake_settings.use_clear = True
    bake_settings.use_cage = False

    if s.bake_type == 'DIFFUSE':
        bake_settings.use_pass_direct = False
        bake_settings.use_pass_indirect = False
        bake_settings.use_pass_color = True
    elif s.bake_type == 'EMIT':
        bake_settings.use_pass_direct = False
        bake_settings.use_pass_indirect = False
        bake_settings.use_pass_color = False

    print(f"[BAKE] {s.bake_type}: {high_obj.name} → {low_obj.name} @ {s.resolution}px")
    print(f"[BAKE] cage_extrusion={s.cage_extrusion}, "
          f"margin={s.margin}px ({s.margin_type})")

    result = bpy.ops.object.bake(
        type=s.bake_type,
        use_selected_to_active=True,
        cage_extrusion=s.cage_extrusion,
        margin=s.margin,
    )
    if result != {'FINISHED'}:
        raise RuntimeError(f"bake вернул {result}")

    diagnose_color(img, s.bake_type)

    # --- Подключение Image Texture к Base Color (только для Diffuse) ---
    if s.bake_type == 'DIFFUSE' and s.connect_diffuse_after_bake:
        if connect_diffuse_to_principled(mat, tex_node):
            print("[BAKE] Image Texture.Color → Principled BSDF.Base Color подключено")
        else:
            print("[BAKE] ⚠️ Не удалось подключить Image Texture к Base Color")

    return img


def connect_diffuse_to_principled(mat, tex_node):
    """Image Texture (Color) → Principled BSDF (Base Color)."""
    if not mat or not mat.use_nodes or mat.node_tree is None:
        return False

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    principled = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
    output = next((n for n in nodes if n.type == 'OUTPUT_MATERIAL'), None)

    tx = tex_node.location[0]
    ty = tex_node.location[1]

    if principled is None:
        principled = nodes.new('ShaderNodeBsdfPrincipled')
        principled.location = (tx + 300, ty)

    if output is None:
        output = nodes.new('ShaderNodeOutputMaterial')
        output.location = (principled.location[0] + 300, principled.location[1])

    already_linked = any(
        link.from_node == principled and link.to_node == output
        and link.to_socket.name == 'Surface'
        for link in links
    )
    if not already_linked:
        for link in list(links):
            if link.to_node == output and link.to_socket.name == 'Surface':
                links.remove(link)
        links.new(principled.outputs['BSDF'], output.inputs['Surface'])

    base_color = principled.inputs.get('Base Color')
    if base_color is None:
        return False

    for link in list(links):
        if link.to_socket == base_color:
            links.remove(link)

    links.new(tex_node.outputs['Color'], base_color)
    return True


def diagnose_color(img, bake_type):
    """Быстрая проверка: чёрная или «нормально-голубая» текстура."""
    try:
        px = list(img.pixels[:4096])
        if not px:
            return
        r, g, b = px[0], px[1], px[2]
        if max(px) < 0.001:
            print("[BAKE] ⚠️ Текстура полностью чёрная.")
            return
        if (bake_type == 'DIFFUSE'
                and abs(r - 0.5) < 0.02
                and abs(g - 0.5) < 0.02
                and b > 0.95):
            print("[BAKE] ⚠️ Результат похож на карту нормалей (голубой).")
    except Exception:
        pass


def save_baked_image(img, low_name, bake_type):
    blend = bpy.data.filepath
    if blend:
        folder = blend.rsplit('/', 1)[0].rsplit('\\', 1)[0]
    else:
        folder = bpy.utils.user_resource('DOCUMENTS', create=True)
    path = f"{folder}/{low_name}_{bake_type}_Baked.png"
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()
    print(f"[BAKE] Сохранено: {path}")
    return path
