bl_info = {
    'name': 'MultiBrush Material Brush Painter',
    'author': 'Francisco Elizade, Daniel Grauer',
    'version': (1, 0, 0),
    'blender': (2, 92, 0),
    'location': 'View3D - Texture Paint mode',
    'description': 'Paint all texture layers of materials simultaneously',
    'category': 'Image Paint',
    'wiki_url': '',
}

import bpy
import mathutils
import math
import random
import copy
import string
from bpy.utils import register_class, unregister_class
from bpy.props import IntProperty, StringProperty, CollectionProperty
from bpy.types import Panel, UIList

# return name of selected object
def get_activeSceneObject():
    return bpy.context.scene.objects.active.name


# ui list item actions
class Uilist_actions(bpy.types.Operator):
    bl_idname = "listbrushmats.list_action"
    bl_label = "List Action"

    action = bpy.props.EnumProperty(
        items=(
            ('SAVE', "Up", ""),
            ('LOAD', "Down", ""),
            ('UPDATE', "Update", ""),
        )
    )
    
    #temp_image = {}

    def invoke(self, context, event):        
        
        # List of brush materials
        scn = context.scene
        ob = context.active_object
        idx = scn.brush_index
        
        
        self.temp_image = []
        
        #Operators inside lists
    
        try:
            item = scn.listbrushmats[idx]
        except IndexError:
            pass
                
        if self.action == 'UPDATE':            
            #list of brushes
            lst = scn.listbrushmats
            #current_index = scn.custom_index

            if len(lst) > 0:
                 # reverse range to remove last item first
                for i in range(len(lst)-1,-1,-1):
                    scn.listbrushmats.remove(i)

            else:
                self.report({'INFO'}, "Nothing to update")
                
            matLen = len(bpy.data.materials)
            for i in range(0,matLen):
                if(bpy.data.materials[i].name != 'TempMat'):
                    item = scn.listbrushmats.add()
                    item.id = len(scn.listbrushmats)
                    item.name = bpy.data.materials[i].name
                scn.brush_index = 0
        
        elif self.action == 'SAVE':
            #Save temporal image by texture_slots in active object
            for i in range(18):
                chkslot = bpy.context.active_object.active_material.texture_slots[i]
                if(chkslot != None):
                    tempimage = bpy.data.images.find(bpy.context.active_object.active_material.texture_slots[i].texture.image.name)
                    bpy.data.images[tempimage].save()
                    #chkslot.texture.image.save()
            
            #pass
        
        elif self.action == 'LOAD':
            #reload saved temporal images to texture_slots in active object
            #make sure we did not change last active object.
            for i in range(18):
                chkslot = bpy.context.active_object.active_material.texture_slots[i]
                if(chkslot != None):
                    tempimage = bpy.data.images.find(bpy.context.active_object.active_material.texture_slots[i].texture.image.name)
                    bpy.data.images[tempimage].reload()
                    
            for area in bpy.context.screen.areas:
                if area.type in ['IMAGE_EDITOR', 'VIEW_3D']:
                    area.tag_redraw()
            #bpy.ops.wm.redraw_timer(type='DRAW', iterations=1)
            #pass
            
        
        return {"FINISHED"}             

# -------------------------------------------------------------------
# draw
# -------------------------------------------------------------------
    
