import bpy
import math

class RETRO_TEXT_OT_Create(bpy.types.Operator):
    bl_idname = "retro.create_text"
    bl_label = "Generate Retro Text"

    def execute(self, context):
        # 1. Create an Undo marker
        bpy.ops.ed.undo_push(message="Generate Retro Text")

        # 2. Cleanup Scene
        bpy.ops.object.select_all(action='DESELECT')
        for obj in bpy.data.objects:
            if obj.type in ('FONT', 'CAMERA'):
                obj.select_set(True)
        
        bpy.ops.object.delete()

        # 3. Add and Style Text
        bpy.ops.object.text_add(location=(0, 0, 0))
        text_obj = bpy.context.object
        text_obj.data.body = context.scene.retro_text_input
        
        if context.scene.retro_font_path:
            try:
                font = bpy.data.fonts.load(context.scene.retro_font_path)
                text_obj.data.font = font
            except:
                self.report({'ERROR'}, "Could not load font file.")

        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
        text_obj.location = (0, 0, 0)
        
        # Geometry Settings
        text_data = text_obj.data
        text_data.extrude = context.scene.retro_text_extrude
        text_data.bevel_depth = 0.05
        text_data.bevel_resolution = 2

        # 4. Add Camera
        bpy.ops.object.camera_add(location=(0, -5, 0))
        cam = bpy.context.object
        context.scene.camera = cam
        
        # Framing
        dim = text_obj.dimensions
        fov = cam.data.angle
        dist = max(dim.x, dim.y) / (2 * math.tan(fov / 2))
        cam.location.y = -(dist * 1.1)
        cam.rotation_euler = (1.57, 0, 0)

        # 5. Material Setup
        mat_name = "Color"
        mat = bpy.data.materials.get(mat_name) or bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        bsdf = nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs['Base Color'].default_value = context.scene.text_color
            bsdf.inputs['Metallic'].default_value = 0.8
            bsdf.inputs['Roughness'].default_value = 0.1
        
        text_obj.data.materials.append(mat)
            
        # 6. Animation
        context.view_layer.objects.active = text_obj
        text_obj.rotation_euler = (1.57, 0, 0)
        text_obj.keyframe_insert(data_path="rotation_euler", frame=1)
        text_obj.rotation_euler = (1.57, 0, 6.28)
        text_obj.keyframe_insert(data_path="rotation_euler", frame=120)
        
        return {'FINISHED'}

class RETRO_TEXT_PT_Panel(bpy.types.Panel):
    bl_label = "Retro Text Generator"
    bl_idname = "RETRO_TEXT_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Retro Tools'

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene, "retro_text_input")
        layout.prop(context.scene, "retro_font_path")
        layout.prop(context.scene, "retro_text_extrude")
        layout.prop(context.scene, "text_color")
        layout.operator("retro.create_text")

def register():
    bpy.utils.register_class(RETRO_TEXT_OT_Create)
    bpy.utils.register_class(RETRO_TEXT_PT_Panel)
    bpy.types.Scene.retro_text_input = bpy.props.StringProperty(name="Text")
    bpy.types.Scene.retro_font_path = bpy.props.StringProperty(name="Font", subtype='FILE_PATH')
    bpy.types.Scene.retro_text_extrude = bpy.props.FloatProperty(name="Extrude", default=0.2)
    bpy.types.Scene.text_color = bpy.props.FloatVectorProperty(
            name = "Color Picker",
            subtype = "COLOR",
            default = (0.8, 0, 0.4, 1)
            size = 4
            )

def unregister():
    bpy.utils.unregister_class(RETRO_TEXT_OT_Create)
    bpy.utils.unregister_class(RETRO_TEXT_PT_Panel)
    del bpy.types.Scene.retro_text_input
    del bpy.types.Scene.retro_font_path
    del bpy.types.Scene.retro_text_extrude
    del bpy.types.Scene.text_color

if __name__ == "__main__":
    register()
