import bpy
import imbuf

bl_info = {
    "name": "Red Handed Tools",
    "blender": (3, 1, 0),
    "category": "Mesh"
}


class REDHANDED_OT_auto_project(bpy.types.Operator):
    """Crop and project a texture onto geometry"""
    bl_idname = "redhanded.autoproj"
    bl_label = "Auto project texture"

    def execute(self, context):
        canvas_obj = context.scene.rh_cam_full
        tool_obj = context.scene.rh_cam_tool
        canvas_cam = canvas_obj.data
        tool_cam = tool_obj.data
        if not isinstance(canvas_cam, bpy.types.Camera) or not isinstance(tool_cam, bpy.types.Camera):
            self.report({'ERROR'}, "One of the selected objects is not a camera.")
            return {'CANCELLED'}

        # Check valid input image
        original_img = context.scene.rh_img_full
        path = bpy.path.abspath(original_img)
        out_img = imbuf.load(path)  # Will get cropped later

        # Check valid scale
        canvas_scale = canvas_cam.ortho_scale
        tool_scale = tool_cam.ortho_scale
        if tool_scale > canvas_scale:
            self.report({'ERROR'}, "Tool camera has a higher scale than the canvas scale.")
            return {'CANCELLED'}

        # Check valid position
        tool_pos = tool_obj.location
        if abs(tool_pos[0]) + tool_scale / 2.0 > canvas_scale / 2.0 or abs(
                tool_pos[1]) + tool_scale / 2.0 > canvas_scale / 2.0:
            self.report({'ERROR'}, "Tool camera is not within canvas.")
            return {'CANCELLED'}

        # Calculate cropping bounds

        pixels_per_unit = out_img.size[0] / canvas_scale
        centre_px = out_img.size[0] / 2
        min_local = (tool_pos[0] - tool_scale / 2.0, tool_pos[1] - tool_scale / 2.0)
        max_local = (tool_pos[0] + tool_scale / 2.0, tool_pos[1] + tool_scale / 2.0)

        min_px = (int(min_local[0] * pixels_per_unit + centre_px), int(min_local[1] * pixels_per_unit + centre_px))
        max_px = (int(max_local[0] * pixels_per_unit + centre_px), int(max_local[1] * pixels_per_unit + centre_px))

        out_img.crop(min_px, max_px)
        out_path = bpy.path.abspath(context.scene.rh_img_output_dir) + 'out_' + bpy.path.basename(original_img)
        imbuf.write(out_img, filepath=out_path)

        # Show output image on tool camera
        reloaded_img = bpy.data.images.load(out_path, check_existing=False)
        tool_cam.show_background_images = True
        tool_cam.background_images.clear()
        tool_cam.background_images.new().image = reloaded_img

        return {'FINISHED'}


class VIEW3D_PT_auto_project(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Red Handed Tools'
    bl_label = 'Auto Texture Projection'

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.prop(context.scene, 'rh_img_output_dir')
        col.prop(context.scene, 'rh_cam_full')
        col.prop(context.scene, 'rh_cam_tool')
        col.prop(context.scene, 'rh_img_full')
        layout.operator('redhanded.autoproj')


blender_classes = [
    REDHANDED_OT_auto_project,
    VIEW3D_PT_auto_project
]


def register():
    bpy.types.Scene.rh_cam_full = bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Canvas camera",
        description="The camera that bounds the entire full-resolution image canvas",
    )
    bpy.types.Scene.rh_cam_tool = bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Tool camera",
        description="The camera to be used as a cropping tool. Also used for UV projection.",
    )
    bpy.types.Scene.rh_img_full = bpy.props.StringProperty(
        name="Image to project",
        description="The image to be cropped and projected onto the object",
        subtype='FILE_PATH'
    )
    bpy.types.Scene.rh_img_output_dir = bpy.props.StringProperty(
        name="Output directory",
        description="Root directory to place cropped images",
        subtype='DIR_PATH'
    )

    for m_class in blender_classes:
        bpy.utils.register_class(m_class)


def unregister():
    del bpy.types.Scene.rh_cam_full
    del bpy.types.Scene.rh_cam_tool
    del bpy.types.Scene.rh_img_full
    del bpy.types.Scene.rh_img_output_dir

    for m_class in blender_classes:
        bpy.utils.unregister_class(m_class)


if __name__ == '__main__':
    register()
