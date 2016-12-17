import os
import bpy
from bpy.types import Operator


def set_render_settings(resolution=None, encoding=None):
    """Sets the render dimensions and encoding settings based on presets
       The presets are stored in the .functions.global_settings module"""

    if not resolution and encoding:
        return None

    rd = bpy.context.scene.render
    ff = bpy.context.scene.render.ffmpeg
    res, enc = resolution, encoding

    rd.resolution_x = res[0]
    rd.resolution_y = res[1]
    rd.resolution_percentage = res[2]
    rd.pixel_aspect_x = res[3]
    rd.pixel_aspect_y = res[4]
    rd.fps = res[5]
    rd.fps_base = res[6]

    rd.image_settings.file_format = enc[0]

    ff.format = enc[1]
    ff.codec = enc[2]
    ff.gopsize = enc[3]
    ff.video_bitrate = enc[4]
    ff.maxrate = enc[5]
    ff.minrate = enc[6]
    ff.buffersize = enc[7]
    ff.packetsize = enc[8]
    ff.muxrate = enc[9]
    ff.audio_codec = enc[10]
    ff.audio_bitrate = enc[11]
    return True


# 1 click render video with correct encoding params for Youtube
# Auto sets the file name
# TODO: Give ability to easily render lower res videos using the proxies generated by revolver, if revolver is installed
#       Automatically switch to the proxy for rendering
# TODO: Auto mode - check if the strips are proxies or full res before calling
class RenderForWeb(Operator):
    bl_idname = "gdquest_vse.render_for_web"
    bl_label = "Render the video for the web"
    bl_description = "Pick a rendering preset and let Blender name and export the video for you"
    bl_options = {"REGISTER"}

    # from bpy.types import EnumProperty
    # TODO: Add menu to pick the rendering presets
    # TODO: Pass the rendering presets to set_render_dim using self.variables
    # TODO: add option to export to different folder
    # TODO: add file naming options

    from .functions.global_settings import RENDER_SETTINGS as RS
    resolution = RS.RESOLUTION.HD_FULL
    encoding = RS.ENCODING.MP4_HIGH
    # render_folder
    # file_name

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        if not bpy.data.is_saved:
            self.report({'WARNING'}, "Save your file first")
            return {'CANCELLED'}

        success = set_render_settings(self.resolution, self.encoding)
        if not success:
            self.report({'WARNING'}, "The rendering presets are not properly set. Cancelling operation")
            return {'CANCELLED'}

        # TODO: Replace with own proxy rendering system
        if 'velvet_revolver' in bpy.context.user_preferences.addons.keys():
            bpy.ops.sequencer.proxy_editing_tofullres()

        filename = bpy.path.basename(bpy.data.filepath)
        filename = os.path.splitext(filename)[0]
        filename += '.mp4'
        bpy.context.scene.render.filepath = "//" + filename if filename != "" else "Video.mp4"
        bpy.ops.render.render({'dict': "override"}, 'INVOKE_DEFAULT', animation=True)
        return {"FINISHED"}
