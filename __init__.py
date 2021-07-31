bl_info = {
    'name': 'Material Brush',
    'description': 'Paint Material image channels at once',
    'author': 'Daniel Grauer, Francisco Elizade',
    'version': (2, 0, 0),
    'blender': (2, 92, 0),
    'location': "View3D > Sidebar > Edit Tab",
    'category': 'Image Paint',
    'wiki_url': 'https://github.com/kromar/blender_Material_Brush',
}

import bpy
from bpy.utils import register_class, unregister_class
from bpy.types import Operator, Brush

    
class PaintStroke(Operator):
    '''paintstroke'''
    bl_idname = "paint.paintstroke"
    bl_label = "paintstroke"
    bl_options = {'REGISTER', 'UNDO'}
    
    stroke = []
    
    def create_paint_stroke(self, event):   
        brushstroke = {
            "name": "defaultStroke",
            "pen_flip": False,
            "is_start": False,
            "location": (0,0,0),
            "mouse": (event.mouse_region_x, event.mouse_region_y),
            "pressure": 1,
            "size": bpy.context.tool_settings.unified_paint_settings.size,
            "time": 0,
            "mouse_event": (0.0, 0.0),
            "x_tilt": 0,
            "y_tilt": 0,
            }
        return brushstroke


    def collect_paint_strokes(self, event):
        brushstroke = self.create_paint_stroke(event)  
        brush = 'TexDraw'   #TODO: feed with active brush name
        if bpy.data.brushes[brush].use_pressure_strength:
            brushstroke["pressure"] = bpy.data.brushes[brush].strength * event.pressure  
        else:
            brushstroke["pressure"] = bpy.data.brushes[brush].strength
        self.stroke = [brushstroke]

    def paint(self, event):     
        self.collect_paint_strokes(event)         
        print(self.stroke)   
        bpy.ops.paint.image_paint(stroke=self.stroke, mode='NORMAL')


    @classmethod
    def poll(cls, context):
        return bpy.ops.paint.image_paint.poll()
        
    def modal(self, context, event): 
        #print("MB keybinding test modal")
        if event.type in {'MOUSEMOVE'}:   
            self.paint(event)         
        elif event.value in {'RELEASE'} or event.type in {'ESC'}:
            return {'FINISHED'}  
        return {'PASS_THROUGH'}
    

    def invoke(self, context, event):
        if event.type in {'LEFTMOUSE'}:               
            self.paint(event)         
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
    

classes = (
    PaintStroke,    
    )


addon_keymaps = []

def register():  
    [register_class(c) for c in classes]
    
    # Keymapping
    kc = bpy.context.window_manager.keyconfigs.addon
    km = kc.keymaps.new(name="Image Paint", space_type='EMPTY', modal=False)
    kmi = km.keymap_items.new("paint.paintstroke", type='LEFTMOUSE', value='PRESS', shift=False, ctrl=False , alt=True)
    kmi.active = True
    addon_keymaps.append((km, kmi))
    


def unregister():    
    # remove keymaps
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()    
    
    [unregister_class(c) for c in classes]
        

if __name__ == "__main__":
    register()        