# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####
#------------------------------------------------------------------------------
# Name:        export.py
# Purpose:     export to cryengine main
#
# Author:      Angelo J. Miner,
#                some code borrowed from fbx exporter Campbell Barton
# Extended by: Duo Oratar
#
# Created:     23/01/2012
# Copyright:   (c) Angelo J. Miner 2012
# License:     GPLv2+
#------------------------------------------------------------------------------


if "bpy" in locals():
    import imp
    imp.reload(utils)
    imp.reload(exceptions)
else:
    import bpy
    from io_export_cryblend import utils, exceptions


from bpy_extras.io_utils import ExportHelper
from io_export_cryblend.dds_converter import DdsConverterRunner
from io_export_cryblend.outPipe import cbPrint
from mathutils import Matrix, Vector
from time import clock
from xml.dom.minidom import Document
import os
import threading
import time
import xml.dom.minidom


AXISES = {
    'X': 0,
    'Y': 1,
    'Z': 2,
}


# replace minidom's function with ours
xml.dom.minidom.Element.writexml = utils.fixed_writexml


class CrytekDaeExporter:
    def __init__(self, config, exe):
        self.__config = config
        self.__doc = Document()
        self.__exe = exe

    def __get_bones(self, armature):
        return [bone for bone in armature.data.bones]

    def export(self):
        # Ensure the correct extension for chosen path
        filepath = bpy.path.ensure_ext(self.__config.filepath, ".dae")
        self.__select_all_export_nodes()

        # Duo Oratar
        # This is a small bit risky (I don't know if including more things
        # in the selected objects will mess things up or not...
        # Easiest solution to the problem though
        cbPrint("Searching for boneGeoms...")
        for i in bpy.context.selectable_objects:
            if "_boneGeometry" in i.name:
                bpy.data.objects[i.name].select = True
                cbPrint("Bone Geometry found: " + i.name)

        root_element = self.__doc.createElement('collada')
        root_element.setAttribute("xmlns",
                               "http://www.collada.org/2005/11/COLLADASchema")
        root_element.setAttribute("version", "1.4.1")
        self.__doc.appendChild(root_element)

        self.__export_asset(root_element)

        # just here for future use
        libcam = self.__doc.createElement("library_cameras")
        root_element.appendChild(libcam)
        liblights = self.__doc.createElement("library_lights")
        root_element.appendChild(liblights)

        self.__export_library_images(root_element)
        self.__export_library_effects(root_element)
        self.__export_library_materials(root_element)
        self.__export_library_geometries(root_element)

        # Duo Oratar
        # Remove the boneGeometry from the selection so we can get on
        # with business as usual
        for i in bpy.context.selected_objects:
            if '_boneGeometry' in i.name:
                bpy.data.objects[i.name].select = False

        self.__export_library_controllers(root_element)
        self.__export_library_animation_clips_and_animations(root_element)
        self.__export_library_visual_scenes(root_element)
        self.__export_scene(root_element)

        write_to_file(self.__config, self.__doc, filepath, self.__exe)

    def __select_all_export_nodes(self):
        for group in bpy.context.blend_data.groups:
            for object_ in group.objects:
                object_.select = True
                cbPrint(object_.name)

    def __get_object_children(self, Parent):
        return [Object for Object in Parent.children
                if Object.type in {'ARMATURE', 'EMPTY', 'MESH'}]

    def wbl(self, pname, bones, obj, node1):
        cbPrint(len(bones), "bones")
        boneExtendedNames = []
        for bone in bones:
            bprnt = bone.parent
            if bprnt:
                cbPrint(bone.name, bone.parent.name)
            bname = bone.name
            nodename = self.__doc.createElement("node")

            pExtension = ''

            # Name Extension
            if (self.__config.include_ik and "_Phys" == bone.name[-5:]):
                exportNodeName = node1.getAttribute('id')[14:]
                starredBoneName = bone.name.replace("_", "*")
                pExtension += '%' + exportNodeName + '%'
                pExtension += '--PRprops_name=' + starredBoneName + '_'

            # IK
            if ("_Phys" == bone.name[-5:] and self.__config.include_ik):
                poseBone = (bpy.data.objects[obj.name[:-5]]
                    ).pose.bones[bone.name[:-5]]

                # Start IK props
                pExtension += 'xmax={!s}_'.format(poseBone.ik_max_x)
                pExtension += 'xmin={!s}_'.format(poseBone.ik_min_x)
                pExtension += 'xdamping={!s}_'.format(
                                                poseBone.ik_stiffness_x)
                pExtension += 'xspringangle={!s}_'.format(0.0)
                pExtension += 'xspringtension={!s}_'.format(1.0)

                pExtension += 'ymax={!s}_'.format(poseBone.ik_max_y)
                pExtension += 'ymin={!s}_'.format(poseBone.ik_min_y)
                pExtension += 'ydamping={!s}_'.format(
                                                poseBone.ik_stiffness_y)
                pExtension += 'yspringangle={!s}_'.format(0.0)
                pExtension += 'yspringtension={!s}_'.format(1.0)

                pExtension += 'zmax={!s}_'.format(poseBone.ik_max_z)
                pExtension += 'zmin={!s}_'.format(poseBone.ik_min_z)
                pExtension += 'zdamping={!s}_'.format(
                                                poseBone.ik_stiffness_z)
                pExtension += 'zspringangle={!s}_'.format(0.0)
                pExtension += 'zspringtension={!s}_'.format(1.0)
                # End IK props

            nodename.setAttribute("id", "%s" % (bname + pExtension))
            nodename.setAttribute("name", "%s" % (bname + pExtension))
            boneExtendedNames.append(bname + pExtension)
            nodename.setIdAttribute('id')

            for object_ in bpy.context.selectable_objects:
                if (object_.name == bone.name
                    or (object_.name == bone.name[:-5]
                        and "_Phys" == bone.name[-5:])
                    ):
                    bpy.data.objects[object_.name].select = True
                    cbPrint("FakeBone found for " + bone.name)
                    # <translate sid="translation">
                    trans = self.__doc.createElement("translate")
                    trans.setAttribute("sid", "translation")
                    transnum = self.__doc.createTextNode("%.4f %.4f %.4f"
                                                  % object_.location[:])
                    trans.appendChild(transnum)
                    # <rotate sid="rotation_Z">
                    rotz = self.__doc.createElement("rotate")
                    rotz.setAttribute("sid", "rotation_Z")
                    rotzn = self.__doc.createTextNode("0 0 1 %.4f"
                                               % (object_.rotation_euler[2]
                                                  * utils.toD))
                    rotz.appendChild(rotzn)
                    # <rotate sid="rotation_Y">
                    roty = self.__doc.createElement("rotate")
                    roty.setAttribute("sid", "rotation_Y")
                    rotyn = self.__doc.createTextNode("0 1 0 %.4f"
                                               % (object_.rotation_euler[1]
                                                  * utils.toD))
                    roty.appendChild(rotyn)
                    # <rotate sid="rotation_X">
                    rotx = self.__doc.createElement("rotate")
                    rotx.setAttribute("sid", "rotation_X")
                    rotxn = self.__doc.createTextNode("1 0 0 %.4f"
                                               % (object_.rotation_euler[0]
                                                  * utils.toD))
                    rotx.appendChild(rotxn)
                    # <scale sid="scale">
                    sc = self.__doc.createElement("scale")
                    sc.setAttribute("sid", "scale")
                    sx = str(object_.scale[0])
                    sy = str(object_.scale[1])
                    sz = str(object_.scale[2])
                    scn = self.__doc.createTextNode("%s"
                                             % utils.addthree(sx, sy, sz))
                    sc.appendChild(scn)
                    nodename.appendChild(trans)
                    nodename.appendChild(rotz)
                    nodename.appendChild(roty)
                    nodename.appendChild(rotx)
                    nodename.appendChild(sc)
                    # Find the boneGeometry object
                    for i in bpy.context.selectable_objects:
                        if i.name == bone.name + "_boneGeometry":
                            ig = self.__doc.createElement("instance_geometry")
                            ig.setAttribute("url", "#%s"
                                            % (bone.name
                                               + "_boneGeometry"))
                            bm = self.__doc.createElement("bind_material")
                            tc = self.__doc.createElement("technique_common")
                            # mat = mesh.materials[:]
                            for mat in i.material_slots:
                                # yes lets go through them 1 at a time
                                im = self.__doc.createElement(
                                                "instance_material")
                                im.setAttribute("symbol", "%s"
                                                % (mat.name))
                                im.setAttribute("target", "#%s"
                                                % (mat.name))
                                bvi = self.__doc.createElement(
                                                "bind_vertex_input")
                                bvi.setAttribute("semantic", "UVMap")
                                bvi.setAttribute("input_semantic",
                                                 "TEXCOORD")
                                bvi.setAttribute("input_set", "0")
                                im.appendChild(bvi)
                                tc.appendChild(im)
                            bm.appendChild(tc)
                            ig.appendChild(bm)
                            nodename.appendChild(ig)

            if bprnt:
                for name in boneExtendedNames:
                    if name[:len(bprnt.name)] == bprnt.name:
                        nodeparent = self.__doc.getElementById(name)
                        cbPrint(bprnt.name)
                        nodeparent.appendChild(nodename)
            else:
                node1.appendChild(nodename)

    def vsp(self, objects, node1):
        for object_ in objects:
            fby = 0
            for ai in object_.rna_type.id_data.items():
                if ai:
                    if ai[1] == "fakebone":
                        fby = 1
                        break
            if fby == 1:  # object_.parent_bone:
                pass
            else:
                cname = object_.name

                nodename = self.__doc.createElement("node")
                nodename.setAttribute("id", "%s" % (cname))
                nodename.setIdAttribute('id')
                # <translate sid="translation">
                trans = self.__doc.createElement("translate")
                trans.setAttribute("sid", "translation")
                transnum = self.__doc.createTextNode("%.4f %.4f %.4f"
                                              % object_.location[:])
                trans.appendChild(transnum)
                # <rotate sid="rotation_Z">
                rotz = self.__doc.createElement("rotate")
                rotz.setAttribute("sid", "rotation_Z")
                rotzn = self.__doc.createTextNode("0 0 1 %s"
                                           % (object_.rotation_euler[2]
                                              * utils.toD))
                rotz.appendChild(rotzn)
                # <rotate sid="rotation_Y">
                roty = self.__doc.createElement("rotate")
                roty.setAttribute("sid", "rotation_Y")
                rotyn = self.__doc.createTextNode("0 1 0 %s"
                                           % (object_.rotation_euler[1]
                                              * utils.toD))
                roty.appendChild(rotyn)
                # <rotate sid="rotation_X">
                rotx = self.__doc.createElement("rotate")
                rotx.setAttribute("sid", "rotation_X")
                rotxn = self.__doc.createTextNode("1 0 0 %s"
                                           % (object_.rotation_euler[0]
                                              * utils.toD))
                rotx.appendChild(rotxn)
                # <scale sid="scale">
                sc = self.__doc.createElement("scale")
                sc.setAttribute("sid", "scale")
                sx = str(object_.scale[0])
                sy = str(object_.scale[1])
                sz = str(object_.scale[2])
                scn = self.__doc.createTextNode(utils.addthree(sx, sy, sz))
                sc.appendChild(scn)
                nodename.appendChild(trans)
                nodename.appendChild(rotz)
                nodename.appendChild(roty)
                nodename.appendChild(rotx)
                nodename.appendChild(sc)

                # List of all the armature deformation modifiers
                ArmatureList = [Modifier
                                for Modifier in object_.modifiers
                                if Modifier.type == "ARMATURE"]
                if ArmatureList:
                    ic = self.__doc.createElement("instance_controller")
                    # This binds the meshObject to the armature
                    # in control of it
                    ic.setAttribute("url", "#%s_%s"
                                    % (ArmatureList[0].object.name,
                                       object_.name))

                name = str(object_.name)
                if (name[:6] != "_joint"):
                    if (object_.type == "MESH"):
                        ig = self.__doc.createElement("instance_geometry")
                        ig.setAttribute("url", "#%s" % (cname))
                        bm = self.__doc.createElement("bind_material")
                        tc = self.__doc.createElement("technique_common")

                        for mat in object_.material_slots:
                            # yes lets go through them 1 at a time
                            im = self.__doc.createElement("instance_material")
                            im.setAttribute("symbol", "%s"
                                            % (mat.name))
                            im.setAttribute("target", "#%s"
                                            % (mat.name))
                            bvi = self.__doc.createElement(
                                                "bind_vertex_input")
                            bvi.setAttribute("semantic", "UVMap")
                            bvi.setAttribute("input_semantic",
                                             "TEXCOORD")
                            bvi.setAttribute("input_set", "0")
                            im.appendChild(bvi)
                            tc.appendChild(im)
                        bm.appendChild(tc)
                        if ArmatureList:
                            ic.appendChild(bm)
                            nodename.appendChild(ic)
                        else:
                            ig.appendChild(bm)
                            nodename.appendChild(ig)

                ex = self.__doc.createElement("extra")
                techcry = self.__doc.createElement("technique")
                techcry.setAttribute("profile", "CryEngine")
                prop2 = self.__doc.createElement("properties")
                cprop = ""
                # Tagging properties onto the end of the item, I think.
                for ai in object_.rna_type.id_data.items():
                    if ai:
                        cprop = ("%s" % (ai[1]))
                        cryprops = self.__doc.createTextNode("%s" % (cprop))
                        prop2.appendChild(cryprops)
                techcry.appendChild(prop2)
                if (name[:6] == "_joint"):
                    b = object_.bound_box
                    vmin = Vector([b[0][0], b[0][1], b[0][2]])
                    vmax = Vector([b[6][0], b[6][1], b[6][2]])
                    ht = self.__doc.createElement("helper")
                    ht.setAttribute("type", "dummy")
                    bbmn = self.__doc.createElement("bound_box_min")
                    vmin0 = str(vmin[0])
                    vmin1 = str(vmin[1])
                    vmin2 = str(vmin[2])
                    bbmnval = self.__doc.createTextNode("%s %s %s"
                                                        % (vmin0[:6],
                                                           vmin1[:6],
                                                           vmin2[:6]))
                    bbmn.appendChild(bbmnval)
                    bbmx = self.__doc.createElement("bound_box_max")
                    vmax0 = str(vmax[0])
                    vmax1 = str(vmax[1])
                    vmax2 = str(vmax[2])
                    bbmxval = self.__doc.createTextNode("%s %s %s"
                                                        % (vmax0[:6],
                                                           vmax1[:6],
                                                           vmax2[:6]))
                    bbmx.appendChild(bbmxval)
                    ht.appendChild(bbmn)
                    ht.appendChild(bbmx)
                    techcry.appendChild(ht)
                ex.appendChild(techcry)
                nodename.appendChild(ex)
                if object_.type == 'ARMATURE':
                    cbPrint("Armature appended.")
                    bonelist = self.__get_bones(object_)
                    self.wbl(cname, bonelist, object_, node1)

                if object_.children:
                    if object_.parent:
                        if object_.parent.type != 'ARMATURE':
                            nodeparent = self.__doc.getElementById("%s"
                                                    % object_.parent.name)
                            cbPrint(nodeparent)
                            if nodeparent:
                                cbPrint("Appending object_ to parent.")
                                cbPrint(nodename)
                                chk = self.__doc.getElementById("%s"
                                                         % object_.name)
                                if chk:
                                    cbPrint(
                                    "Object already appended to parent.")
                                else:
                                    nodeparent.appendChild(nodename)
                            ChildList = self.__get_object_children(object_)
                            self.vsp(ChildList, node1)
                    else:
                        if object_.type != 'ARMATURE':
                            node1.appendChild(nodename)
                            ChildList = self.__get_object_children(object_)
                            self.vsp(ChildList, node1)

                else:
                    if object_.parent:
                        if object_.parent.type != 'ARMATURE':
                            nodeparent = self.__doc.getElementById("%s"
                                                    % object_.parent.name)
                            cbPrint(nodeparent)
                            if nodeparent:
                                cbPrint("Appending object_ to parent.")
                                cbPrint(nodename)
                                chk = self.__doc.getElementById("%s"
                                                         % object_.name)
                                if chk:
                                    cbPrint(
                                    "Object already appended to parent.")
                                else:
                                    nodeparent.appendChild(nodename)

                            cbPrint("Armparent.")
                        else:
                            node1.appendChild(nodename)
                    else:
                        if object_.name == "animnode":
                            cbPrint("Animnode.")
                        else:
                            node1.appendChild(nodename)
        return node1

    def extract_anil(self, i, ax):
        act = i.animation_data.action
        curves = act.fcurves
        fcus = {}
        for fcu in curves:
            # location
            # X
            if fcu.data_path == 'location' and fcu.array_index == AXISES[ax]:
                anmlx = self.__doc.createElement("animation")
                anmlx.setAttribute("id", i.name + "_location_" + ax)
                fcus[fcu.array_index] = fcu
                intangx = ""
                outtangx = ""
                inpx = ""
                outpx = ""
                intx = ""
                temp = fcus[AXISES[ax]].keyframe_points
                ii = 0
                for keyx in temp:
                    khlx = keyx.handle_left[0]
                    khly = keyx.handle_left[1]
                    khrx = keyx.handle_right[0]
                    khry = keyx.handle_right[1]
                    frame, value = keyx.co
                    time = utils.convert_time(frame)
                    intx += ("%s " % (keyx.interpolation))
                    inpx += ("%.6f " % (time))
                    outpx += ("%.6f " % (value))

                    intangfirst = utils.convert_time(khlx)
                    outangfirst = utils.convert_time(khrx)
                    intangx += ("%.6f %.6f " % (intangfirst, khly))
                    outtangx += ("%.6f %.6f " % (outangfirst, khry))
                    ii += 1
                # input
                sinpx = self.__doc.createElement("source")
                sinpx.setAttribute("id", i.name + "_location_" + ax + "-input")
                inpxfa = self.__doc.createElement("float_array")
                inpxfa.setAttribute("id", i.name + "_location_" + ax + "-input-array")
                inpxfa.setAttribute("count", "%s" % (ii))
                sinpxdat = self.__doc.createTextNode("%s" % (inpx))
                inpxfa.appendChild(sinpxdat)
                tcinpx = self.__doc.createElement("technique_common")
                accinpx = self.__doc.createElement("accessor")
                accinpx.setAttribute("source", "#" + i.name + "_location_" + ax + "-input-array")
                accinpx.setAttribute("count", "%s" % (ii))
                accinpx.setAttribute("stride", "1")
                parinpx = self.__doc.createElement("param")
                parinpx.setAttribute("name", "TIME")
                parinpx.setAttribute("type", "float")
                accinpx.appendChild(parinpx)
                tcinpx.appendChild(accinpx)
                sinpx.appendChild(inpxfa)
                sinpx.appendChild(tcinpx)
                # output
                soutpx = self.__doc.createElement("source")
                soutpx.setAttribute("id", i.name + "_location_" + ax + "-output")
                outpxfa = self.__doc.createElement("float_array")
                outpxfa.setAttribute("id", i.name + "_location_" + ax + "-output-array")
                outpxfa.setAttribute("count", "%s" % (ii))
                soutpxdat = self.__doc.createTextNode("%s" % (outpx))
                outpxfa.appendChild(soutpxdat)
                tcoutpx = self.__doc.createElement("technique_common")
                accoutpx = self.__doc.createElement("accessor")
                accoutpx.setAttribute("source", "#" + i.name + "_location_" + ax + "-output-array")
                accoutpx.setAttribute("count", "%s" % (ii))
                accoutpx.setAttribute("stride", "1")
                paroutpx = self.__doc.createElement("param")
                paroutpx.setAttribute("name", "VALUE")
                paroutpx.setAttribute("type", "float")
                accoutpx.appendChild(paroutpx)
                tcoutpx.appendChild(accoutpx)
                soutpx.appendChild(outpxfa)
                soutpx.appendChild(tcoutpx)
                # interpolation
                sintpx = self.__doc.createElement("source")
                sintpx.setAttribute("id", i.name + "_location_" + ax + "-interpolation")
                intpxfa = self.__doc.createElement("Name_array")
                intpxfa.setAttribute("id", i.name + "_location_" + ax + "-interpolation-array")
                intpxfa.setAttribute("count", "%s" % (ii))
                sintpxdat = self.__doc.createTextNode("%s" % (intx))
                intpxfa.appendChild(sintpxdat)
                tcintpx = self.__doc.createElement("technique_common")
                accintpx = self.__doc.createElement("accessor")
                accintpx.setAttribute("source", "#" + i.name + "_location_" + ax + "-interpolation-array")
                accintpx.setAttribute("count", "%s" % (ii))
                accintpx.setAttribute("stride", "1")
                parintpx = self.__doc.createElement("param")
                parintpx.setAttribute("name", "INTERPOLATION")
                parintpx.setAttribute("type", "name")
                accintpx.appendChild(parintpx)
                tcintpx.appendChild(accintpx)
                sintpx.appendChild(intpxfa)
                sintpx.appendChild(tcintpx)
                # intangent
                sintangpx = self.__doc.createElement("source")
                sintangpx.setAttribute("id", i.name + "_location_" + ax + "-intangent")
                intangpxfa = self.__doc.createElement("float_array")
                intangpxfa.setAttribute("id", i.name + "_location_" + ax + "-intangent-array")
                intangpxfa.setAttribute("count", "%s" % ((ii) * 2))
                sintangpxdat = self.__doc.createTextNode("%s" % (intangx))
                intangpxfa.appendChild(sintangpxdat)
                tcintangpx = self.__doc.createElement("technique_common")
                accintangpx = self.__doc.createElement("accessor")
                accintangpx.setAttribute("source", "#" + i.name + "_location_" + ax + "-intangent-array")
                accintangpx.setAttribute("count", "%s" % (ii))
                accintangpx.setAttribute("stride", "2")
                parintangpx = self.__doc.createElement("param")
                parintangpx.setAttribute("name", "X")
                parintangpx.setAttribute("type", "float")
                parintangpxy = self.__doc.createElement("param")
                parintangpxy.setAttribute("name", "Y")
                parintangpxy.setAttribute("type", "float")
                accintangpx.appendChild(parintangpx)
                accintangpx.appendChild(parintangpxy)
                tcintangpx.appendChild(accintangpx)
                sintangpx.appendChild(intangpxfa)
                sintangpx.appendChild(tcintangpx)
                # outtangent
                soutangpx = self.__doc.createElement("source")
                soutangpx.setAttribute("id", i.name + "_location_" + ax + "-outtangent")
                outangpxfa = self.__doc.createElement("float_array")
                outangpxfa.setAttribute("id", i.name + "_location_" + ax + "-outtangent-array")
                outangpxfa.setAttribute("count", "%s" % ((ii) * 2))
                soutangpxdat = self.__doc.createTextNode("%s" % (outtangx))
                outangpxfa.appendChild(soutangpxdat)
                tcoutangpx = self.__doc.createElement("technique_common")
                accoutangpx = self.__doc.createElement("accessor")
                accoutangpx.setAttribute("source", "#" + i.name + "_location_" + ax + "-outtangent-array")
                accoutangpx.setAttribute("count", "%s" % (ii))
                accoutangpx.setAttribute("stride", "2")
                paroutangpx = self.__doc.createElement("param")
                paroutangpx.setAttribute("name", "X")
                paroutangpx.setAttribute("type", "float")
                paroutangpxy = self.__doc.createElement("param")
                paroutangpxy.setAttribute("name", "Y")
                paroutangpxy.setAttribute("type", "float")
                accoutangpx.appendChild(paroutangpx)
                accoutangpx.appendChild(paroutangpxy)
                tcoutangpx.appendChild(accoutangpx)
                soutangpx.appendChild(outangpxfa)
                soutangpx.appendChild(tcoutangpx)
                # sampler
                samx = self.__doc.createElement("sampler")
                samx.setAttribute("id", i.name + "_location_" + ax + "-sampler")
                semip = self.__doc.createElement("input")
                semip.setAttribute("semantic", "INPUT")
                semip.setAttribute("source", "#" + i.name + "_location_" + ax + "-input")
                semop = self.__doc.createElement("input")
                semop.setAttribute("semantic", "OUTPUT")
                semop.setAttribute("source", "#" + i.name + "_location_" + ax + "-output")
                seminter = self.__doc.createElement("input")
                seminter.setAttribute("semantic", "INTERPOLATION")
                seminter.setAttribute("source", "#" + i.name + "_location_" + ax + "-interpolation")
                semintang = self.__doc.createElement("input")
                semintang.setAttribute("semantic", "IN_TANGENT")
                semintang.setAttribute("source", "#" + i.name + "_location_" + ax + "-intangent")
                semoutang = self.__doc.createElement("input")
                semoutang.setAttribute("semantic", "OUT_TANGENT")
                semoutang.setAttribute("source", "#" + i.name + "_location_" + ax + "-outtangent")
                samx.appendChild(semip)
                samx.appendChild(semop)
                samx.appendChild(seminter)
                chanx = self.__doc.createElement("channel")
                chanx.setAttribute("source", "#" + i.name + "_location_" + ax + "-sampler")
                chanx.setAttribute("target", i.name + "/translation." + ax)
                anmlx.appendChild(sinpx)
                anmlx.appendChild(soutpx)
                anmlx.appendChild(sintpx)
                anmlx.appendChild(sintangpx)
                anmlx.appendChild(soutangpx)
                anmlx.appendChild(samx)
                anmlx.appendChild(chanx)
                cbPrint(ii)
                cbPrint(inpx)
                cbPrint(outpx)
                cbPrint(intx)
                cbPrint(intangx)
                cbPrint(outtangx)
                cbPrint("done" + ax)
        return anmlx

    def extract_anir(self, i, ax):
        act = i.animation_data.action
        curves = act.fcurves
        fcus = {}
        for fcu in curves:
        # rotation_euler
            if fcu.data_path == 'rotation_euler' and fcu.array_index == AXISES[ax]:
                anmrx = self.__doc.createElement("animation")
                anmrx.setAttribute("id", i.name + "_rotation_euler_" + ax)
                fcus[fcu.array_index] = fcu
                intangx = ""
                outtangx = ""
                inpx = ""
                outpx = ""
                intx = ""
                temp = fcus[AXISES[ax]].keyframe_points

                ii = len(temp)
                for keyx in temp:
                    khlx = keyx.handle_left[0]
                    khly = keyx.handle_left[1]
                    khrx = keyx.handle_right[0]
                    khry = keyx.handle_right[1]
                    frame, value = keyx.co
                    time = utils.convert_time(frame)
                    intx += ("%s " % (keyx.interpolation))
                    inpx += ("%.6f " % (time))
                    outpx += ("%.6f " % (value * utils.toD))
                    intangfirst = utils.convert_time(khlx)
                    outangfirst = utils.convert_time(khrx)
                    intangx += ("%.6f %.6f " % (intangfirst, khly))
                    outtangx += ("%.6f %.6f " % (outangfirst, khry))

                # input
                sinpx = self.__doc.createElement("source")
                sinpx.setAttribute("id", i.name + "_rotation_euler_" + ax + "-input")
                inpxfa = self.__doc.createElement("float_array")
                inpxfa.setAttribute("id", i.name + "_rotation_euler_" + ax + "-input-array")
                inpxfa.setAttribute("count", "%s" % (ii))
                sinpxdat = self.__doc.createTextNode("%s" % (inpx))
                inpxfa.appendChild(sinpxdat)
                tcinpx = self.__doc.createElement("technique_common")
                accinpx = self.__doc.createElement("accessor")
                accinpx.setAttribute("source", "#" + i.name + "_rotation_euler_" + ax + "-input-array")
                accinpx.setAttribute("count", "%s" % (ii))
                accinpx.setAttribute("stride", "1")
                parinpx = self.__doc.createElement("param")
                parinpx.setAttribute("name", "TIME")
                parinpx.setAttribute("type", "float")
                accinpx.appendChild(parinpx)
                tcinpx.appendChild(accinpx)
                sinpx.appendChild(inpxfa)
                sinpx.appendChild(tcinpx)
                # output
                soutpx = self.__doc.createElement("source")
                soutpx.setAttribute("id", i.name + "_rotation_euler_" + ax + "-output")
                outpxfa = self.__doc.createElement("float_array")
                outpxfa.setAttribute("id", i.name + "_rotation_euler_" + ax + "-output-array")
                outpxfa.setAttribute("count", "%s" % (ii))
                soutpxdat = self.__doc.createTextNode("%s" % (outpx))
                outpxfa.appendChild(soutpxdat)
                tcoutpx = self.__doc.createElement("technique_common")
                accoutpx = self.__doc.createElement("accessor")
                accoutpx.setAttribute("source", "#" + i.name + "_rotation_euler_" + ax + "-output-array")
                accoutpx.setAttribute("count", "%s" % (ii))
                accoutpx.setAttribute("stride", "1")
                paroutpx = self.__doc.createElement("param")
                paroutpx.setAttribute("name", "VALUE")
                paroutpx.setAttribute("type", "float")
                accoutpx.appendChild(paroutpx)
                tcoutpx.appendChild(accoutpx)
                soutpx.appendChild(outpxfa)
                soutpx.appendChild(tcoutpx)
                # interpolation
                sintpx = self.__doc.createElement("source")
                sintpx.setAttribute("id", i.name + "_rotation_euler_" + ax + "-interpolation")
                intpxfa = self.__doc.createElement("Name_array")
                intpxfa.setAttribute("id", i.name + "_rotation_euler_" + ax + "-interpolation-array")
                intpxfa.setAttribute("count", "%s" % (ii))
                sintpxdat = self.__doc.createTextNode("%s" % (intx))
                intpxfa.appendChild(sintpxdat)
                tcintpx = self.__doc.createElement("technique_common")
                accintpx = self.__doc.createElement("accessor")
                accintpx.setAttribute("source", "#" + i.name + "_rotation_euler_" + ax + "-interpolation-array")
                accintpx.setAttribute("count", "%s" % (ii))
                accintpx.setAttribute("stride", "1")
                parintpx = self.__doc.createElement("param")
                parintpx.setAttribute("name", "INTERPOLATION")
                parintpx.setAttribute("type", "name")
                accintpx.appendChild(parintpx)
                tcintpx.appendChild(accintpx)
                sintpx.appendChild(intpxfa)
                sintpx.appendChild(tcintpx)
                # intangent
                sintangpx = self.__doc.createElement("source")
                sintangpx.setAttribute("id", i.name + "_rotation_euler_" + ax + "-intangent")
                intangpxfa = self.__doc.createElement("float_array")
                intangpxfa.setAttribute("id", i.name + "_rotation_euler_" + ax + "-intangent-array")
                intangpxfa.setAttribute("count", "%s" % ((ii) * 2))
                sintangpxdat = self.__doc.createTextNode("%s" % (intangx))
                intangpxfa.appendChild(sintangpxdat)
                tcintangpx = self.__doc.createElement("technique_common")
                accintangpx = self.__doc.createElement("accessor")
                accintangpx.setAttribute("source", "#" + i.name + "_rotation_euler_" + ax + "-intangent-array")
                accintangpx.setAttribute("count", "%s" % (ii))
                accintangpx.setAttribute("stride", "2")
                parintangpx = self.__doc.createElement("param")
                parintangpx.setAttribute("name", "X")
                parintangpx.setAttribute("type", "float")
                parintangpxy = self.__doc.createElement("param")
                parintangpxy.setAttribute("name", "Y")
                parintangpxy.setAttribute("type", "float")
                accintangpx.appendChild(parintangpx)
                accintangpx.appendChild(parintangpxy)
                tcintangpx.appendChild(accintangpx)
                sintangpx.appendChild(intangpxfa)
                sintangpx.appendChild(tcintangpx)
                # outtangent
                soutangpx = self.__doc.createElement("source")
                soutangpx.setAttribute("id", i.name + "_rotation_euler_" + ax + "-outtangent")
                outangpxfa = self.__doc.createElement("float_array")
                outangpxfa.setAttribute("id", i.name + "_rotation_euler_" + ax + "-outtangent-array")
                outangpxfa.setAttribute("count", "%s" % ((ii) * 2))
                soutangpxdat = self.__doc.createTextNode("%s" % (outtangx))
                outangpxfa.appendChild(soutangpxdat)
                tcoutangpx = self.__doc.createElement("technique_common")
                accoutangpx = self.__doc.createElement("accessor")
                accoutangpx.setAttribute("source", "#" + i.name + "_rotation_euler_" + ax + "-outtangent-array")
                accoutangpx.setAttribute("count", "%s" % (ii))
                accoutangpx.setAttribute("stride", "2")
                paroutangpx = self.__doc.createElement("param")
                paroutangpx.setAttribute("name", "X")
                paroutangpx.setAttribute("type", "float")
                paroutangpxy = self.__doc.createElement("param")
                paroutangpxy.setAttribute("name", "Y")
                paroutangpxy.setAttribute("type", "float")
                accoutangpx.appendChild(paroutangpx)
                accoutangpx.appendChild(paroutangpxy)
                tcoutangpx.appendChild(accoutangpx)
                soutangpx.appendChild(outangpxfa)
                soutangpx.appendChild(tcoutangpx)
                # sampler
                samx = self.__doc.createElement("sampler")
                samx.setAttribute("id", i.name + "_rotation_euler_" + ax + "-sampler")
                semip = self.__doc.createElement("input")
                semip.setAttribute("semantic", "INPUT")
                semip.setAttribute("source", "#" + i.name + "_rotation_euler_" + ax + "-input")
                semop = self.__doc.createElement("input")
                semop.setAttribute("semantic", "OUTPUT")
                semop.setAttribute("source", "#" + i.name + "_rotation_euler_" + ax + "-output")
                seminter = self.__doc.createElement("input")
                seminter.setAttribute("semantic", "INTERPOLATION")
                seminter.setAttribute("source", "#" + i.name + "_rotation_euler_" + ax + "-interpolation")
                semintang = self.__doc.createElement("input")
                semintang.setAttribute("semantic", "IN_TANGENT")
                semintang.setAttribute("source", "#" + i.name + "_rotation_euler_" + ax + "-intangent")
                semoutang = self.__doc.createElement("input")
                semoutang.setAttribute("semantic", "OUT_TANGENT")
                semoutang.setAttribute("source", "#" + i.name + "_rotation_euler_" + ax + "-outtangent")
                samx.appendChild(semip)
                samx.appendChild(semop)
                samx.appendChild(seminter)
                chanx = self.__doc.createElement("channel")
                chanx.setAttribute("source", "#" + i.name + "_rotation_euler_" + ax + "-sampler")
                chanx.setAttribute("target", i.name + "/rotation_" + ax + ".ANGLE")
                anmrx.appendChild(sinpx)
                anmrx.appendChild(soutpx)
                anmrx.appendChild(sintpx)
                anmrx.appendChild(sintangpx)
                anmrx.appendChild(soutangpx)
                anmrx.appendChild(samx)
                anmrx.appendChild(chanx)
                cbPrint(ii)
                cbPrint(inpx)
                cbPrint(outpx)
                cbPrint(intx)
                cbPrint(intangx)
                cbPrint(outtangx)
                cbPrint("donerotx")
        return anmrx

    def __get_bone_names_for_idref(self, bones):
        bones_for_idref = []

        for bone in bones:
            bones_for_idref.append(bone.name)

        return " ".join(bones_for_idref)

    def __export_float_array(self, armature_bones, flar):
        for bone in armature_bones:
            rmatrix = 0
            for scene_object in bpy.context.scene.objects:
                if scene_object.name == bone.name:
                    rmatrix = scene_object.matrix_local
                    break

            if rmatrix == 0:
                return

            cbPrint("rmatrix%s" % rmatrix)
            lmtx1 = "%.6f %.6f %.6f %.6f " % (rmatrix[0][0], rmatrix[0][1],
                rmatrix[0][2], -rmatrix[0][3])
            lmtx2 = "%.6f %.6f %.6f %.6f " % (rmatrix[1][0], rmatrix[1][1],
                rmatrix[1][2], (rmatrix[1][3] * -1))
            lmtx3 = "%.6f %.6f %.6f %.6f " % (rmatrix[2][0], rmatrix[2][1],
                rmatrix[2][2], -rmatrix[2][3])
            lmtx4 = "%.6f %.6f %.6f %.6f " % (rmatrix[3][0], rmatrix[3][1],
                rmatrix[3][2], rmatrix[3][3])
            flarm1 = self.__doc.createTextNode("%s" % lmtx1)
            flar.appendChild(flarm1)
            flarm2 = self.__doc.createTextNode("%s" % lmtx2)
            flar.appendChild(flarm2)
            flarm3 = self.__doc.createTextNode("%s" % lmtx3)
            flar.appendChild(flarm3)
            flarm4 = self.__doc.createTextNode("%s" % lmtx4)
            flar.appendChild(flarm4)

    def __export_asset(self, parent_element):
        # Attributes are x=y values inside a tag
        asset = self.__doc.createElement("asset")
        parent_element.appendChild(asset)
        contrib = self.__doc.createElement("contributor")
        asset.appendChild(contrib)
        auth = self.__doc.createElement("author")
        contrib.appendChild(auth)
        authname = self.__doc.createTextNode("Blender User")
        auth.appendChild(authname)
        authtool = self.__doc.createElement("authoring_tool")
        authtname = self.__doc.createTextNode(
            "CryENGINE exporter for Blender" +
            "v%s by angjminer, extended by Duo Oratar" % (bpy.app.version_string))
        authtool.appendChild(authtname)
        contrib.appendChild(authtool)
        created = self.__doc.createElement("created")
        asset.appendChild(created)
        modified = self.__doc.createElement("modified")
        asset.appendChild(modified)
        unit = self.__doc.createElement("unit")
        unit.setAttribute("name", "meter")
        unit.setAttribute("meter", "1")
        asset.appendChild(unit)
        uax = self.__doc.createElement("up_axis")
        zup = self.__doc.createTextNode("Z_UP")
        uax.appendChild(zup)
        asset.appendChild(uax)

    def __export_library_images(self, parent_element):
        library_images = self.__doc.createElement("library_images")
        parent_element.appendChild(library_images)

        images_to_convert = []

        for image in self.__get_texture_images_for_selected_objects():
            if self.__config.convert_source_image_to_dds:
                image_path = utils.get_path_with_new_extension(image.filepath,
                                                               "dds")
                images_to_convert.append(image)

            else:
                image_path = image.filepath

            image_path = utils.get_relative_path(image_path)

            image_element = self.__doc.createElement("image")
            image_element.setAttribute("id", "%s" % image.name)
            image_element.setAttribute("name", "%s" % image.name)
            init_from = self.__doc.createElement("init_from")
            path_node = self.__doc.createTextNode("%s" % image_path)
            init_from.appendChild(path_node)
            image_element.appendChild(init_from)
            library_images.appendChild(image_element)

        if self.__config.convert_source_image_to_dds:
            converter = DdsConverterRunner(self.__exe)
            converter.start_conversion(
                       images_to_convert,
                       self.__config.refresh_rc,
                       self.__config.save_tiff_during_conversion)

    def __get_texture_images_for_selected_objects(self):
        images = []
        textures = self.__get_textures_for_selected_objects()

        for texture in textures:
            try:
                if self.is_valid_image(texture.image):
                    images.append(texture.image)

            except AttributeError:
                # don't care about non image textures
                pass

        # return only unique images
        return list(set(images))

    def __get_textures_for_selected_objects(self):
        materials = self.__get_materials_for_selected_objects()
        return self.__get_textures_for_materials(materials)

    def __get_materials_for_selected_objects(self):
        materials = []
        for object_ in bpy.context.selected_objects:
            for material_slot in object_.material_slots:
                materials.append(material_slot.material)

        return materials

    def __get_textures_for_materials(self, materials):
        texture_slots = self.__get_texture_slots_for_materials(materials)
        return self.__get_textures_for_texture_slots(texture_slots)

    def __get_texture_slots_for_materials(self, materials):
        texture_slots = []

        for material in materials:
            texture_slots.extend(
                            self.__get_texture_slots_for_material(material))

        return texture_slots

    def __get_texture_slots_for_material(self, material):
        texture_slots = []
        for texture_slot in material.texture_slots:
            # texture_slot is able to be None
            if texture_slot and texture_slot.texture.type == 'IMAGE':
                texture_slots.append(texture_slot)

        return texture_slots

    def __get_textures_for_texture_slots(self, texture_slots):
        return [texture_slot.texture for texture_slot in texture_slots]

    def is_valid_image(self, image):
        return image.has_data and image.filepath

    def __export_library_effects(self, parent_element):
        current_element = self.__doc.createElement("library_effects")
        parent_element.appendChild(current_element)

        for material in self.__get_materials_for_selected_objects():
            self.__export_library_effects_material(material, current_element)

    def __export_library_effects_material(self, material, current_element):
        dtex = 0
        stex = 0
        ntex = 0
        dimage = ""
        simage = ""
        nimage = ""
        texture_slots = self.__get_texture_slots_for_material(material)
        for texture_slot in texture_slots:
            image = texture_slot.texture.image
            if texture_slot.use_map_color_diffuse:
                dtex = 1
                dimage = image.name
                dnpsurf = self.__doc.createElement("newparam")
                dnpsurf.setAttribute("sid", "%s-surface" % image.name)
                dsrf = self.__doc.createElement("surface")
                dsrf.setAttribute("type", "2D")
                if1 = self.__doc.createElement("init_from")
                if1tn = self.__doc.createTextNode("%s" % (image.name))
                if1.appendChild(if1tn)
                dsrf.appendChild(if1)
                dnpsurf.appendChild(dsrf)
                dnpsamp = self.__doc.createElement("newparam")
                dnpsamp.setAttribute("sid", "%s-sampler" % image.name)
                dsamp = self.__doc.createElement("sampler2D")
                if2 = self.__doc.createElement("source")
                if2tn = self.__doc.createTextNode(
                    "%s-surface" % (image.name))
                if2.appendChild(if2tn)
                dsamp.appendChild(if2)
                dnpsamp.appendChild(dsamp)
            if texture_slot.use_map_color_spec:
                stex = 1
                simage = image.name
                snpsurf = self.__doc.createElement("newparam")
                snpsurf.setAttribute("sid", "%s-surface" % image.name)
                ssrf = self.__doc.createElement("surface")
                ssrf.setAttribute("type", "2D")
                sif1 = self.__doc.createElement("init_from")
                sif1tn = self.__doc.createTextNode(
                    "%s" % (image.name))
                sif1.appendChild(sif1tn)
                ssrf.appendChild(sif1)
                snpsurf.appendChild(ssrf)
                snpsamp = self.__doc.createElement("newparam")
                snpsamp.setAttribute("sid", "%s-sampler" % image.name)
                ssamp = self.__doc.createElement("sampler2D")
                sif2 = self.__doc.createElement("source")
                sif2tn = self.__doc.createTextNode(
                    "%s-surface" % (image.name))
                sif2.appendChild(sif2tn)
                ssamp.appendChild(sif2)
                snpsamp.appendChild(ssamp)
            if texture_slot.use_map_normal:
                ntex = 1
                nimage = image.name
                nnpsurf = self.__doc.createElement("newparam")
                nnpsurf.setAttribute("sid", "%s-surface" % image.name)
                nsrf = self.__doc.createElement("surface")
                nsrf.setAttribute("type", "2D")
                nif1 = self.__doc.createElement("init_from")
                nif1tn = self.__doc.createTextNode(
                    "%s" % (image.name))
                nif1.appendChild(nif1tn)
                nsrf.appendChild(nif1)
                nnpsurf.appendChild(nsrf)
                nnpsamp = self.__doc.createElement("newparam")
                nnpsamp.setAttribute("sid", "%s-sampler" % image.name)
                nsamp = self.__doc.createElement("sampler2D")
                if2 = self.__doc.createElement("source")
                if2tn = self.__doc.createTextNode(
                    "%s-surface" % (image.name))
                if2.appendChild(if2tn)
                nsamp.appendChild(if2)
                nnpsamp.appendChild(nsamp)

        effid = self.__doc.createElement("effect")
        effid.setAttribute("id", "%s_fx" % (material.name))
        prof_com = self.__doc.createElement("profile_COMMON")
        if dtex == 1:
            prof_com.appendChild(dnpsurf)
            prof_com.appendChild(dnpsamp)
        if stex == 1:
            prof_com.appendChild(snpsurf)
            prof_com.appendChild(snpsamp)
        if ntex == 1:
            prof_com.appendChild(nnpsurf)
            prof_com.appendChild(nnpsamp)
        tech_com = self.__doc.createElement("technique")
        tech_com.setAttribute("sid", "common")
        phong = self.__doc.createElement("phong")
        emis = self.__doc.createElement("emission")
        color = self.__doc.createElement("color")
        color.setAttribute("sid", "emission")
        cot = utils.getcol(material.emit, material.emit, material.emit, 1.0)
        emit = self.__doc.createTextNode("%s" % (cot))
        color.appendChild(emit)
        emis.appendChild(color)
        amb = self.__doc.createElement("ambient")
        color = self.__doc.createElement("color")
        color.setAttribute("sid", "ambient")
        cot = utils.getcol(material.ambient,
                           material.ambient,
                           material.ambient,
                           1.0)
        ambcol = self.__doc.createTextNode("%s" % (cot))
        color.appendChild(ambcol)
        amb.appendChild(color)
        dif = self.__doc.createElement("diffuse")
        if dtex == 1:
            dtexr = self.__doc.createElement("texture")
            dtexr.setAttribute("texture", "%s-sampler" % dimage)
            dif.appendChild(dtexr)
        else:
            color = self.__doc.createElement("color")
            color.setAttribute("sid", "diffuse")
            cot = utils.getcol(material.diffuse_color.r,
                material.diffuse_color.g,
                material.diffuse_color.b, 1.0)
            difcol = self.__doc.createTextNode("%s" % (cot))
            color.appendChild(difcol)
            dif.appendChild(color)
        spec = self.__doc.createElement("specular")
        if stex == 1:
            stexr = self.__doc.createElement("texture")
            stexr.setAttribute("texture", "%s-sampler" % simage)
            spec.appendChild(stexr)
        else:
            color = self.__doc.createElement("color")
            color.setAttribute("sid", "specular")
            cot = utils.getcol(material.specular_color.r,
                material.specular_color.g,
                material.specular_color.b, 1.0)
            speccol = self.__doc.createTextNode("%s" % (cot))
            color.appendChild(speccol)
            spec.appendChild(color)
        shin = self.__doc.createElement("shininess")
        flo = self.__doc.createElement("float")
        flo.setAttribute("sid", "shininess")
        cot = material.specular_hardness
        shinval = self.__doc.createTextNode("%s" % (cot))
        flo.appendChild(shinval)
        shin.appendChild(flo)
        ioref = self.__doc.createElement("index_of_refraction")
        flo = self.__doc.createElement("float")
        flo.setAttribute("sid", "index_of_refraction")
        cot = material.alpha
        iorval = self.__doc.createTextNode("%s" % (cot))
        flo.appendChild(iorval)
        ioref.appendChild(flo)
        phong.appendChild(emis)
        phong.appendChild(amb)
        phong.appendChild(dif)
        phong.appendChild(spec)
        phong.appendChild(shin)
        phong.appendChild(ioref)
        if ntex == 1:
            bump = self.__doc.createElement("normal")
            ntexr = self.__doc.createElement("texture")
            ntexr.setAttribute("texture", "%s-sampler" % nimage)
            bump.appendChild(ntexr)
            phong.appendChild(bump)
        tech_com.appendChild(phong)
        prof_com.appendChild(tech_com)
        extra = self.__doc.createElement("extra")
        techn = self.__doc.createElement("technique")
        techn.setAttribute("profile", "GOOGLEEARTH")
        ds = self.__doc.createElement("double_sided")
        dsval = self.__doc.createTextNode("1")
        ds.appendChild(dsval)
        techn.appendChild(ds)
        extra.appendChild(techn)
        prof_com.appendChild(extra)
        effid.appendChild(prof_com)
        extra = self.__doc.createElement("extra")
        techn = self.__doc.createElement("technique")
        techn.setAttribute("profile", "MAX3D")
        ds = self.__doc.createElement("double_sided")
        dsval = self.__doc.createTextNode("1")
        ds.appendChild(dsval)
        techn.appendChild(ds)
        extra.appendChild(techn)
        effid.appendChild(extra)
        current_element.appendChild(effid)

    def __export_library_materials(self, parent_element):
        library_materials = self.__doc.createElement("library_materials")
        materials = self.__get_materials_for_selected_objects()

        for material in materials:
            material_element = self.__doc.createElement("material")
            material_element.setAttribute("id", "%s" % (material.name))
            material_element.setAttribute("name", "%s" % (material.name))
            instance_effect = self.__doc.createElement("instance_effect")
            instance_effect.setAttribute("url", "#%s_fx" % (material.name))
            material_element.appendChild(instance_effect)
            library_materials.appendChild(material_element)

        parent_element.appendChild(library_materials)

    def __export_library_geometries(self, parent_element):
        libgeo = self.__doc.createElement("library_geometries")
        parent_element.appendChild(libgeo)

        start_time = clock()
        for object_ in self.__get_objects_for_library_geometries():
            if object_.mode == 'EDIT':
                bpy.ops.object.mode_set(mode='OBJECT')
            object_.data.update(calc_tessface=1)
            mesh = object_.data
            me_verts = mesh.vertices[:]
            mname = object_.name
            geo = self.__doc.createElement("geometry")
            geo.setAttribute("id", "%s" % (mname))
            me = self.__doc.createElement("mesh")
            # positions
            sourcep = self.__doc.createElement("source")
            sourcep.setAttribute("id", "%s-positions" % (mname))

            float_positions = []
            for vertice in me_verts:
                float_positions.append("%.6f %.6g %.6f" % vertice.co[:])

            cbPrint('vert loc took %.4f sec.' % (clock() - start_time))
            far = self.__doc.createElement("float_array")
            far.setAttribute("id", "%s-positions-array" % (mname))
            far.setAttribute("count", "%s" % (str(len(mesh.vertices) * 3)))
            mpos = self.__doc.createTextNode(" ".join(float_positions))
            far.appendChild(mpos)
            techcom = self.__doc.createElement("technique_common")
            acc = self.__doc.createElement("accessor")
            acc.setAttribute("source", "#%s-positions-array" % (mname))
            acc.setAttribute("count", "%s" % (str(len(mesh.vertices))))
            acc.setAttribute("stride", "3")
            parx = self.__doc.createElement("param")
            parx.setAttribute("name", "X")
            parx.setAttribute("type", "float")
            pary = self.__doc.createElement("param")
            pary.setAttribute("name", "Y")
            pary.setAttribute("type", "float")
            parz = self.__doc.createElement("param")
            parz.setAttribute("name", "Z")
            parz.setAttribute("type", "float")
            acc.appendChild(parx)
            acc.appendChild(pary)
            acc.appendChild(parz)
            techcom.appendChild(acc)
            sourcep.appendChild(far)
            sourcep.appendChild(techcom)
            me.appendChild(sourcep)
            # positions
            # normals
            float_normals = ""
            float_normals_count = ""
            iin = 0
            iin = ""
            start_time = clock()
            # mesh.sort_faces()
            # mesh.calc_normals()
            face_index_pairs = mesh.tessfaces
            ush = 0
            has_sharp_edges = 0
            # for f in mesh.tessfaces:
            for f in face_index_pairs:
                if f.use_smooth:
                    for v_idx in f.vertices:
                        for e_idx in mesh.edges:
                            for ev in e_idx.vertices:
                                if ev == v_idx:
                                    if e_idx.use_edge_sharp:
                                        ush = 1
                                        has_sharp_edges = 1
                                    else:
                                        ush = 2

                        if ush == 1:
                            v = me_verts[v_idx]
                            noKey = utils.veckey3d21(f.normal)
                            float_normals += '%.6f %.6f %.6f ' % noKey
                            iin += "1"
                        if ush == 2:
                            v = me_verts[v_idx]
                            noKey = utils.veckey3d21(v.normal)
                            float_normals += '%.6f %.6f %.6f ' % noKey
                            iin += "1"
                        ush = 0

                else:
                    fnc = ""
                    fns = 0
                    fnlx = 0
                    fnly = 0
                    fnlz = 0
                    if self.__config.avg_pface:
                        if fns == 0:
                            fnlx = f.normal.x
                            fnly = f.normal.y
                            fnlz = f.normal.z
                            fnc += "1"
                            cbPrint("face%s" % fnlx)
                        for fn in face_index_pairs:
                            if (f.normal.angle(fn.normal) <
                                .052):
                                if (f.normal.angle(fn.normal) >
                                    - .052):
                                    fnlx = fn.normal.x + fnlx
                                    fnly = fn.normal.x + fnly
                                    fnlz = fn.normal.x + fnlz
                                    fnc += "1"
                                    fns = 1

                        cbPrint("facen2%s" % (fnlx / len(fnc)))
                        iin += "1"
                        float_normals += '%.6f %.6f %.6f ' % (fnlx / len(fnc),
                            fnly / len(fnc),
                            fnlz / len(fnc))
                    else:
                        noKey = utils.veckey3d21(f.normal)
                        float_normals += '%.6f %.6f %.6f ' % noKey
                        iin += "1"  # for v_idx in f.vertices:

            # Hard, each vert gets normal
            # from the face.
            float_normals_count = len(iin) * 3
            cbPrint('normals took %.4f sec.' % (clock() - start_time))
            float_vertsc = len(iin)
            cbPrint(str(float_vertsc))
            iin = 0
            sourcenor = self.__doc.createElement("source")
            sourcenor.setAttribute("id", "%s-normals" % (mname))
            farn = self.__doc.createElement("float_array")
            farn.setAttribute("id", "%s-normals-array" % (mname))
            farn.setAttribute("count", "%s" % (float_normals_count))
            fpos = self.__doc.createTextNode("%s" % (float_normals))
            farn.appendChild(fpos)
            tcom = self.__doc.createElement("technique_common")
            acc = self.__doc.createElement("accessor")
            acc.setAttribute("source", "%s-normals-array" % (mname))
            acc.setAttribute("count", "%s" % (float_vertsc))
            acc.setAttribute("stride", "3")
            parx = self.__doc.createElement("param")
            parx.setAttribute("name", "X")
            parx.setAttribute("type", "float")
            pary = self.__doc.createElement("param")
            pary.setAttribute("name", "Y")
            pary.setAttribute("type", "float")
            parz = self.__doc.createElement("param")
            parz.setAttribute("name", "Z")
            parz.setAttribute("type", "float")
            acc.appendChild(parx)
            acc.appendChild(pary)
            acc.appendChild(parz)
            tcom.appendChild(acc)
            sourcenor.appendChild(farn)
            sourcenor.appendChild(tcom)
            me.appendChild(sourcenor)
            # end normals
            # uv we will make assumptions here because this is
            # for a game export so there should allways
            # be a uv set
            uvs = self.__doc.createElement("source")
            uvlay = []
            # lay = object_.data.uv_textures.active
            # if lay:
            start_time = clock()
            uvlay = object_.data.tessface_uv_textures
            if uvlay:
                cbPrint("Found UV map.")
            elif (object_.type == "MESH"):
                bpy.ops.mesh.uv_texture_add()
                cbPrint("Your UV map is missing, adding.")
            for uvindex, uvlayer in enumerate(uvlay):
                mapslot = uvindex
                mapname = str(uvlayer.name)
                uvid = "%s-%s-%s" % (mname, mapname, mapslot)
                i_n = -1
                ii = 0  # Count how many UVs we write
                test = ""
                for uf in uvlayer.data:
                # workaround, since uf.uv iteration
                # is wrong atm
                    for uv in uf.uv:
                        if i_n == -1:
                            test += '%.6f %.6f ' % uv[:]
                            i_n = 0
                        else:
                            if i_n == 7:
                        # fw('\n\t\t\t ')
                                i_n = 0
                            test += '%.6f %.6f ' % uv[:]
                        i_n += 1
                        ii += 1  # One more UV

                uvc1 = str((ii) * 2)
                uvc2 = str(ii)

            uvs.setAttribute("id", "%s-%s-%s" % (mname, mapname, mapslot))
            cbPrint('UVs took %.4f sec.' % (clock() - start_time))
            fa = self.__doc.createElement("float_array")
            fa.setAttribute("id", "%s-array" % (uvid))
            fa.setAttribute("count", "%s" % (uvc1))
            uvp = self.__doc.createTextNode("%s" % (test))
            fa.appendChild(uvp)
            tc2 = self.__doc.createElement("technique_common")
            acc2 = self.__doc.createElement("accessor")
            acc2.setAttribute("source", "#%s-array" % (uvid))
            acc2.setAttribute("count", "%s" % (uvc2))
            acc2.setAttribute("stride", "2")
            pars = self.__doc.createElement("param")
            pars.setAttribute("name", "S")
            pars.setAttribute("type", "float")
            part = self.__doc.createElement("param")
            part.setAttribute("name", "T")
            part.setAttribute("type", "float")
            acc2.appendChild(pars)
            acc2.appendChild(part)
            tc2.appendChild(acc2)
            uvs.appendChild(fa)
            uvs.appendChild(tc2)
            me.appendChild(uvs)
            # enduv
            # vertcol
            # from fbx exporter
            vcols = self.__doc.createElement("source")
            cn = 0
            # list for vert alpha if found
            alpha_found = 0
            alpha_list = []
            if object_.data.tessface_vertex_colors:
                collayers = object_.data.tessface_vertex_colors
                # TODO merge these two for loops
                for collayer in collayers:
                    ni = -1
                    colname = str(collayer.name)
                    if colname == "alpha":
                        alpha_found = 1
                        for fi, cf in enumerate(collayer.data):
                            cbPrint(str(fi))
                            if len(mesh.tessfaces[fi].vertices) == 4:
                                colors = [cf.color1[:],
                                          cf.color2[:],
                                          cf.color3[:],
                                          cf.color4[:]]
                            else:
                                colors = [cf.color1[:],
                                          cf.color2[:],
                                          cf.color3[:]]
                            for colr in colors:
                                tmp = [fi, colr[0]]

                            alpha_list.append(tmp)

                        for vca in alpha_list:
                            cbPrint(str(vca))

                for collayer in collayers:
                    ni = -1
                    ii = 0  # Count how many Colors we write
                    vcol = ""
                    colname = str(collayer.name)
                    if colname == "alpha":
                        cbPrint("Alpha.")
                    else:
                        for fi, cf in enumerate(collayer.data):
                            colors = [cf.color1[:], cf.color2[:], cf.color3[:]]
                            if len(mesh.tessfaces[fi].vertices) == 4:
                                colors.append(cf.color4[:])

                            for colr in colors:
                                if ni == -1:
                                    if alpha_found == 1:
                                        tmp = alpha_list[fi]
                                        vcol += '%.6f %.6f %.6f ' % colr
                                        vcol += '%.6f ' % tmp[1]
                                        cbPrint(colr[0])
                                    else:
                                        vcol += '%.6f %.6f %.6f ' % colr
                                    ni = 0
                                else:
                                    if ni == 7:
                                        ni = 0
                                    if alpha_found == 1:
                                        tmp = alpha_list[fi]
                                        vcol += '%.6f %.6f %.6f ' % colr
                                        vcol += '%.6f ' % tmp[1]
                                        cbPrint(colr[0])
                                    else:
                                        vcol += '%.6f %.6f %.6f ' % colr
                                ni += 1
                                ii += 1  # One more Color

                                # thankyou fbx
                        if cn == 1:
                            vcolc1 = str((ii) * 4)
                        else:
                            vcolc1 = str((ii) * 3)
                        # vcolc1=str((ii)*3)
                        vcolc2 = str(ii)

                vcols.setAttribute("id", "%s-colors" % (mname))
                fa = self.__doc.createElement("float_array")
                fa.setAttribute("id", "%s-colors-array" % (mname))
                fa.setAttribute("count", "%s" % (vcolc1))
                vcolp = self.__doc.createTextNode("%s" % (vcol))
                fa.appendChild(vcolp)
                tc2 = self.__doc.createElement("technique_common")
                acc3 = self.__doc.createElement("accessor")
                acc3.setAttribute("source", "#%s-colors-array" % (mname))
                acc3.setAttribute("count", "%s" % (vcolc2))
                if alpha_found == 1:
                    acc3.setAttribute("stride", "4")
                else:
                    acc3.setAttribute("stride", "3")
                parr = self.__doc.createElement("param")
                parr.setAttribute("name", "R")
                parr.setAttribute("type", "float")
                parg = self.__doc.createElement("param")
                parg.setAttribute("name", "G")
                parg.setAttribute("type", "float")
                parb = self.__doc.createElement("param")
                parb.setAttribute("name", "B")
                parb.setAttribute("type", "float")
                para = self.__doc.createElement("param")
                para.setAttribute("name", "A")
                para.setAttribute("type", "float")
                acc3.appendChild(parr)
                acc3.appendChild(parg)
                acc3.appendChild(parb)
                if alpha_found == 1:
                    acc3.appendChild(para)
                alpha_found = 0
                tc2.appendChild(acc3)
                vcols.appendChild(fa)
                vcols.appendChild(tc2)
            me.appendChild(vcols)
            # endvertcol
            # vertices
            vertic = self.__doc.createElement("vertices")
            vertic.setAttribute("id", "%s-vertices" % (mname))
            inputsem1 = self.__doc.createElement("input")
            inputsem1.setAttribute("semantic", "POSITION")
            inputsem1.setAttribute("source", "#%s-positions" % (mname))
            vertic.appendChild(inputsem1)
            me.appendChild(vertic)
            # end vertices
            # polylist
            mat = mesh.materials[:]
            start_time = clock()
            if mat:
                # yes lets go through them 1 at a time
                for im in enumerate(mat):
                    polyl = self.__doc.createElement("polylist")
                    polyl.setAttribute("material", "%s" % (im[1].name))
                    verts = ""
                    face_count = ""
                    face_counter = 0
                    ni = 0
                    texindex = 0
                    nverts = ""
                    for f in face_index_pairs:
                        fi = f.vertices[:]
                        if f.material_index == im[0]:
                            nverts += str(len(f.vertices)) + " "
                            face_count += str(
                                "%s" % (face_counter))
                            for v in f.vertices:
                                verts += str(v) + " "
                                if f.use_smooth:
                                    if has_sharp_edges == 1:
                                        verts += str("%s " % (ni))
                                        ni += 1
                                    else:
                                        verts += str(v) + " "
                                    # verts += str("%s "%(ni))
                                    # ni += 1
                                else:
                                    verts += str("%s " % (ni))
                                verts += str("%s " % (texindex))
                                if mesh.vertex_colors:
                                    verts += str(
                                        "%s " % (texindex))
                                texindex += 1

                        if f.use_smooth:
                            if has_sharp_edges != 1:
                                ni += len(f.vertices)
                        else:
                            ni += 1  # #<--naughty naughty
                        if f.material_index == im[0]:
                            texindex = texindex
                        else:
                            texindex += len(fi)  # 4#3

                    cbPrint(str(ni))
                    verts += ""
                    cbPrint('polylist took %.4f sec.' % (clock() - start_time))
                    polyl.setAttribute("count", "%s" % (len(face_count)))
                    inpv = self.__doc.createElement("input")
                    inpv.setAttribute("semantic", "VERTEX")
                    inpv.setAttribute("source", "#%s-vertices" % (mname))
                    inpv.setAttribute("offset", "0")
                    polyl.appendChild(inpv)
                    inpn = self.__doc.createElement("input")
                    inpn.setAttribute("semantic", "NORMAL")
                    inpn.setAttribute("source", "#%s-normals" % (mname))
                    inpn.setAttribute("offset", "1")
                    polyl.appendChild(inpn)
                    inpuv = self.__doc.createElement("input")
                    inpuv.setAttribute("semantic", "TEXCOORD")
                    inpuv.setAttribute("source", "#%s" % (uvid))
                    # will allways be 2, vcolors can be 2 or 3
                    inpuv.setAttribute("offset", "2")
                    inpuv.setAttribute("set", "%s" % (mapslot))
                    polyl.appendChild(inpuv)
                    if mesh.vertex_colors:
                        inpvcol = self.__doc.createElement("input")
                        inpvcol.setAttribute("semantic", "COLOR")
                        inpvcol.setAttribute("source", "#%s-colors" % (mname))
                        # vcolors can be 2 or 3
                        inpvcol.setAttribute("offset", "3")
                        polyl.appendChild(inpvcol)
                    vc = self.__doc.createElement("vcount")
                    vcl = self.__doc.createTextNode("%s" % (nverts))
                    vc.appendChild(vcl)
                    pl = self.__doc.createElement("p")
                    pltn = self.__doc.createTextNode("%s" % (verts))
                    pl.appendChild(pltn)
                    polyl.appendChild(vc)
                    polyl.appendChild(pl)
                    me.appendChild(polyl)

                    # endpolylist
            has_sharp_edges = 0
            emt = self.__doc.createElement("extra")
            emtt = self.__doc.createElement("technique")
            emtt.setAttribute("profile", "MAYA")
            dsd = self.__doc.createElement("double_sided")
            dsdtn = self.__doc.createTextNode("1")
            dsd.appendChild(dsdtn)
            emtt.appendChild(dsd)
            emt.appendChild(emtt)
            me.appendChild(emt)
            geo.appendChild(me)
            libgeo.appendChild(geo)

            # bpy.data.meshes.remove(mesh)

    def __get_objects_for_library_geometries(self):
        objects = []
        for object_ in bpy.context.selected_objects:
            if (object_.name[:6] != "_joint"):
                if (object_.type == "MESH"):
                    objects.append(object_)

        return objects

    def __export_library_controllers(self, parent_element):
        libcont = self.__doc.createElement("library_controllers")

        for selected_object in bpy.context.selected_objects:
            if not "_boneGeometry" in selected_object.name:
                # "some" code borrowed from dx exporter
                armatures = self.__get_armatures(selected_object)

                if armatures:
                    self.__process_bones(libcont, selected_object, armatures)

        parent_element.appendChild(libcont)

    def __get_armatures(self, object_):
        return [modifier for modifier in object_.modifiers
                if modifier.type == "ARMATURE"]

    def __process_bones(self, libcont, object_, armatures):
        armature = armatures[0].object

        contr = self.__doc.createElement("controller")
        contr.setAttribute("id", "%s_%s" % (armature.name, object_.name))
        libcont.appendChild(contr)
        skin_node = self.__doc.createElement("skin")
        skin_node.setAttribute("source", "#%s" % object_.name)
        contr.appendChild(skin_node)
        mtx = utils.matrix_to_string(Matrix())
        bsm = self.__doc.createElement("bind_shape_matrix")
        bsmv = self.__doc.createTextNode("%s" % mtx)
        bsm.appendChild(bsmv)
        skin_node.appendChild(bsm)
        src = self.__doc.createElement("source")
        src.setAttribute("id", "%s_%s_joints" % (armature.name, object_.name))

        armature_bones = self.__get_bones(armature)
        idar = self.__doc.createElement("IDREF_array")
        idar.setAttribute("id", "%s_%s_joints_array"
                          % (armature.name, object_.name))
        idar.setAttribute("count", "%s" % len(armature_bones))
        blist = self.__get_bone_names_for_idref(armature_bones)

        cbPrint(blist)
        jnl = self.__doc.createTextNode("%s" % blist)
        idar.appendChild(jnl)
        src.appendChild(idar)
        tcom = self.__doc.createElement("technique_common")
        acc = self.__doc.createElement("accessor")
        acc.setAttribute("source", "#%s_%s_joints_array"
                         % (armature.name, object_.name))
        acc.setAttribute("count", "%s" % len(armature_bones))
        acc.setAttribute("stride", "1")
        paran = self.__doc.createElement("param")
        paran.setAttribute("type", "IDREF")
        acc.appendChild(paran)
        tcom.appendChild(acc)
        src.appendChild(tcom)
        skin_node.appendChild(src)
        source_node = self.__doc.createElement("source")
        source_node.setAttribute("id", "%s_%s_matrices"
                                 % (armature.name, object_.name))

        float_array_node = self.__doc.createElement("float_array")
        float_array_node.setAttribute("id", "%s_%s_matrices_array"
                                      % (armature.name, object_.name))
        float_array_node.setAttribute("count", "%s"
                                      % (len(armature_bones) * 16))

        self.__export_float_array(armature_bones, float_array_node)
        source_node.appendChild(float_array_node)

        tcommat = self.__doc.createElement("technique_common")
        accm = self.__doc.createElement("accessor")
        accm.setAttribute("source", "#%s_%s_matrices_array"
                          % (armature.name, object_.name))
        accm.setAttribute("count", "%s" % (len(armature_bones)))
        accm.setAttribute("stride", "16")
        paranm = self.__doc.createElement("param")
        paranm.setAttribute("type", "float4x4")
        accm.appendChild(paranm)
        tcommat.appendChild(accm)
        source_node.appendChild(tcommat)
        skin_node.appendChild(source_node)
        srcw = self.__doc.createElement("source")
        srcw.setAttribute("id", "%s_%s_weights"
                          % (armature.name, object_.name))
        flarw = self.__doc.createElement("float_array")
        flarw.setAttribute("id", "%s_%s_weights_array"
                           % (armature.name, object_.name))
        wa = ""
        vw = ""
        me = object_.data
        vcntr = ""
        vcount = 0

        for v in me.vertices:
            for g in v.groups:
                wa += "%.6f " % g.weight
                for gr in object_.vertex_groups:
                    if gr.index == g.group:
                        for bone_id, bone in enumerate(armature_bones):
                            if bone.name == gr.name:
                                vw += "%s " % bone_id

                vw += "%s " % str(vcount)
                vcount += 1
                cbPrint("Doing weights.")

            vcntr += "%s " % len(v.groups)

        flarw.setAttribute("count", "%s" % vcount)
        lfarwa = self.__doc.createTextNode("%s" % wa)
        flarw.appendChild(lfarwa)
        tcomw = self.__doc.createElement("technique_common")
        accw = self.__doc.createElement("accessor")
        accw.setAttribute("source", "#%s_%s_weights_array"
                          % (armature.name, object_.name))
        accw.setAttribute("count", "%s" % vcount)
        accw.setAttribute("stride", "1")
        paranw = self.__doc.createElement("param")
        paranw.setAttribute("type", "float")
        accw.appendChild(paranw)
        tcomw.appendChild(accw)
        srcw.appendChild(flarw)
        srcw.appendChild(tcomw)
        skin_node.appendChild(srcw)

        jnts = self.__doc.createElement("joints")
        is1 = self.__doc.createElement("input")
        is1.setAttribute("semantic", "JOINT")
        is1.setAttribute("source", "#%s_%s_joints"
                         % (armature.name, object_.name))
        jnts.appendChild(is1)
        is2 = self.__doc.createElement("input")
        is2.setAttribute("semantic", "INV_BIND_MATRIX")
        is2.setAttribute("source", "#%s_%s_matrices"
                         % (armature.name, object_.name))
        jnts.appendChild(is2)
        skin_node.appendChild(jnts)
        vertw = self.__doc.createElement("vertex_weights")
        vertw.setAttribute("count", "%s" % len(me.vertices))
        is3 = self.__doc.createElement("input")
        is3.setAttribute("semantic", "JOINT")
        is3.setAttribute("offset", "0")
        is3.setAttribute("source", "#%s_%s_joints"
                         % (armature.name, object_.name))
        vertw.appendChild(is3)
        is4 = self.__doc.createElement("input")
        is4.setAttribute("semantic", "WEIGHT")
        is4.setAttribute("offset", "1")
        is4.setAttribute("source", "#%s_%s_weights"
                         % (armature.name, object_.name))
        vertw.appendChild(is4)
        vcnt = self.__doc.createElement("vcount")
        vcnt1 = self.__doc.createTextNode("%s" % vcntr)
        vcnt.appendChild(vcnt1)
        vertw.appendChild(vcnt)
        vlst = self.__doc.createElement("v")
        vlst1 = self.__doc.createTextNode("%s" % vw)
        vlst.appendChild(vlst1)
        vertw.appendChild(vlst)
        skin_node.appendChild(vertw)

    def __export_library_animation_clips_and_animations(self, parent_element):
        libanmcl = self.__doc.createElement("library_animation_clips")
        libanm = self.__doc.createElement("library_animations")
        parent_element.appendChild(libanmcl)
        parent_element.appendChild(libanm)

        asw = 0
        ande = 0
        ande2 = 0
        for i in bpy.context.selected_objects:
            lnname = str(i.name)
            for item in bpy.context.blend_data.groups:
                if item:
                    ename = str(item.id_data.name)

            if lnname[:8] == "animnode":
                ande2 = 1
                actname = i["animname"]
                sf = i["startframe"]
                ef = i["endframe"]
                cbPrint(actname)
                cbPrint(sf)
                cbPrint(ef)
                anicl = self.__doc.createElement("animation_clip")
                anicl.setAttribute("id", "%s-%s" % (actname, ename[14:]))
                anicl.setAttribute("start", "%s" % (utils.convert_time(sf)))
                anicl.setAttribute("end", "%s" % (utils.convert_time(ef)))
                for i in bpy.context.selected_objects:
                    if i.animation_data:
                        if i.type == 'ARMATURE':
                            cbPrint("Object is armature, cannot process animations.")
                        elif i.animation_data.action:

                            for axis in iter(AXISES):
                                anm = self.extract_anil(i, axis)
                                libanm.appendChild(anm)

                            for axis in iter(AXISES):
                                anm = self.extract_anir(i, axis)
                                libanm.appendChild(anm)

                            self.__export_instance_animation_parameters(i,
                                                                        anicl)

                libanmcl.appendChild(anicl)

        if ande2 == 0:
            for i in bpy.context.selected_objects:
                if i.animation_data:
                    if i.type == 'ARMATURE':
                        cbPrint("Object is armature, cannot process animations.")
                    else:
                        if i.animation_data.action:
                            for item in bpy.context.blend_data.groups:
                                if item:
                                    ename = str(item.id_data.name)

                            act = i.animation_data.action
                            curves = act.fcurves
                            frstrt = curves.data.frame_range[0]
                            frend = curves.data.frame_range[1]
                            anmlx = self.extract_anil(i, 'X')
                            anmly = self.extract_anil(i, 'Y')
                            anmlz = self.extract_anil(i, 'Z')
                            anmrx = self.extract_anir(i, 'X')
                            anmry = self.extract_anir(i, 'Y')
                            anmrz = self.extract_anir(i, 'Z')
                            # animationclip name and framerange
                            for ai in i.children:
                                aname = str(ai.name)
                                if aname[:8] == "animnode":
                                    ande = 1
                                    cbPrint(ai["animname"])
                                    cbPrint(ai["startframe"])
                                    cbPrint(ai["endframe"])
                                    act_name = ai["animname"]
                                    start_frame = ai["startframe"]
                                    end_frame = ai["endframe"]

                                    anicl = self.__export__animation_clip(
                                                                i,
                                                                ename,
                                                                act_name,
                                                                start_frame,
                                                                end_frame)
                                    libanmcl.appendChild(anicl)

                            if ande == 0:
                                if self.__config.merge_anm:
                                    if asw == 0:
                                        anicl = self.__export__animation_clip(
                                                                i,
                                                                ename,
                                                                act.name,
                                                                frstrt,
                                                                frend)
                                        asw = 1
                                    else:
                                        cbPrint("Merging clips.")
                                else:
                                    anicl = self.__export__animation_clip(
                                                                i,
                                                                ename,
                                                                act.name,
                                                                frstrt,
                                                                frend)
                        if asw == 0:
                            libanmcl.appendChild(anicl)
                        libanm.appendChild(anmlx)
                        libanm.appendChild(anmly)
                        libanm.appendChild(anmlz)
                        libanm.appendChild(anmrx)
                        libanm.appendChild(anmry)
                        libanm.appendChild(anmrz)

            if asw == 1:
                libanmcl.appendChild(anicl)

    def __export__animation_clip(self, i, ename, act_name, start_frame, end_frame):
        anicl = self.__doc.createElement("animation_clip")
        anicl.setAttribute("id", "%s-%s" % (act_name, ename[14:]))
        anicl.setAttribute("start", "%s" % (utils.convert_time(start_frame)))
        anicl.setAttribute("end", "%s" % (utils.convert_time(end_frame)))
        self.__export_instance_animation_parameters(i, anicl)

        return anicl

    def __export_instance_animation_parameters(self, i, anicl):
        self.__export_instance_parameter(i, anicl, "location")
        self.__export_instance_parameter(i, anicl, "rotation_euler")

    def __export_instance_parameter(self, i, anicl, parameter):
        for axis in iter(AXISES):
            inst = self.__doc.createElement("instance_animation")
            inst.setAttribute("url", "#%s_%s_%s" % (i.name, parameter, axis))
            anicl.appendChild(inst)

    def __export_library_visual_scenes(self, parent_element):
        current_element = self.__doc.createElement("library_visual_scenes")
        visual_scene = self.__doc.createElement("visual_scene")
        current_element.appendChild(visual_scene)
        parent_element.appendChild(current_element)

        # doesnt matter what name we have here as long as it is
        # the same for <scene>
        visual_scene.setAttribute("id", "scene")
        visual_scene.setAttribute("name", "scene")
        for item in bpy.context.blend_data.groups:
            if item:
                ename = str(item.id_data.name)
                node1 = self.__doc.createElement("node")
                node1.setAttribute("id", "%s" % (ename))
                node1.setIdAttribute('id')
            visual_scene.appendChild(node1)
            node1 = self.vsp(item.objects, node1)
            # exportnode settings
            ext1 = self.__doc.createElement("extra")
            tc3 = self.__doc.createElement("technique")
            tc3.setAttribute("profile", "CryEngine")
            prop1 = self.__doc.createElement("properties")
            if self.__config.export_type == 'CGF':
                pcgf = self.__doc.createTextNode("fileType=cgf")
                prop1.appendChild(pcgf)
            if self.__config.export_type == 'CGA & ANM':
                pcga = self.__doc.createTextNode("fileType=cgaanm")
                prop1.appendChild(pcga)
            if self.__config.export_type == 'CHR & CAF':
                pchrcaf = self.__doc.createTextNode("fileType=chrcaf")
                prop1.appendChild(pchrcaf)
            if self.__config.donot_merge:
                pdnm = self.__doc.createTextNode("DoNotMerge")
                prop1.appendChild(pdnm)
            tc3.appendChild(prop1)
            ext1.appendChild(tc3)
            node1.appendChild(ext1)

    def __export_scene(self, parent_element):
        # <scene> nothing really changes here or rather it doesnt need to.
        scene = self.__doc.createElement("scene")
        ivs = self.__doc.createElement("instance_visual_scene")
        ivs.setAttribute("url", "#scene")
        scene.appendChild(ivs)
        parent_element.appendChild(scene)


