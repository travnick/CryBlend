# Changelog:

## 5.2
#### Compatibility:
* Only compatible with CryEngine 3.5 and up.
* Only compatible with Blender 2.7 and up.
* Supports primary assets: CGF, CGA, CHR, SKIN, ANM, I_CAF.
* Compatible with LumberYard.

#### UI Changes:
* Added new Animation Node menuitem to create I_CAF and ANM nodes.
* Added new Export Animation menuitem to separate animation and mesh exporting.

#### New Features:
* Support multiple I_CAF and ANM animation files exporting.
* Animation and character nodes can be located in same project.

#### Improvements/Fixes:
* CGA and ANM exporting have been fixed.
* Mesh exporting logs have been improved.

## 5.1
#### Compatibility:
* Only compatible with CryEngine 3.5 and up.
* Only compatible with Blender 2.7 and up.
* Supports primary assets: CGF, CGA, CHR, SKIN, ANM, I_CAF.
* Compatible with LumberYard.

#### UI Changes:
* Apply Scale Animation.
* Edit Inverse Kinematics panel in Bone Utilities.
* Do materials and fix weight default were set to false in export menu.
* Add Property is changed with User Defined Properties menu.
* Same options in quick menu, left tab panel and main menu.

#### New Features:
* Skeleton Physic.
* New Inverse Kinematics Bone Panel in Bone Utilities.
* Cycles render material support.
* Completely new interactive User Defined Property system.
* Added apply rotation and scale for skeleton that have animation without break bone.
* Delete .animsettings, .caf, .$animsettings files if there are exist for clean reexport animation.
* Set main material name which show in cryengine.
* Change selected material physic in Do Material panel.
* More material notation formats supported.
* New material management options.
* Proxies improvement.
* Export only selected nodes.
* Game folder selection to better management of textures.
* Remove unused vertex groups option.

#### Improvements/Fixes:
* Texture export fix.
* Skeleton Animation.
* Blender 2.74 and up Skeleton and Animation support.
* Now bone names replace double underscore with whitespace like maya.
* CGF file is processed one time by rc.
* Proxies problems.
* Faster skin export.
* More than 8 bones per vertex fix.
* Residual vertex groups in skins generating problems.
* Problem creating few branches in touch bending.

## 5.0
#### Compatibility:
* Only compatible with CryEngine 3.5 and up.
* Only compatible with Blender 2.7 and up.
* Supports primary assets: CGF, CGA, CHR, SKIN, ANM, I_CAF.

#### UI Changes:
* Added new CryBlend tab using Blender 2.7 tabs UI.
* Added new hotkey activated dropdown menu (SHIFT Q).
* Added properties expandable menu.
* Material physics UI added to Material Properties Tab.
* Fakebones removed from UI.
* AnimNodes removed.

#### New Features:
* Can now create CGF nodes from object names.
* Added apply transforms tool.
* Added automatic material naming tool.
* Added basic proxy tool.
* Added touch bending tools for adding and naming branches and branch joints.
* Added root bone tool for quickly adding a root bone at the origin to any skeleton.
* New generate scripts tool for generating base CHRPARAMS, CDF, ENT, and LUA files.
* CryExportNodes now have a type which determines the type of node instead of on export.
* Added DAE/RCDONE file toggle, apply modifiers, script generation, and fix weights options to export UI.

#### Improvements/Fixes:
* Export time significantly reduced.
* Removed naming restrictions.
* Repaired CHR pipeline.
* Vertex alpha repaired?

#### Code features:
* Thorough code clean up, renamed variables, extracted methods, etc.
* Heavily reworked export.py.
* Sped up export time significantly by revising export of normals (specifically smooth shading).
* Reduced what is printed to the console to reduce export time.
* Reworked major functions, reworked animation export, and moved fakebones from UI to code.
* Deleted obsolete file hbanim.py and increased usage of utils.py.
* ExportNodes now use file extension of asset type instead of CryExportNode_ prefix.
* Animations draw names from ExportNode of animation and frame range from the scene.
* DAE files are now run once through RC and then CGF, CGA, CHR, and SKIN's are run through a second time (two passes).

## 4.13
#### Features:
* Improved find weightless vertices utility.
* Smart UV projection used in place of default UV unwrapping for exports missing a UV map.
* Added support for green channel inversion when converting normal maps to DDS.
* Removed find underweight/overweight utilities and replaced them with an automatic weights correction tool.
* Added/Revised tooltips for all operators.
* Added material ID padding to fix assignment problems in CryEngine.
* Only compatible with Blender v2.70 and up.

#### Code features:
* Thorough code clean up, renamed variables, extracted methods etc.

## 4.12.2
#### Fixes:
* Fixed bug #39 (Adding UVs to wrong object).

## 4.12.1
* Just version number fix.

