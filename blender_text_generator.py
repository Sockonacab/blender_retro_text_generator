import bpy
import math

class RETRO_TEXT_OT_Create(bpy.types.Operator):
    bl_idname = "retro.create_text"
    bl_label = "Generate Retro Text"

    def execute(self, context):
        scene = context.scene
        fps = scene.retro_fps

        # 1. Create an Undo marker
        bpy.ops.ed.undo_push(message="Generate Retro Text")

        # 2. Cleanup Scene
        bpy.ops.object.select_all(action='DESELECT')
        for obj in bpy.data.objects:
            if obj.type in ('FONT', 'CAMERA', 'LIGHT'):
                obj.select_set(True)
        bpy.ops.object.delete()

        # 3. Add and Style Text
        bpy.ops.object.text_add(location=(0, 0, 0))
        text_obj = bpy.context.object
        text_obj.data.body = scene.retro_text_input
        text_obj.data.space_character = scene.retro_space_character
        
        if scene.retro_font_path:
            try:
                font = bpy.data.fonts.load(scene.retro_font_path)
                text_obj.data.font = font
            except:
                self.report({'ERROR'}, "Could not load font file.")

        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
        text_obj.location = (0, 0, 0)
        
        # Geometry Settings
        text_data = text_obj.data
        text_data.extrude = scene.retro_text_extrude
        text_data.bevel_depth = scene.retro_bevel_depth
        text_data.bevel_resolution = 2

        # 4. Add Camera
        bpy.ops.object.camera_add(location=(0, -5, 0))
        cam = bpy.context.object
        scene.camera = cam
        
        # Framing
        dim = text_obj.dimensions
        fov = cam.data.angle
        dist = max(dim.x, dim.y) / (2 * math.tan(fov / 2))
        cam.location.y = -(dist * 1.1)
        cam.rotation_euler = (1.57, 0, 0)

        # 4b. Add Retro Studio Lighting Layout
        bpy.ops.object.light_add(type='SUN', location=(3, -4, 5))
        sun_light = bpy.context.object
        sun_light.name = "Retro_KeyLight"
        sun_light.data.energy = 4.0
        sun_light.rotation_euler = (0.6, 0.0, 0.5)

        bpy.ops.object.light_add(type='POINT', location=(-4, 2, 3))
        kick_light = bpy.context.object
        kick_light.name = "Retro_KickLight"
        kick_light.data.energy = 150.0
        kick_light.data.color = (0.0, 0.6, 1.0)

        # 5. Material Setup
        mat_name = "Color"
        mat = bpy.data.materials.get(mat_name) or bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        bsdf = nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs['Base Color'].default_value = scene.text_color
            bsdf.inputs['Metallic'].default_value = scene.mat_metalic
            bsdf.inputs['Roughness'].default_value = 0.1
        
        text_obj.data.materials.clear()
        text_obj.data.materials.append(mat)
            
        # 6. Process Selection Menu & Dynamic Keyframing
        context.view_layer.objects.active = text_obj
        anim_choice = scene.retro_anim_preset
        
        text_obj.rotation_mode = 'XYZ'
        text_obj.rotation_euler = (1.57, 0, 0)
        text_obj.scale = (1.0, 1.0, 1.0)

        scene.render.fps = fps

        if anim_choice == 'ROTATION':
            total_duration = 3.0
            end_frame = max(2, int(total_duration * fps))

            text_obj.keyframe_insert(data_path="rotation_euler", frame=1)
            text_obj.rotation_euler = (1.57, 0, 2 * math.pi) 
            text_obj.keyframe_insert(data_path="rotation_euler", frame=end_frame + 1)
            
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
                        
            scene.frame_start = 1
            scene.frame_end = end_frame

        elif anim_choice == 'BOUNCY_SCALE':
            timestamps = [0.0, 0.5, 0.65, 1.0, 1.15, 1.33, 1.8, 2.0]
            scales = [
                (0.0, 0.0, 0.0),
                (1.0, 1.0, 1.0),
                (0.7, 0.7, 0.7),
                (0.9, 0.9, 0.9),
                (0.8, 0.8, 0.8),
                (0.85, 0.85, 0.85),
                (0.9, 0.9, 0.9),
                (0.0, 0.0, 0.0)
            ]

            for time_sec, scale_val in zip(timestamps, scales):
                # Calculate exactly which frame this timestamp lands on based on current FPS
                target_frame = max(1, int(time_sec * fps))
                text_obj.scale = scale_val
                text_obj.keyframe_insert(data_path="scale", frame=target_frame)
            
            scene.frame_start = 1
            scene.frame_end = max(2, int(2.0 * fps))
        elif anim_choice == 'WAVE':
            bpy.ops.object.modifier_add(type='WAVE')

        return {'FINISHED'}