def write_to_file(config, doc, file_name, exe):
    xml_string = doc.toprettyxml(indent="  ")
    file = open(file_name, "w")
    file.write(xml_string)
    file.close()

    dae_file_for_rc = utils.get_absolute_path_for_rc(file_name)
    rc_params = ["/verbose", "/threads=cores"]
    if config.refresh_rc:
        rc_params.append("/refresh")

    if config.run_rc or config.do_materials:
        if config.do_materials:
            rc_params.append("/createmtl=1")

        rc_process = utils.run_rc(exe, dae_file_for_rc, rc_params)

        if config.do_materials:
            mtl_fix_thread = threading.Thread(
                target=fix_normalmap_in_mtls,
                args=(rc_process, file_name)
            )
            mtl_fix_thread.start()

    if config.make_layer:
        layer = make_layer(file_name)
        lyr_file_name = os.path.splitext(file_name)[0] + ".lyr"
        file = open(lyr_file_name, 'w')
        file.write(layer)
        file.close()


def make_layer(fname):
    lName = "ExportedLayer"
    layerDoc = Document()
    # ObjectLayer
    objLayer = layerDoc.createElement("ObjectLayer")
    # Layer
    layer = layerDoc.createElement("Layer")
    layer.setAttribute('name', lName)
    layer.setAttribute('GUID', utils.generateGUID())
    layer.setAttribute('FullName', lName)
    layer.setAttribute('External', '0')
    layer.setAttribute('Exportable', '1')
    layer.setAttribute('ExportLayerPak', '1')
    layer.setAttribute('DefaultLoaded', '0')
    layer.setAttribute('HavePhysics', '1')
    layer.setAttribute('Expanded', '0')
    layer.setAttribute('IsDefaultColor', '1')
    # Layer Objects
    layerObjects = layerDoc.createElement("LayerObjects")
    # Actual Objects
    for group in bpy.context.blend_data.groups:
        if group.objects > 1:
            origin = 0, 0, 0
            rotation = 1, 0, 0, 0
        else:
            origin = group.objects[0].location
            rotation = group.objects[0].delta_rotation_quaternion
        if 'CryExportNode' in group.name:
            object_node = layerDoc.createElement("Object")
            object_node.setAttribute('name', group.name[14:])
            object_node.setAttribute('Type', 'Entity')
            object_node.setAttribute('Id', utils.generateGUID())
            object_node.setAttribute('LayerGUID', layer.getAttribute('GUID'))
            object_node.setAttribute('Layer', lName)
            positionString = "{!s}, {!s}, {!s}".format(
                origin[0], origin[1], origin[2])
            object_node.setAttribute('Pos', positionString)
            rotationString = "{!s}, {!s}, {!s}, {!s}".format(
                rotation[0], rotation[1],
                rotation[2], rotation[3])
            object_node.setAttribute('Rotate', rotationString)
            object_node.setAttribute('EntityClass', 'BasicEntity')
            object_node.setAttribute('FloorNumber', '-1')
            object_node.setAttribute('RenderNearest', '0')
            object_node.setAttribute('NoStaticDecals', '0')
            object_node.setAttribute('CreatedThroughPool', '0')
            object_node.setAttribute('MatLayersMask', '0')
            object_node.setAttribute('OutdoorOnly', '0')
            object_node.setAttribute('CastShadow', '1')
            object_node.setAttribute('MotionBlurMultiplier', '1')
            object_node.setAttribute('LodRatio', '100')
            object_node.setAttribute('ViewDistRatio', '100')
            object_node.setAttribute('HiddenInGame', '0')
            properties = layerDoc.createElement("Properties")
            properties.setAttribute('object_Model', '/Objects/'
                                    + group.name[14:] + '.cgf')
            properties.setAttribute('bCanTriggerAreas', '0')
            properties.setAttribute('bExcludeCover', '0')
            properties.setAttribute('DmgFactorWhenCollidingAI', '1')
            properties.setAttribute('esFaction', '')
            properties.setAttribute('bHeavyObject', '0')
            properties.setAttribute('bInteractLargeObject', '0')
            properties.setAttribute('bMissionCritical', '0')
            properties.setAttribute('bPickable', '0')
            properties.setAttribute('soclasses_SmartObjectClass', '')
            properties.setAttribute('bUsable', '0')
            properties.setAttribute('UseMessage', '0')
            health = layerDoc.createElement("Health")
            health.setAttribute('bInvulnerable', '1')
            health.setAttribute('MaxHealth', '500')
            health.setAttribute('bOnlyEnemyFire', '1')
            interest = layerDoc.createElement("Interest")
            interest.setAttribute('soaction_Action', '')
            interest.setAttribute('bInteresting', '0')
            interest.setAttribute('InterestLevel', '1')
            interest.setAttribute('Pause', '15')
            interest.setAttribute('Radius', '20')
            interest.setAttribute('bShared', '0')
            vOffset = layerDoc.createElement('vOffset')
            vOffset.setAttribute('x', '0')
            vOffset.setAttribute('y', '0')
            vOffset.setAttribute('z', '0')
            interest.appendChild(vOffset)
            properties.appendChild(health)
            properties.appendChild(interest)
            object_node.appendChild(properties)
            layerObjects.appendChild(object_node)

    layer.appendChild(layerObjects)
    objLayer.appendChild(layer)
    layerDoc.appendChild(objLayer)
    return layerDoc.toprettyxml(indent="  ")