## 4.12
#### Features:
* Added support for rc 3.4.5 to handle textures conversion to DDS while using rc from 3.5.4.
* Added error message if many texture slots have same texture type.
* Added error message if texture slot has no texture.

#### Code features:
* Merged functions extract_aniXX.
* Fixed usage of cbPrint().
* Refactored configuration handler.
* Code clean up, renamed variables, extracted methods etc.

#### Fixes:
* Layer creation does not crash and maybe generates correct layers.
* Fixed buggy implementation of GUID (UUID) generator.

## 4.11.1
#### Fixes:
* Fixed bug in matrix_to_string function (#24).

## 4.11.0
#### Features:
* Created new layout for exporting options (#22).
* Improved configuration handling (#20).
* Added converter to DDS (#12).
* Added button to save tiff (DDS exporting) (#18).
* Added "Select textures directory" to CryBlend menu - helps with generating proper texture paths in .mtl files (#16).
* Improved relative paths in .mtl (#16).
* Added option "Profile CryBlend" that helps in tracking performance issues  (#16).
* "Find the Resource Compiler" now shows current RC path (#20).

#### Improvements in code:
* Configuration simplified and moved to separate module (#20).
* Replaced some string concatenation by creating a list of strings (#19).
* Removed useless code  (#6).
* Refactored export.py:__export_library_animation_clips_and_animations() to reduce duplicated code.
* And other changes.

## 4.9.9
#### Fixes:
* Fixed the previous fixes
* Fixed animation export for .anm

## 4.9.8
#### Fixes:
* Fixed incorrect index numbers in the extract_ani functions.

## 4.9.7
#### Fixes:
* Fixed the fix of a fix from last time, this is getting stupid.

## 4.9.6
#### Fixes:
* Fixed .cga export, again.

## 4.9.5
#### Features:
* Refactored some more code

#### Fixes:
* Fixed that drop-down menu from the last update

## 4.9.4
#### Features:
* Added a drop-down menu for file type selection at export time
* Refactored code

## 4.9.3
#### Features:
* Added remove bone geometry tool and fixed minor glitch with add bone geometry tool
* Error handling improved.
* It works on wine (Linux/Mac OS).

#### Fixes:
* Normal maps are now properly exported into mtl file.
* Fixed bug if image path is empty

## 4.9.2.1
#### Features:
* Code formatted to match PEP-8.

## 4.9.2
#### Fixes:
* Non relative paths to textures in .mtl file.

## 4.9.1.1
#### Fixes:
* Spelling issues.
* Trailing white spaces.

## 4.9.1
#### Fixes:
* #4 - Few registered class are not unregistered properly.

## 4.9
#### Features:
* New tool for locating lines that are connected to too many faces.
* Upgraded the find degenerate faces tool to make it easier to use.

## 4.8.3
#### Features:
* The current file directory is now the automatic destination for an export after the first one.

# Since 4.8.3 CryBlend is hosted on Github

## 4.8.2
#### Features
* Removed logging, finally.

## 4.8.1
#### Features
* Improved version number handling
* Switched to new better version number system

#### Fixes:
* Fixed the log sometimes going into the open file directory

## 4.8
#### Fixes:
* Fixing the fact that I broke things in 4.7, sorry guys.

## 4.7
#### Fixes:
* Another bugfix, this update makes Cryblend compatible with changes relating to context made in the latest Blender development builds. (Courtesy of bitset who figured this out).

## 4.6
#### Fixes:
* Just a bug fix release, fixed an issue where the exporter was just recording and longer and longer and longer log file, I had a 100MB log file when I discovered the glitch. The log file will now wipe itself out each time you start Blender ready to receive new information. The log can be found at C:\Program Files\Blender Foundation\Blender\CryBlend Export.log

## 4.5
#### Features
* New Find No UVs function for finding objects that lack a UV mesh layout automatically.
* New Remove all FakeBones feature for removing fakebones rapidly in the event you need to change the number of bones in your skeleton.

## 4.4
#### Features
* Added extra tools for handling mesh weighting problems.
* Removed unnecessary show console button.
* Changed IK export to be optional via a checkbox at export time.
* Added exporting layers for rapid scene reassembly in the CryEngine 3 (KNOWN ISSUE SEE BELOW).

#### Fixes:
* Fixed up a few problems causing character export to fail.

## 4.3
#### Features
* IK constraints (max, min and damping) are now exported onto the phys skeleton (from the other skeleton).
* Added "Add boneGeometry" button to add boneGeometry objects for the currently selected armatures.
* Added "Rename Phys Bones" button to add "_Phys" to the end of all bone names in armatures whose names contain "_Phys".

#### Fixes:
* Fixed up the terminal output of CryBlend
* A few miscellaneous bug fixes.

## 4.2
#### Features
* Support for physics on exported characters (.chr)
