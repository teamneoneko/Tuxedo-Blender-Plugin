import bpy
import os
from .bake import BakeAddCopyOnly, BakeAddProp, BakeButton, BakePresetAll, BakePresetDesktop, BakePresetGmod, BakePresetGmodPhong, BakePresetQuest, BakePresetSecondlife, BakeRemoveCopyOnly, BakeRemoveProp, BakeTutorialButton
from .ui import BakePanel, Bake_Lod_Delete, Bake_Lod_New, Bake_Platform_Delete, Bake_Platform_List, Bake_Platform_New, Choose_Steam_Library, Open_GPU_Settings, ToolPanel, SmartDecimation, FT_Shapes_UL

from .class_register import register_all, unregister_all
from .properties import set_steam_library, register_properties


import glob
from os.path import dirname, basename, isfile, join

modules = glob.glob(join(dirname(__file__), "ui_sections/*.py"))
for module_name in [ basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py')]:
    exec("from .ui_sections import "+module_name)
#tools importing same bad way
modules = glob.glob(join(dirname(__file__), "tools/*.py"))
for module_name in [ basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py')]:
    exec("from .tools import "+module_name)
from bpy.types import Scene
from sys import platform
from .ui_sections.advanced_platform_options import Bake_PT_advanced_platform_options

from . import globals


def register():
    register_all()
    # Properties
    register_properties()
    custom_icons()
    #needs to be after registering properties, because it accesses a property - @989onan
    print("========= READING STEAM REGISTRY KEYS FOR GMOD =========")
    
    try:
        import subprocess
        import sys
        batch_path = ""
        if platform == "linux":
            batch_path = dirname(__file__)+"/assets/tools/readsteamlinux.sh"
        elif platform == "darwin":
            batch_path = dirname(__file__)+"/assets/tools/readsteammac.sh"
        else:
            batch_path = dirname(__file__)+"/assets/tools/readregistrysteamkey.bat"
        process = subprocess.Popen([batch_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = process.communicate()
        
        if out:
            print("found steam install, it is")
            print(out)
            libraryfolders = str(out.decode()).replace("b", "").strip().replace("\"","")[:-9]+"steamapps/libraryfolders.vdf"
            
            print("rooting around in your steam libraries for gmod...")
            f = open(libraryfolders, "r")
            library_path = ""
            for line in f.readlines():
                #print(line)
                
                if line.strip().startswith("\"path\""):
                    print("previous found library didn't have garry's mod")
                    
                    
                    library_path = line.strip().replace("\\\\", "/").replace("\"path\"", "").strip().replace("\"","")+"/"
                    print("found a library: "+library_path)
                else:
                    if line.strip().startswith("\"4000\""):
                        print("above library has garrys mod, setting to that.")
                        set_steam_library(library_path)
                        break
                
        else:
            print("could not find steam install! Please check your steam installation!")
        if properties.get_steam_library(None) == "":
            print("previous found library didn't have garry's mod")
            print("!!Could not find garry's mod install!!")
    except Exception as e:
        print("Could not read steam libraries! Error below.")
        print(e)
    print("========= FINISHED READING STEAM REGISTRY KEYS FOR GMOD =========")



def custom_icons():
    import bpy.utils.previews
    globals.icons_dict = bpy.utils.previews.new()
    icons_dir = os.path.join(os.path.dirname(__file__), "images", "icons")

    for icon,file in globals.icon_names.items():
        globals.icons_dict.load(icon, os.path.join(icons_dir, file), 'IMAGE')


def unregister():
    unregister_all()
    if hasattr(globals, 'icons_dict'):
        bpy.utils.previews.remove(globals.icons_dict)

if __name__ == '__main__':
    register()
