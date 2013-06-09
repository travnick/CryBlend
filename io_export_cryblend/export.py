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
#-------------------------------------------------------------------------------
# Name:        export.py
# Purpose:     export to cryengine main
#
# Author:      angelo j miner, some code borrowed from fbx exporter Campbell Barton
# Extended by: Duo Oratar
#
# Created:     23/01/2012
# Copyright:   (c) angelo 2012
# Licence:     GPLv2+
#-------------------------------------------------------------------------------




import os
import subprocess
import bpy
import math
import mathutils
import time
from time import clock
from mathutils import *
from math import *
import random

from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
import io_export_cryblend
#from io_export_cryblend import *
from io_export_cryblend import utils
#from io_export_cryblend import hbanim
#from hbanim import *
#from io_export_cryblend import vs
import xml.dom.minidom
from xml.dom.minidom import *#Document

from io_export_cryblend.outPipe import cbPrint
    

#rc = 'G:\\apps\\CryENGINE_PC_v3_3_9_3410_FreeSDK\\Bin32\\rc\\rc.exe'#path to your rc.exe
#rc = r'G:\apps\CryENGINE_PC_v3_4_0_3696_freeSDK\Bin32\rc\rc.exe'#path to your rc.exe#thankyou Borgleader
#the following func is from http://ronrothman.com/public/leftbraned/xml-dom-minidom-toprettyxml-and-silly-whitespace/ modified to use the current ver of shipped python
def fixed_writexml(self, writer, indent="", addindent="", newl=""):
    # indent = current indentation
    # addindent = indentation to add to higher levels
    # newl = newline string
        writer.write(indent+"<" + self.tagName)
        attrs = self._get_attributes()
        a_names = sorted(attrs.keys())
        for a_name in a_names:
            writer.write(" %s=\"" % a_name)
            xml.dom.minidom._write_data(writer, attrs[a_name].value)
            writer.write("\"")
        if self.childNodes:
            if len(self.childNodes) == 1 and self.childNodes[0].nodeType == xml.dom.minidom.Node.TEXT_NODE:
                writer.write(">")
                self.childNodes[0].writexml(writer, "", "", "")
                writer.write("</%s>%s" % (self.tagName, newl))
                return
            writer.write(">%s"%(newl))
            for node in self.childNodes:
                node.writexml(writer,indent+addindent,addindent,newl)
            writer.write("%s</%s>%s" % (indent,self.tagName,newl))
        else:
            writer.write("/>%s"%(newl))
# replace minidom's function with ours
xml.dom.minidom.Element.writexml = fixed_writexml
#end http://ronrothman.com/public/leftbraned/xml-dom-minidom-toprettyxml-and-silly-whitespace/
def write(self, doc, fname, exe):
    s = doc
    s = doc.toprettyxml(indent="  ")
    f = open(fname, "w")
    f.write(s)
    mystr = "/createmtl=1 "
    r = subprocess.Popen
    if self.run_rc:
        cbPrint(str(exe))#rc))
        cbPrint(fname)
        r([str(exe),str(fname)])
    if self.run_rcm:
        cbPrint(str(exe))#rc))
        cbPrint(mystr)
        cbPrint(fname)
        r([str(exe),str(mystr),str(fname)])
    if self.make_layer:
        lName = "ExportedLayer"
        layerDoc = Document()
        #ObjectLayer
        objLayer = layerDoc.createElement("ObjectLayer")
        #Layer
        layer = layerDoc.createElement("Layer")
        layer.setAttribute('name', lName)
        layer.setAttribute('GUID', generateGUID())
        layer.setAttribute('FullName', lName)
        layer.setAttribute('External', '0')
        layer.setAttribute('Exportable', '1')
        layer.setAttribute('ExportLayerPak', '1')
        layer.setAttribute('DefaultLoaded', '0')
        layer.setAttribute('HavePhysics', '1')
        layer.setAttribute('Expanded', '0')
        layer.setAttribute('IsDefaultColor', '1')
        #Layer Objects
        layerObjects = layerDoc.createElement("LayerObjects")
        #Actual Objects
        for group in bpy.context.blend_data.groups:
            count = 0
            for item in group.objects:
                count += 1
            
            if count > 1:
                origin = (0,0,0)
                rotation = (1,0,0,0)
            else:
                origin = group.objects[0].location
                rotation = group.objects[0].delta_rotation_quaternion
        
            if 'CryExportNode' in group.name:
                object = layerDoc.createElement("Object")
                object.setAttribute('name', group.name[14:])
                object.setAttribute('Type', 'Entity')
                object.setAttribute('Id', generateGUID())
                object.setAttribute('LayerGUID', layer.getAttribute('GUID'))
                object.setAttribute('Layer', lName)
                object.setAttribute('Pos', str(origin[0]) + ', ' + str(origin[1]) + ', ' + str(origin[2]))
                object.setAttribute('Rotate', str(rotation[0]) + ', ' + str(rotation[1]) + ', ' + str(rotation[2]) + ', ' + str(rotation[3]))
                object.setAttribute('EntityClass', 'BasicEntity')
                object.setAttribute('FloorNumber', '-1')
                object.setAttribute('RenderNearest', '0')
                object.setAttribute('NoStaticDecals', '0')
                object.setAttribute('CreatedThroughPool', '0')
                object.setAttribute('MatLayersMask', '0')
                object.setAttribute('OutdoorOnly', '0')
                object.setAttribute('CastShadow', '1')
                object.setAttribute('MotionBlurMultiplier', '1')
                object.setAttribute('LodRatio', '100')
                object.setAttribute('ViewDistRatio', '100')
                object.setAttribute('HiddenInGame', '0')
                
                properties = layerDoc.createElement("Properties")
                properties.setAttribute('object_Model', '/Objects/'+group.name[14:]+'.cgf')
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
                object.appendChild(properties)
                layerObjects.appendChild(object)
        layer.appendChild(layerObjects)
        objLayer.appendChild(layer)
        layerDoc.appendChild(objLayer)
        s = layerDoc.toprettyxml(indent="  ")
        f = open(fname[:len(fname)-4]+'.lyr', 'w')
        f.write(s)
        f.close()
#doc = Document()

def generateGUID():
    GUID = '{'
    GUID += randomSector(8)
    GUID += '-'
    GUID += randomSector(4)
    GUID += '-'
    GUID += randomSector(4)
    GUID += '-'
    GUID += randomSector(4)
    GUID += '-'
    GUID += randomSector(12)
    GUID += '}'
    return GUID

def randomSector(length):
    charOptions = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
    sector = ''
    counter = 0
    while counter < length:
        sector += charOptions[random.randrange(0,36)]
        counter += 1
    return sector    
    
class ExportCrytekDae:
    def execute(self, context, exe):
        filepath = bpy.path.ensure_ext(self.filepath, ".dae") #Ensure the correct extension for chosen path
        #make sure everything in our cryexportnode is selected
        for i in bpy.context.selectable_objects:#        for item in bpy.context.blend_data.groups:
            for group in bpy.context.blend_data.groups:#bpy.data.groups:
                for item in group.objects:
                    if item.name == i.name: #If item in group is selectable
                        bpy.data.objects[i.name].select = True
                        cbPrint(i.name)
                        
        #Duo Oratar
        #This is a small bit risky (I don't know if including more things in the selected objects will mess things up or not...
        #Easiest solution to the problem though
        cbPrint ("Searching for boneGeoms...")
        for i in bpy.context.selectable_objects:
            if "_boneGeometry" in i.name:
                bpy.data.objects[i.name].select = True
                cbPrint ("Bone Geometry found: " + i.name)
                        
        doc = Document() #New XML document
        col = doc.createElement('collada') #Top level element
#asset
        col.setAttribute("xmlns","http://www.collada.org/2005/11/COLLADASchema") #Attributes are x=y values inside a tag
        col.setAttribute("version","1.4.1")
        doc.appendChild(col) #Adding the newly created element into the Doc...
        asset = doc.createElement("asset")
        col.appendChild(asset)
        contrib = doc.createElement("contributor")
        asset.appendChild(contrib)
        auth = doc.createElement("author")
        contrib.appendChild(auth)
        authname = doc.createTextNode("Blender User")
        auth.appendChild(authname)
        authtool = doc.createElement("authoring_tool")
        authtname = doc.createTextNode("CryENGINE exporter for Blender v%s by angjminer, extended by Duo Oratar"% (bpy.app.version_string))
        authtool.appendChild(authtname)
        contrib.appendChild(authtool)
        created = doc.createElement("created")
        asset.appendChild(created)
        modified = doc.createElement("modified")
        asset.appendChild(modified)
        unit = doc.createElement("unit")
        unit.setAttribute("name","meter")
        unit.setAttribute("meter","1")
        asset.appendChild(unit)
        uax = doc.createElement("up_axis")
        zup = doc.createTextNode("Z_UP")
        uax.appendChild(zup)
        asset.appendChild(uax)

#end asset
#just here for future use
        libcam = doc.createElement("library_cameras")
        col.appendChild(libcam)
        liblights = doc.createElement("library_lights")
        col.appendChild(liblights)
#just here for future use
#library images
        libima = doc.createElement("library_images")
        for image in bpy.data.images:
                    imaname = (image.name)
                    fp = (bpy.path.abspath(image.filepath))
                    if image:
                        imaid = doc.createElement("image")
                        imaid.setAttribute("id","%s"%(imaname))
                        imaid.setAttribute("name","%s"%(imaname))
                        infrom = doc.createElement("init_from")
                        fpath = doc.createTextNode("%s"%(fp))
                        infrom.appendChild(fpath)
                        imaid.appendChild(infrom)
                        libima.appendChild(imaid)
        col.appendChild(libima)
#end library images
#library effects
        libeff = doc.createElement("library_effects")
        for mat in bpy.data.materials:
            #is there a material?
            if mat:
                dtex = 0
                stex = 0
                ntex = 0
                dimage=""
                simage=""
                nimage=""
                for mtex in (mat.texture_slots):
                    if mtex and mtex.texture.type == 'IMAGE':
                        image = mtex.texture.image
                        if image:
                            if mtex.use_map_color_diffuse:
                                dtex = 1
                                dimage=image.name
                                dnpsurf=doc.createElement("newparam")
                                dnpsurf.setAttribute("sid","%s-surface"% image.name)
                                dsrf=doc.createElement("surface")
                                dsrf.setAttribute("type","2D")
                                if1=doc.createElement("init_from")
                                if1tn=doc.createTextNode("%s"%(image.name))
                                if1.appendChild(if1tn)
                                dsrf.appendChild(if1)
                                dnpsurf.appendChild(dsrf)
                                dnpsamp=doc.createElement("newparam")
                                dnpsamp.setAttribute("sid","%s-sampler"% image.name)
                                dsamp=doc.createElement("sampler2D")
                                #dsamp.setAttribute("type","2D")
                                if2=doc.createElement("source")
                                if2tn=doc.createTextNode("%s-surface"%(image.name))
                                if2.appendChild(if2tn)
                                dsamp.appendChild(if2)
                                dnpsamp.appendChild(dsamp)
                            if mtex.use_map_color_spec:
                                stex = 1
                                simage=image.name
                                snpsurf=doc.createElement("newparam")
                                snpsurf.setAttribute("sid","%s-surface"% image.name)
                                ssrf=doc.createElement("surface")
                                ssrf.setAttribute("type","2D")
                                sif1=doc.createElement("init_from")
                                sif1tn=doc.createTextNode("%s"%(image.name))
                                sif1.appendChild(sif1tn)
                                ssrf.appendChild(sif1)
                                snpsurf.appendChild(ssrf)
                                snpsamp=doc.createElement("newparam")
                                snpsamp.setAttribute("sid","%s-sampler"% image.name)
                                ssamp=doc.createElement("sampler2D")
                                sif2=doc.createElement("source")
                                sif2tn=doc.createTextNode("%s-surface"%(image.name))
                                sif2.appendChild(sif2tn)
                                ssamp.appendChild(sif2)
                                snpsamp.appendChild(ssamp)
                            if mtex.use_map_normal:
                                ntex = 1
                                nimage=image.name
                                nnpsurf=doc.createElement("newparam")
                                nnpsurf.setAttribute("sid","%s-surface"% image.name)
                                nsrf=doc.createElement("surface")
                                nsrf.setAttribute("type","2D")
                                nif1=doc.createElement("init_from")
                                nif1tn=doc.createTextNode("%s"%(image.name))
                                nif1.appendChild(nif1tn)
                                nsrf.appendChild(nif1)
                                nnpsurf.appendChild(nsrf)
                                nnpsamp=doc.createElement("newparam")
                                nnpsamp.setAttribute("sid","%s-sampler"% image.name)
                                nsamp=doc.createElement("sampler2D")
                                if2=doc.createElement("source")
                                if2tn=doc.createTextNode("%s-surface"%(image.name))
                                if2.appendChild(if2tn)
                                nsamp.appendChild(if2)
                                nnpsamp.appendChild(nsamp)
                effid = doc.createElement("effect")
                effid.setAttribute("id","%s_fx"%(mat.name))
                prof_com = doc.createElement("profile_COMMON")
                if dtex == 1:
                    prof_com.appendChild(dnpsurf)
                    prof_com.appendChild(dnpsamp)
                if stex == 1:
                    prof_com.appendChild(snpsurf)
                    prof_com.appendChild(snpsamp)
                if ntex == 1:
                    prof_com.appendChild(nnpsurf)
                    prof_com.appendChild(nnpsamp)
                tech_com = doc.createElement("technique")
                tech_com.setAttribute("sid","common")
                phong = doc.createElement("phong")
                emis = doc.createElement("emission")
                color = doc.createElement("color")
                color.setAttribute("sid","emission")
                cot = utils.getcol(mat.emit,mat.emit,mat.emit,1.0)
                emit = doc.createTextNode("%s"%(cot))
                color.appendChild(emit)
                emis.appendChild(color)
                amb = doc.createElement("ambient")
                color = doc.createElement("color")
                color.setAttribute("sid","ambient")
                cot = utils.getcol(mat.ambient,mat.ambient,mat.ambient,1.0)
                ambcol = doc.createTextNode("%s"%(cot))
                color.appendChild(ambcol)
                amb.appendChild(color)
                dif = doc.createElement("diffuse")
                if dtex == 1:
                    dtexr = doc.createElement("texture")
                    dtexr.setAttribute("texture","%s-sampler"% dimage)
                    dif.appendChild(dtexr)
                else:
                    color = doc.createElement("color")
                    color.setAttribute("sid","diffuse")
                    cot = utils.getcol(mat.diffuse_color.r,mat.diffuse_color.g,mat.diffuse_color.b,1.0)
                    difcol = doc.createTextNode("%s"%(cot))
                    color.appendChild(difcol)
                    dif.appendChild(color)
                spec = doc.createElement("specular")
                if stex == 1:
                    stexr = doc.createElement("texture")
                    stexr.setAttribute("texture","%s-sampler"% simage)
                    spec.appendChild(stexr)
                else:
                    color = doc.createElement("color")
                    color.setAttribute("sid","specular")
                    cot = utils.getcol(mat.specular_color.r,mat.specular_color.g,mat.specular_color.b,1.0)
                    speccol = doc.createTextNode("%s"%(cot))
                    color.appendChild(speccol)
                    spec.appendChild(color)
                shin = doc.createElement("shininess")
                flo = doc.createElement("float")
                flo.setAttribute("sid","shininess")
                cot = (mat.specular_hardness)
                shinval = doc.createTextNode("%s"%(cot))
                flo.appendChild(shinval)
                shin.appendChild(flo)
                ioref = doc.createElement("index_of_refraction")
                flo = doc.createElement("float")
                flo.setAttribute("sid","index_of_refraction")
                cot = (mat.alpha)
                iorval = doc.createTextNode("%s"%(cot))
                flo.appendChild(iorval)
                ioref.appendChild(flo)
                phong.appendChild(emis)
                phong.appendChild(amb)
                phong.appendChild(dif)
                phong.appendChild(spec)
                phong.appendChild(shin)
                phong.appendChild(ioref)
                if ntex == 1:
                    bump = doc.createElement("normal")
                    ntexr = doc.createElement("texture")
                    ntexr.setAttribute("texture","%s-sampler"% nimage)
                    bump.appendChild(ntexr)
                    phong.appendChild(bump)
                tech_com.appendChild(phong)
                prof_com.appendChild(tech_com)
                extra = doc.createElement("extra")
                techn = doc.createElement("technique")
                techn.setAttribute("profile","GOOGLEEARTH")
                ds = doc.createElement("double_sided")
                dsval = doc.createTextNode("1")
                ds.appendChild(dsval)
                techn.appendChild(ds)
                extra.appendChild(techn)
                prof_com.appendChild(extra)
                effid.appendChild(prof_com)
                extra = doc.createElement("extra")
                techn = doc.createElement("technique")
                techn.setAttribute("profile","MAX3D")
                ds = doc.createElement("double_sided")
                dsval = doc.createTextNode("1")
                ds.appendChild(dsval)
                techn.appendChild(ds)
                extra.appendChild(techn)
                effid.appendChild(extra)
                libeff.appendChild(effid)
        col.appendChild(libeff)
