bl_info = {
    'name': 'Material Brush',
    'author': 'Francisco Elizade, Daniel Grauer',
    'version': (1, 0, 1),
    'blender': (2, 92, 0),
    'location': 'View3D - Texture Paint mode',
    'description': 'Paint all texture layers of materials simultaneously',
    'category': 'Image Paint',
    'wiki_url': 'https://github.com/kromar/blender_PBR_Brush',
}

import bpy
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

    action: bpy.props.EnumProperty(
        items=(
            ('SAVE', "Up", ""),
            ('LOAD', "Down", ""),
            ('UPDATE', "Update", ""),
        )
    )
    
    #temp_image = {}


    def invoke(self, context, event):        
        
        # List of brush materials
        scene = context.scene
        ob = context.active_object
        idx = scene.brush_index  
        self.temp_image = []
        
        #Operators inside lists    
        try:
            item = scene.listbrushmats[idx]
        except IndexError:
            pass
                
        if self.action == 'UPDATE':           
            scene.listbrushmats.clear()                            
            for i in range(len(bpy.data.materials)):
                if(bpy.data.materials[i] != bpy.context.active_object.active_material):
                    item = scene.listbrushmats.add()
                    item.id = len(scene.listbrushmats)
                    item.name = bpy.data.materials[i].name
                scene.brush_index = 0
            self.report({'INFO'}, "Updated Brush List")

        
        elif self.action == 'SAVE':
            #Save temporal image by texture_paint_slots in active object
            for i in range(18):
                chkslot = bpy.context.active_object.active_material.texture_paint_slots[i]
                if(chkslot != None):
                    tempimage = bpy.data.images.find(bpy.context.active_object.active_material.texture_paint_slots[i].texture.image.name)
                    bpy.data.images[tempimage].save()
                    #chkslot.texture.image.save()
            
            #pass
        
        elif self.action == 'LOAD':
            #reload saved temporal images to texture_paint_slots in active object
            #make sure we did not change last active object.
            for i in range(18):
                chkslot = bpy.context.active_object.active_material.texture_paint_slots[i]
                if(chkslot != None):
                    tempimage = bpy.data.images.find(bpy.context.active_object.active_material.texture_paint_slots[i].texture.image.name)
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
class PBRB_UL_brushitems(UIList):
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        split = layout.split(factor=0.8)
        split.prop(item, "name", text="", emboss=False, translate=False, icon='BRUSH_TEXDRAW')
        split.label(text="Index: %d" % (index))

    def invoke(self, context, event):
        pass
    
    
# draw the panel
class UIListMaterial(Panel):
    """Creates a Panel in the Object properties window"""
    bl_idname = 'OBJECT_PT_my_panel'
    bl_space_type = 'VIEW_3D'    
    bl_region_type = 'UI'
    bl_category = 'Tool'
    bl_context = 'imagepaint'
    bl_label = "Material Brush"

    def draw(self, context):
        layout = self.layout
        scene = bpy.context.scene

        rows = 2
        row = layout.row()
        row.label(text="Select Brush")
        col = row.column(align=True)
        col.operator("listbrushmats.list_action", icon='FILE_REFRESH', text="Update List").action = 'UPDATE'
        
        row = layout.row()
        row.template_list("PBRB_UL_brushitems", "", scene, "listbrushmats", scene, "brush_index", rows=rows)        
        

        row = layout.row()
        row.label(text="Alt+Left Mouse Button to paint")
        #layout.label(text="Save Painted Material")
        row = layout.row(align=True)
        row.operator("listbrushmats.list_action", text = "Save Textures").action = 'SAVE'
        row.operator("listbrushmats.list_action", text = "Reload Textures").action = 'LOAD'
        
        #row.label("Select Material:")
        #row = layout.row()
        #row.template_list("UL_items", "", scene, "listmaterials", scene, "custom_index", rows=rows)
        
        #set the texfaces using this material.
        brush_index = bpy.context.scene.brush_index      #brush iNdex
        #mn = bpy.context.scene.custom_index     #material iNdex        
        main(bpy.context, brush_index)

# Create custom property group
class CustomProp(bpy.types.PropertyGroup):
    '''name:  StringProperty() '''
    id: IntProperty()
    test: IntProperty()
    #temp_images = []
    