class RETRO_TEXT_OT_SetupExport(bpy.types.Operator):
    bl_idname = "retro.setup_export"
    bl_label = "Configure Render Settings"
    bl_description = "Automatically applies background transparency and output paths"

    def execute(self, context):
        scene = context.scene
        scene.render.film_transparent = True
        scene.render.image_settings.file_format = 'PNG'
        scene.render.image_settings.color_mode = 'RGBA'
        
        if scene.retro_export_path:
            scene.render.filepath = scene.retro_export_path
            
        self.report({'INFO'}, "Render settings applied")
        return {'FINISHED'}


class RETRO_TEXT_OT_ApplyRetroCrunch(bpy.types.Operator):
    bl_idname = "retro.apply_retro_crunch"
    bl_label = "Apply Retro Style Crunch"
    bl_description = "Alters engine settings to enforce a low-res pixelated color layout"

    def execute(self, context):
        scene = context.scene

        scene.render.resolution_x = 256
        scene.render.resolution_y = 256
        scene.render.resolution_percentage = 100

        scene.render.filter_size = 0.01

        scene.render.fps = scene.retro_fps

        scene.display_settings.display_device = 'sRGB'
        scene.view_settings.view_transform = 'Standard'
        scene.view_settings.look = 'High Contrast'

        self.report({'INFO'}, "Low-res pixel scaling applied.")
        return {'FINISHED'}


class RETRO_TEXT_PT_Panel(bpy.types.Panel):
    bl_label = "Retro Text Generator"
    bl_idname = "RETRO_TEXT_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Retro Tools'

    def draw(self, context):
        layout = self.layout
        
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
        box.prop(context.scene, "retro_fps") # Displays the new FPS slider
        
        layout.separator()
        layout.operator("retro.create_text", icon='PLAY')
        
        box = layout.box()
        box.label(text="Web Export Configuration:", icon='EXPORT')
        box.prop(context.scene, "retro_export_path")
        
        row = box.row(align=True)
        row.operator("retro.setup_export", icon='REC')
        row.operator("retro.apply_retro_crunch", icon='MOD_NOISE')


def register():
    bpy.utils.register_class(RETRO_TEXT_OT_Create)
    bpy.utils.register_class(RETRO_TEXT_OT_SetupExport)
    bpy.utils.register_class(RETRO_TEXT_OT_ApplyRetroCrunch)
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
    
    bpy.types.Scene.retro_fps = bpy.props.IntProperty(
        name="Target FPS", 
        default=12, 
        min=1, 
        max=60,
        description="Alters engine playback speed and scales timeline boundaries automatically"
    )
    
    bpy.types.Scene.retro_anim_preset = bpy.props.EnumProperty(
        name="Animation Preset",
        description="Choose the animation preset to apply to the retro text",
        items=[
            ('ROTATION', "Rotation Loop", "Spins the text over 120 frames"),
            ('BOUNCY_SCALE', "Bouncy Scale Up", "Scale text from 0 to full to 0"),
            ('WAVE', "Wavy animation", "Text letters moves up and down independently")
        ],
        default='ROTATION'
    )
    
    bpy.types.Scene.retro_export_path = bpy.props.StringProperty(
        name="Output Folder",
        subtype='DIR_PATH',
        default="//render/"
    )

def unregister():
    bpy.utils.unregister_class(RETRO_TEXT_OT_Create)
    bpy.utils.unregister_class(RETRO_TEXT_OT_SetupExport)
    bpy.utils.unregister_class(RETRO_TEXT_OT_ApplyRetroCrunch)
    bpy.utils.unregister_class(RETRO_TEXT_PT_Panel)
    del bpy.types.Scene.retro_text_input
    del bpy.types.Scene.retro_font_path
    del bpy.types.Scene.retro_text_extrude
    del bpy.types.Scene.retro_bevel_depth
    del bpy.types.Scene.retro_space_character
    del bpy.types.Scene.text_color
    del bpy.types.Scene.mat_metalic
    del bpy.types.Scene.retro_fps
    del bpy.types.Scene.retro_anim_preset
    del bpy.types.Scene.retro_export_path

if __name__ == "__main__":
    register()
