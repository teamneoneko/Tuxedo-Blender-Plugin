import bpy
import typing
from bpy.utils import register_class, unregister_class

classes = []
ordered_classes = []
properties_registry = []  
initial_scene_props = set()
initial_object_props = set()

#Stolen from cats. I will not pretend or say I made this - @989onan
def wrapper_registry(class_obj):
    if hasattr(class_obj, 'bl_rna'):
        classes.append(class_obj)
    return class_obj

def register_property(obj_type, prop_name, prop_def):
    """Register a property and track it for cleanup"""
    setattr(obj_type, prop_name, prop_def)
    properties_registry.append((obj_type, prop_name))

def _capture_initial_properties():
    """Capture initial properties before registration"""
    global initial_scene_props, initial_object_props
    initial_scene_props = set(dir(bpy.types.Scene))
    initial_object_props = set(dir(bpy.types.Object))

def _track_new_properties():
    """Find and track all newly added properties"""
    global properties_registry
    
    # Find new Scene properties
    current_scene_props = set(dir(bpy.types.Scene))
    new_scene_props = current_scene_props - initial_scene_props
    for prop in new_scene_props:
        if not prop.startswith('_'):
            properties_registry.append((bpy.types.Scene, prop))
    
    # Find new Object properties  
    current_object_props = set(dir(bpy.types.Object))
    new_object_props = current_object_props - initial_object_props
    for prop in new_object_props:
        if not prop.startswith('_'):
            properties_registry.append((bpy.types.Object, prop))

def order_classes():
    deps_dict = {}
    classes_to_register = set(iter_classes_to_register())
    for class_obj in classes_to_register:
        deps_dict[class_obj] = set(iter_own_register_deps(class_obj, classes_to_register))

    ordered_classes.clear()
    # Then put everything else sorted into the list
    for class_obj in toposort(deps_dict):
        ordered_classes.append(class_obj)

def register_all():
    """Register all classes and properties in correct order"""
    print("========= STARTING TUXEDO REGISTRY =========")
    
    # On re-enable, use ordered_classes if classes is empty
    if not classes and ordered_classes:
        classes.extend(ordered_classes)
    elif not classes:
        # If both are empty, rebuild from modules
        _rebuild_classes_from_modules()
    
    _capture_initial_properties()
    if not ordered_classes:
        order_classes()
    
    # Register classes (use ordered_classes if available)
    classes_to_register = ordered_classes if ordered_classes else classes
    for cls in classes_to_register:
        try:
            register_class(cls)
            try:
                print("registered class " + cls.bl_label)
            except Exception as e:
                print("tried to register class with no label.")
                print(e)
        except ValueError as e1:
            if "already registered" in str(e1):
                try:
                    print(f"skipped already registered class {cls.bl_label}")
                except:
                    print(f"skipped already registered class")
            else:
                try:
                    print("failed to register " + cls.bl_label)
                    print(e1)
                except Exception as e2:
                    print("tried to register class with no label.")
                    print(e1)
                    print(e2)

def _rebuild_classes_from_modules():
    """Rebuild classes list by re-importing decorated modules"""
    global classes
    import importlib
    import sys
    import glob
    from os.path import dirname, basename, isfile, join
    
    # Re-import key modules that contain @wrapper_registry decorators
    try:
        from . import bake
        importlib.reload(bake)
    except Exception as e:
        print(f"Failed to reload bake: {e}")
    
    try:
        from . import ui
        importlib.reload(ui)
    except Exception as e:
        print(f"Failed to reload ui: {e}")
    
    # Reload all ui_sections
    try:
        ui_sections_path = join(dirname(__file__), "ui_sections")
        modules = glob.glob(join(ui_sections_path, "*.py"))
        for module_file in modules:
            if isfile(module_file) and not module_file.endswith('__init__.py'):
                module_name = basename(module_file)[:-3]
                try:
                    exec(f"from .ui_sections import {module_name}")
                    mod = sys.modules.get(f"unofficial_tuxedo_blender_plugin.ui_sections.{module_name}")
                    if mod:
                        importlib.reload(mod)
                except Exception as e:
                    print(f"Failed to reload ui_sections.{module_name}: {e}")
    except Exception as e:
        print(f"Failed to reload ui_sections: {e}")
    
    # Reload all tools modules
    try:
        tools_path = join(dirname(__file__), "tools")
        modules = glob.glob(join(tools_path, "*.py"))
        for module_file in modules:
            if isfile(module_file) and not module_file.endswith('__init__.py'):
                module_name = basename(module_file)[:-3]
                try:
                    exec(f"from .tools import {module_name}")
                    mod = sys.modules.get(f"unofficial_tuxedo_blender_plugin.tools.{module_name}")
                    if mod:
                        importlib.reload(mod)
                except Exception as e:
                    print(f"Failed to reload tools.{module_name}: {e}")
    except Exception as e:
        print(f"Failed to reload tools: {e}")

def unregister_all():
    """Unregister all classes and properties in reverse order"""
    print("========= DEREGISTERING TUXEDO =========")
    
    # Track any new properties added since last registration
    _track_new_properties()
    
    # Unregister classes in reverse order
    for cls in reversed(classes):
        try:
            unregister_class(cls)
        except (RuntimeError, ValueError) as e:
            pass
    
    # Unregister properties in reverse order
    for obj_type, prop_name in reversed(properties_registry):
        if hasattr(obj_type, prop_name):
            try:
                delattr(obj_type, prop_name)
            except Exception as e:
                print(f"Failed to delete {obj_type.__name__}.{prop_name}: {e}")
    
    # Clear registries (do this AFTER trying to unregister, not before or ir causes issues)
    classes.clear()
    properties_registry.clear()
    initial_scene_props.clear()
    initial_object_props.clear()
    
    print("========= DEREGISTERING TUXEDO FINISHED =========")


def iter_classes_to_register():
    for class_obj in classes:
        yield class_obj


def iter_own_register_deps(class_obj, own_classes):
    yield from (dep for dep in iter_register_deps(class_obj) if dep in own_classes)


def iter_register_deps(class_obj):
    for value in typing.get_type_hints(class_obj, {}, {}).values():
        dependency = get_dependency_from_annotation(value)
        if dependency is not None:
            yield dependency


def get_dependency_from_annotation(value):
    if isinstance(value, tuple) and len(value) == 2:
        if value[0] in (bpy.props.PointerProperty, bpy.props.CollectionProperty):
            return value[1]["type"]
    return None


# Find order to register to solve dependencies
#################################################

def toposort(deps_dict):
    sorted_list = []
    sorted_values = set()
    while len(deps_dict) > 0:
        unsorted = []
        for value, deps in deps_dict.items():
            if len(deps) == 0:
                sorted_list.append(value)
                sorted_values.add(value)
            else:
                unsorted.append(value)
        deps_dict = {value : deps_dict[value] - sorted_values for value in unsorted}
    
    sort_order(sorted_list) #to sort by 'bl_order' so we can choose how things may appear in the ui
    return sorted_list

def sort_order(sorted_list):
    ordered_list = []
    for classei in sorted_list:
        if hasattr(classei, 'bl_order'):
            ordered_list.append(classei)
            sorted_list.remove(classei)
    ordered_list.sort(key=lambda x: x.bl_order, reverse=False)
    sorted_list.extend(ordered_list)