#end library effects
# library materials
        libmat = doc.createElement("library_materials")
        for mat in bpy.data.materials:
                matt = doc.createElement("material")
                matt.setAttribute("id","%s"%(mat.name))
                matt.setAttribute("name","%s"%(mat.name))
                ie = doc.createElement("instance_effect")
                ie.setAttribute("url","#%s_fx"%(mat.name))
                matt.appendChild(ie)
                libmat.appendChild(matt)
        col.appendChild(libmat)
#end library materials
# library geometries
        libgeo = doc.createElement("library_geometries")
        start_time = clock()
        for i in bpy.context.selected_objects:
            if i:
                name=str(i.name)
                if (name[:6] != "_joint"):
                    if (i.type == "MESH"):
                            if i.mode == 'EDIT':
                                bpy.ops.object.mode_set(mode='OBJECT')
                            i.data.update(calc_tessface=1)
                            mesh = i.data
                            me_verts = mesh.vertices[:]
                            uv_layer_count=len(mesh.uv_textures)
                            mname = (i.name)
                            geo = doc.createElement("geometry")
                            geo.setAttribute("id","%s"%(mname))
                            me = doc.createElement("mesh")
                            #positions
                            sourcep = doc.createElement("source")
                            sourcep.setAttribute("id", "%s-positions"%(mname))
                            float_positions=""
                            iv = -1
                            for v in me_verts:
                                if iv == -1:
                                    float_positions+=("%.6f %.6g %.6f " % v.co[:])
                                    iv = 0
                                else:
                                    if iv == 7:
                                        iv = 0
                                    float_positions+=("%.6f %.6g %.6f " % v.co[:])
                                iv += 1
                            cbPrint('vert loc took %.4f sec.' % (clock() - start_time))
                            far = doc.createElement("float_array")
                            far.setAttribute("id","%s-positions-array"%(mname))
                            far.setAttribute("count","%s"%(str(len(mesh.vertices)*3)))
                            mpos = doc.createTextNode("%s"%(float_positions))
                            far.appendChild(mpos)
                            techcom = doc.createElement("technique_common")
                            acc =doc.createElement("accessor")
                            acc.setAttribute("source","#%s-positions-array"%(mname))
                            acc.setAttribute("count","%s"%(str(len(mesh.vertices))))
                            acc.setAttribute("stride","3")
                            parx = doc.createElement("param")
                            parx.setAttribute("name","X")
                            parx.setAttribute("type","float")
                            pary = doc.createElement("param")
                            pary.setAttribute("name","Y")
                            pary.setAttribute("type","float")
                            parz = doc.createElement("param")
                            parz.setAttribute("name","Z")
                            parz.setAttribute("type","float")
                            acc.appendChild(parx)
                            acc.appendChild(pary)
                            acc.appendChild(parz)
                            techcom.appendChild(acc)
                            sourcep.appendChild(far)
                            sourcep.appendChild(techcom)
                            me.appendChild(sourcep)
                            #positions
                            #normals
                            float_normals=""
                            tfloat_normals=""
                            float_normals_count=""
                            float_faces=""
                            float_vnorm=""
                            ob = context.object
                            iin = 0
                            #borrowed from obj exporter modified by angelo j miner
                            def veckey3d(v):
                                #return round(v.x, 6), round(v.y, 6), round(v.z, 6)
                                return round(v.x/32767.0), round(v.y/32767.0), round(v.z/32767.0)
                            def veckey3d2(v):
                                return v.x, v.y, v.z
                            def veckey3d21(v):
                                return round(v.x, 6), round(v.y, 6), round(v.z, 6)
                            def veckey3d3(vn,fn):
                                facenorm=fn
                                return round((facenorm.x*vn.x)/2), round((facenorm.y*vn.y)/2), round((facenorm.z*vn.z)/2)

                            iin = ""
                            start_time = clock()
                            #mesh.sort_faces()
                            #mesh.calc_normals()
                            face_index_pairs = [(face, index) for index, face in enumerate(mesh.tessfaces)]
                            ush = 0
                            has_sharp_edges = 0


                            #for f in mesh.tessfaces:
                            for f, f_index in face_index_pairs:
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
                                            noKey = veckey3d21(f.normal)
                                            float_normals+=('%.6f %.6f %.6f ' % noKey)
                                            iin += "1"
                                        if ush == 2:
                                            v = me_verts[v_idx]
                                            noKey = veckey3d21(v.normal)
                                            float_normals+=('%.6f %.6f %.6f ' % noKey)
                                            iin += "1"
                                        ush = 0



                                else:
                                    # Hard, each vert gets normal from the face.
                                    fnc = ""
                                    fns = 0
                                    fnlx = 0
                                    fnly = 0
                                    fnlz = 0
                                    if self.avg_pface:
                                        if fns == 0:
                                            fnlx = f.normal.x
                                            fnly = f.normal.y
                                            fnlz = f.normal.z
                                            fnc += "1"
                                            cbPrint("face%s"% fnlx)

                                        for fn, f_index in face_index_pairs:
                                            if f.normal.angle(fn.normal) < .052:
                                                if f.normal.angle(fn.normal) > -.052:
                                                    fnlx = fn.normal.x + fnlx
                                                    fnly = fn.normal.x + fnly
                                                    fnlz = fn.normal.x + fnlz
                                                    fnc += "1"
                                                    fns = 1
                                        cbPrint("facen2%s"% ((fnlx/(len(fnc)))))
                                        iin += "1"
                                        float_normals+=('%.6f %.6f %.6f ' % ((fnlx/(len(fnc))),(fnly/(len(fnc))),(fnlz/(len(fnc)))))
                                    else:
                                        #for v_idx in f.vertices:
                                        noKey = veckey3d21(f.normal)
                                        float_normals+=('%.6f %.6f %.6f ' % noKey)
                                        iin += "1"

                            float_normals_count=len(iin)*3
                            cbPrint('normals took %.4f sec.' % (clock() - start_time))
                            float_vertsc=len(iin)
                            cbPrint(str(float_vertsc))
                            iin = 0
                            sourcenor = doc.createElement("source")
                            sourcenor.setAttribute("id","%s-normals"%(mname))
                            farn = doc.createElement("float_array")
                            farn.setAttribute("id","%s-normals-array"%(mname))
                            farn.setAttribute("count","%s"%(float_normals_count))
                            fpos = doc.createTextNode("%s"%(float_normals))
                            farn.appendChild(fpos)
                            tcom=doc.createElement("technique_common")
                            acc=doc.createElement("accessor")
                            acc.setAttribute("source","%s-normals-array"%(mname))
                            acc.setAttribute("count","%s"%(float_vertsc))
                            acc.setAttribute("stride","3")
                            parx = doc.createElement("param")
                            parx.setAttribute("name","X")
                            parx.setAttribute("type","float")
                            pary = doc.createElement("param")
                            pary.setAttribute("name","Y")
                            pary.setAttribute("type","float")
                            parz = doc.createElement("param")
                            parz.setAttribute("name","Z")
                            parz.setAttribute("type","float")
                            acc.appendChild(parx)
                            acc.appendChild(pary)
                            acc.appendChild(parz)
                            tcom.appendChild(acc)
                            sourcenor.appendChild(farn)
                            sourcenor.appendChild(tcom)
                            me.appendChild(sourcenor)
                            #end normals
                            #uv we will make assumptions here because this is for a game export so there should allways be a uv set
                            uvs= doc.createElement("source")
        #thankyou fbx exporter
                            tempc=""
                            uvlay = []
                            #lay = i.data.uv_textures.active
                            #if lay:
                            start_time = clock()
                            uvlay = i.data.tessface_uv_textures
                            if uvlay:
                                cbPrint("Found UV map.")
                            else:
                                if (i.type == "MESH"):
                                    bpy.ops.mesh.uv_texture_add()
                                    cbPrint("Your UV map is missing, adding.")
                            for uvindex, uvlayer in enumerate(uvlay):
                                        mapslot = uvindex
                                        mapname = str(uvlayer.name)
                                        uvid=("%s-%s-%s"%(mname,mapname,mapslot))
                                        i_n = -1
                                        ii = 0  # Count how many UVs we write
                                        test=""
                                        uvc = ""

                                        for uf in uvlayer.data:
                                        # workaround, since uf.uv iteration is wrong atm
                                            for uv in uf.uv:
                                                if i_n == -1:
                                                    test+=('%.6f %.6f ' % uv[:])
                                                    i_n = 0
                                                else:
                                                    if i_n == 7:
                                                        #fw('\n\t\t\t ')
                                                        i_n = 0
                                                    test+=('%.6f %.6f ' % uv[:])
                                                i_n += 1
                                                ii += 1  # One more UV
        #thankyou
                                        uvc1=str((ii)*2)
                                        uvc2=str(ii)
                            uvs.setAttribute("id","%s-%s-%s"%(mname,mapname,mapslot))
                            cbPrint('UVs took %.4f sec.' % (clock() - start_time))
                            fa=doc.createElement("float_array")
                            fa.setAttribute("id","%s-array"%(uvid))
                            fa.setAttribute("count","%s"%(uvc1))
                            uvp=doc.createTextNode("%s"%(test))
                            fa.appendChild(uvp)
                            tc2=doc.createElement("technique_common")
                            acc2=doc.createElement("accessor")
                            acc2.setAttribute("source","#%s-array"%(uvid))
                            acc2.setAttribute("count","%s"%(uvc2))
                            acc2.setAttribute("stride","2")
                            pars=doc.createElement("param")
                            pars.setAttribute("name","S")
                            pars.setAttribute("type","float")
                            part=doc.createElement("param")
                            part.setAttribute("name","T")
                            part.setAttribute("type","float")
                            acc2.appendChild(pars)
                            acc2.appendChild(part)
                            tc2.appendChild(acc2)
                            uvs.appendChild(fa)
                            uvs.appendChild(tc2)
                            me.appendChild(uvs)
                            #enduv
                            #vertcol
                            #from fbx exporter
                            collayers = []
                            vcols= doc.createElement("source")
                            cn = 0
                            #list for vert alpha if found
                            alpha_found = 0
                            alpha_list = []
                            def va(index, color):
                                return index, color

                            if len(i.data.tessface_vertex_colors):
                                collayers = i.data.tessface_vertex_colors
                                for colindex, collayer in enumerate(collayers):
                                    ni = -1
                                    colname=str(collayer.name)
                                    if colname == "alpha":
                                        alpha_found = 1
                                        for fi, cf in enumerate(collayer.data):
                                            cbPrint(str(fi))
                                            if len(mesh.tessfaces[fi].vertices) == 4:
                                                colors = cf.color1[:], cf.color2[:], cf.color3[:], cf.color4[:]
                                            else:
                                                colors = cf.color1[:], cf.color2[:], cf.color3[:]
                                            for colr in colors:
                                                tmp = va(fi, colr[0])
                                            alpha_list.append(tmp)
                                                #if ni == -1:
                                                 #   alpha_list.append(tmp)
                                                  #  ni = 0
                                                #else:
                                                 #   if ni == 7:
                                                  #      ni = 0
                                                   #     alpha_list.append(tmp)

                                        for vca in alpha_list:
                                            cbPrint(str(vca))



                            if len(i.data.tessface_vertex_colors):
                                #vcols= doc.createElement("source")
                                collayers = i.data.tessface_vertex_colors
                                for colindex, collayer in enumerate(collayers):
                                    ni = -1
                                    ii = 0  # Count how many Colors we write
                                    vcol = ""
                                    colname=str(collayer.name)
                                    if colname == "alpha":
                                        cbPrint("Alpha.")
                                    else:
                                        for fi, cf in enumerate(collayer.data):
                                            if len(mesh.tessfaces[fi].vertices) == 4:
                                                colors = cf.color1[:], cf.color2[:], cf.color3[:], cf.color4[:]
                                            else:
                                                colors = cf.color1[:], cf.color2[:], cf.color3[:]
                                            for colr in colors:
                                                if ni == -1:
                                                    if alpha_found == 1:#colname == "alpha":
                                                        tmp = alpha_list[fi]
                                                        vcol += ('%.6f %.6f %.6f ' % colr)
                                                        vcol += ('%.6f ' % tmp[1])
                                                        cbPrint(colr[0])
                                                    else:
                                                        vcol += ('%.6f %.6f %.6f ' % colr)
                                                    ni = 0
                                                else:
                                                    if ni == 7:
                                                        ni = 0
                                                    if alpha_found == 1:#colname == "alpha":
                                                        tmp = alpha_list[fi]
                                                        vcol += ('%.6f %.6f %.6f ' % colr)
                                                        vcol += ('%.6f ' % tmp[1])
                                                        cbPrint(colr[0])
                                                    else:
                                                        vcol += ('%.6f %.6f %.6f ' % colr)
                                                ni += 1
                                                ii += 1  # One more Color
                                                #thankyou fbx
                                        if cn == 1:
                                            vcolc1=str((ii)*4)
                                        else:
                                            vcolc1=str((ii)*3)
                                        #vcolc1=str((ii)*3)
                                        vcolc2=str(ii)
                                vcols.setAttribute("id","%s-colors"%(mname))
                                fa=doc.createElement("float_array")
                                fa.setAttribute("id","%s-colors-array"%(mname))
                                fa.setAttribute("count","%s"%(vcolc1))
                                vcolp=doc.createTextNode("%s"%(vcol))
                                fa.appendChild(vcolp)
                                tc2=doc.createElement("technique_common")
                                acc3=doc.createElement("accessor")
                                acc3.setAttribute("source","#%s-colors-array"%(mname))
                                acc3.setAttribute("count","%s"%(vcolc2))
                                if alpha_found == 1:
                                    acc3.setAttribute("stride","4")
                                else:
                                    acc3.setAttribute("stride","3")
                                parr=doc.createElement("param")
                                parr.setAttribute("name","R")
                                parr.setAttribute("type","float")
                                parg=doc.createElement("param")
                                parg.setAttribute("name","G")
                                parg.setAttribute("type","float")
                                parb=doc.createElement("param")
                                parb.setAttribute("name","B")
                                parb.setAttribute("type","float")
                                para=doc.createElement("param")
                                para.setAttribute("name","A")
                                para.setAttribute("type","float")
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
                            #endvertcol
                            #vertices
                            vertic=doc.createElement("vertices")
                            vertic.setAttribute("id","%s-vertices"%(mname))
                            inputsem1=doc.createElement("input")
                            inputsem1.setAttribute("semantic","POSITION")
                            inputsem1.setAttribute("source","#%s-positions"%(mname))
                            vertic.appendChild(inputsem1)
                            me.appendChild(vertic)
                            #end vertices
                            #polylist
                            mat = mesh.materials[:]
                            me_faces = mesh.tessfaces[:]
                            start_time = clock()
                            if mat:
                                #yes lets go through them 1 at a time
                                for im in enumerate(mat):
                                    polyl=doc.createElement("polylist")#triangles")
                                    polyl.setAttribute("material","%s"%(im[1].name))
                                    verts = ""
                                    face_count = ""
                                    face_counter = 0
                                    ni = 0
                                    vi = 0
                                    totfaces = len(mesh.tessfaces)
                                    texindex = 0
                                    matn = ""
                                    nverts = ""
                                    for f, f_index in face_index_pairs:#for f in me_faces:
                                        fi = f.vertices[:]
                                        if f.material_index == im[0]:
                                            nverts += str(len(f.vertices)) + " "
                                            face_count += str("%s"%(face_counter))
                                            for v in f.vertices:
                                                verts += str(v) + " "
                                                if f.use_smooth:
                                                    #if self.sh_edge:
                                                    if has_sharp_edges == 1:
                                                        verts += str("%s "%(ni))
                                                        ni += 1
                                                    else:
                                                        verts += str(v) + " "
                                                        #verts += str("%s "%(ni))
                                                        #ni += 1
                                                else:
                                                    verts += str("%s "%(ni))
                                                verts += str("%s "%(texindex))
                                                if len(mesh.vertex_colors):
                                                    verts += str("%s "%(texindex))
                                                texindex += 1

                                            matn = im[0]

                                        if f.use_smooth:
                                            if has_sharp_edges == 1:
                                                vi = 2
                                            else:
                                                ni += len(f.vertices)
                                        else:
                                            ni += 1##<--naughty naughty

                                        if f.material_index == im[0]:
                                            texindex = texindex
                                        else:
                                            texindex += len(fi)#4#3

                                    cbPrint(str(ni))
                                    verts += ""
                                    cbPrint('polylist took %.4f sec.' % (clock() - start_time))
                                    polyl.setAttribute("count","%s"%(len(face_count)))
                                    inpv=doc.createElement("input")
                                    inpv.setAttribute("semantic","VERTEX")
                                    inpv.setAttribute("source","#%s-vertices"%(mname))
                                    inpv.setAttribute("offset","0")
                                    polyl.appendChild(inpv)
                                    inpn=doc.createElement("input")
                                    inpn.setAttribute("semantic","NORMAL")
                                    inpn.setAttribute("source","#%s-normals"%(mname))
                                    inpn.setAttribute("offset","1")
                                    polyl.appendChild(inpn)
                                    inpuv=doc.createElement("input")
                                    inpuv.setAttribute("semantic","TEXCOORD")
                                    inpuv.setAttribute("source","#%s"%(uvid))
                                    inpuv.setAttribute("offset","2")#will allways be 2, vcolors can be 2 or 3
                                    inpuv.setAttribute("set","%s"%(mapslot))
                                    polyl.appendChild(inpuv)
                                    if len(mesh.vertex_colors):
                                        inpvcol=doc.createElement("input")
                                        inpvcol.setAttribute("semantic","COLOR")
                                        inpvcol.setAttribute("source","#%s-colors"%(mname))
                                        inpvcol.setAttribute("offset","3")#vcolors can be 2 or 3
                                        polyl.appendChild(inpvcol)
                                    vc=doc.createElement("vcount")
                                    vcl=doc.createTextNode("%s"%(nverts))
                                    vc.appendChild(vcl)
                                    pl=doc.createElement("p")
                                    pltn=doc.createTextNode("%s"%(verts))
                                    pl.appendChild(pltn)
                                    polyl.appendChild(vc)
                                    polyl.appendChild(pl)
                                    me.appendChild(polyl)
                                    #endpolylist
                            has_sharp_edges = 0
                            emt=doc.createElement("extra")
                            emtt=doc.createElement("technique")
                            emtt.setAttribute("profile", "MAYA")
                            dsd=doc.createElement("double_sided")
                            dsdtn=doc.createTextNode("1")
                            dsd.appendChild(dsdtn)
                            emtt.appendChild(dsd)
                            emt.appendChild(emtt)
                            me.appendChild(emt)
                            geo.appendChild(me)
                            libgeo.appendChild(geo)
                            #bpy.data.meshes.remove(mesh)
        col.appendChild(libgeo)
        
        #Duo Oratar
        #Remove the boneGeometry from the selection so we can get on with business as usual
        for i in bpy.context.selected_objects:
            if '_boneGeometry' in i.name:
                bpy.data.objects[i.name].select = False
        
