"""Сам процесс запекания, автоподключение нод и сохранение на диск."""

import bpy
from .utils import force_select


def _setup_render_engine(scene, s):
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = s.samples

    if s.use_gpu:
        try:
            prefs = bpy.context.preferences.addons['cycles'].preferences
            prefs.compute_device_type = 'OPTIX'
            prefs.get_devices()
            has_gpu = any(d.type != 'CPU' and d.use for d in prefs.devices)
            scene.cycles.device = 'GPU' if has_gpu else 'CPU'
        except Exception:
            scene.cycles.device = 'CPU'
    else:
        scene.cycles.device = 'CPU'


def bake_texture(high_obj, low_obj, s, context):
    scene = context.scene
    _setup_render_engine(scene, s)

    img_name = f"{low_obj.name}_{s.bake_type}_Baked"
    if img_name in bpy.data.images:
        bpy.data.images.remove(bpy.data.images[img_name])
    img = bpy.data.images.new(img_name, width=s.resolution, height=s.resolution)

    if s.bake_type in {'NORMAL', 'AO', 'ROUGHNESS', 'METALLIC', 'EMIT'}:
        img.colorspace_settings.name = 'Non-Color'  # type: ignore
    else:
        img.colorspace_settings.name = 'sRGB'  # type: ignore

    mat = _get_or_create_bake_material(low_obj)
    nodes = mat.node_tree.nodes
    tex_node = nodes.new('ShaderNodeTexImage')
    tex_node.image = img  # type: ignore
    nodes.active = tex_node
    tex_node.select = True

    if s.auto_fix_selection:
        force_select(high_obj, low_obj, context)
    else:
        bpy.ops.object.select_all(action='DESELECT')
        high_obj.select_set(True)
        low_obj.select_set(True)
        context.view_layer.objects.active = low_obj

    actual_bake_type = s.bake_type
    original_materials = list(high_obj.data.materials)
    metallic_links_to_restore = []

    if s.bake_type == 'METALLIC':
        actual_bake_type = 'EMIT'
        for i, orig_mat in enumerate(original_materials):
            if not orig_mat or not orig_mat.use_nodes:
                continue
            temp_mat = orig_mat.copy()
            high_obj.data.materials[i] = temp_mat
            principled = next((n for n in temp_mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
            output = next((n for n in temp_mat.node_tree.nodes if n.type == 'OUTPUT_MATERIAL'), None)
            if principled and output:
                metallic_sock = principled.inputs.get('Metallic')
                if metallic_sock:
                    source_socket = metallic_sock.links[0].from_socket if metallic_sock.is_linked else None
                    if metallic_sock.is_linked:
                        temp_mat.node_tree.links.remove(metallic_sock.links[0])
                    emission = temp_mat.node_tree.nodes.new('ShaderNodeEmission')
                    if source_socket:
                        temp_mat.node_tree.links.new(source_socket, emission.inputs['Color'])
                    else:
                        val = metallic_sock.default_value
                        emission.inputs['Color'].default_value = (val, val, val, 1.0)
                    for link in list(output.inputs['Surface'].links):
                        temp_mat.node_tree.links.remove(link)
                    temp_mat.node_tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])

    elif s.bake_type == 'DIFFUSE':
        for orig_mat in original_materials:
            if not orig_mat or not orig_mat.use_nodes or not orig_mat.node_tree:
                continue
            principled = next((n for n in orig_mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
            if principled:
                metallic_sock = principled.inputs.get('Metallic')
                if metallic_sock and metallic_sock.is_linked:
                    link = metallic_sock.links[0]
                    metallic_links_to_restore.append((orig_mat, metallic_sock, link.from_socket, metallic_sock.default_value))
                    orig_mat.node_tree.links.remove(link)
                    metallic_sock.default_value = 0.0

    bake_settings = scene.render.bake
    bake_settings.use_selected_to_active = True
    bake_settings.cage_extrusion = s.cage_extrusion
    bake_settings.margin = s.margin
    bake_settings.margin_type = s.margin_type
    bake_settings.use_clear = s.use_clear
    bake_settings.use_cage = False

    if s.bake_type in {'DIFFUSE', 'EMIT', 'METALLIC'}:
        bake_settings.use_pass_direct = False
        bake_settings.use_pass_indirect = False
        bake_settings.use_pass_color = (s.bake_type == 'DIFFUSE')

    result = {'CANCELLED'}
    try:
        result = bpy.ops.object.bake(
            type=actual_bake_type, use_selected_to_active=True,
            cage_extrusion=s.cage_extrusion, margin=s.margin,
        )
    finally:
        if s.bake_type == 'METALLIC':
            for i, orig_mat in enumerate(original_materials):
                temp_mat = high_obj.data.materials[i]
                if temp_mat and temp_mat != orig_mat:
                    high_obj.data.materials[i] = orig_mat
                    bpy.data.materials.remove(temp_mat)
        elif s.bake_type == 'DIFFUSE':
            for orig_mat, sock, from_socket, old_val in metallic_links_to_restore:
                if orig_mat.node_tree:
                    orig_mat.node_tree.links.new(from_socket, sock)
                    sock.default_value = old_val

    if result != {'FINISHED'}:
        raise RuntimeError(f"bake вернул {result}")

    diagnose_color(img, s.bake_type)

    if s.connect_after_bake:
        if connect_texture_to_principled(mat, tex_node, s.bake_type):
            print("[BAKE] Текстура подключена к материалу")

    if getattr(s, "align_nodes_after_bake", False):
        align_material_nodes(mat)

    return img


def _get_or_create_bake_material(low_obj):
    mat_name = f"{low_obj.name}_BakeMat"
    mat = bpy.data.materials.get(mat_name)
    if mat is None or not mat.use_nodes:
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True
    if not mat.node_tree:
        raise RuntimeError("Ошибка Node Tree")
    if low_obj.data.materials:
        low_obj.data.materials[0] = mat
    else:
        low_obj.data.materials.append(mat)
    return mat


def connect_texture_to_principled(mat, tex_node, bake_type):
    if not mat or not mat.use_nodes or mat.node_tree is None:
        return False
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    principled = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
    output = next((n for n in nodes if n.type == 'OUTPUT_MATERIAL'), None)
    tx, ty = tex_node.location[0], tex_node.location[1]

    if principled is None:
        principled = nodes.new('ShaderNodeBsdfPrincipled')
        principled.location = (tx + 300, ty)
    if output is None:
        output = nodes.new('ShaderNodeOutputMaterial')
        output.location = (principled.location[0] + 300, principled.location[1])

    # Заменили переменную 'l' на 'lnk' для исправления E741
    surface_linked = any(
        lnk.from_node == principled and lnk.to_node == output and lnk.to_socket.name == 'Surface'
        for lnk in links
    )
    if not surface_linked:
        for lnk in list(links):
            if lnk.to_node == output and lnk.to_socket.name == 'Surface':
                links.remove(lnk)
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
    target = principled.inputs.get(socket_name)
    if target is None:
        return False
    for link in list(links):
        if link.to_socket == target:
            links.remove(link)
    links.new(tex_node.outputs['Color'], target)
    return True


def _connect_base_color(links, tex_node, principled):
    base_color = principled.inputs.get('Base Color')
    if base_color is None:
        return False
    for link in list(links):
        if link.to_socket == base_color:
            src_node = link.from_node
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
        normal_map.location = (principled.location[0] - 250, principled.location[1] - 150)
        links.new(normal_map.outputs['Normal'], normal_input)
    for link in list(links):
        if link.to_node == normal_map and link.to_socket.name == 'Color':
            links.remove(link)
    links.new(tex_node.outputs['Color'], normal_map.inputs['Color'])
    return True


def _connect_emission(links, tex_node, principled):
    emission_input = principled.inputs.get('Emission Color') or principled.inputs.get('Emission')
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
    base_color = principled.inputs.get('Base Color')
    if base_color is None:
        return False
    existing_mix = None
    for link in list(links):
        if link.to_socket == base_color:
            if link.from_node.type == 'MIX_RGB' and link.from_node.blend_type == 'MULTIPLY':
                existing_mix = link.from_node
            break
    if existing_mix is not None:
        for link in list(links):
            if link.to_node == existing_mix and link.to_socket.name == 'Color2':
                links.remove(link)
        links.new(tex_node.outputs['Color'], existing_mix.inputs['Color2'])
        return True
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
    mix.location = (principled.location[0] - 300, principled.location[1] + 100)
    if existing_source is not None:
        links.new(existing_source, mix.inputs['Color1'])
    else:
        mix.inputs['Color1'].default_value = (default_color[0], default_color[1], default_color[2], 1.0)
    links.new(tex_node.outputs['Color'], mix.inputs['Color2'])
    links.new(mix.outputs['Color'], base_color)
    return True


def align_material_nodes(mat):
    if not mat or not mat.use_nodes or not mat.node_tree:
        return
    nodes = mat.node_tree.nodes
    cache = {}

    def get_depth(n, visiting):
        if n in cache:
            return cache[n]
        if n in visiting:
            return 0
        visiting.add(n)
        max_in_depth = -1
        for inp in n.inputs:
            for link in inp.links:
                d = get_depth(link.from_node, visiting)
                max_in_depth = max(max_in_depth, d)
        visiting.remove(n)
        depth = (max_in_depth + 1) if max_in_depth >= 0 else 0
        cache[n] = depth
        return depth

    for n in nodes:
        get_depth(n, set())

    columns = {}
    for n in nodes:
        if n.type == 'FRAME':
            continue
        d = cache.get(n, 0)
        columns.setdefault(d, []).append(n)

    for d, col_nodes in columns.items():
        col_nodes.sort(key=lambda n: (n.name, n.type))
        for i, n in enumerate(col_nodes):
            n.location = (d * 300, -i * 200)


def diagnose_color(img, bake_type):
    try:
        pixels = list(img.pixels[:4096])
        if not pixels:
            return
        if max(pixels) < 0.001:
            print("[BAKE] ⚠️ Текстура полностью чёрная.")
            return
        r, g, b = pixels[0], pixels[1], pixels[2]
        if bake_type == 'DIFFUSE' and abs(r - 0.5) < 0.02 and abs(g - 0.5) < 0.02 and b > 0.95:
            print("[BAKE] ⚠️ Результат похож на карту нормалей (голубой).")
    except Exception:
        pass


def save_baked_image(img, low_name, bake_type):
    blend = bpy.data.filepath
    folder = blend.rsplit('/', 1)[0].rsplit('\\', 1)[0] if blend else bpy.utils.user_resource('DOCUMENTS', create=True)
    path = f"{folder}/{low_name}_{bake_type}_Baked.png"
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()
    print(f"[BAKE] Сохранено: {path}")
    return path