class material_paint(bpy.types.Operator):
    '''Paint material layers'''
    bl_idname = "paint.material_paint"
    bl_label = "Material paint"
    bl_options = {'REGISTER', 'UNDO'}
    time = 0
    stroke = []
 
    def fill_brush_stroke(self, x, y):
       
        brushstroke = {
            "name": "defaultStroke",
            "pen_flip": False,
            "is_start": False,
            "location": (0,0,0),
            "mouse": (x, y),
            "pressure": 1,
            "size": bpy.context.tool_settings.unified_paint_settings.size,
            "time": self.time,
            "x_tilt": 0,
            "y_tilt": 0
            }
               
        return brushstroke
   
    @classmethod
    def poll(cls, context):
        return bpy.ops.paint.image_paint.poll()
   
    def modal(self, context, event): 
        if event.type == 'MOUSEMOVE':
            self.stroke = []
            brushstroke = self.fill_brush_stroke(event.mouse_region_x, event.mouse_region_y)
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
            
            brush_index = bpy.context.scene.brush_index
            #mn = bpy.context.scene.custom_index
            
            move_x = event.mouse_region_x - self.last_mouse_x
            move_y = event.mouse_region_y - self.last_mouse_y
            move_length = math.sqrt(move_x * move_x + move_y * move_y)
            
            brush_spacing = stroke[0]["size"] * 2 * (bpy.context.tool_settings.image_paint.brush.spacing / 100) #40
            
            
            
            if (move_length >= brush_spacing):              #bpy.context.tool_settings.image_paint.brush.spacing
                if (self.lastmapmode == 'RANDOM'):
                    bpy.context.tool_settings.image_paint.brush.texture_slot.map_mode = 'TILED'
                    bpy.context.tool_settings.image_paint.brush.texture_slot.offset[0] = random.uniform(-2.0, 2.0)
                    bpy.context.tool_settings.image_paint.brush.texture_slot.offset[1] = random.uniform(-2.0, 2.0)
                    
                elif (self.lastmapmode == 'VIEW_PLANE'):
                    # map_mode = 'View Plane'
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
                           angle = math.pi - angle
                    bpy.context.tool_settings.image_paint.brush.texture_slot.angle = angle 
                
                    #self.offset = angcos, angle
                    #self.execute(context)
                    #context.area.header_text_set("Offset %.4f %.4f" % tuple(self.offset))
                
                #bpy.context.tool_settings.image_paint.brush.texture_slot.offset[1] -= move_y
                #event.mouse_region_x / bpy.context.region.width
                for i in range(18):
                    check_brush = bpy.data.materials[brush_index].texture_paint_slots[i]           # brush slot
                    check_material = bpy.context.object.active_material.texture_paint_slots[i]
                    if(check_brush != None):
                        brush_slot = bpy.data.materials[brush_index].texture_paint_slots[i].name
                        brush_texture_slot = bpy.data.textures[brush_slot]                                 # brush texture slot
                        bpy.context.tool_settings.image_paint.brush.texture = brush_texture_slot
                        if(check_material != None):
                            bpy.context.object.active_material.paint_active_slot = i                    
                            bpy.ops.paint.image_paint(stroke=stroke)
                        
                self.last_mouse_x = event.mouse_region_x
                self.last_mouse_y = event.mouse_region_y
                
            
            self.time = 0
            
            self.stroke = []
       
        elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            bpy.context.tool_settings.image_paint.brush.texture_slot.angle = self.lastangle
            bpy.context.tool_settings.image_paint.brush.texture_slot.map_mode = self.lastmapmode
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
            self.lastmapmode = bpy.context.tool_settings.image_paint.brush.texture_slot.map_mode
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
            
            brush_index = bpy.context.scene.brush_index
            #mn = bpy.context.scene.custom_index
            
            if (self.lastmapmode == 'RANDOM'):
                bpy.context.tool_settings.image_paint.brush.texture_slot.map_mode = 'TILED'
                bpy.context.tool_settings.image_paint.brush.texture_slot.offset[0] = random.uniform(-2.0, 2.0)
                bpy.context.tool_settings.image_paint.brush.texture_slot.offset[1] = random.uniform(-2.0, 2.0)
            
            elif (self.lastmapmode == 'VIEW_PLANE'):
                bpy.context.tool_settings.image_paint.brush.texture_slot.map_mode = 'TILED'
                # map_mode = 'View Plane'
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

            
            #TODO: replace this part with the new node texture system    
            
            #bpy.context.tool_settings.image_paint.brush.texture_slot.offset[1] -= move_y
            for i in range(len(bpy.data.materials[brush_index].texture_paint_slots)):
                check_brush = bpy.data.materials[brush_index].texture_paint_slots[i]           # brush slot
                check_material = bpy.context.object.active_material.texture_paint_slots[i]
                
                """  
                if(check_brush != None):
                    brush_slot = bpy.data.materials[brush_index].texture_paint_slots[i].name
                    brush_texture_slot = bpy.data.textures[brush_slot]                                 # brush texture slot
                    bpy.context.tool_settings.image_paint.brush.texture = brush_texture_slot
                    if(check_material != None):
                        bpy.context.object.active_material.paint_active_slot = i                    
                        bpy.ops.paint.image_paint(stroke=stroke) 
                #"""

            for mat in bpy.data.materials:
                material = bpy.data.materials[mat.name]
                if material.use_nodes:
                    print("material:", mat.name, "using nodes \n")
                    for node in material.node_tree.nodes:	
                        print("node: ", node.type)                                
                        if node.type == 'TEX_IMAGE' and node.image:
                            print("IMAGES: ", node.image.name, node.image)	
                        elif node.type == 'GROUP':
                            print("group found")


                
            #-----------------------------------#    
            
            self.time = 0
            
            self.stroke = []
            ###
            context.window_manager.modal_handler_add(self)
        
        return {'RUNNING_MODAL'}
    
# main definition
def main(context,brush_index):
    #brush_index is the index of the texture in the brush material list
    ob = context.active_object
    
    def invoke(self, context, event):
        info = 'Lets %s ' % ('see')
        self.report({'INFO'}, info)

# -------------------------------------------------------------------
# register
# -------------------------------------------------------------------
classes = (
    Uilist_actions,
    PBRB_UL_brushitems,
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