#end library geometries
        def GetBones(Arm):
            return [Bone for Bone in Arm.data.bones]
                    #if Bone.type in {'ARMATURE', 'EMPTY', 'MESH'}]



        #bonelist = []
#library controllers aka skining info
        libcont = doc.createElement("library_controllers")
        start_time = clock()
        for i in bpy.context.selected_objects:
            bonelist = []
            blist=""
            mtx=""
            mtx4_xneg90 = Matrix.Rotation(-math.pi / 2.0, 4, 'X')
            mtx4_x90 = Matrix.Rotation(math.pi / 2.0, 4, 'X')
            mtx4_y90 = Matrix.Rotation(math.pi / 2.0, 4, 'Y')
            mtx4_z90 = Matrix.Rotation(math.pi / 2.0, 4, 'Z')
            mtx4_z180 = Matrix.Rotation((2*math.pi) / 2.0, 4, 'Z')
            mtx4_y180 = Matrix.Rotation((2*math.pi) / 2.0, 4, 'Y')
            smtx = Matrix()
            if i and not "_boneGeometry" in i.name:
                #"some" code borrowed from dx exporter
                ArmatureList = [Modifier for Modifier in i.modifiers if Modifier.type == "ARMATURE"]
                if ArmatureList:
                    bonenum = 0
                    ArmatureObject = ArmatureList[0].object
                    ArmatureBones = GetBones(ArmatureObject)
                    PoseBones = ArmatureObject.pose.bones
                    contr = doc.createElement("controller")
                    contr.setAttribute("id","%s_%s"%(ArmatureList[0].object.name,i.name))
                    libcont.appendChild(contr)
                    sknsrc = doc.createElement("skin")
                    sknsrc.setAttribute("source","#%s"%i.name)
                    contr.appendChild(sknsrc)
                    mtx += ("%s "%smtx[0][0])
                    mtx += ("%s "%smtx[1][0])
                    mtx += ("%s "%smtx[2][0])
                    mtx += ("%s "%smtx[3][0])
                    mtx += ("%s "%smtx[0][1])
                    mtx += ("%s "%smtx[1][1])
                    mtx += ("%s "%smtx[2][1])
                    mtx += ("%s "%smtx[3][1])
                    mtx += ("%s "%smtx[0][2])
                    mtx += ("%s "%smtx[1][2])
                    mtx += ("%s "%smtx[2][2])
                    mtx += ("%s "%smtx[3][2])
                    mtx += ("%s "%smtx[0][3])
                    mtx += ("%s "%smtx[1][3])
                    mtx += ("%s "%smtx[2][3])
                    mtx += ("%s "%smtx[3][3])
                    bsm = doc.createElement("bind_shape_matrix")
                    bsmv = doc.createTextNode("%s"%mtx)
                    bsm.appendChild(bsmv)
                    sknsrc.appendChild(bsm)
                    src = doc.createElement("source")
                    src.setAttribute("id", "%s_%s_joints"%(ArmatureList[0].object.name,i.name))

                    idar = doc.createElement("IDREF_array")
                    idar.setAttribute("id","%s_%s_joints_array"%(ArmatureList[0].object.name,i.name))
                    idar.setAttribute("count","%s"%len(ArmatureBones))
                    #blist += ("%s "%ArmatureList[0].object.name)
                    for Bone in ArmatureBones:
                        blist += ("%s "%Bone.name)
                    cbPrint(blist)
                    jnl = doc.createTextNode("%s"%blist)
                    idar.appendChild(jnl)
                    src.appendChild(idar)
                    tcom = doc.createElement("technique_common")
                    acc = doc.createElement("accessor")
                    acc.setAttribute("source", "#%s_%s_joints_array"%(ArmatureList[0].object.name,i.name))
                    acc.setAttribute("count","%s"%len(ArmatureBones))
                    acc.setAttribute("stride","1")
                    paran = doc.createElement("param")
                    #paran.setAttribute("name", "JOINT")
                    paran.setAttribute("type", "IDREF")
                    acc.appendChild(paran)
                    tcom.appendChild(acc)
                    src.appendChild(tcom)
                    sknsrc.appendChild(src)
                    srcm = doc.createElement("source")
                    srcm.setAttribute("id", "%s_%s_matrices"%(ArmatureList[0].object.name,i.name))
                    flar = doc.createElement("float_array")
                    flar.setAttribute("id", "%s_%s_matrices_array"%(ArmatureList[0].object.name,i.name))
                    flar.setAttribute("count","%s"%(len(ArmatureBones)*16))
                    armRot = ArmatureObject.matrix_world.to_quaternion()

                    def blistbn(bonename, num):
                        return bonename, num
                    for Bone in ArmatureBones:
                        tmp = blistbn(Bone.name, bonenum)
                        bonelist.append(tmp)
                        bonenum += 1
                        lmtx1=""
                        lmtx2=""
                        lmtx3=""
                        lmtx4=""
                        '''
                        sx ry rz lx
                        rx sy rz ly
                        rx ry sz lz
                        0  0  0  1
                        sx, sy, sz == 1 when writen out
                        lx, ly, lz == location
                        before sx, sy, sz == 1,
                        ry == sx * ry * 10
                        rz == sx * rz * 10
                        eg:
                            sx ,(ry == sx * ry * 10),(rz == sx * rz * 10), lx
                        continue through y , z
                        '''
                        PoseBone = PoseBones[Bone.name]
                        for sb in bpy.context.scene.objects:
                            if sb.name == Bone.name:
                                bmatrix = sb.matrix_local

                        #if PoseBone.parent:
                            #for sb in bpy.context.scene.objects:
                                #if sb.name == Bone.parent.name:
                                    #pbmatrix = sb.matrix_local# * mtx4_y180
                            #pbmatrix = PoseBones[Bone.name].bone.parent.matrix_local
                            #rmatrix = pbmatrix.inverted() * bmatrix
                            #rmatrix = rmatrix * mtx4_z90
                            #rmatrix = bmatrix#.inverted()
                        #else:
                            #rmatrix = bmatrix#.inverted()

                        #if not PoseBone.parent:
                            #rmatrix = mtx4_xneg90 * armRot.to_matrix().to_4x4() * bmatrix
                        #else:
                        #rmatrix = ArmatureObject.matrix_world * PoseBone.bone.head_local

                        #cbPrint(bmatrix)
                        #bmatrix = bmatrix * mtx4_xneg90
                        #bmatrix = bmatrix * -1
                        #cbPrint(bmatrix)
                        #bmatrix = bmatrix * mtx4_xneg90
                        #b_loc, b_rot, b_scale = bmatrix.decompose()
                        #b_loc = b_loc * -1
                        #rmatrix = b_rot.to_matrix()
                        #rmatrix = rmatrix.to_4x4()
                        rmatrix = bmatrix
                        cbPrint("rmatrix%s"%rmatrix)
                        #rmatrix = rmatrix * mtx4_xneg90
                        '''
                        if PoseBone.parent:
                            lmtx1 += ("%.6f %.6f %.6f %.6f "%(rmatrix[0][0], rmatrix[0][1], rmatrix[0][2], -rmatrix[0][3]))
                            lmtx2 += ("%.6f %.6f %.6f %.6f "%(rmatrix[1][0], rmatrix[1][1], rmatrix[1][2], -rmatrix[2][3]))
                            lmtx3 += ("%.6f %.6f %.6f %.6f "%(rmatrix[2][0], rmatrix[2][1], rmatrix[2][2], (rmatrix[1][3]*-1)))
                            lmtx4 += ("%.6f %.6f %.6f %.6f "%(rmatrix[3][0], rmatrix[3][1], rmatrix[3][2], rmatrix[3][3]))


                        else:
                            lmtx1 += ("%.6f %.6f %.6f %.6f "%(rmatrix[0][0], rmatrix[0][1], rmatrix[0][2], -rmatrix[0][3]))
                            lmtx2 += ("%.6f %.6f %.6f %.6f "%(rmatrix[1][0], rmatrix[1][1], rmatrix[1][2], (rmatrix[1][3]*-1)))
                            lmtx3 += ("%.6f %.6f %.6f %.6f "%(rmatrix[2][0], rmatrix[2][1], rmatrix[2][2], -rmatrix[2][3]))
                            lmtx4 += ("%.6f %.6f %.6f %.6f "%(rmatrix[3][0], rmatrix[3][1], rmatrix[3][2], rmatrix[3][3]))
                        '''
                        lmtx1 += ("%.6f %.6f %.6f %.6f "%(rmatrix[0][0], rmatrix[0][1], rmatrix[0][2], -rmatrix[0][3]))#b_loc[0]))#rmatrix[0][3]))#
                        lmtx2 += ("%.6f %.6f %.6f %.6f "%(rmatrix[1][0], rmatrix[1][1], rmatrix[1][2], (rmatrix[1][3]*-1)))#b_loc[1]))#rmatrix[1][3]))#
                        lmtx3 += ("%.6f %.6f %.6f %.6f "%(rmatrix[2][0], rmatrix[2][1], rmatrix[2][2], -rmatrix[2][3]))#b_loc[2]))#rmatrix[2][3]))#
                        lmtx4 += ("%.6f %.6f %.6f %.6f "%(rmatrix[3][0], rmatrix[3][1], rmatrix[3][2], rmatrix[3][3]))
                        flarm1 = doc.createTextNode("%s"%lmtx1)
                        flar.appendChild(flarm1)
                        flarm2 = doc.createTextNode("%s"%lmtx2)
                        flar.appendChild(flarm2)
                        flarm3 = doc.createTextNode("%s"%lmtx3)
                        flar.appendChild(flarm3)
                        flarm4 = doc.createTextNode("%s"%lmtx4)
                        flar.appendChild(flarm4)
                    srcm.appendChild(flar)
                    tcommat = doc.createElement("technique_common")
                    accm = doc.createElement("accessor")
                    accm.setAttribute("source", "#%s_%s_matrices_array"%(ArmatureList[0].object.name,i.name))
                    accm.setAttribute("count","%s"%(len(ArmatureBones)))
                    accm.setAttribute("stride","16")
                    paranm = doc.createElement("param")
                    #paran.setAttribute("name", "JOINT")
                    paranm.setAttribute("type", "float4x4")
                    accm.appendChild(paranm)
                    tcommat.appendChild(accm)
                    srcm.appendChild(tcommat)
                    sknsrc.appendChild(srcm)
                    srcw = doc.createElement("source")
                    srcw.setAttribute("id", "%s_%s_weights"%(ArmatureList[0].object.name,i.name))
                    flarw = doc.createElement("float_array")
                    flarw.setAttribute("id", "%s_%s_weights_array"%(ArmatureList[0].object.name,i.name))

                    wa = ""
                    vw = ""
                    me = i.data
                    vcntr = ""
                    vcount = 0
                    #for Bone in ArmatureBones:
                        #for vg in i.vertex_groups:

                    for v in me.vertices:
                        if v.groups:
                            #wa += ("%.6f "%v.groups[0].weight)
                            for g in v.groups:
                                wa += ("%.6f "%g.weight)#("%.6f "%g.weight)
                                for gr in i.vertex_groups:
                                    if gr.index == g.group:
                                        for bn in bonelist:
                                            if bn[0] == gr.name:
                                                vw += ("%s "%bn[1])
                                #vw += ("%s "%g.group)#v.groups.name)#[0])#.group[0])#g.group)#
                                vw += ("%s "%str(vcount))
                                vcount += 1
                                cbPrint("Doing weights.")
                        vcntr += ("%s "%len(v.groups))
                    flarw.setAttribute("count","%s"%vcount)#len(me.vertices))
                    lfarwa = doc.createTextNode("%s"%wa)
                    flarw.appendChild(lfarwa)
                    tcomw = doc.createElement("technique_common")
                    accw = doc.createElement("accessor")
                    accw.setAttribute("source", "#%s_%s_weights_array"%(ArmatureList[0].object.name,i.name))
                    accw.setAttribute("count","%s"%vcount)#len(me.vertices))
                    accw.setAttribute("stride","1")
                    paranw = doc.createElement("param")
                    paranw.setAttribute("type", "float")
                    accw.appendChild(paranw)
                    tcomw.appendChild(accw)
                    srcw.appendChild(flarw)
                    srcw.appendChild(tcomw)
                    sknsrc.appendChild(srcw)
                    #cbPrint(vw)
                    jnts = doc.createElement("joints")
                    is1 = doc.createElement("input")
                    is1.setAttribute("semantic", "JOINT")
                    is1.setAttribute("source", "#%s_%s_joints"%(ArmatureList[0].object.name,i.name))
                    jnts.appendChild(is1)
                    is2 = doc.createElement("input")
                    is2.setAttribute("semantic", "INV_BIND_MATRIX")
                    is2.setAttribute("source", "#%s_%s_matrices"%(ArmatureList[0].object.name,i.name))
                    jnts.appendChild(is2)
                    sknsrc.appendChild(jnts)
                    vertw = doc.createElement("vertex_weights")
                    vertw.setAttribute("count","%s"%len(me.vertices))
                    is3 = doc.createElement("input")
                    is3.setAttribute("semantic", "JOINT")
                    is3.setAttribute("offset", "0")
                    is3.setAttribute("source", "#%s_%s_joints"%(ArmatureList[0].object.name,i.name))
                    vertw.appendChild(is3)
                    is4 = doc.createElement("input")
                    is4.setAttribute("semantic", "WEIGHT")
                    is4.setAttribute("offset", "1")
                    is4.setAttribute("source", "#%s_%s_weights"%(ArmatureList[0].object.name,i.name))
                    vertw.appendChild(is4)
                    vcnt = doc.createElement("vcount")
                    vcnt1 = doc.createTextNode("%s"%vcntr)
                    vcnt.appendChild(vcnt1)
                    vertw.appendChild(vcnt)
                    vlst = doc.createElement("v")
                    vlst1 = doc.createTextNode("%s"%vw)
                    vlst.appendChild(vlst1)
                    vertw.appendChild(vlst)
                    sknsrc.appendChild(vertw)










        col.appendChild(libcont)