def fix_normalmap_in_mtls(rc_process, dae_file):
    SUCCESS = 0

    return_code = rc_process.wait()

    if return_code == SUCCESS:
        export_directory = os.path.dirname(dae_file)

        mtl_files = utils.get_mtl_files_in_directory(export_directory)

        for mtl_file_name in mtl_files:
            fix_normalmap_in_mtl(mtl_file_name)


def fix_normalmap_in_mtl(mtl_file_name):
    TMP_FILE_SUFFIX = ".tmp"
    BAD_TAG_NAME = "<Texture Map=\"NormalMap\" File=\""
    GOOD_TAG_NAME = "<Texture Map=\"Bumpmap\" File=\""

    tmp_mtl_file_name = mtl_file_name + TMP_FILE_SUFFIX
    mtl_old_file = open(mtl_file_name, "r")
    mtl_new_file = open(tmp_mtl_file_name, "w")

    for line in mtl_old_file:
        line = line.replace(BAD_TAG_NAME, GOOD_TAG_NAME)
        mtl_new_file.write(line)

    mtl_old_file.close()
    mtl_new_file.close()

    os.remove(mtl_file_name)
    os.rename(tmp_mtl_file_name, mtl_file_name)


def save(config, context, exe):
    # prevent wasting time for exporting if RC was not found
    if not os.path.isfile(exe):
        raise exceptions.NoRcSelectedException

    exporter = CrytekDaeExporter(config, exe)
    exporter.export()


def menu_func_export(self, context):
    self.layout.operator(CrytekDaeExporter.bl_idname, text="Export Crytek Dae")


def register():
    bpy.utils.register_class(CrytekDaeExporter)
    bpy.types.INFO_MT_file_export.append(menu_func_export)

    bpy.utils.register_class(TriangulateMeError)
    bpy.utils.register_class(Error)


def unregister():
    bpy.utils.unregister_class(CrytekDaeExporter)
    bpy.types.INFO_MT_file_export.remove(menu_func_export)
    bpy.utils.unregister_class(TriangulateMeError)
    bpy.utils.unregister_class(Error)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.export_mesh.crytekdae('INVOKE_DEFAULT')
