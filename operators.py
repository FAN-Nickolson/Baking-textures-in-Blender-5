"""Все операторы аддона."""

import bpy
from bpy.props import StringProperty

from .utils import find_object, ensure_uv_unwrap, t
from .preflight import preflight_check
from .bake import bake_texture, save_baked_image


class BAKOT_OT_preflight_report(bpy.types.Operator):
    bl_idname = "bake_helper.preflight_report"
    bl_label = "Preflight Report"
    bl_description = "Shows found issues and automatic fixes"

    warnings: StringProperty(default="")  # noqa: F722
    fixes: StringProperty(default="")     # noqa: F722

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=560)

    def draw(self, context):
        layout = self.layout
        lang = context.scene.bake_helper.language
        if self.fixes:
            box = layout.box()
            box.label(text=t(lang, "Автоматически исправлено:", "Automatically fixed:"), icon='CHECKMARK')
            for line in self.fixes.split("\n"):
                if line.strip():
                    box.label(text=line)
        if self.warnings:
            box = layout.box()
            box.label(text=t(lang, "Требует внимания:", "Requires attention:"), icon='ERROR')
            for line in self.warnings.split("\n"):
                if line.strip():
                    box.label(text=line)
        else:
            box = layout.box()
            box.label(text=t(lang, "Проблем не найдено.", "No issues found."), icon='CHECKMARK')

    def execute(self, context):
        return {'FINISHED'}


class BAKOT_OT_bake_high_to_low(bpy.types.Operator):
    bl_idname = "bake_helper.bake_high_to_low"
    bl_label = "Bake High → Low"
    bl_description = "Bakes the selected map from high-poly to low-poly"

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        s = context.scene.bake_helper
        lang = s.language

        if not s.high_name or not s.low_name:
            self.report({'ERROR'}, t(lang, "Укажите оба объекта", "Please specify both objects"))
            return {'CANCELLED'}

        try:
            high = find_object(s.high_name, "High-poly")
            low = find_object(s.low_name, "Low-poly")
        except ValueError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

        warnings, fixes, undo_actions = preflight_check(high, low, s, context)
        critical = [w for w in warnings if w.strip().startswith("❌")]

        if critical:
            self.report({'ERROR'}, t(lang, f"Критических проблем: {len(critical)}. Смотри отчёт.", f"Critical issues: {len(critical)}."))
            if s.run_preflight:
                bpy.ops.bake_helper.preflight_report('INVOKE_DEFAULT', warnings="\n".join(warnings), fixes="\n".join(fixes))
            return {'CANCELLED'}

        old_materials = [slot.material for slot in low.material_slots]

        try:
            img = bake_texture(high, low, s, context)
        except Exception as e:
            import traceback
            traceback.print_exc()

            if old_materials:
                for i, old_mat in enumerate(old_materials):
                    if i < len(low.material_slots):
                        low.material_slots[i].material = old_mat

            self.report({'ERROR'}, t(lang, f"Ошибка: {e}", f"Error: {e}"))
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
                self.report({'WARNING'}, t(lang, f"Не сохранено: {e}", f"Not saved: {e}"))

        for action in undo_actions:
            try:
                action()
            except Exception:
                pass

        msg = t(lang, f"Готово: {img.name}", f"Done: {img.name}")
        if saved_path:
            msg += f" → {saved_path}"
        self.report({'INFO'}, msg)
        return {'FINISHED'}


class BAKOT_OT_unwrap_low_only(bpy.types.Operator):
    bl_idname = "bake_helper.unwrap_low_only"
    bl_label = "Make UV Now"
    bl_description = "Creates UV unwrap for low-poly without baking"

    def execute(self, context):
        s = context.scene.bake_helper
        lang = s.language
        if not s.low_name:
            self.report({'ERROR'}, t(lang, "Укажите имя low-poly", "Specify low-poly"))
            return {'CANCELLED'}
        try:
            obj = find_object(s.low_name, "Low-poly")
            _created, msg = ensure_uv_unwrap(obj, s.unwrap_method, s.unwrap_margin, context)
            self.report({'INFO'}, msg)
        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        return {'FINISHED'}


class BAKOT_OT_fill_from_selection(bpy.types.Operator):
    bl_idname = "bake_helper.fill_from_selection"
    bl_label = "Take from Selection"
    bl_description = "Active = Low, second selected = High"

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) >= 2

    def execute(self, context):
        s = context.scene.bake_helper
        lang = s.language
        sel = context.selected_objects
        active = context.view_layer.objects.active

        low = active if active in sel else sel[0]
        highs = [o for o in sel if o != low]

        if len(highs) != 1:
            self.report({'ERROR'}, t(lang, "Выделите ровно 2 объекта", "Select exactly 2 objects"))
            return {'CANCELLED'}

        s.low_name = low.name
        s.high_name = highs[0].name
        self.report({'INFO'}, f"High: {s.high_name}, Low: {s.low_name}")
        return {'FINISHED'}