#end library controllers aka skining info
#library_animations

        #fps_b = bpy.context.scene.render.fps_base
        #fps = bpy.context.scene.render.fps
        fps_b = bpy.context.scene.render.fps_base
        fps = bpy.context.scene.render.fps
        def convert_time(frx):
            s = ((fps_b * frx) / fps)
            return s

        def extract_anilx(self, i):
            act = i.animation_data.action
            curves = act.fcurves
            fcus = {}
            for fcu in curves:
                #location
                #X
                if fcu.data_path == 'location'and fcu.array_index == 0:
                    anmlx = doc.createElement("animation")
                    anmlx.setAttribute("id","%s_location_X"%(i.name))
                    fcus[fcu.array_index] = fcu
                    intangx = ""
                    outtangx = ""
                    inpx = ""
                    outpx = ""
                    intx = ""
                    temp = fcus[0].keyframe_points
                    ii = 0
                    pvalue = 0
                    for keyx in temp:
                        khlx = keyx.handle_left[0]
                        khly = keyx.handle_left[1]
                        khrx = keyx.handle_right[0]
                        khry = keyx.handle_right[1]
                        frame, value = keyx.co
                        time = convert_time(frame)
                        intx += ("%s "%(keyx.interpolation))
                        inpx += ("%.6f "%(time))
                        outpx += ("%.6f "%(value))

                        intangfirst = convert_time(khlx)
                        outangfirst = convert_time(khrx)
                        intangx += ("%.6f %.6f "%(intangfirst,khly))
                        outtangx += ("%.6f %.6f "%(outangfirst,khry))
                        ii += 1
                    #input
                    sinpx = doc.createElement("source")
                    sinpx.setAttribute("id","%s_location_X-input"%(i.name))
                    inpxfa = doc.createElement("float_array")
                    inpxfa.setAttribute("id","%s_location_X-input-array"%(i.name))
                    inpxfa.setAttribute("count","%s"%(ii))
                    sinpxdat = doc.createTextNode("%s"%(inpx))
                    inpxfa.appendChild(sinpxdat)
                    tcinpx = doc.createElement("technique_common")
                    accinpx = doc.createElement("accessor")
                    accinpx.setAttribute("source","#%s_location_X-input-array"%(i.name))
                    accinpx.setAttribute("count","%s"%(ii))
                    accinpx.setAttribute("stride","1")
                    parinpx = doc.createElement("param")
                    parinpx.setAttribute("name","TIME")
                    parinpx.setAttribute("type","float")
                    accinpx.appendChild(parinpx)
                    tcinpx.appendChild(accinpx)
                    sinpx.appendChild(inpxfa)
                    sinpx.appendChild(tcinpx)
                    #output
                    soutpx = doc.createElement("source")
                    soutpx.setAttribute("id","%s_location_X-output"%(i.name))
                    outpxfa = doc.createElement("float_array")
                    outpxfa.setAttribute("id","%s_location_X-output-array"%(i.name))
                    outpxfa.setAttribute("count","%s"%(ii))
                    soutpxdat = doc.createTextNode("%s"%(outpx))
                    outpxfa.appendChild(soutpxdat)
                    tcoutpx = doc.createElement("technique_common")
                    accoutpx = doc.createElement("accessor")
                    accoutpx.setAttribute("source","#%s_location_X-output-array"%(i.name))
                    accoutpx.setAttribute("count","%s"%(ii))
                    accoutpx.setAttribute("stride","1")
                    paroutpx = doc.createElement("param")
                    paroutpx.setAttribute("name","VALUE")
                    paroutpx.setAttribute("type","float")
                    accoutpx.appendChild(paroutpx)
                    tcoutpx.appendChild(accoutpx)
                    soutpx.appendChild(outpxfa)
                    soutpx.appendChild(tcoutpx)
                    #interpolation
                    sintpx = doc.createElement("source")
                    sintpx.setAttribute("id","%s_location_X-interpolation"%(i.name))
                    intpxfa = doc.createElement("Name_array")
                    intpxfa.setAttribute("id","%s_location_X-interpolation-array"%(i.name))
                    intpxfa.setAttribute("count","%s"%(ii))
                    sintpxdat = doc.createTextNode("%s"%(intx))
                    intpxfa.appendChild(sintpxdat)
                    tcintpx = doc.createElement("technique_common")
                    accintpx = doc.createElement("accessor")
                    accintpx.setAttribute("source","#%s_location_X-interpolation-array"%(i.name))
                    accintpx.setAttribute("count","%s"%(ii))
                    accintpx.setAttribute("stride","1")
                    parintpx = doc.createElement("param")
                    parintpx.setAttribute("name","INTERPOLATION")
                    parintpx.setAttribute("type","name")
                    accintpx.appendChild(parintpx)
                    tcintpx.appendChild(accintpx)
                    sintpx.appendChild(intpxfa)
                    sintpx.appendChild(tcintpx)
                    #intangent
                    sintangpx = doc.createElement("source")
                    sintangpx.setAttribute("id","%s_location_X-intangent"%(i.name))
                    intangpxfa = doc.createElement("float_array")
                    intangpxfa.setAttribute("id","%s_location_X-intangent-array"%(i.name))
                    intangpxfa.setAttribute("count","%s"%((ii)*2))
                    sintangpxdat = doc.createTextNode("%s"%(intangx))
                    intangpxfa.appendChild(sintangpxdat)
                    tcintangpx = doc.createElement("technique_common")
                    accintangpx = doc.createElement("accessor")
                    accintangpx.setAttribute("source","#%s_location_X-intangent-array"%(i.name))
                    accintangpx.setAttribute("count","%s"%(ii))
                    accintangpx.setAttribute("stride","2")
                    parintangpx = doc.createElement("param")
                    parintangpx.setAttribute("name","X")
                    parintangpx.setAttribute("type","float")
                    parintangpxy = doc.createElement("param")
                    parintangpxy.setAttribute("name","Y")
                    parintangpxy.setAttribute("type","float")
                    accintangpx.appendChild(parintangpx)
                    accintangpx.appendChild(parintangpxy)
                    tcintangpx.appendChild(accintangpx)
                    sintangpx.appendChild(intangpxfa)
                    sintangpx.appendChild(tcintangpx)
                    #outtangent
                    soutangpx = doc.createElement("source")
                    soutangpx.setAttribute("id","%s_location_X-outtangent"%(i.name))
                    outangpxfa = doc.createElement("float_array")
                    outangpxfa.setAttribute("id","%s_location_X-outtangent-array"%(i.name))
                    outangpxfa.setAttribute("count","%s"%((ii)*2))
                    soutangpxdat = doc.createTextNode("%s"%(outtangx))
                    outangpxfa.appendChild(soutangpxdat)
                    tcoutangpx = doc.createElement("technique_common")
                    accoutangpx = doc.createElement("accessor")
                    accoutangpx.setAttribute("source","#%s_location_X-outtangent-array"%(i.name))
                    accoutangpx.setAttribute("count","%s"%(ii))
                    accoutangpx.setAttribute("stride","2")
                    paroutangpx = doc.createElement("param")
                    paroutangpx.setAttribute("name","X")
                    paroutangpx.setAttribute("type","float")
                    paroutangpxy = doc.createElement("param")
                    paroutangpxy.setAttribute("name","Y")
                    paroutangpxy.setAttribute("type","float")
                    accoutangpx.appendChild(paroutangpx)
                    accoutangpx.appendChild(paroutangpxy)
                    tcoutangpx.appendChild(accoutangpx)
                    soutangpx.appendChild(outangpxfa)
                    soutangpx.appendChild(tcoutangpx)
                    #sampler
                    samx = doc.createElement("sampler")
                    samx.setAttribute("id","%s_location_X-sampler"%(i.name))
                    semip = doc.createElement("input")
                    semip.setAttribute("semantic","INPUT")
                    semip.setAttribute("source","#%s_location_X-input"%(i.name))
                    semop = doc.createElement("input")
                    semop.setAttribute("semantic","OUTPUT")
                    semop.setAttribute("source","#%s_location_X-output"%(i.name))
                    seminter = doc.createElement("input")
                    seminter.setAttribute("semantic","INTERPOLATION")
                    seminter.setAttribute("source","#%s_location_X-interpolation"%(i.name))
                    semintang = doc.createElement("input")
                    semintang.setAttribute("semantic","IN_TANGENT")
                    semintang.setAttribute("source","#%s_location_X-intangent"%(i.name))
                    semoutang = doc.createElement("input")
                    semoutang.setAttribute("semantic","OUT_TANGENT")
                    semoutang.setAttribute("source","#%s_location_X-outtangent"%(i.name))
                    samx.appendChild(semip)
                    samx.appendChild(semop)
                    samx.appendChild(seminter)
                    #samx.appendChild(semintang)
                    #samx.appendChild(semoutang)
                    chanx = doc.createElement("channel")
                    chanx.setAttribute("source","#%s_location_X-sampler"%(i.name))
                    chanx.setAttribute("target","%s/translation.X"%(i.name))
                    anmlx.appendChild(sinpx)
                    anmlx.appendChild(soutpx)
                    anmlx.appendChild(sintpx)
                    anmlx.appendChild(sintangpx)
                    anmlx.appendChild(soutangpx)
                    anmlx.appendChild(samx)
                    anmlx.appendChild(chanx)
                    #libanm.appendChild(anmlx)
                    cbPrint(ii)
                    cbPrint(inpx)
                    cbPrint(outpx)
                    cbPrint(intx)
                    cbPrint(intangx)
                    cbPrint(outtangx)
                    cbPrint("donex")
            return anmlx
        def extract_anily(self, i):
            act = i.animation_data.action
            curves = act.fcurves
            fcus = {}
            for fcu in curves:
                    #Y
                if fcu.data_path == 'location'and fcu.array_index == 1:
                    anmly = doc.createElement("animation")
                    anmly.setAttribute("id","%s_location_Y"%(i.name))
                    fcus[fcu.array_index] = fcu
                    intangy = ""
                    outtangy = ""
                    inpy = ""
                    outpy = ""
                    inty = ""
                    tempy = fcus[1].keyframe_points
                    ii = 0
                    for key in tempy:
                        khlx = key.handle_left[0]
                        khly = key.handle_left[1]
                        khrx = key.handle_right[0]
                        khry = key.handle_right[1]
                        frame, value = key.co
                        time = convert_time(frame)
                        inty += ("%s "%(key.interpolation))
                        inpy += ("%.6f "%(time))
                        outpy += ("%.6f "%(value))
                        intangfirst = convert_time(khlx)
                        outangfirst = convert_time(khrx)
                        intangy += ("%.6f %.6f "%(intangfirst,khly))
                        outtangy += ("%.6f %.6f "%(outangfirst,khry))
                        ii += 1
                    #input
                    sinpy = doc.createElement("source")
                    sinpy.setAttribute("id","%s_location_Y-input"%(i.name))
                    inpyfa = doc.createElement("float_array")
                    inpyfa.setAttribute("id","%s_location_Y-input-array"%(i.name))
                    inpyfa.setAttribute("count","%s"%(ii))
                    sinpydat = doc.createTextNode("%s"%(inpy))
                    inpyfa.appendChild(sinpydat)
                    tcinpy = doc.createElement("technique_common")
                    accinpy = doc.createElement("accessor")
                    accinpy.setAttribute("source","#%s_location_Y-input-array"%(i.name))
                    accinpy.setAttribute("count","%s"%(ii))
                    accinpy.setAttribute("stride","1")
                    parinpy = doc.createElement("param")
                    parinpy.setAttribute("name","TIME")
                    parinpy.setAttribute("type","float")
                    accinpy.appendChild(parinpy)
                    tcinpy.appendChild(accinpy)
                    sinpy.appendChild(inpyfa)
                    sinpy.appendChild(tcinpy)
                    #output
                    soutpy = doc.createElement("source")
                    soutpy.setAttribute("id","%s_location_Y-output"%(i.name))
                    outpyfa = doc.createElement("float_array")
                    outpyfa.setAttribute("id","%s_location_Y-output-array"%(i.name))
                    outpyfa.setAttribute("count","%s"%(ii))
                    soutpydat = doc.createTextNode("%s"%(outpy))
                    outpyfa.appendChild(soutpydat)
                    tcoutpy = doc.createElement("technique_common")
                    accoutpy = doc.createElement("accessor")
                    accoutpy.setAttribute("source","#%s_location_Y-output-array"%(i.name))
                    accoutpy.setAttribute("count","%s"%(ii))
                    accoutpy.setAttribute("stride","1")
                    paroutpy = doc.createElement("param")
                    paroutpy.setAttribute("name","VALUE")
                    paroutpy.setAttribute("type","float")
                    accoutpy.appendChild(paroutpy)
                    tcoutpy.appendChild(accoutpy)
                    soutpy.appendChild(outpyfa)
                    soutpy.appendChild(tcoutpy)
                    #interpolation
                    sintpy = doc.createElement("source")
                    sintpy.setAttribute("id","%s_location_Y-interpolation"%(i.name))
                    intpyfa = doc.createElement("Name_array")
                    intpyfa.setAttribute("id","%s_location_Y-interpolation-array"%(i.name))
                    intpyfa.setAttribute("count","%s"%(ii))
                    sintpydat = doc.createTextNode("%s"%(inty))
                    intpyfa.appendChild(sintpydat)
                    tcintpy = doc.createElement("technique_common")
                    accintpy = doc.createElement("accessor")
                    accintpy.setAttribute("source","#%s_location_Y-interpolation-array"%(i.name))
                    accintpy.setAttribute("count","%s"%(ii))
                    accintpy.setAttribute("stride","1")
                    parintpy = doc.createElement("param")
                    parintpy.setAttribute("name","INTERPOLATION")
                    parintpy.setAttribute("type","name")
                    accintpy.appendChild(parintpy)
                    tcintpy.appendChild(accintpy)
                    sintpy.appendChild(intpyfa)
                    sintpy.appendChild(tcintpy)
                    #intangent
                    sintangpy = doc.createElement("source")
                    sintangpy.setAttribute("id","%s_location_Y-intangent"%(i.name))
                    intangpyfa = doc.createElement("float_array")
                    intangpyfa.setAttribute("id","%s_location_Y-intangent-array"%(i.name))
                    intangpyfa.setAttribute("count","%s"%((ii)*2))
                    sintangpydat = doc.createTextNode("%s"%(intangy))
                    intangpyfa.appendChild(sintangpydat)
                    tcintangpy = doc.createElement("technique_common")
                    accintangpy = doc.createElement("accessor")
                    accintangpy.setAttribute("source","#%s_location_Y-intangent-array"%(i.name))
                    accintangpy.setAttribute("count","%s"%(ii))
                    accintangpy.setAttribute("stride","2")
                    parintangpy = doc.createElement("param")
                    parintangpy.setAttribute("name","X")
                    parintangpy.setAttribute("type","float")
                    parintangpyy = doc.createElement("param")
                    parintangpyy.setAttribute("name","Y")
                    parintangpyy.setAttribute("type","float")
                    accintangpy.appendChild(parintangpy)
                    accintangpy.appendChild(parintangpyy)
                    tcintangpy.appendChild(accintangpy)
                    sintangpy.appendChild(intangpyfa)
                    sintangpy.appendChild(tcintangpy)
                    #outtangent
                    soutangpy = doc.createElement("source")
                    soutangpy.setAttribute("id","%s_location_Y-outtangent"%(i.name))
                    outangpyfa = doc.createElement("float_array")
                    outangpyfa.setAttribute("id","%s_location_Y-outtangent-array"%(i.name))
                    outangpyfa.setAttribute("count","%s"%((ii)*2))
                    soutangpydat = doc.createTextNode("%s"%(outtangy))
                    outangpyfa.appendChild(soutangpydat)
                    tcoutangpy = doc.createElement("technique_common")
                    accoutangpy = doc.createElement("accessor")
                    accoutangpy.setAttribute("source","#%s_location_Y-outtangent-array"%(i.name))
                    accoutangpy.setAttribute("count","%s"%(ii))
                    accoutangpy.setAttribute("stride","2")
                    paroutangpy = doc.createElement("param")
                    paroutangpy.setAttribute("name","X")
                    paroutangpy.setAttribute("type","float")
                    paroutangpyy = doc.createElement("param")
                    paroutangpyy.setAttribute("name","Y")
                    paroutangpyy.setAttribute("type","float")
                    accoutangpy.appendChild(paroutangpy)
                    accoutangpy.appendChild(paroutangpyy)
                    tcoutangpy.appendChild(accoutangpy)
                    soutangpy.appendChild(outangpyfa)
                    soutangpy.appendChild(tcoutangpy)
                    #sampler
                    samy = doc.createElement("sampler")
                    samy.setAttribute("id","%s_location_Y-sampler"%(i.name))
                    semip = doc.createElement("input")
                    semip.setAttribute("semantic","INPUT")
                    semip.setAttribute("source","#%s_location_Y-input"%(i.name))
                    semop = doc.createElement("input")
                    semop.setAttribute("semantic","OUTPUT")
                    semop.setAttribute("source","#%s_location_Y-output"%(i.name))
                    seminter = doc.createElement("input")
                    seminter.setAttribute("semantic","INTERPOLATION")
                    seminter.setAttribute("source","#%s_location_Y-interpolation"%(i.name))
                    semintang = doc.createElement("input")
                    semintang.setAttribute("semantic","IN_TANGENT")
                    semintang.setAttribute("source","#%s_location_Y-intangent"%(i.name))
                    semoutang = doc.createElement("input")
                    semoutang.setAttribute("semantic","OUT_TANGENT")
                    semoutang.setAttribute("source","#%s_location_Y-outtangent"%(i.name))
                    samy.appendChild(semip)
                    samy.appendChild(semop)
                    samy.appendChild(seminter)
                    #samy.appendChild(semintang)
                    #samy.appendChild(semoutang)
                    chany = doc.createElement("channel")
                    chany.setAttribute("source","#%s_location_Y-sampler"%(i.name))
                    chany.setAttribute("target","%s/translation.Y"%(i.name))
                    anmly.appendChild(sinpy)
                    anmly.appendChild(soutpy)
                    anmly.appendChild(sintpy)
                    anmly.appendChild(sintangpy)
                    anmly.appendChild(soutangpy)
                    anmly.appendChild(samy)
                    anmly.appendChild(chany)
                    #libanm.appendChild(anmly)
                    cbPrint(ii)
                    cbPrint(inpy)
                    cbPrint(outpy)
                    cbPrint(inty)
                    cbPrint(intangy)
                    cbPrint(outtangy)
                    cbPrint("doney")
            return anmly
        def extract_anilz(self, i):
            act = i.animation_data.action
            curves = act.fcurves
            fcus = {}
            for fcu in curves:
                  #Z
                if fcu.data_path == 'location'and fcu.array_index == 2:
                    anmlz = doc.createElement("animation")
                    anmlz.setAttribute("id","%s_location_Z"%(i.name))
                    fcus[fcu.array_index] = fcu
                    intangz = ""
                    outtangz = ""
                    inpz = ""
                    outpz = ""
                    intz = ""
                    tempz = fcus[2].keyframe_points
                    ii = 0
                    for key in tempz:
                        khlx = key.handle_left[0]
                        khly = key.handle_left[1]
                        khrx = key.handle_right[0]
                        khry = key.handle_right[1]
                        frame, value = key.co
                        time = convert_time(frame)
                        intz += ("%s "%(key.interpolation))
                        inpz += ("%.6f "%(time))
                        outpz += ("%.6f "%(value))
                        intangfirst = convert_time(khlx)
                        outangfirst = convert_time(khrx)
                        intangz += ("%.6f %.6f "%(intangfirst,khly))
                        outtangz += ("%.6f %.6f "%(outangfirst,khry))
                        ii += 1
                    #input
                    sinpz = doc.createElement("source")
                    sinpz.setAttribute("id","%s_location_Z-input"%(i.name))
                    inpzfa = doc.createElement("float_array")
                    inpzfa.setAttribute("id","%s_location_Z-input-array"%(i.name))
                    inpzfa.setAttribute("count","%s"%(ii))
                    sinpzdat = doc.createTextNode("%s"%(inpz))
                    inpzfa.appendChild(sinpzdat)
                    tcinpz = doc.createElement("technique_common")
                    accinpz = doc.createElement("accessor")
                    accinpz.setAttribute("source","#%s_location_Z-input-array"%(i.name))
                    accinpz.setAttribute("count","%s"%(ii))
                    accinpz.setAttribute("stride","1")
                    parinpz = doc.createElement("param")
                    parinpz.setAttribute("name","TIME")
                    parinpz.setAttribute("type","float")
                    accinpz.appendChild(parinpz)
                    tcinpz.appendChild(accinpz)
                    sinpz.appendChild(inpzfa)
                    sinpz.appendChild(tcinpz)
                    #output
                    soutpz = doc.createElement("source")
                    soutpz.setAttribute("id","%s_location_Z-output"%(i.name))
                    outpzfa = doc.createElement("float_array")
                    outpzfa.setAttribute("id","%s_location_Z-output-array"%(i.name))
                    outpzfa.setAttribute("count","%s"%(ii))
                    soutpzdat = doc.createTextNode("%s"%(outpz))
                    outpzfa.appendChild(soutpzdat)
                    tcoutpz = doc.createElement("technique_common")
                    accoutpz = doc.createElement("accessor")
                    accoutpz.setAttribute("source","#%s_location_Z-output-array"%(i.name))
                    accoutpz.setAttribute("count","%s"%(ii))
                    accoutpz.setAttribute("stride","1")
                    paroutpz = doc.createElement("param")
                    paroutpz.setAttribute("name","VALUE")
                    paroutpz.setAttribute("type","float")
                    accoutpz.appendChild(paroutpz)
                    tcoutpz.appendChild(accoutpz)
                    soutpz.appendChild(outpzfa)
                    soutpz.appendChild(tcoutpz)
                    #interpolation
                    sintpz = doc.createElement("source")
                    sintpz.setAttribute("id","%s_location_Z-interpolation"%(i.name))
                    intpzfa = doc.createElement("Name_array")
                    intpzfa.setAttribute("id","%s_location_Z-interpolation-array"%(i.name))
                    intpzfa.setAttribute("count","%s"%(ii))
                    sintpzdat = doc.createTextNode("%s"%(intz))
                    intpzfa.appendChild(sintpzdat)
                    tcintpz = doc.createElement("technique_common")
                    accintpz = doc.createElement("accessor")
                    accintpz.setAttribute("source","#%s_location_Z-interpolation-array"%(i.name))
                    accintpz.setAttribute("count","%s"%(ii))
                    accintpz.setAttribute("stride","1")
                    parintpz = doc.createElement("param")
                    parintpz.setAttribute("name","INTERPOLATION")
                    parintpz.setAttribute("type","name")
                    accintpz.appendChild(parintpz)
                    tcintpz.appendChild(accintpz)
                    sintpz.appendChild(intpzfa)
                    sintpz.appendChild(tcintpz)
                    #intangent
                    sintangpz = doc.createElement("source")
                    sintangpz.setAttribute("id","%s_location_Z-intangent"%(i.name))
                    intangpzfa = doc.createElement("float_array")
                    intangpzfa.setAttribute("id","%s_location_Z-intangent-array"%(i.name))
                    intangpzfa.setAttribute("count","%s"%((ii)*2))
                    sintangpzdat = doc.createTextNode("%s"%(intangz))
                    intangpzfa.appendChild(sintangpzdat)
                    tcintangpz = doc.createElement("technique_common")
                    accintangpz = doc.createElement("accessor")
                    accintangpz.setAttribute("source","#%s_location_Z-intangent-array"%(i.name))
                    accintangpz.setAttribute("count","%s"%(ii))
                    accintangpz.setAttribute("stride","2")
                    parintangpz = doc.createElement("param")
                    parintangpz.setAttribute("name","X")
                    parintangpz.setAttribute("type","float")
                    parintangpyz = doc.createElement("param")
                    parintangpyz.setAttribute("name","Y")
                    parintangpyz.setAttribute("type","float")
                    accintangpz.appendChild(parintangpz)
                    accintangpz.appendChild(parintangpyz)
                    tcintangpz.appendChild(accintangpz)
                    sintangpz.appendChild(intangpzfa)
                    sintangpz.appendChild(tcintangpz)
                    #outtangent
                    soutangpz = doc.createElement("source")
                    soutangpz.setAttribute("id","%s_location_Z-outtangent"%(i.name))
                    outangpzfa = doc.createElement("float_array")
                    outangpzfa.setAttribute("id","%s_location_Z-outtangent-array"%(i.name))
                    outangpzfa.setAttribute("count","%s"%((ii)*2))
                    soutangpzdat = doc.createTextNode("%s"%(outtangz))
                    outangpzfa.appendChild(soutangpzdat)
                    tcoutangpz = doc.createElement("technique_common")
                    accoutangpz = doc.createElement("accessor")
                    accoutangpz.setAttribute("source","#%s_location_Z-outtangent-array"%(i.name))
                    accoutangpz.setAttribute("count","%s"%(ii))
                    accoutangpz.setAttribute("stride","2")
                    paroutangpz = doc.createElement("param")
                    paroutangpz.setAttribute("name","X")
                    paroutangpz.setAttribute("type","float")
                    paroutangpyz = doc.createElement("param")
                    paroutangpyz.setAttribute("name","Y")
                    paroutangpyz.setAttribute("type","float")
                    accoutangpz.appendChild(paroutangpz)
                    accoutangpz.appendChild(paroutangpyz)
                    tcoutangpz.appendChild(accoutangpz)
                    soutangpz.appendChild(outangpzfa)
                    soutangpz.appendChild(tcoutangpz)
                    #sampler
                    samz = doc.createElement("sampler")
                    samz.setAttribute("id","%s_location_Z-sampler"%(i.name))
                    semip = doc.createElement("input")
                    semip.setAttribute("semantic","INPUT")
                    semip.setAttribute("source","#%s_location_Z-input"%(i.name))
                    semop = doc.createElement("input")
                    semop.setAttribute("semantic","OUTPUT")
                    semop.setAttribute("source","#%s_location_Z-output"%(i.name))
                    seminter = doc.createElement("input")
                    seminter.setAttribute("semantic","INTERPOLATION")
                    seminter.setAttribute("source","#%s_location_Z-interpolation"%(i.name))
                    semintang = doc.createElement("input")
                    semintang.setAttribute("semantic","IN_TANGENT")
                    semintang.setAttribute("source","#%s_location_Z-intangent"%(i.name))
                    semoutang = doc.createElement("input")
                    semoutang.setAttribute("semantic","OUT_TANGENT")
                    semoutang.setAttribute("source","#%s_location_Z-outtangent"%(i.name))
                    samz.appendChild(semip)
                    samz.appendChild(semop)
                    samz.appendChild(seminter)
                    #samz.appendChild(semintang)
                    #samz.appendChild(semoutang)
                    chanz = doc.createElement("channel")
                    chanz.setAttribute("source","#%s_location_Z-sampler"%(i.name))
                    chanz.setAttribute("target","%s/translation.Z"%(i.name))
                    anmlz.appendChild(sinpz)
                    anmlz.appendChild(soutpz)
                    anmlz.appendChild(sintpz)
                    anmlz.appendChild(sintangpz)
                    anmlz.appendChild(soutangpz)
                    anmlz.appendChild(samz)
                    anmlz.appendChild(chanz)
                    #libanm.appendChild(anmlz)
                    cbPrint(ii)
                    cbPrint(inpz)
                    cbPrint(outpz)
                    cbPrint(intz)
                    cbPrint(intangz)
                    cbPrint(outtangz)
                    cbPrint("donez")
            return anmlz
        def extract_anirx(self, i):
            act = i.animation_data.action
            curves = act.fcurves
            fcus = {}
            for fcu in curves:
        #rotation_euler
                #X
                if fcu.data_path == 'rotation_euler'and fcu.array_index == 0:
                    anmrx = doc.createElement("animation")
                    anmrx.setAttribute("id","%s_rotation_euler_X"%(i.name))
                    fcus[fcu.array_index] = fcu
                    intangx = ""
                    outtangx = ""
                    inpx = ""
                    outpx = ""
                    intx = ""
                    temp = fcus[0].keyframe_points
                    ii = 0
                    for keyx in temp:
                        khlx = keyx.handle_left[0]
                        khly = keyx.handle_left[1]
                        khrx = keyx.handle_right[0]
                        khry = keyx.handle_right[1]
                        frame, value = keyx.co
                        time = convert_time(frame)
                        intx += ("%s "%(keyx.interpolation))
                        inpx += ("%.6f "%(time))
                        outpx += ("%.6f "%(value * utils.toD))
                        intangfirst = convert_time(khlx)
                        outangfirst = convert_time(khrx)
                        intangx += ("%.6f %.6f "%(intangfirst,khly))
                        outtangx += ("%.6f %.6f "%(outangfirst,khry))
                        ii += 1
                    #input
                    sinpx = doc.createElement("source")
                    sinpx.setAttribute("id","%s_rotation_euler_X-input"%(i.name))
                    inpxfa = doc.createElement("float_array")
                    inpxfa.setAttribute("id","%s_rotation_euler_X-input-array"%(i.name))
                    inpxfa.setAttribute("count","%s"%(ii))
                    sinpxdat = doc.createTextNode("%s"%(inpx))
                    inpxfa.appendChild(sinpxdat)
                    tcinpx = doc.createElement("technique_common")
                    accinpx = doc.createElement("accessor")
                    accinpx.setAttribute("source","#%s_rotation_euler_X-input-array"%(i.name))
                    accinpx.setAttribute("count","%s"%(ii))
                    accinpx.setAttribute("stride","1")
                    parinpx = doc.createElement("param")
                    parinpx.setAttribute("name","TIME")
                    parinpx.setAttribute("type","float")
                    accinpx.appendChild(parinpx)
                    tcinpx.appendChild(accinpx)
                    sinpx.appendChild(inpxfa)
                    sinpx.appendChild(tcinpx)
                    #output
                    soutpx = doc.createElement("source")
                    soutpx.setAttribute("id","%s_rotation_euler_X-output"%(i.name))
                    outpxfa = doc.createElement("float_array")
                    outpxfa.setAttribute("id","%s_rotation_euler_X-output-array"%(i.name))
                    outpxfa.setAttribute("count","%s"%(ii))
                    soutpxdat = doc.createTextNode("%s"%(outpx))
                    outpxfa.appendChild(soutpxdat)
                    tcoutpx = doc.createElement("technique_common")
                    accoutpx = doc.createElement("accessor")
                    accoutpx.setAttribute("source","#%s_rotation_euler_X-output-array"%(i.name))
                    accoutpx.setAttribute("count","%s"%(ii))
                    accoutpx.setAttribute("stride","1")
                    paroutpx = doc.createElement("param")
                    paroutpx.setAttribute("name","VALUE")
                    paroutpx.setAttribute("type","float")
                    accoutpx.appendChild(paroutpx)
                    tcoutpx.appendChild(accoutpx)
                    soutpx.appendChild(outpxfa)
                    soutpx.appendChild(tcoutpx)
                    #interpolation
                    sintpx = doc.createElement("source")
                    sintpx.setAttribute("id","%s_rotation_euler_X-interpolation"%(i.name))
                    intpxfa = doc.createElement("Name_array")
                    intpxfa.setAttribute("id","%s_rotation_euler_X-interpolation-array"%(i.name))
                    intpxfa.setAttribute("count","%s"%(ii))
                    sintpxdat = doc.createTextNode("%s"%(intx))
                    intpxfa.appendChild(sintpxdat)
                    tcintpx = doc.createElement("technique_common")
                    accintpx = doc.createElement("accessor")
                    accintpx.setAttribute("source","#%s_rotation_euler_X-interpolation-array"%(i.name))
                    accintpx.setAttribute("count","%s"%(ii))
                    accintpx.setAttribute("stride","1")
                    parintpx = doc.createElement("param")
                    parintpx.setAttribute("name","INTERPOLATION")
                    parintpx.setAttribute("type","name")
                    accintpx.appendChild(parintpx)
                    tcintpx.appendChild(accintpx)
                    sintpx.appendChild(intpxfa)
                    sintpx.appendChild(tcintpx)
                    #intangent
                    sintangpx = doc.createElement("source")
                    sintangpx.setAttribute("id","%s_rotation_euler_X-intangent"%(i.name))
                    intangpxfa = doc.createElement("float_array")
                    intangpxfa.setAttribute("id","%s_rotation_euler_X-intangent-array"%(i.name))
                    intangpxfa.setAttribute("count","%s"%((ii)*2))
                    sintangpxdat = doc.createTextNode("%s"%(intangx))
                    intangpxfa.appendChild(sintangpxdat)
                    tcintangpx = doc.createElement("technique_common")
                    accintangpx = doc.createElement("accessor")
                    accintangpx.setAttribute("source","#%s_rotation_euler_X-intangent-array"%(i.name))
                    accintangpx.setAttribute("count","%s"%(ii))
                    accintangpx.setAttribute("stride","2")
                    parintangpx = doc.createElement("param")
                    parintangpx.setAttribute("name","X")
                    parintangpx.setAttribute("type","float")
                    parintangpxy = doc.createElement("param")
                    parintangpxy.setAttribute("name","Y")
                    parintangpxy.setAttribute("type","float")
                    accintangpx.appendChild(parintangpx)
                    accintangpx.appendChild(parintangpxy)
                    tcintangpx.appendChild(accintangpx)
                    sintangpx.appendChild(intangpxfa)
                    sintangpx.appendChild(tcintangpx)
                    #outtangent
                    soutangpx = doc.createElement("source")
                    soutangpx.setAttribute("id","%s_rotation_euler_X-outtangent"%(i.name))
                    outangpxfa = doc.createElement("float_array")
                    outangpxfa.setAttribute("id","%s_rotation_euler_X-outtangent-array"%(i.name))
                    outangpxfa.setAttribute("count","%s"%((ii)*2))
                    soutangpxdat = doc.createTextNode("%s"%(outtangx))
                    outangpxfa.appendChild(soutangpxdat)
                    tcoutangpx = doc.createElement("technique_common")
                    accoutangpx = doc.createElement("accessor")
                    accoutangpx.setAttribute("source","#%s_rotation_euler_X-outtangent-array"%(i.name))
                    accoutangpx.setAttribute("count","%s"%(ii))
                    accoutangpx.setAttribute("stride","2")
                    paroutangpx = doc.createElement("param")
                    paroutangpx.setAttribute("name","X")
                    paroutangpx.setAttribute("type","float")
                    paroutangpxy = doc.createElement("param")
                    paroutangpxy.setAttribute("name","Y")
                    paroutangpxy.setAttribute("type","float")
                    accoutangpx.appendChild(paroutangpx)
                    accoutangpx.appendChild(paroutangpxy)
                    tcoutangpx.appendChild(accoutangpx)
                    soutangpx.appendChild(outangpxfa)
                    soutangpx.appendChild(tcoutangpx)
                    #sampler
                    samx = doc.createElement("sampler")
                    samx.setAttribute("id","%s_rotation_euler_X-sampler"%(i.name))
                    semip = doc.createElement("input")
                    semip.setAttribute("semantic","INPUT")
                    semip.setAttribute("source","#%s_rotation_euler_X-input"%(i.name))
                    semop = doc.createElement("input")
                    semop.setAttribute("semantic","OUTPUT")
                    semop.setAttribute("source","#%s_rotation_euler_X-output"%(i.name))
                    seminter = doc.createElement("input")
                    seminter.setAttribute("semantic","INTERPOLATION")
                    seminter.setAttribute("source","#%s_rotation_euler_X-interpolation"%(i.name))
                    semintang = doc.createElement("input")
                    semintang.setAttribute("semantic","IN_TANGENT")
                    semintang.setAttribute("source","#%s_rotation_euler_X-intangent"%(i.name))
                    semoutang = doc.createElement("input")
                    semoutang.setAttribute("semantic","OUT_TANGENT")
                    semoutang.setAttribute("source","#%s_rotation_euler_X-outtangent"%(i.name))
                    samx.appendChild(semip)
                    samx.appendChild(semop)
                    samx.appendChild(seminter)
                    #samx.appendChild(semintang)
                    #samx.appendChild(semoutang)
                    chanx = doc.createElement("channel")
                    chanx.setAttribute("source","#%s_rotation_euler_X-sampler"%(i.name))
                    chanx.setAttribute("target","%s/rotation_x.ANGLE"%(i.name))
                    anmrx.appendChild(sinpx)
                    anmrx.appendChild(soutpx)
                    anmrx.appendChild(sintpx)
                    anmrx.appendChild(sintangpx)
                    anmrx.appendChild(soutangpx)
                    anmrx.appendChild(samx)
                    anmrx.appendChild(chanx)
                    #libanm.appendChild(anmrx)
                    cbPrint(ii)
                    cbPrint(inpx)
                    cbPrint(outpx)
                    cbPrint(intx)
                    cbPrint(intangx)
                    cbPrint(outtangx)
                    cbPrint("donerotx")
            return anmrx
        def extract_aniry(self, i):
            act = i.animation_data.action
            curves = act.fcurves
            fcus = {}
            for fcu in curves:
                    #Y
                if fcu.data_path == 'rotation_euler'and fcu.array_index == 1:
                    anmry = doc.createElement("animation")
                    anmry.setAttribute("id","%s_rotation_euler_Y"%(i.name))
                    fcus[fcu.array_index] = fcu

                    intangy = ""
                    outtangy = ""
                    inpy = ""
                    outpy = ""
                    inty = ""
                    tempy = fcus[1].keyframe_points
                    ii = 0
                    for key in tempy:
                        khlx = key.handle_left[0]
                        khly = key.handle_left[1]
                        khrx = key.handle_right[0]
                        khry = key.handle_right[1]
                        frame, value = key.co
                        time = convert_time(frame)
                        inty += ("%s "%(key.interpolation))
                        inpy += ("%.6f "%(time))
                        outpy += ("%.6f "%(value * utils.toD))
                        intangfirst = convert_time(khlx)
                        outangfirst = convert_time(khrx)
                        intangy += ("%.6f %.6f "%(intangfirst,khly))
                        outtangy += ("%.6f %.6f "%(outangfirst,khry))
                        ii += 1
                    #input
                    sinpy = doc.createElement("source")
                    sinpy.setAttribute("id","%s_rotation_euler_Y-input"%(i.name))
                    inpyfa = doc.createElement("float_array")
                    inpyfa.setAttribute("id","%s_rotation_euler_Y-input-array"%(i.name))
                    inpyfa.setAttribute("count","%s"%(ii))
                    sinpydat = doc.createTextNode("%s"%(inpy))
                    inpyfa.appendChild(sinpydat)
                    tcinpy = doc.createElement("technique_common")
                    accinpy = doc.createElement("accessor")
                    accinpy.setAttribute("source","#%s_rotation_euler_Y-input-array"%(i.name))
                    accinpy.setAttribute("count","%s"%(ii))
                    accinpy.setAttribute("stride","1")
                    parinpy = doc.createElement("param")
                    parinpy.setAttribute("name","TIME")
                    parinpy.setAttribute("type","float")
                    accinpy.appendChild(parinpy)
                    tcinpy.appendChild(accinpy)
                    sinpy.appendChild(inpyfa)
                    sinpy.appendChild(tcinpy)
                    #output
                    soutpy = doc.createElement("source")
                    soutpy.setAttribute("id","%s_rotation_euler_Y-output"%(i.name))
                    outpyfa = doc.createElement("float_array")
                    outpyfa.setAttribute("id","%s_rotation_euler_Y-output-array"%(i.name))
                    outpyfa.setAttribute("count","%s"%(ii))
                    soutpydat = doc.createTextNode("%s"%(outpy))
                    outpyfa.appendChild(soutpydat)
                    tcoutpy = doc.createElement("technique_common")
                    accoutpy = doc.createElement("accessor")
                    accoutpy.setAttribute("source","#%s_rotation_euler_Y-output-array"%(i.name))
                    accoutpy.setAttribute("count","%s"%(ii))
                    accoutpy.setAttribute("stride","1")
                    paroutpy = doc.createElement("param")
                    paroutpy.setAttribute("name","VALUE")
                    paroutpy.setAttribute("type","float")
                    accoutpy.appendChild(paroutpy)
                    tcoutpy.appendChild(accoutpy)
                    soutpy.appendChild(outpyfa)
                    soutpy.appendChild(tcoutpy)
                    #interpolation
                    sintpy = doc.createElement("source")
                    sintpy.setAttribute("id","%s_rotation_euler_Y-interpolation"%(i.name))
                    intpyfa = doc.createElement("Name_array")
                    intpyfa.setAttribute("id","%s_rotation_euler_Y-interpolation-array"%(i.name))
                    intpyfa.setAttribute("count","%s"%(ii))
                    sintpydat = doc.createTextNode("%s"%(inty))
                    intpyfa.appendChild(sintpydat)
                    tcintpy = doc.createElement("technique_common")
                    accintpy = doc.createElement("accessor")
                    accintpy.setAttribute("source","#%s_rotation_euler_Y-interpolation-array"%(i.name))
                    accintpy.setAttribute("count","%s"%(ii))
                    accintpy.setAttribute("stride","1")
                    parintpy = doc.createElement("param")
                    parintpy.setAttribute("name","INTERPOLATION")
                    parintpy.setAttribute("type","name")
                    accintpy.appendChild(parintpy)
                    tcintpy.appendChild(accintpy)
                    sintpy.appendChild(intpyfa)
                    sintpy.appendChild(tcintpy)
                    #intangent
                    sintangpy = doc.createElement("source")
                    sintangpy.setAttribute("id","%s_rotation_euler_Y-intangent"%(i.name))
                    intangpyfa = doc.createElement("float_array")
                    intangpyfa.setAttribute("id","%s_rotation_euler_Y-intangent-array"%(i.name))
                    intangpyfa.setAttribute("count","%s"%((ii)*2))
                    sintangpydat = doc.createTextNode("%s"%(intangy))
                    intangpyfa.appendChild(sintangpydat)
                    tcintangpy = doc.createElement("technique_common")
                    accintangpy = doc.createElement("accessor")
                    accintangpy.setAttribute("source","#%s_rotation_euler_Y-intangent-array"%(i.name))
                    accintangpy.setAttribute("count","%s"%(ii))
                    accintangpy.setAttribute("stride","2")
                    parintangpy = doc.createElement("param")
                    parintangpy.setAttribute("name","X")
                    parintangpy.setAttribute("type","float")
                    parintangpyy = doc.createElement("param")
                    parintangpyy.setAttribute("name","Y")
                    parintangpyy.setAttribute("type","float")
                    accintangpy.appendChild(parintangpy)
                    accintangpy.appendChild(parintangpyy)
                    tcintangpy.appendChild(accintangpy)
                    sintangpy.appendChild(intangpyfa)
                    sintangpy.appendChild(tcintangpy)
                    #outtangent
                    soutangpy = doc.createElement("source")
                    soutangpy.setAttribute("id","%s_rotation_euler_Y-outtangent"%(i.name))
                    outangpyfa = doc.createElement("float_array")
                    outangpyfa.setAttribute("id","%s_rotation_euler_Y-outtangent-array"%(i.name))
                    outangpyfa.setAttribute("count","%s"%((ii)*2))
                    soutangpydat = doc.createTextNode("%s"%(outtangy))
                    outangpyfa.appendChild(soutangpydat)
                    tcoutangpy = doc.createElement("technique_common")
                    accoutangpy = doc.createElement("accessor")
                    accoutangpy.setAttribute("source","#%s_rotation_euler_Y-outtangent-array"%(i.name))
                    accoutangpy.setAttribute("count","%s"%(ii))
                    accoutangpy.setAttribute("stride","2")
                    paroutangpy = doc.createElement("param")
                    paroutangpy.setAttribute("name","X")
                    paroutangpy.setAttribute("type","float")
                    paroutangpyy = doc.createElement("param")
                    paroutangpyy.setAttribute("name","Y")
                    paroutangpyy.setAttribute("type","float")
                    accoutangpy.appendChild(paroutangpy)
                    accoutangpy.appendChild(paroutangpyy)
                    tcoutangpy.appendChild(accoutangpy)
                    soutangpy.appendChild(outangpyfa)
                    soutangpy.appendChild(tcoutangpy)
                    #sampler
                    samy = doc.createElement("sampler")
                    samy.setAttribute("id","%s_rotation_euler_Y-sampler"%(i.name))
                    semip = doc.createElement("input")
                    semip.setAttribute("semantic","INPUT")
                    semip.setAttribute("source","#%s_rotation_euler_Y-input"%(i.name))
                    semop = doc.createElement("input")
                    semop.setAttribute("semantic","OUTPUT")
                    semop.setAttribute("source","#%s_rotation_euler_Y-output"%(i.name))
                    seminter = doc.createElement("input")
                    seminter.setAttribute("semantic","INTERPOLATION")
                    seminter.setAttribute("source","#%s_rotation_euler_Y-interpolation"%(i.name))
                    semintang = doc.createElement("input")
                    semintang.setAttribute("semantic","IN_TANGENT")
                    semintang.setAttribute("source","#%s_rotation_euler_Y-intangent"%(i.name))
                    semoutang = doc.createElement("input")
                    semoutang.setAttribute("semantic","OUT_TANGENT")
                    semoutang.setAttribute("source","#%s_rotation_euler_Y-outtangent"%(i.name))
                    samy.appendChild(semip)
                    samy.appendChild(semop)
                    samy.appendChild(seminter)
                    #samy.appendChild(semintang)
                    #samy.appendChild(semoutang)
                    chany = doc.createElement("channel")
                    chany.setAttribute("source","#%s_rotation_euler_Y-sampler"%(i.name))
                    chany.setAttribute("target","%s/rotation_y.ANGLE"%(i.name))
                    anmry.appendChild(sinpy)
                    anmry.appendChild(soutpy)
                    anmry.appendChild(sintpy)
                    anmry.appendChild(sintangpy)
                    anmry.appendChild(soutangpy)
                    anmry.appendChild(samy)
                    anmry.appendChild(chany)
                    #libanm.appendChild(anmry)
                    cbPrint(ii)
                    cbPrint(inpy)
                    cbPrint(outpy)
                    cbPrint(inty)
                    cbPrint(intangy)
                    cbPrint(outtangy)
                    cbPrint("doneroty")
            return anmry
        def extract_anirz(self, i):
            act = i.animation_data.action
            curves = act.fcurves
            fcus = {}
            for fcu in curves:
                  #Z
                if fcu.data_path == 'rotation_euler'and fcu.array_index == 2:
                    anmrz = doc.createElement("animation")
                    anmrz.setAttribute("id","%s_rotation_euler_Z"%(i.name))
                    fcus[fcu.array_index] = fcu

                    intangz = ""
                    outtangz = ""
                    inpz = ""
                    outpz = ""
                    intz = ""
                    tempz = fcus[2].keyframe_points
                    ii = 0
                    for key in tempz:
                        khlx = key.handle_left[0]
                        khly = key.handle_left[1]
                        khrx = key.handle_right[0]
                        khry = key.handle_right[1]
                        frame, value = key.co
                        time = convert_time(frame)
                        intz += ("%s "%(key.interpolation))
                        inpz += ("%.6f "%(time))
                        outpz += ("%.6f "%(value * utils.toD))
                        intangfirst = convert_time(khlx)
                        outangfirst = convert_time(khrx)
                        intangz += ("%.6f %.6f "%(intangfirst,khly))
                        outtangz += ("%.6f %.6f "%(outangfirst,khry))
                        ii += 1
                    #input
                    sinpz = doc.createElement("source")
                    sinpz.setAttribute("id","%s_rotation_euler_Z-input"%(i.name))
                    inpzfa = doc.createElement("float_array")
                    inpzfa.setAttribute("id","%s_rotation_euler_Z-input-array"%(i.name))
                    inpzfa.setAttribute("count","%s"%(ii))
                    sinpzdat = doc.createTextNode("%s"%(inpz))
                    inpzfa.appendChild(sinpzdat)
                    tcinpz = doc.createElement("technique_common")
                    accinpz = doc.createElement("accessor")
                    accinpz.setAttribute("source","#%s_rotation_euler_Z-input-array"%(i.name))
                    accinpz.setAttribute("count","%s"%(ii))
                    accinpz.setAttribute("stride","1")
                    parinpz = doc.createElement("param")
                    parinpz.setAttribute("name","TIME")
                    parinpz.setAttribute("type","float")
                    accinpz.appendChild(parinpz)
                    tcinpz.appendChild(accinpz)
                    sinpz.appendChild(inpzfa)
                    sinpz.appendChild(tcinpz)
                    #output
                    soutpz = doc.createElement("source")
                    soutpz.setAttribute("id","%s_rotation_euler_Z-output"%(i.name))
                    outpzfa = doc.createElement("float_array")
                    outpzfa.setAttribute("id","%s_rotation_euler_Z-output-array"%(i.name))
                    outpzfa.setAttribute("count","%s"%(ii))
                    soutpzdat = doc.createTextNode("%s"%(outpz))
                    outpzfa.appendChild(soutpzdat)
                    tcoutpz = doc.createElement("technique_common")
                    accoutpz = doc.createElement("accessor")
                    accoutpz.setAttribute("source","#%s_rotation_euler_Z-output-array"%(i.name))
                    accoutpz.setAttribute("count","%s"%(ii))
                    accoutpz.setAttribute("stride","1")
                    paroutpz = doc.createElement("param")
                    paroutpz.setAttribute("name","VALUE")
                    paroutpz.setAttribute("type","float")
                    accoutpz.appendChild(paroutpz)
                    tcoutpz.appendChild(accoutpz)
                    soutpz.appendChild(outpzfa)
                    soutpz.appendChild(tcoutpz)
                    #interpolation
                    sintpz = doc.createElement("source")
                    sintpz.setAttribute("id","%s_rotation_euler_Z-interpolation"%(i.name))
                    intpzfa = doc.createElement("Name_array")
                    intpzfa.setAttribute("id","%s_rotation_euler_Z-interpolation-array"%(i.name))
                    intpzfa.setAttribute("count","%s"%(ii))
                    sintpzdat = doc.createTextNode("%s"%(intz))
                    intpzfa.appendChild(sintpzdat)
                    tcintpz = doc.createElement("technique_common")
                    accintpz = doc.createElement("accessor")
                    accintpz.setAttribute("source","#%s_rotation_euler_Z-interpolation-array"%(i.name))
                    accintpz.setAttribute("count","%s"%(ii))
                    accintpz.setAttribute("stride","1")
                    parintpz = doc.createElement("param")
                    parintpz.setAttribute("name","INTERPOLATION")
                    parintpz.setAttribute("type","name")
                    accintpz.appendChild(parintpz)
                    tcintpz.appendChild(accintpz)
                    sintpz.appendChild(intpzfa)
                    sintpz.appendChild(tcintpz)
                    #intangent
                    sintangpz = doc.createElement("source")
                    sintangpz.setAttribute("id","%s_rotation_euler_Z-intangent"%(i.name))
                    intangpzfa = doc.createElement("float_array")
                    intangpzfa.setAttribute("id","%s_rotation_euler_Z-intangent-array"%(i.name))
                    intangpzfa.setAttribute("count","%s"%((ii)*2))
                    sintangpzdat = doc.createTextNode("%s"%(intangz))
                    intangpzfa.appendChild(sintangpzdat)
                    tcintangpz = doc.createElement("technique_common")
                    accintangpz = doc.createElement("accessor")
                    accintangpz.setAttribute("source","#%s_rotation_euler_Z-intangent-array"%(i.name))
                    accintangpz.setAttribute("count","%s"%(ii))
                    accintangpz.setAttribute("stride","2")
                    parintangpz = doc.createElement("param")
                    parintangpz.setAttribute("name","X")
                    parintangpz.setAttribute("type","float")
                    parintangpyz = doc.createElement("param")
                    parintangpyz.setAttribute("name","Y")
                    parintangpyz.setAttribute("type","float")
                    accintangpz.appendChild(parintangpz)
                    accintangpz.appendChild(parintangpyz)
                    tcintangpz.appendChild(accintangpz)
                    sintangpz.appendChild(intangpzfa)
                    sintangpz.appendChild(tcintangpz)
                    #outtangent
                    soutangpz = doc.createElement("source")
                    soutangpz.setAttribute("id","%s_rotation_euler_Z-outtangent"%(i.name))
                    outangpzfa = doc.createElement("float_array")
                    outangpzfa.setAttribute("id","%s_rotation_euler_Z-outtangent-array"%(i.name))
                    outangpzfa.setAttribute("count","%s"%((ii)*2))
                    soutangpzdat = doc.createTextNode("%s"%(outtangz))
                    outangpzfa.appendChild(soutangpzdat)
                    tcoutangpz = doc.createElement("technique_common")
                    accoutangpz = doc.createElement("accessor")
                    accoutangpz.setAttribute("source","#%s_rotation_euler_Z-outtangent-array"%(i.name))
                    accoutangpz.setAttribute("count","%s"%(ii))
                    accoutangpz.setAttribute("stride","2")
                    paroutangpz = doc.createElement("param")
                    paroutangpz.setAttribute("name","X")
                    paroutangpz.setAttribute("type","float")
                    paroutangpyz = doc.createElement("param")
                    paroutangpyz.setAttribute("name","Y")
                    paroutangpyz.setAttribute("type","float")
                    accoutangpz.appendChild(paroutangpz)
                    accoutangpz.appendChild(paroutangpyz)
                    tcoutangpz.appendChild(accoutangpz)
                    soutangpz.appendChild(outangpzfa)
                    soutangpz.appendChild(tcoutangpz)
                    #sampler
                    samz = doc.createElement("sampler")
                    samz.setAttribute("id","%s_rotation_euler_Z-sampler"%(i.name))
                    semip = doc.createElement("input")
                    semip.setAttribute("semantic","INPUT")
                    semip.setAttribute("source","#%s_rotation_euler_Z-input"%(i.name))
                    semop = doc.createElement("input")
                    semop.setAttribute("semantic","OUTPUT")
                    semop.setAttribute("source","#%s_rotation_euler_Z-output"%(i.name))
                    seminter = doc.createElement("input")
                    seminter.setAttribute("semantic","INTERPOLATION")
                    seminter.setAttribute("source","#%s_rotation_euler_Z-interpolation"%(i.name))
                    semintang = doc.createElement("input")
                    semintang.setAttribute("semantic","IN_TANGENT")
                    semintang.setAttribute("source","#%s_rotation_euler_Z-intangent"%(i.name))
                    semoutang = doc.createElement("input")
                    semoutang.setAttribute("semantic","OUT_TANGENT")
                    semoutang.setAttribute("source","#%s_rotation_euler_Z-outtangent"%(i.name))
                    samz.appendChild(semip)
                    samz.appendChild(semop)
                    samz.appendChild(seminter)
                    #samz.appendChild(semintang)
                    #samz.appendChild(semoutang)
                    chanz = doc.createElement("channel")
                    chanz.setAttribute("source","#%s_rotation_euler_Z-sampler"%(i.name))
                    chanz.setAttribute("target","%s/rotation_z.ANGLE"%(i.name))
                    anmrz.appendChild(sinpz)
                    anmrz.appendChild(soutpz)
                    anmrz.appendChild(sintpz)
                    anmrz.appendChild(sintangpz)
                    anmrz.appendChild(soutangpz)
                    anmrz.appendChild(samz)
                    anmrz.appendChild(chanz)
                    #libanm.appendChild(anmrz)
                    cbPrint(ii)
                    cbPrint(inpz)
                    cbPrint(outpz)
                    cbPrint(intz)
                    cbPrint(intangz)
                    cbPrint(outtangz)
                    cbPrint("donerotz")
            return anmrz
        libanmcl = doc.createElement("library_animation_clips")
        libanm = doc.createElement("library_animations")
        asw = 0
        ande = 0
        ande2 = 0
        for i in bpy.context.selected_objects:
            idat = i.data
            lnname = str(i.name)
            for item in bpy.context.blend_data.groups:
                if item:
                    ename=str(item.id_data.name)
            if lnname[:8] == "animnode":
                ande2 = 1
                cbPrint(i["animname"])
                cbPrint(i["startframe"])
                cbPrint(i["endframe"])
                actname = i["animname"]
                sf = i["startframe"]
                ef = i["endframe"]
                anicl = doc.createElement("animation_clip")
                anicl.setAttribute("id","%s-%s"%(actname,ename[14:]))
                anicl.setAttribute("start","%s"%(convert_time(sf)))
                anicl.setAttribute("end","%s"%(convert_time(ef)))
                for i in bpy.context.selected_objects:
                    if i.animation_data:
                        if i.type == 'ARMATURE':
                            cbPrint("Object is armature, cannot process animations.")
                        else:
                            if i.animation_data.action:
                                act = i.animation_data.action
                                curves = act.fcurves
                                frstrt=curves.data.frame_range[0]
                                frend=curves.data.frame_range[1]
                                anmlx = extract_anilx(self, i)
                                anmly = extract_anily(self, i)
                                anmlz = extract_anilz(self, i)
                                anmrx = extract_anirx(self, i)
                                anmry = extract_aniry(self, i)
                                anmrz = extract_anirz(self, i)
                                instlx = doc.createElement("instance_animation")
                                instlx.setAttribute("url","#%s_location_X"%(i.name))
                                anicl.appendChild(instlx)
                                instly = doc.createElement("instance_animation")
                                instly.setAttribute("url","#%s_location_Y"%(i.name))
                                anicl.appendChild(instly)
                                instlz = doc.createElement("instance_animation")
                                instlz.setAttribute("url","#%s_location_Z"%(i.name))
                                anicl.appendChild(instlz)
                                instrx = doc.createElement("instance_animation")
                                instrx.setAttribute("url","#%s_rotation_euler_X"%(i.name))
                                anicl.appendChild(instrx)
                                instry = doc.createElement("instance_animation")
                                instry.setAttribute("url","#%s_rotation_euler_Y"%(i.name))
                                anicl.appendChild(instry)
                                instrz = doc.createElement("instance_animation")
                                instrz.setAttribute("url","#%s_rotation_euler_Z"%(i.name))
                                anicl.appendChild(instrz)
                                libanm.appendChild(anmlx)
                                libanm.appendChild(anmly)
                                libanm.appendChild(anmlz)
                                libanm.appendChild(anmrx)
                                libanm.appendChild(anmry)
                                libanm.appendChild(anmrz)
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
                                    ename=str(item.id_data.name)


                            act = i.animation_data.action
                            curves = act.fcurves
                            frstrt=curves.data.frame_range[0]
                            frend=curves.data.frame_range[1]
                            anmlx = extract_anilx(self, i)
                            anmly = extract_anily(self, i)
                            anmlz = extract_anilz(self, i)
                            anmrx = extract_anirx(self, i)
                            anmry = extract_aniry(self, i)
                            anmrz = extract_anirz(self, i)
                            #animationclip name and framerange
                            for ai in i.children:
                                aname=str(ai.name)
                                if aname[:8] == "animnode":

                                    ande = 1
                                    cbPrint(ai["animname"])
                                    cbPrint(ai["startframe"])
                                    cbPrint(ai["endframe"])
                                    actname = ai["animname"]
                                    sf = ai["startframe"]
                                    ef = ai["endframe"]
                                    anicl = doc.createElement("animation_clip")
                                    anicl.setAttribute("id","%s-%s"%(actname,ename[14:]))
                                    anicl.setAttribute("start","%s"%(convert_time(sf)))
                                    anicl.setAttribute("end","%s"%(convert_time(ef)))
                                    instlx = doc.createElement("instance_animation")
                                    instlx.setAttribute("url","#%s_location_X"%(i.name))
                                    anicl.appendChild(instlx)
                                    instly = doc.createElement("instance_animation")
                                    instly.setAttribute("url","#%s_location_Y"%(i.name))
                                    anicl.appendChild(instly)
                                    instlz = doc.createElement("instance_animation")
                                    instlz.setAttribute("url","#%s_location_Z"%(i.name))
                                    anicl.appendChild(instlz)
                                    instrx = doc.createElement("instance_animation")
                                    instrx.setAttribute("url","#%s_rotation_euler_X"%(i.name))
                                    anicl.appendChild(instrx)
                                    instry = doc.createElement("instance_animation")
                                    instry.setAttribute("url","#%s_rotation_euler_Y"%(i.name))
                                    anicl.appendChild(instry)
                                    instrz = doc.createElement("instance_animation")
                                    instrz.setAttribute("url","#%s_rotation_euler_Z"%(i.name))
                                    anicl.appendChild(instrz)
                                    libanmcl.appendChild(anicl)

                            if ande == 0:
                                if self.merge_anm:
                                    if asw == 0:
                                        anicl = doc.createElement("animation_clip")
                                        anicl.setAttribute("id","%s-%s"%(act.name,ename[14:]))
                                        anicl.setAttribute("start","%s"%(convert_time(frstrt)))
                                        anicl.setAttribute("end","%s"%(convert_time(frend)))
                                        instlx = doc.createElement("instance_animation")
                                        instlx.setAttribute("url","#%s_location_X"%(i.name))
                                        anicl.appendChild(instlx)
                                        instly = doc.createElement("instance_animation")
                                        instly.setAttribute("url","#%s_location_Y"%(i.name))
                                        anicl.appendChild(instly)
                                        instlz = doc.createElement("instance_animation")
                                        instlz.setAttribute("url","#%s_location_Z"%(i.name))
                                        anicl.appendChild(instlz)
                                        instrx = doc.createElement("instance_animation")
                                        instrx.setAttribute("url","#%s_rotation_euler_X"%(i.name))
                                        anicl.appendChild(instrx)
                                        instry = doc.createElement("instance_animation")
                                        instry.setAttribute("url","#%s_rotation_euler_Y"%(i.name))
                                        anicl.appendChild(instry)
                                        instrz = doc.createElement("instance_animation")
                                        instrz.setAttribute("url","#%s_rotation_euler_Z"%(i.name))
                                        anicl.appendChild(instrz)


                                        asw = 1
                                    else:
                                        cbPrint("Merging clips.")
                                else:
                                    anicl = doc.createElement("animation_clip")
                                    anicl.setAttribute("id","%s-%s"%(act.name,ename[14:]))
                                    anicl.setAttribute("start","%s"%(convert_time(frstrt)))
                                    anicl.setAttribute("end","%s"%(convert_time(frend)))

                                    instlx = doc.createElement("instance_animation")
                                    instlx.setAttribute("url","#%s_location_X"%(i.name))
                                    anicl.appendChild(instlx)
                                    instly = doc.createElement("instance_animation")
                                    instly.setAttribute("url","#%s_location_Y"%(i.name))
                                    anicl.appendChild(instly)
                                    instlz = doc.createElement("instance_animation")
                                    instlz.setAttribute("url","#%s_location_Z"%(i.name))
                                    anicl.appendChild(instlz)
                                    instrx = doc.createElement("instance_animation")
                                    instrx.setAttribute("url","#%s_rotation_euler_X"%(i.name))
                                    anicl.appendChild(instrx)
                                    instry = doc.createElement("instance_animation")
                                    instry.setAttribute("url","#%s_rotation_euler_Y"%(i.name))
                                    anicl.appendChild(instry)
                                    instrz = doc.createElement("instance_animation")
                                    instrz.setAttribute("url","#%s_rotation_euler_Z"%(i.name))
                                    anicl.appendChild(instrz)



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
        col.appendChild(libanmcl)
        col.appendChild(libanm)
        asw = 0
        ande2 = 0

