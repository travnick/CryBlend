# Changelog:

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