# custom list
class UL_brushitems(UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        split = layout.split(factor=0.3)
        split.label(text="Index: %d" % (index))
        split.prop(item, "name", text="", emboss=False, translate=False, icon='MATERIAL')

    def invoke(self, context, event):
        pass
    
# personalizado list
#class UL_items(UIList):


# draw the panel
class UIListMaterial(Panel):
    """Creates a Panel in the Object properties window"""
    bl_idname = 'OBJECT_PT_my_panel'
    bl_space_type = 'VIEW_3D'    
    bl_region_type = 'UI'
    bl_category = 'Tool'

    bl_context = 'imagepaint'

    bl_label = "MultiBrush: Material Brush Paint"

    def draw(self, context):
        layout = self.layout
        scn = bpy.context.scene

        rows = 2
        row = layout.row()
        row.label(text="Select Brush:")
        col = row.column(align=True)
        col.operator("listbrushmats.list_action", icon='GROUP_VCOL', text="").action = 'UPDATE'
        
        row = layout.row()
        row.template_list("UL_brushitems", "", scn, "listbrushmats", scn, "brush_index", rows=rows)
        
        
        row = layout.row()
        layout.label(text="Save Material:")
        row = layout.row(align=True)
        row.operator("listbrushmats.list_action", text = "Save Images").action = 'SAVE'
        row.operator("listbrushmats.list_action", text = "Reload Images").action = 'LOAD'
        
        #row.label("Select Material:")
        #row = layout.row()
        #row.template_list("UL_items", "", scn, "listmaterials", scn, "custom_index", rows=rows)
        
        #set the texfaces using this material.
        bn = bpy.context.scene.brush_index      #brush iNdex
        #mn = bpy.context.scene.custom_index     #material iNdex        
        main(bpy.context, bn)

# Create custom property group
class CustomProp(bpy.types.PropertyGroup):
    '''name = StringProperty() '''
    id = IntProperty()
    prueba = IntProperty()
    #temp_images = []
    
class material_paint(bpy.types.Operator):
    '''Paint material layers'''
    bl_idname = "paint.material_paint"
    bl_label = "Material paint"
    bl_options = {'REGISTER', 'UNDO'}
    time = 0
    stroke = []
 
    def fill_brush_stroke(self, x, y):
       
        brushstroke = {"name":"defaultStroke",
                "pen_flip":False,
                "is_start":False,
                "location":(0,0,0),
                "mouse":(x, y),
                "pressure":1,
                "size": bpy.context.tool_settings.unified_paint_settings.size,      #bpy.context.tool_settings.unified_paint_settings.size
                "time": self.time
               }
               
        return brushstroke
   
    @classmethod
    def poll(cls, context):
        return bpy.ops.paint.image_paint.poll()
   
    def modal(self, context, event): 
        if event.type == 'MOUSEMOVE':
            self.stroke = []
            brushstroke = self.fill_brush_stroke(event.mouse_region_x,
                                       event.mouse_region_y)
            brushstroke["is_start"] = True
            self.stroke.append(copy.deepcopy(brushstroke))
            brushstroke["is_start"] = False
            self.stroke.append(brushstroke)
            args = (self, context)
                
            x = self.stroke[0]["mouse"][0]
            y = self.stroke[0]["mouse"][1] 
            stroke = []
            self.time = 0.0
            stroke.append( self.fill_brush_stroke( x, y ) )
            stroke[0]["is_start"] = True
            
            bn = bpy.context.scene.brush_index
            #mn = bpy.context.scene.custom_index
            
            move_x = event.mouse_region_x - self.last_mouse_x
            move_y = event.mouse_region_y - self.last_mouse_y
            move_length = math.sqrt(move_x * move_x + move_y * move_y)
            
            brush_spacing = stroke[0]["size"] * 2 * (bpy.context.tool_settings.image_paint.brush.spacing / 100) #40
            
            
            
            if (move_length >= brush_spacing):              #bpy.context.tool_settings.image_paint.brush.spacing
                if (self.lastmapmode == 'RANDOM'):
                    bpy.context.tool_settings.image_paint.brush.texture_slot.tex_paint_map_mode = 'TILED'
                    bpy.context.tool_settings.image_paint.brush.texture_slot.offset[0] = random.uniform(-2.0, 2.0)
                    bpy.context.tool_settings.image_paint.brush.texture_slot.offset[1] = random.uniform(-2.0, 2.0)
                    
                elif (self.lastmapmode == 'VIEW_PLANE'):
                    # tex_paint_map_mode = 'View Plane'
                    offset_x = event.mouse_region_x - (bpy.context.region.width/2)
                    offset_x = offset_x / stroke[0]["size"]
                    bpy.context.tool_settings.image_paint.brush.texture_slot.offset[0] = offset_x * -1
                    offset_y = event.mouse_region_y - (bpy.context.region.height/2)
                    offset_y = offset_y / stroke[0]["size"]
                    bpy.context.tool_settings.image_paint.brush.texture_slot.offset[1] = offset_y * -1 - math.ceil(stroke[0]["size"] / 25)
                    
                    #-----------------------------------#
            
                if(bpy.context.tool_settings.image_paint.brush.texture_slot.use_random == True):
                    randomangle = bpy.context.tool_settings.image_paint.brush.texture_slot.random_angle
                    bpy.context.tool_settings.image_paint.brush.texture_slot.angle = random.uniform(0.0, randomangle)
                        
                elif(bpy.context.tool_settings.image_paint.brush.texture_slot.use_rake == True):
                    angcos = move_x / move_length
                    angsin = move_y / move_length
                    angle = math.atan2(angsin, angcos)
                    if(angle < 0):
                           angle = 3.1415927410125732 + (angle * -1)
                    bpy.context.tool_settings.image_paint.brush.texture_slot.angle = angle 
                
                    #self.offset = angcos, angle
                    #self.execute(context)
                    #context.area.header_text_set("Offset %.4f %.4f" % tuple(self.offset))
                
                #bpy.context.tool_settings.image_paint.brush.texture_slot.offset[1] -= move_y
                #event.mouse_region_x / bpy.context.region.width
                for i in range(18):
                    chk_brush = bpy.data.materials[bn].texture_slots[i]           # brush slot
                    chk_mat = bpy.context.object.active_material.texture_slots[i]
                    if(chk_brush != None):
                        bs = bpy.data.materials[bn].texture_slots[i].name
                        bts = bpy.data.textures[bs]                                 # brush texture slot
                        bpy.context.tool_settings.image_paint.brush.texture = bts
                        if(chk_mat != None):
                            bpy.context.object.active_material.paint_active_slot = i                    
                            bpy.ops.paint.image_paint(stroke=stroke)
                        
                self.last_mouse_x = event.mouse_region_x
                self.last_mouse_y = event.mouse_region_y
                
            
            self.time = 0
            
            self.stroke = []
       
        elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            bpy.context.tool_settings.image_paint.brush.texture_slot.angle = self.lastangle
            bpy.context.tool_settings.image_paint.brush.texture_slot.tex_paint_map_mode = self.lastmapmode
            bpy.context.tool_settings.image_paint.brush.texture = self.lastBrush
            bpy.context.object.active_material.paint_active_slot = self.lastSlot
            bpy.context.tool_settings.image_paint.brush.texture_slot.offset[0]=0
            bpy.context.tool_settings.image_paint.brush.texture_slot.offset[1]=0
            #bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'FINISHED'}
            
        return {'RUNNING_MODAL'}
   
    def invoke(self, context, event):
        if (event.type == 'LEFTMOUSE'):
            self.last_mouse_x = event.mouse_region_x
            self.last_mouse_y = event.mouse_region_y
            
            self.lastangle = bpy.context.tool_settings.image_paint.brush.texture_slot.angle
            self.lastmapmode = bpy.context.tool_settings.image_paint.brush.texture_slot.tex_paint_map_mode
            self.lastBrush = bpy.context.tool_settings.image_paint.brush.texture
            self.lastSlot = bpy.context.object.active_material.paint_active_slot
            ###  
            self.stroke = []
            brushstroke = self.fill_brush_stroke(event.mouse_region_x,
                                       event.mouse_region_y)        # First position
            brushstroke["is_start"] = True
            self.stroke.append(copy.deepcopy(brushstroke))
            brushstroke["is_start"] = False
            self.stroke.append(brushstroke)
            args = (self, context)
                
            x = self.stroke[0]["mouse"][0]
            y = self.stroke[0]["mouse"][1] 
            stroke = []
            self.time = 0.0
            stroke.append( self.fill_brush_stroke( x, y ) )
            stroke[0]["is_start"] = True
            
            bn = bpy.context.scene.brush_index
            #mn = bpy.context.scene.custom_index
            
            if (self.lastmapmode == 'RANDOM'):
                bpy.context.tool_settings.image_paint.brush.texture_slot.tex_paint_map_mode = 'TILED'
                bpy.context.tool_settings.image_paint.brush.texture_slot.offset[0] = random.uniform(-2.0, 2.0)
                bpy.context.tool_settings.image_paint.brush.texture_slot.offset[1] = random.uniform(-2.0, 2.0)
            
            elif (self.lastmapmode == 'VIEW_PLANE'):
                bpy.context.tool_settings.image_paint.brush.texture_slot.tex_paint_map_mode = 'TILED'
                # tex_paint_map_mode = 'View Plane'
                offset_x = event.mouse_region_x - (bpy.context.region.width/2)
                offset_x = offset_x / stroke[0]["size"]
                bpy.context.tool_settings.image_paint.brush.texture_slot.offset[0] = offset_x * -1            
                offset_y = event.mouse_region_y - (bpy.context.region.height/2)
                offset_y = offset_y / stroke[0]["size"]
                bpy.context.tool_settings.image_paint.brush.texture_slot.offset[1] = offset_y * -1 - math.ceil(stroke[0]["size"] / 25)
                #self.offset = offset_x, offset_y
                #self.execute(context)
                #context.area.header_text_set("Offset %.4f %.4f" % tuple(self.offset))
                #-----------------------------------#
                
            if(bpy.context.tool_settings.image_paint.brush.texture_slot.use_random == True):
                randomangle = bpy.context.tool_settings.image_paint.brush.texture_slot.random_angle
                bpy.context.tool_settings.image_paint.brush.texture_slot.angle = random.uniform(0.0, randomangle)
            
            elif(bpy.context.tool_settings.image_paint.brush.texture_slot.use_rake == True):
                    #angcos = move_x / move_length
                    #angsin = move_y / move_length
                    #angle = math.atan2(angsin, angcos)
                    bpy.context.tool_settings.image_paint.brush.texture_slot.angle = 0
                    
            #bpy.context.tool_settings.image_paint.brush.texture_slot.offset[1] -= move_y
            for i in range(18):
                chk_brush = bpy.data.materials[bn].texture_slots[i]           # brush slot
                chk_mat = bpy.context.object.active_material.texture_slots[i]
                if(chk_brush != None):
                    bs = bpy.data.materials[bn].texture_slots[i].name
                    bts = bpy.data.textures[bs]                                 # brush texture slot
                    bpy.context.tool_settings.image_paint.brush.texture = bts
                    if(chk_mat != None):
                        bpy.context.object.active_material.paint_active_slot = i                    
                        bpy.ops.paint.image_paint(stroke=stroke)
            
            self.time = 0
            
            self.stroke = []
            ###
            context.window_manager.modal_handler_add(self)
            
            
        
        return {'RUNNING_MODAL'}
    
# main definition
def main(context,bn):
    #bn is the index of the texture in the brush material list
    ob = context.active_object
    
    def invoke(self, context, event):
        info = 'Lets %s ' % ('see')
        self.report({'INFO'}, info)

# -------------------------------------------------------------------
# register
# -------------------------------------------------------------------
classes = (
    Uilist_actions,
    UL_brushitems,
    UIListMaterial,
    CustomProp,
    material_paint,    
    )


def register():    
    [register_class(c) for c in classes]

    bpy.types.Scene.listbrushmats = CollectionProperty(type=CustomProp)
    km = bpy.context.window_manager.keyconfigs.default.keymaps['Image Paint']
    kmi = km.keymap_items.new("paint.material_paint", 'LEFTMOUSE', 'PRESS', alt=True)
    bpy.types.Scene.brush_index = IntProperty()
    #bpy.types.Scene.brush_slots_num = IntProperty()
    
    #bpy.types.Scene.listmaterials = CollectionProperty(type=CustomProp)
    #bpy.types.Scene.custom_index = IntProperty()

def unregister():    
    [unregister_class(c) for c in classes]
        
    del bpy.types.Scene.listbrushmats
    km = bpy.context.window_manager.keyconfigs.default.keymaps['Image Paint']
    kmi = km.keymap_items.find('paint.material_paint')
    km.keymap_items.remove(km.keymap_items[kmi])
    
    del bpy.types.Scene.brush_index
    #bpy.types.Scene.brush_slots_num = IntProperty()
    
    
    #del bpy.types.Scene.listmaterials
    #del bpy.types.Scene.custom_index

if __name__ == "__main__":
    register()