#library_visual_scenes
        libvs = doc.createElement("library_visual_scenes")
        #cprop = ""
#try group for cryexportnode?----Yes It Is Good :)
#        for item in bpy.context.blend_data.groups:

#test


        def wbl(self, pname, bonelist, obj):
            cbPrint(len(bonelist), "bones")
            boneExtendedNames = []
            for Bone in bonelist:
                bprnt = Bone.parent
                if bprnt:
                    cbPrint(Bone.name, Bone.parent.name)
                bname = Bone.name
                nodename = bname
                nodename=doc.createElement("node")
                
                pExtension = ''
                
                #Name Extension
                extend = False
                if extend or self.include_ik and "_Phys" == Bone.name[len(Bone.name)-5:]:
                    exportNodeName = node1.getAttribute('id')[14:]
                    boneName = Bone.name
                    starredBoneName = ''
                    for char in boneName:
                        if char == '_':
                            char = '*'
                        starredBoneName += char
                    pExtension += '%'+exportNodeName+'%'
                    pExtension += '--PRprops_name='+starredBoneName+'_'
                
                #IK
                if "_Phys" == Bone.name[len(Bone.name)-5:] and self.include_ik:
                    poseBone = bpy.data.objects[obj.name[:len(obj.name)-5]].pose.bones[Bone.name[:len(Bone.name)-5]]
                    
                    #Start IK props
                    pExtension += 'xmax='+str(poseBone.ik_max_x)+'_'
                    pExtension += 'xmin='+str(poseBone.ik_min_x)+'_'
                    pExtension += 'xdamping='+str(poseBone.ik_stiffness_x)+'_'
                    pExtension += 'xspringangle='+str(0.0)+'_'
                    pExtension += 'xspringtension='+str(1.0)+'_'
                    
                    pExtension += 'ymax='+str(poseBone.ik_max_y)+'_'
                    pExtension += 'ymin='+str(poseBone.ik_min_y)+'_'
                    pExtension += 'ydamping='+str(poseBone.ik_stiffness_y)+'_'
                    pExtension += 'yspringangle='+str(0.0)+'_'
                    pExtension += 'yspringtension='+str(1.0)+'_'
                    
                    pExtension += 'zmax='+str(poseBone.ik_max_z)+'_'
                    pExtension += 'zmin='+str(poseBone.ik_min_z)+'_'
                    pExtension += 'zdamping='+str(poseBone.ik_stiffness_z)+'_'
                    pExtension += 'zspringangle='+str(0.0)+'_'
                    pExtension += 'zspringtension='+str(1.0)+'_'
                    #End IK props
                
                if extend:
                    pExtension += '_'
                
                nodename.setAttribute("id","%s"%(bname+pExtension))
                nodename.setAttribute("name", "%s"%(bname+pExtension))
                boneExtendedNames.append(bname+pExtension)
                nodename.setIdAttribute('id')  

                for object in bpy.context.selectable_objects:
                    if object.name == Bone.name or (object.name == Bone.name[:len(Bone.name)-5] and "_Phys" == Bone.name[len(Bone.name)-5:]):
                        bpy.data.objects[object.name].select = True
                        #fbone = object
                        cbPrint("FakeBone found for " + Bone.name)
                        #<translate sid="translation">
                        trans=doc.createElement("translate")
                        trans.setAttribute("sid","translation")
                        transnum=doc.createTextNode("%.4f %.4f %.4f"%object.location[:])
                        trans.appendChild(transnum)
                        #<rotate sid="rotation_Z">
                        rotz=doc.createElement("rotate")
                        rotz.setAttribute("sid","rotation_Z")
                        rotzn=doc.createTextNode("0 0 1 %.4f"%(object.rotation_euler[2] * utils.toD))
                        rotz.appendChild(rotzn)
                        #<rotate sid="rotation_Y">
                        roty=doc.createElement("rotate")
                        roty.setAttribute("sid","rotation_Y")
                        rotyn=doc.createTextNode("0 1 0 %.4f"%(object.rotation_euler[1] * utils.toD))
                        roty.appendChild(rotyn)
                        #<rotate sid="rotation_X">
                        rotx=doc.createElement("rotate")
                        rotx.setAttribute("sid","rotation_X")
                        rotxn=doc.createTextNode("1 0 0 %.4f"%(object.rotation_euler[0] * utils.toD))
                        rotx.appendChild(rotxn)
                        #<scale sid="scale">
                        sc=doc.createElement("scale")
                        sc.setAttribute("sid","scale")
                        sx=str(object.scale[0])
                        sy=str(object.scale[1])
                        sz=str(object.scale[2])
                        scn=doc.createTextNode("%s"%utils.addthree(sx,sy,sz))
                        sc.appendChild(scn)
                        nodename.appendChild(trans)
                        nodename.appendChild(rotz)
                        nodename.appendChild(roty)
                        nodename.appendChild(rotx)
                        nodename.appendChild(sc)
                        for i in bpy.context.selectable_objects: #Find the boneGeometry object
                            if i.name == Bone.name + "_boneGeometry":
                                ig=doc.createElement("instance_geometry")
                                ig.setAttribute("url","#%s"%(Bone.name+"_boneGeometry"))
                                bm=doc.createElement("bind_material")
                                tc=doc.createElement("technique_common")
                                #mat = mesh.materials[:]
                                for mat in i.material_slots:
                                    if mat:
                                    #yes lets go through them 1 at a time
                                        im=doc.createElement("instance_material")
                                        im.setAttribute("symbol","%s"%(mat.name))
                                        im.setAttribute("target","#%s"%(mat.name))
                                        bvi=doc.createElement("bind_vertex_input")
                                        bvi.setAttribute("semantic","UVMap")
                                        bvi.setAttribute("input_semantic","TEXCOORD")
                                        bvi.setAttribute("input_set","0")
                                        im.appendChild(bvi)
                                        tc.appendChild(im)
                                bm.appendChild(tc)
                                ig.appendChild(bm)
                                nodename.appendChild(ig)

                if bprnt:
                    for name in boneExtendedNames:
                        if name[:len(bprnt.name)] == bprnt.name:
                            nodeparent = doc.getElementById(name)
                            cbPrint(bprnt.name)
                            nodeparent.appendChild(nodename)                    
                else: #Root bone (of any armature type)
                    #nodeparent = doc.getElementById("%s"%pname)
                    #nodeparent.appendChild(nodename)
                    node1.appendChild(nodename)#nodeparent)

    
        def GetObjectChildren(Parent):
            return [Object for Object in Parent.children
                    if Object.type in {'ARMATURE', 'EMPTY', 'MESH'}]

        def vsp(self, objectl):
            ol = len(objectl)

            for object in objectl:
                fby = 0
                for ai in object.rna_type.id_data.items():
                    if ai:
                        if ai[1] == "fakebone":
                            fby =1
                if fby == 1:#object.parent_bone:
                    pass
                else:
                    if object.type == 'ARMATURE':
                        cname=(object.name)
                    else:
                        cname=(object.name)
                    nodename = cname
                    nodename=doc.createElement("node")
                    nodename.setAttribute("id","%s"%(cname))
                    nodename.setIdAttribute('id')
                    #<translate sid="translation">
                    trans=doc.createElement("translate")
                    trans.setAttribute("sid","translation")
                    transnum=doc.createTextNode("%.4f %.4f %.4f"%object.location[:])
                    trans.appendChild(transnum)
                    #<rotate sid="rotation_Z">
                    rotz=doc.createElement("rotate")
                    rotz.setAttribute("sid","rotation_Z")
                    rotzn=doc.createTextNode("0 0 1 %s"%(object.rotation_euler[2] * utils.toD))
                    rotz.appendChild(rotzn)
                    #<rotate sid="rotation_Y">
                    roty=doc.createElement("rotate")
                    roty.setAttribute("sid","rotation_Y")
                    rotyn=doc.createTextNode("0 1 0 %s"%(object.rotation_euler[1] * utils.toD))
                    roty.appendChild(rotyn)
                    #<rotate sid="rotation_X">
                    rotx=doc.createElement("rotate")
                    rotx.setAttribute("sid","rotation_X")
                    rotxn=doc.createTextNode("1 0 0 %s"%(object.rotation_euler[0] * utils.toD))
                    rotx.appendChild(rotxn)
                    #<scale sid="scale">
                    sc=doc.createElement("scale")
                    sc.setAttribute("sid","scale")
                    sx=str(object.scale[0])
                    sy=str(object.scale[1])
                    sz=str(object.scale[2])
                    scn=doc.createTextNode("%s"%utils.addthree(sx,sy,sz))
                    sc.appendChild(scn)
                    nodename.appendChild(trans)
                    nodename.appendChild(rotz)
                    nodename.appendChild(roty)
                    nodename.appendChild(rotx)
                    nodename.appendChild(sc)

                    ArmatureList = [Modifier for Modifier in object.modifiers if Modifier.type == "ARMATURE"] #List of all the armature deformation modifiers
                    if ArmatureList:
                        #PoseBones = ArmatureObject.pose.bones
                        ArmatureObject = ArmatureList[0].object
                        ic = doc.createElement("instance_controller")
                        ic.setAttribute("url", "#%s_%s"%(ArmatureList[0].object.name,object.name)) #This binds the meshObject to the armature in control of it

                    name=str(object.name)
                    if (name[:6] != "_joint"):
                        if (object.type == "MESH"):
                            ig=doc.createElement("instance_geometry")
                            ig.setAttribute("url","#%s"%(cname))
                            bm=doc.createElement("bind_material")
                            tc=doc.createElement("technique_common")
                            #mat = mesh.materials[:]
                            for mat in object.material_slots:
                                if mat:
                                #yes lets go through them 1 at a time
                                    im=doc.createElement("instance_material")
                                    im.setAttribute("symbol","%s"%(mat.name))
                                    im.setAttribute("target","#%s"%(mat.name))
                                    bvi=doc.createElement("bind_vertex_input")
                                    bvi.setAttribute("semantic","UVMap")
                                    bvi.setAttribute("input_semantic","TEXCOORD")
                                    bvi.setAttribute("input_set","0")
                                    im.appendChild(bvi)
                                    tc.appendChild(im)
                            bm.appendChild(tc)
                            if ArmatureList:
                                ic.appendChild(bm)
                                nodename.appendChild(ic)
                            else:
                                ig.appendChild(bm)
                                nodename.appendChild(ig)

                            #nodename.appendChild(ig)
                    ex=doc.createElement("extra")
                    techcry=doc.createElement("technique")
                    techcry.setAttribute("profile","CryEngine")
                    prop2=doc.createElement("properties")
                    cprop = ""
                    for ai in object.rna_type.id_data.items():#Tagging properties onto the end of the item, I think.
                        if ai:
                            #cprop +=("%s=%s"%(i[0],i[1]))
                            cprop =("%s"%(ai[1]))
                            cryprops=doc.createTextNode("%s"%(cprop))
                            prop2.appendChild(cryprops)
                    techcry.appendChild(prop2)
                    if (name[:6] == "_joint"):
                        b=object.bound_box
                        vmin = Vector([b[0][0],b[0][1],b[0][2]])
                        vmax = Vector([b[6][0],b[6][1],b[6][2]])
                        ht=doc.createElement("helper")
                        ht.setAttribute("type","dummy")
                        bbmn=doc.createElement("bound_box_min")
                        vmin0 = str(vmin[0])
                        vmin1 = str(vmin[1])
                        vmin2 = str(vmin[2])
                        #bbmnval=doc.createTextNode("%s %s %s"%(vmin[0],vmin[1],vmin[2]))
                        bbmnval=doc.createTextNode("%s %s %s"%(vmin0[:6],vmin1[:6],vmin2[:6]))
                        bbmn.appendChild(bbmnval)
                        bbmx=doc.createElement("bound_box_max")
                        vmax0 = str(vmax[0])
                        vmax1 = str(vmax[1])
                        vmax2 = str(vmax[2])
                        #bbmxval=doc.createTextNode("%s %s %s"%(vmax[0],vmax[1],vmax[2]))
                        bbmxval=doc.createTextNode("%s %s %s"%(vmax0[:6],vmax1[:6],vmax2[:6]))
                        bbmx.appendChild(bbmxval)
                        ht.appendChild(bbmn)
                        ht.appendChild(bbmx)
                        techcry.appendChild(ht)
                    ex.appendChild(techcry)
                    nodename.appendChild(ex)
                    if object.type == 'ARMATURE':
                        #node1.appendChild(nodename)
                        cbPrint("Armature appended.")
                        bonelist = GetBones(object)
                        wbl(self, cname, bonelist, object)
                        #return node1
                    if object.children:
                        if object.parent:
                            if object.parent.type != 'ARMATURE':
                                nodeparent = doc.getElementById("%s"%object.parent.name)
                                cbPrint(nodeparent)
                                if nodeparent:
                                    cbPrint("Appending object to parent.")
                                    cbPrint(nodename)
                                    chk = doc.getElementById("%s"%object.name)
                                    if chk:
                                        cbPrint("Object already appended to parent.")
                                    else:
                                        nodeparent.appendChild(nodename)
                                ChildList = GetObjectChildren(object)
                                vsp(self, ChildList)
                        else:
                            if object.type != 'ARMATURE':
                                node1.appendChild(nodename)
                                ChildList = GetObjectChildren(object)
                                vsp(self, ChildList)
                        #return node1

                    else:
                        if object.parent:
                            if object.parent.type != 'ARMATURE':
                                nodeparent = doc.getElementById("%s"%object.parent.name)
                                cbPrint(nodeparent)
                                if nodeparent:
                                    cbPrint("Appending object to parent.")
                                    cbPrint(nodename)
                                    chk = doc.getElementById("%s"%object.name)
                                    if chk:
                                        cbPrint("Object already appended to parent.")
                                    else:
                                        nodeparent.appendChild(nodename)

                                #return node1
                                cbPrint("Armparent.")
                            else:
                                node1.appendChild(nodename)
                        else:
                            if object.name == "animnode":
                                cbPrint("Animnode.")
                            else:
                                node1.appendChild(nodename)
                        #return node1
            return node1




