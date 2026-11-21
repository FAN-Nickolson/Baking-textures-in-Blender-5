import bpy
from bpy.props import StringProperty

from .utils import _find_object
from .preflight import preflight_check
from .bake import bake_texture, save_baked_image


# ============================================================
# ОКНО ОТЧЁТА ПРЕДПРОВЕРКИ
# ============================================================
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


# ============================================================
# ГЛАВНЫЙ ОПЕРАТОР
# ============================================================
class BAKOT_OT_settings(bpy.types.Operator):
    bl_idname = "bake_helper.settings"
    bl_label = "Настройки запекания"
    bl_description = "Заполните поля и нажмите OK, чтобы начать запекание"

    def invoke(self, context, event):
        s = context.scene.bake_helper
        sel = context.selected_objects
        if len(sel) >= 2 and not s.high_name and not s.low_name:
            active = context.view_layer.objects.active
            low = active if active in sel else sel[0]
            highs = [o for o in sel if o != low]
            s.low_name  = low.name
            s.high_name = highs[0].name if highs else ""
        return context.window_manager.invoke_props_dialog(self, width=440)

    def draw(self, context):
        s = context.scene.bake_helper
        layout = self.layout

        col = layout.column(align=True)
        col.label(text="Объекты (точные имена из Outliner):")
        col.prop(s, "high_name")
        col.prop(s, "low_name")

        layout.separator()
        col = layout.column(align=True)
        col.label(text="Параметры запекания:")
        col.prop(s, "bake_type")
        col.prop(s, "resolution")
        col.prop(s, "cage_extrusion")

        col = layout.column(align=True)
        col.label(text="Отступы (Margin):")
        col.prop(s, "margin")
        col.prop(s, "margin_type")

        col = layout.column(align=True)
        col.prop(s, "samples")

        layout.separator()
        col = layout.column(align=True)
        col.label(text="Автопроверки (рекомендуется включить):")
        col.prop(s, "auto_fix_selection")
        col.prop(s, "auto_zero_metallic")
        col.prop(s, "auto_boost_cage")
        col.prop(s, "auto_fix_normals")
        col.prop(s, "run_preflight")

        layout.separator()
        layout.prop(s, "save_to_disk")

    def execute(self, context):
        s = context.scene.bake_helper

        if not s.high_name or not s.low_name:
            self.report({'ERROR'}, "Укажите оба объекта")
            return {'CANCELLED'}
        if s.high_name.strip() == s.low_name.strip():
            self.report({'ERROR'}, "High и Low — это должны быть разные объекты")
            return {'CANCELLED'}

        try:
            high = _find_object(s.high_name, "High-poly")
            low  = _find_object(s.low_name,  "Low-poly")
        except ValueError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

        if high.type != 'MESH' or low.type != 'MESH':
            self.report({'ERROR'}, "Оба объекта должны быть мешами (MESH)")
            return {'CANCELLED'}

        # ===== ПРЕДПОЛЁТНАЯ ДИАГНОСТИКА =====
        warnings, fixes, undo_actions = preflight_check(high, low, s, context)

        critical = [w for w in warnings if w.strip().startswith("❌")]
        if critical:
            self.report(
                {'ERROR'},
                f"Найдено критических проблем: {len(critical)}. "
                f"Смотри отчёт предпроверки."
            )
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

        # ===== ЗАПЕКАНИЕ =====
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


# ============================================================
# ОПЕРАТОР БЫСТРОГО СТАРТА
# ============================================================
class BAKOT_OT_quick(bpy.types.Operator):
    bl_idname = "bake_helper.quick"
    bl_label = "Быстрое запекание по выделению"
    bl_description = "Выделите два объекта (low активный) — скрипт подставит имена"

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
            self.report({'ERROR'}, "Выделите ровно 2 объекта: high-poly и low-poly")
            return {'CANCELLED'}

        s.low_name = low.name
        s.high_name = highs[0].name
        bpy.ops.bake_helper.settings('INVOKE_DEFAULT')
        return {'FINISHED'}