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

    # --- Материал-приёмник (переиспользуем существующий) ---
    mat = _get_or_create_bake_material(low_obj)
    nodes = mat.node_tree.nodes
    tex_node = nodes.new('ShaderNodeTexImage')
    tex_node.image = img  # type: ignore[attr-defined]
    nodes.active = tex_node
    tex_node.select = True

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

    # --- Автоподключение к Principled BSDF ---
    if s.connect_after_bake:
        if connect_texture_to_principled(mat, tex_node, s.bake_type):
            print(f"[BAKE] {s.bake_type}: текстура подключена к материалу")
        else:
            print(f"[BAKE] ⚠️ Не удалось подключить {s.bake_type} к материалу")

    return img


def _get_or_create_bake_material(low_obj):
    """Переиспользует материал {low_name}_BakeMat, если он уже создан."""
    mat_name = f"{low_obj.name}_BakeMat"
    mat = bpy.data.materials.get(mat_name)
    if mat is None or not mat.use_nodes:
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True
    if mat.node_tree is None:
        raise RuntimeError(f"Не удалось создать node tree для '{mat.name}'")

    if low_obj.data.materials:
        low_obj.data.materials[0] = mat
    else:
        low_obj.data.materials.append(mat)
    return mat


# ============================================================
# АВТОПОДКЛЮЧЕНИЕ: диспетчер + функции по типам
# ============================================================
def connect_texture_to_principled(mat, tex_node, bake_type):
    """Подключает Image Texture к нужному входу Principled BSDF."""
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

    # Principled → Output
    surface_linked = any(
        link.from_node == principled and link.to_node == output
        and link.to_socket.name == 'Surface'
        for link in links
    )
    if not surface_linked:
        for link in list(links):
            if link.to_node == output and link.to_socket.name == 'Surface':
                links.remove(link)
        links.new(principled.outputs['BSDF'], output.inputs['Surface'])

    if bake_type == 'DIFFUSE':
        return _connect_base_color(links, tex_node, principled)
    elif bake_type == 'NORMAL':
        return _connect_normal(links, nodes, tex_node, principled)
    elif bake_type == 'ROUGHNESS':
        return _connect_simple(links, tex_node, principled, 'Roughness')
    elif bake_type == 'METALLIC':
        return _connect_simple(links, tex_node, principled, 'Metallic')
    elif bake_type == 'EMIT':
        return _connect_emission(links, tex_node, principled)
    elif bake_type == 'AO':
        return _connect_ao(links, nodes, tex_node, principled)
    return False


def _connect_simple(links, tex_node, principled, socket_name):
    """Image.Color → Principled.<socket_name>"""
    target = principled.inputs.get(socket_name)
    if target is None:
        return False
    for link in list(links):
        if link.to_socket == target:
            links.remove(link)
    links.new(tex_node.outputs['Color'], target)
    return True


def _connect_base_color(links, tex_node, principled):
    """Image.Color → Base Color (учитывает существующий AO Mix)."""
    base_color = principled.inputs.get('Base Color')
    if base_color is None:
        return False

    for link in list(links):
        if link.to_socket == base_color:
            src_node = link.from_node
            # Если Base Color питается от AO-Mix — обновляем его Color1
            if src_node.type == 'MIX_RGB' and src_node.blend_type == 'MULTIPLY':
                for l2 in list(links):
                    if l2.to_node == src_node and l2.to_socket.name == 'Color1':
                        links.remove(l2)
                links.new(tex_node.outputs['Color'], src_node.inputs['Color1'])
                return True
            else:
                links.remove(link)

    links.new(tex_node.outputs['Color'], base_color)
    return True


def _connect_normal(links, nodes, tex_node, principled):
    """Image.Color → Normal Map.Color → Principled.Normal"""
    normal_input = principled.inputs.get('Normal')
    if normal_input is None:
        return False

    normal_map = None
    for link in list(links):
        if link.to_socket == normal_input:
            if link.from_node.type == 'NORMAL_MAP':
                normal_map = link.from_node
            else:
                links.remove(link)
            break

    if normal_map is None:
        normal_map = nodes.new('ShaderNodeNormalMap')
        normal_map.location = (
            principled.location[0] - 250,
            principled.location[1] - 150,
        )
        links.new(normal_map.outputs['Normal'], normal_input)

    for link in list(links):
        if link.to_node == normal_map and link.to_socket.name == 'Color':
            links.remove(link)
    links.new(tex_node.outputs['Color'], normal_map.inputs['Color'])
    return True


def _connect_emission(links, tex_node, principled):
    """Image.Color → Emission Color, Emission Strength = 1.0"""
    emission_input = principled.inputs.get('Emission Color')
    if emission_input is None:
        emission_input = principled.inputs.get('Emission')
    if emission_input is None:
        return False

    for link in list(links):
        if link.to_socket == emission_input:
            links.remove(link)
    links.new(tex_node.outputs['Color'], emission_input)

    strength = principled.inputs.get('Emission Strength')
    if strength is not None and not strength.is_linked:
        strength.default_value = 1.0

    return True


def _connect_ao(links, nodes, tex_node, principled):
    """Image.Color → Mix(Multiply).Color2 → Base Color."""
    base_color = principled.inputs.get('Base Color')
    if base_color is None:
        return False

    # Уже есть AO Mix — обновляем Color2
    existing_mix = None
    for link in list(links):
        if link.to_socket == base_color:
            if (link.from_node.type == 'MIX_RGB'
                    and link.from_node.blend_type == 'MULTIPLY'):
                existing_mix = link.from_node
            break

    if existing_mix is not None:
        for link in list(links):
            if link.to_node == existing_mix and link.to_socket.name == 'Color2':
                links.remove(link)
        links.new(tex_node.outputs['Color'], existing_mix.inputs['Color2'])
        return True

    # Создаём новый Mix
    default_color = tuple(base_color.default_value)
    existing_source = None
    for link in list(links):
        if link.to_socket == base_color:
            existing_source = link.from_socket
            links.remove(link)
            break

    mix = nodes.new('ShaderNodeMixRGB')
    mix.blend_type = 'MULTIPLY'
    mix.inputs['Fac'].default_value = 1.0
    mix.location = (
        principled.location[0] - 300,
        principled.location[1] + 100,
    )

    if existing_source is not None:
        links.new(existing_source, mix.inputs['Color1'])
    else:
        mix.inputs['Color1'].default_value = (
            default_color[0], default_color[1], default_color[2], 1.0,
        )

    links.new(tex_node.outputs['Color'], mix.inputs['Color2'])
    links.new(mix.outputs['Color'], base_color)
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