#test
        vs=doc.createElement("visual_scene")
        vs.setAttribute("id","scene")#doesnt matter what name we have here as long as it is the same for <scene>
        vs.setAttribute("name","scene")
        libvs.appendChild(vs)
        col.appendChild(libvs)
        for item in bpy.context.blend_data.groups:
            mesh = i.data
            if (i.type == "MESH"): 
                mat = mesh.materials[:]
            if item:
                ename=str(item.id_data.name)
                node1=doc.createElement("node")
                node1.setAttribute("id","%s"%(ename))
                node1.setIdAttribute('id')
            vs.appendChild(node1)
            objectl = []
            objectl = item.objects

            node1 = vsp(self, objectl)
            #exportnode settings
            ext1=doc.createElement("extra")
            tc3=doc.createElement("technique")
            tc3.setAttribute("profile","CryEngine")
            prop1=doc.createElement("properties")
            if self.is_cgf:
                pcgf=doc.createTextNode("fileType=cgf")
                prop1.appendChild(pcgf)
            if self.is_cga:
                pcga=doc.createTextNode("fileType=cgaanm")
                prop1.appendChild(pcga)
            if self.is_chrcaf:
                pchrcaf=doc.createTextNode("fileType=chrcaf")
                prop1.appendChild(pchrcaf)
            if self.donot_merge:
                pdnm=doc.createTextNode("DoNotMerge")
                prop1.appendChild(pdnm)
            tc3.appendChild(prop1)
            ext1.appendChild(tc3)
            node1.appendChild(ext1)
