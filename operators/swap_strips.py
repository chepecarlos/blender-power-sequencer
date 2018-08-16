import bpy
from operator import attrgetter

class SwapStrips(bpy.types.Operator):
    """
    Swaps the 2 selected strips between them. More specific, places the first
    strip in the channel and starting frame (frame_final_start) of the second
    strip, and places the second strip in the channel and starting frame
    (frame_final_end) of the first strip. If there is no space for the swap, it 
    does nothing. If at least 1 of the selected strips is of effect type, the
    operator won't have any effect.
    """
    bl_idname = "power_sequencer.swap_strips"
    bl_label = "Swap Strips"
    bl_description = "Swaps the 2 selected strips between them"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return len(bpy.context.selected_sequences) == 2

    def execute(self, context):
        strip_1 = context.selected_sequences[0]
        strip_2 = context.selected_sequences[1]
        
        if strip_1.lock or strip_2.lock:
            return {'CANCELLED'}
        
        if hasattr(strip_1, 'input_1') or hasattr(strip_2, 'input_1'):
            return {'CANCELLED'}
        
        s1_start, s1_channel = strip_1.frame_final_start, strip_1.channel
        s2_start, s2_channel = strip_2.frame_final_start, strip_2.channel
        
        self.move_to_end(strip_1, context)
        self.move_to_end(strip_2, context)
        
        s1_start_2 = strip_1.frame_final_start
        s2_start_2 = strip_2.frame_final_start
        
        group_1 = {s:s.channel for s in context.sequences \
                if s.frame_final_start == s1_start_2 and s != strip_1}
        group_2 = {s:s.channel for s in context.sequences \
                if s.frame_final_start == s2_start_2 and s != strip_2}
        
        strip_2.select = False
        bpy.ops.transform.seq_slide(value=(s2_start - \
                strip_1.frame_final_start, s2_channel - strip_1.channel))
                
        bpy.ops.sequencer.select_all(action='DESELECT')
        strip_2.select = True
        bpy.ops.transform.seq_slide(value=(s1_start - \
                strip_2.frame_final_start, s1_channel - strip_2.channel))
                
        if not self.fits(strip_1, group_1, s2_start, s1_channel, s2_channel, \
                context) or not self.fits(strip_2, group_2, s1_start, \
                s2_channel, s1_channel, context):
            self.reconstruct(strip_1, s1_channel, group_1, context)
            self.reconstruct(strip_2, s2_channel, group_2, context)
            
            bpy.ops.sequencer.select_all(action='DESELECT')
            strip_1.select = True
            bpy.ops.transform.seq_slide(value=(s1_start - \
                    strip_1.frame_final_start, s1_channel - strip_1.channel))
                
            bpy.ops.sequencer.select_all(action='DESELECT')
            strip_2.select = True
            bpy.ops.transform.seq_slide(value=(s2_start - \
                    strip_2.frame_final_start, s2_channel - strip_2.channel))
                    
            bpy.ops.sequencer.select_all(action='DESELECT')
            strip_1.select = True
            strip_2.select = True
                
            return {'CANCELLED'}
        
        bpy.ops.sequencer.select_all(action='DESELECT')
        strip_1.select = True
        strip_2.select = True
        
        return {'FINISHED'}

    def move_to_frame(self, strip, frame, context):
        """
        Moves a strip based on its frame_final_start without changing its
        duration.
        Args:
        - strip: The strip to be moved.
        - frame: The frame, the frame_final_start of the strip will be placed 
                 at.
        """
        selected_strips = context.selected_sequences
        bpy.ops.sequencer.select_all(action='DESELECT')
        strip.select = True
        
        bpy.ops.transform.seq_slide(value=(frame - strip.frame_final_start, 0))
        
        bpy.ops.sequencer.select_all(action='DESELECT')
        for s in selected_strips:
            s.select = True
        
    def move_to_end(self, strip, context):
        """
        Moves a strip to an empty slot at the end of the sequencer, different 
        than its initial slot.
        Args:
        - strip: The strip to move.
        """
        end_frame = max(context.sequences, key=attrgetter('frame_final_end'))\
                .frame_final_end
        self.move_to_frame(strip, end_frame, context)
        
    def fits(self, strip, group, frame, init_channel, target_channel, context):
        """
        Checks if a swap has been successful or not.
        Args:
        - strip: The core strip of the swap.
        - group: The effect strips of the core strip.
        - frame: The starting frame of the target location.
        - init_channel: The initial channel of the strip, before the swap took
                        place.
        - target_channel: The channel of the target location.
        Returns: True if the swap was successful, otherwise False.
        """
        if strip.frame_final_start != frame or strip.channel != target_channel:
            return False
        
        offset = strip.channel - init_channel
        for s in group.keys():
            if s.channel != group[s] + offset:
                return False
        
        return True
    
    def reconstruct(self, strip, init_channel, group, context):
        """
        Reconstructs a failed swap, based on a core strip. After its done, the
        core strip is placed at the end of the sequencer, in an empty slot.
        Args:
        - strip: The core strip of the swap.
        - init_channel: The initial channel of the core strip.
        - group: A dictionary with the effect strips of the core strip, and
                 their target channels.
        """
        self.move_to_end(strip, context)
        bpy.ops.sequencer.select_all(action='DESELECT')
        strip.select = True
        bpy.ops.transform.seq_slide(value=(0, init_channel - strip.channel))
        
        for s in group.keys():
            channel = group[s]
            for u in group.keys():
                if u.channel == channel and u != s:
                    u.channel += 1
            s.channel = channel
