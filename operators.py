"""Все операторы аддона."""

import bpy
from bpy.props import StringProperty

from .utils import find_object, ensure_uv_unwrap
from .preflight import preflight_check
from .bake import bake_texture, save_baked_image


class BAKOT_OT_preflight_report(bpy.types.Operator):
    bl_idname = "bake_helper.preflight_report"
    bl_label = "Отчёт предпроверки"
    bl_description = "Показывает найденные проблемы и автоматические исправления"

    warnings: StringProperty(default="")
    fixes: StringProperty(default="")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=560)

    def draw(self, context):
        layout = self.layout
        if self.fixes:
            box = layout.box()
            box.label(text="Автоматически исправлено:", icon='CHECKMARK')
            for line in self.fixes.split("\n"):
                if line.strip():
                    box.label(text=line)
        if self.warnings:
            box = layout.box()
            box.label(text="Требует внимания:", icon='ERROR')
            for line in self.warnings.split("\n"):
                if line.strip():
                    box.label(text=line)
        else:
            box = layout.box()
            box.label(text="Проблем не найдено — можно запекать.", icon='CHECKMARK')

    def execute(self, context):
        return {'FINISHED'}


class BAKOT_OT_bake_high_to_low(bpy.types.Operator):
    bl_idname = "bake_helper.bake_high_to_low"
    bl_label = "Запечь High → Low"
    bl_description = "Запекает выбранную карту с high-poly объекта на low-poly"

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        s = context.scene.bake_helper

        if not s.high_name or not s.low_name:
            self.report({'ERROR'}, "Укажите оба объекта")
            return {'CANCELLED'}
        if s.high_name.strip() == s.low_name.strip():
            self.report({'ERROR'}, "High и Low должны быть разными объектами")
            return {'CANCELLED'}

        try:
            high = find_object(s.high_name, "High-poly")
            low  = find_object(s.low_name,  "Low-poly")
        except ValueError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

        if high.type != 'MESH' or low.type != 'MESH':
            self.report({'ERROR'}, "Оба объекта должны быть мешами (MESH)")
            return {'CANCELLED'}

        warnings, fixes, undo_actions = preflight_check(high, low, s, context)

        critical = [w for w in warnings if w.strip().startswith("❌")]
        if critical:
            self.report({'ERROR'},
                        f"Критических проблем: {len(critical)}. Смотри отчёт.")
            for w in critical:
                print(f"[PREFLIGHT] {w}")
            if s.run_preflight:
                bpy.ops.bake_helper.preflight_report(
                    'INVOKE_DEFAULT',
                    warnings="\n".join(warnings),
                    fixes="\n".join(fixes),
                )
            return {'CANCELLED'}

        if s.run_preflight and (warnings or fixes):
            print("\n===== ОТЧЁТ ПРЕДПРОВЕРКИ =====")
            for f in fixes:
                print(f"[PREFLIGHT] {f}")
            for w in warnings:
                print(f"[PREFLIGHT] {w}")
            print("================================\n")

        try:
            img = bake_texture(high, low, s, context)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.report({'ERROR'}, f"Ошибка: {e}")
            for action in undo_actions:
                try:
                    action()
                except Exception:
                    pass
            return {'CANCELLED'}

        saved_path = ""
        if s.save_to_disk:
            try:
                saved_path = save_baked_image(img, low.name, s.bake_type)
            except Exception as e:
                self.report({'WARNING'}, f"Запечено, но не сохранено: {e}")

        for action in undo_actions:
            try:
                action()
            except Exception:
                pass

        msg = f"Готово: {img.name}" + (f" → {saved_path}" if saved_path else "")
        if fixes:
            msg += f" | авто-исправлений: {len(fixes)}"
        self.report({'INFO'}, msg)
        return {'FINISHED'}


class BAKOT_OT_unwrap_low_only(bpy.types.Operator):
    bl_idname = "bake_helper.unwrap_low_only"
    bl_label = "Сделать UV сейчас"
    bl_description = "Создаёт UV-развёртку для low-poly без запекания"

    def execute(self, context):
        s = context.scene.bake_helper
        if not s.low_name:
            self.report({'ERROR'}, "Укажите имя low-poly объекта")
            return {'CANCELLED'}
        try:
            obj = find_object(s.low_name, "Low-poly")
        except ValueError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

        if obj.type != 'MESH':
            self.report({'ERROR'}, "Объект не является мешем")
            return {'CANCELLED'}

        try:
            created, msg = ensure_uv_unwrap(
                obj, s.unwrap_method, s.unwrap_margin, context
            )
            self.report({'INFO'}, msg)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.report({'ERROR'}, f"Ошибка UV: {e}")
            return {'CANCELLED'}
        return {'FINISHED'}


class BAKOT_OT_fill_from_selection(bpy.types.Operator):
    bl_idname = "bake_helper.fill_from_selection"
    bl_label = "Взять имена из выделения"
    bl_description = "Активный = Low, второй выделенный = High"

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) >= 2

    def execute(self, context):
        s = context.scene.bake_helper
        sel = context.selected_objects
        active = context.view_layer.objects.active

        low = active if active in sel else sel[0]
        highs = [o for o in sel if o != low]
        if len(highs) != 1:
            self.report({'ERROR'}, "Выделите ровно 2 объекта")
            return {'CANCELLED'}

        s.low_name = low.name
        s.high_name = highs[0].name
        self.report({'INFO'}, f"High: {s.high_name}, Low: {s.low_name}")
        return {'FINISHED'}