#end library_visual_scenes
#  <scene> nothing really changes here or rather it doesnt need to.
        scene=doc.createElement("scene")
        ivs=doc.createElement("instance_visual_scene")
        ivs.setAttribute("url","#scene")
        scene.appendChild(ivs)
        col.appendChild(scene)
#  <scene>
        # write to file
        write(self, doc, filepath, exe)

def save(self, context, exe):

        exp = ExportCrytekDae#(self,context)
        exp.execute(self, context, exe)

        return {'FINISHED'}  # so the script wont run after we have batch exported.

def menu_func_export(self, context):
    self.layout.operator(ExportCrytekDae.bl_idname, text="Export Crytek Dae")


def register():
    bpy.utils.register_class(ExportCrytekDae)
    bpy.types.INFO_MT_file_export.append(menu_func_export)

    bpy.utils.register_class(TriangulateMeError)
    bpy.utils.register_class(Error)

def unregister():
    bpy.utils.unregister_class(ExportCrytekDae)
    bpy.types.INFO_MT_file_export.remove(menu_func_export)
    bpy.utils.unregister_class(TriangulateMeError)
    bpy.utils.unregister_class(Error)

if __name__ == "__main__":
    register()

    # test call
    bpy.ops.export_mesh.crytekdae('INVOKE_DEFAULT')

