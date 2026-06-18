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
        text_obj.data.space_character = context.scene.retro_space_character
        
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
        text_data.bevel_depth = context.scene.retro_bevel_depth
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
            bsdf.inputs['Metallic'].default_value = context.scene.mat_metalic
            bsdf.inputs['Roughness'].default_value = 0.1
        
        text_obj.data.materials.clear()
        text_obj.data.materials.append(mat)
            
        # 6. Process Selection Menu
        context.view_layer.objects.active = text_obj
        anim_choice = context.scene.retro_anim_preset
        
        # Reset default structural transformation values first
        text_obj.rotation_mode = 'XYZ'
        text_obj.rotation_euler = (1.57, 0, 0)
        text_obj.scale = (1.0, 1.0, 1.0)
        
        if anim_choice == 'ROTATION':
            # Linear Spinning Loop
            text_obj.keyframe_insert(data_path="rotation_euler", frame=1)
            text_obj.rotation_euler = (1.57, 0, 2 * math.pi) 
            text_obj.keyframe_insert(data_path="rotation_euler", frame=121)
            
            # Apply LINEAR interpolation for modern Slotted/Layered Action layouts (Blender 4.4+)
            if text_obj.animation_data and text_obj.animation_data.action:
                action = text_obj.animation_data.action
                fcurves_list = []
                if hasattr(action, "layers") and action.layers:
                    for layer in action.layers:
                        for strip in layer.strips:
                            if not fcurves_list and hasattr(strip, "channelbags"):
                                for cb in strip.channelbags:
                                    fcurves_list.extend(cb.fcurves)
                if not fcurves_list and hasattr(action, "fcurves"):
                    fcurves_list = action.fcurves
                    
                for fcurve in fcurves_list:
                    for kp in fcurve.keyframe_points:
                        kp.interpolation = 'LINEAR'
                        
            context.scene.frame_start = 1
            context.scene.frame_end = 120

        elif anim_choice == 'BOUNCY_SCALE':
            # Bouncy Scale-Up Intro
            # Frame 1: Invisible
            text_obj.scale = (0.0, 0.0, 0.0)
            text_obj.keyframe_insert(data_path="scale", frame=1)

            text_obj.scale = (1.0, 1.0, 1.0)
            text_obj.keyframe_insert(data_path="scale", frame=15)

            text_obj.scale = (0.7, 0.7, 0.7)
            text_obj.keyframe_insert(data_path="scale", frame=20)

            text_obj.scale = (0.9, 0.9, 0.9)
            text_obj.keyframe_insert(data_path="scale", frame=30)

            text_obj.scale = (0.8, 0.8, 0.8)
            text_obj.keyframe_insert(data_path="scale", frame=35)

            text_obj.scale = (0.85, 0.85, 0.85)
            text_obj.keyframe_insert(data_path="scale", frame=40)

            text_obj.scale = (0.9, 0.9, 0.9)
            text_obj.keyframe_insert(data_path="scale", frame=55)

            text_obj.scale = (0.0, 0.0, 0.0)
            text_obj.keyframe_insert(data_path="scale", frame=60)
            
            context.scene.frame_start = 1
            context.scene.frame_end = 60

        return {'FINISHED'}

class RETRO_TEXT_PT_Panel(bpy.types.Panel):
    bl_label = "Retro Text Generator"
    bl_idname = "RETRO_TEXT_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Retro Tools'

    def draw(self, context):
        layout = self.layout
        
        # Fix: Using 'TEXT' instead of 'FONTP_TEXT'
        box = layout.box()
        box.label(text="Text Configuration:", icon='TEXT')
        box.prop(context.scene, "retro_text_input")
        box.prop(context.scene, "retro_font_path")
        box.prop(context.scene, "retro_space_character")
        
        box = layout.box()
        box.label(text="Style & Geometry:", icon='MODIFIER')
        box.prop(context.scene, "retro_text_extrude")
        box.prop(context.scene, "retro_bevel_depth")
        box.prop(context.scene, "text_color")
        box.prop(context.scene, "mat_metalic")
        
        box = layout.box()
        box.label(text="Animation Settings:", icon='ANIM')
        box.prop(context.scene, "retro_anim_preset", text="Preset")
        
        layout.separator()
        layout.operator("retro.create_text", icon='PLAY')

def register():
    bpy.utils.register_class(RETRO_TEXT_OT_Create)
    bpy.utils.register_class(RETRO_TEXT_PT_Panel)
    
    bpy.types.Scene.retro_text_input = bpy.props.StringProperty(name="Text", default="RETRO")
    bpy.types.Scene.retro_font_path = bpy.props.StringProperty(name="Font", subtype='FILE_PATH')
    bpy.types.Scene.retro_text_extrude = bpy.props.FloatProperty(name="Extrude", default=0.2, min=0, max=0.4)
    bpy.types.Scene.retro_bevel_depth = bpy.props.FloatProperty(name="Bevel Depth", default=0.05, min=0, max=0.2)
    bpy.types.Scene.retro_space_character = bpy.props.FloatProperty(name="Character Space", default=1, min=1, max=10)
    bpy.types.Scene.text_color = bpy.props.FloatVectorProperty(
            name = "Color Picker",
            subtype = "COLOR",
            default = (0.8, 0, 0.4, 1),
            size = 4
            )
    bpy.types.Scene.mat_metalic = bpy.props.FloatProperty(name="Metalic", default=0.8, min=0, max=1)
    
    bpy.types.Scene.retro_anim_preset = bpy.props.EnumProperty(
        name="Animation Preset",
        description="Choose the animation preset to apply to the retro text",
        items=[
            ('ROTATION', "Rotation Loop", "Spins the text over 120 frames"),
            ('BOUNCY_SCALE', "Bouncy Scale Up", "Scale text from 0 to full to 0")
        ],
        default='ROTATION'
    )

def unregister():
    bpy.utils.unregister_class(RETRO_TEXT_OT_Create)
    bpy.utils.unregister_class(RETRO_TEXT_PT_Panel)
    del bpy.types.Scene.retro_text_input
    del bpy.types.Scene.retro_font_path
    del bpy.types.Scene.retro_text_extrude
    del bpy.types.Scene.retro_bevel_depth
    del bpy.types.Scene.retro_space_character
    del bpy.types.Scene.text_color
    del bpy.types.Scene.mat_metalic
    del bpy.types.Scene.retro_anim_preset

if __name__ == "__main__":
    register()
