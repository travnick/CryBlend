#------------------------------------------------------------------------------
# Name:        hardbodyanimutils
# Purpose:     hardbody animation export functions
#
# Author:      Angelo J. Miner
#
# Created:     30/05/2012
# Copyright:   (c) Angelo J. Miner 2012
# License:     GPLv2+
#------------------------------------------------------------------------------
#!/usr/bin/env python


def convert_time(frx):
    s = ((fps_b * frx) / fps)
    return s


def extract_anilx(self, i):
    fcus = {}
    for fcu in curves:
        # location
        # X
        if fcu.data_path == 'location'and fcu.array_index == 0:
            anmlx = doc.createElement("animation")
            anmlx.setAttribute("id", "%s_location_X" % (i.name))
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
                intx += ("%s " % (keyx.interpolation))
                inpx += ("%s " % (time))
                outpx += ("%s " % (value))
                intangfirst = convert_time(khlx)
                outangfirst = convert_time(khrx)
                intangx += ("%s %s " % (intangfirst, khly))
                outtangx += ("%s %s " % (outangfirst, khry))
                ii += 1
            # input
            sinpx = doc.createElement("source")
            sinpx.setAttribute("id", "%s_location_X-input" % (i.name))
            inpxfa = doc.createElement("float_array")
            inpxfa.setAttribute("id", "%s_location_X-input-array" % (i.name))
            inpxfa.setAttribute("count", "%s" % (ii))
            sinpxdat = doc.createTextNode("%s" % (inpx))
            inpxfa.appendChild(sinpxdat)
            tcinpx = doc.createElement("technique_common")
            accinpx = doc.createElement("accessor")
            accinpx.setAttribute("source", "#%s_location_X-input-array"
                                 % (i.name))
            accinpx.setAttribute("count", "%s" % (ii))
            accinpx.setAttribute("stride", "1")
            parinpx = doc.createElement("param")
            parinpx.setAttribute("name", "TIME")
            parinpx.setAttribute("type", "float")
            accinpx.appendChild(parinpx)
            tcinpx.appendChild(accinpx)
            sinpx.appendChild(inpxfa)
            sinpx.appendChild(tcinpx)
            # output
            soutpx = doc.createElement("source")
            soutpx.setAttribute("id", "%s_location_X-output" % (i.name))
            outpxfa = doc.createElement("float_array")
            outpxfa.setAttribute("id", "%s_location_X-output-array" % (i.name))
            outpxfa.setAttribute("count", "%s" % (ii))
            soutpxdat = doc.createTextNode("%s" % (outpx))
            outpxfa.appendChild(soutpxdat)
            tcoutpx = doc.createElement("technique_common")
            accoutpx = doc.createElement("accessor")
            accoutpx.setAttribute("source", "#%s_location_X-output-array"
                                  % (i.name))
            accoutpx.setAttribute("count", "%s" % (ii))
            accoutpx.setAttribute("stride", "1")
            paroutpx = doc.createElement("param")
            paroutpx.setAttribute("name", "VALUE")
            paroutpx.setAttribute("type", "float")
            accoutpx.appendChild(paroutpx)
            tcoutpx.appendChild(accoutpx)
            soutpx.appendChild(outpxfa)
            soutpx.appendChild(tcoutpx)
            # interpolation
            sintpx = doc.createElement("source")
            sintpx.setAttribute("id", "%s_location_X-interpolation" % (i.name))
            intpxfa = doc.createElement("Name_array")
            intpxfa.setAttribute("id", "%s_location_X-interpolation-array"
                                 % (i.name))
            intpxfa.setAttribute("count", "%s" % (ii))
            sintpxdat = doc.createTextNode("%s" % (intx))
            intpxfa.appendChild(sintpxdat)
            tcintpx = doc.createElement("technique_common")
            accintpx = doc.createElement("accessor")
            accintpx.setAttribute("source",
                                  "#%s_location_X-interpolation-array"
                                  % (i.name))
            accintpx.setAttribute("count", "%s" % (ii))
            accintpx.setAttribute("stride", "1")
            parintpx = doc.createElement("param")
            parintpx.setAttribute("name", "INTERPOLATION")
            parintpx.setAttribute("type", "name")
            accintpx.appendChild(parintpx)
            tcintpx.appendChild(accintpx)
            sintpx.appendChild(intpxfa)
            sintpx.appendChild(tcintpx)
            # intangent
            sintangpx = doc.createElement("source")
            sintangpx.setAttribute("id", "%s_location_X-intangent" % (i.name))
            intangpxfa = doc.createElement("float_array")
            intangpxfa.setAttribute("id", "%s_location_X-intangent-array"
                                    % (i.name))
            intangpxfa.setAttribute("count", "%s" % ((ii) * 2))
            sintangpxdat = doc.createTextNode("%s" % (intangx))
            intangpxfa.appendChild(sintangpxdat)
            tcintangpx = doc.createElement("technique_common")
            accintangpx = doc.createElement("accessor")
            accintangpx.setAttribute("source", "#%s_location_X-intangent-array"
                                     % (i.name))
            accintangpx.setAttribute("count", "%s" % (ii))
            accintangpx.setAttribute("stride", "2")
            parintangpx = doc.createElement("param")
            parintangpx.setAttribute("name", "X")
            parintangpx.setAttribute("type", "float")
            parintangpxy = doc.createElement("param")
            parintangpxy.setAttribute("name", "Y")
            parintangpxy.setAttribute("type", "float")
            accintangpx.appendChild(parintangpx)
            accintangpx.appendChild(parintangpxy)
            tcintangpx.appendChild(accintangpx)
            sintangpx.appendChild(intangpxfa)
            sintangpx.appendChild(tcintangpx)
            # outtangent
            soutangpx = doc.createElement("source")
            soutangpx.setAttribute("id", "%s_location_X-outtangent" % (i.name))
            outangpxfa = doc.createElement("float_array")
            outangpxfa.setAttribute("id", "%s_location_X-outtangent-array"
                                    % (i.name))
            outangpxfa.setAttribute("count", "%s" % ((ii) * 2))
            soutangpxdat = doc.createTextNode("%s" % (outtangx))
            outangpxfa.appendChild(soutangpxdat)
            tcoutangpx = doc.createElement("technique_common")
            accoutangpx = doc.createElement("accessor")
            accoutangpx.setAttribute("source",
                                     "#%s_location_X-outtangent-array"
                                     % (i.name))
            accoutangpx.setAttribute("count", "%s" % (ii))
            accoutangpx.setAttribute("stride", "2")
            paroutangpx = doc.createElement("param")
            paroutangpx.setAttribute("name", "X")
            paroutangpx.setAttribute("type", "float")
            paroutangpxy = doc.createElement("param")
            paroutangpxy.setAttribute("name", "Y")
            paroutangpxy.setAttribute("type", "float")
            accoutangpx.appendChild(paroutangpx)
            accoutangpx.appendChild(paroutangpxy)
            tcoutangpx.appendChild(accoutangpx)
            soutangpx.appendChild(outangpxfa)
            soutangpx.appendChild(tcoutangpx)
            # sampler
            samx = doc.createElement("sampler")
            samx.setAttribute("id", "%s_location_X-sampler" % (i.name))
            semip = doc.createElement("input")
            semip.setAttribute("semantic", "INPUT")
            semip.setAttribute("source", "#%s_location_X-input" % (i.name))
            semop = doc.createElement("input")
            semop.setAttribute("semantic", "OUTPUT")
            semop.setAttribute("source", "#%s_location_X-output" % (i.name))
            seminter = doc.createElement("input")
            seminter.setAttribute("semantic", "INTERPOLATION")
            seminter.setAttribute("source", "#%s_location_X-interpolation"
                                  % (i.name))
            semintang = doc.createElement("input")
            semintang.setAttribute("semantic", "IN_TANGENT")
            semintang.setAttribute("source", "#%s_location_X-intangent"
                                   % (i.name))
            semoutang = doc.createElement("input")
            semoutang.setAttribute("semantic", "OUT_TANGENT")
            semoutang.setAttribute("source", "#%s_location_X-outtangent"
                                   % (i.name))
            samx.appendChild(semip)
            samx.appendChild(semop)
            samx.appendChild(seminter)
            samx.appendChild(semintang)
            samx.appendChild(semoutang)
            chanx = doc.createElement("channel")
            chanx.setAttribute("source", "#%s_location_X-sampler" % (i.name))
            chanx.setAttribute("target", "%s/translation.X" % (i.name))
            anmlx.appendChild(sinpx)
            anmlx.appendChild(soutpx)
            anmlx.appendChild(sintpx)
            anmlx.appendChild(sintangpx)
            anmlx.appendChild(soutangpx)
            anmlx.appendChild(samx)
            anmlx.appendChild(chanx)
            # libanm.appendChild(anmlx)
            print(ii)
            print(inpx)
            print(outpx)
            print(intx)
            print(intangx)
            print(outtangx)
            print("donex")
    return anmlx


def extract_anily(self, i):
    fcus = {}
    for fcu in curves:
            # Y
        if fcu.data_path == 'location'and fcu.array_index == 1:
            anmly = doc.createElement("animation")
            anmly.setAttribute("id", "%s_location_Y" % (i.name))
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
                inty += ("%s " % (key.interpolation))
                inpy += ("%s " % (time))
                outpy += ("%s " % (value))
                intangfirst = convert_time(khlx)
                outangfirst = convert_time(khrx)
                intangy += ("%s %s " % (intangfirst, khly))
                outtangy += ("%s %s " % (outangfirst, khry))
                ii += 1
            # input
            sinpy = doc.createElement("source")
            sinpy.setAttribute("id", "%s_location_Y-input" % (i.name))
            inpyfa = doc.createElement("float_array")
            inpyfa.setAttribute("id", "%s_location_Y-input-array" % (i.name))
            inpyfa.setAttribute("count", "%s" % (ii))
            sinpydat = doc.createTextNode("%s" % (inpy))
            inpyfa.appendChild(sinpydat)
            tcinpy = doc.createElement("technique_common")
            accinpy = doc.createElement("accessor")
            accinpy.setAttribute("source", "#%s_location_Y-input-array"
                                 % (i.name))
            accinpy.setAttribute("count", "%s" % (ii))
            accinpy.setAttribute("stride", "1")
            parinpy = doc.createElement("param")
            parinpy.setAttribute("name", "TIME")
            parinpy.setAttribute("type", "float")
            accinpy.appendChild(parinpy)
            tcinpy.appendChild(accinpy)
            sinpy.appendChild(inpyfa)
            sinpy.appendChild(tcinpy)
            # output
            soutpy = doc.createElement("source")
            soutpy.setAttribute("id", "%s_location_Y-output" % (i.name))
            outpyfa = doc.createElement("float_array")
            outpyfa.setAttribute("id", "%s_location_Y-output-array" % (i.name))
            outpyfa.setAttribute("count", "%s" % (ii))
            soutpydat = doc.createTextNode("%s" % (outpy))
            outpyfa.appendChild(soutpydat)
            tcoutpy = doc.createElement("technique_common")
            accoutpy = doc.createElement("accessor")
            accoutpy.setAttribute("source", "#%s_location_Y-output-array"
                                  % (i.name))
            accoutpy.setAttribute("count", "%s" % (ii))
            accoutpy.setAttribute("stride", "1")
            paroutpy = doc.createElement("param")
            paroutpy.setAttribute("name", "VALUE")
            paroutpy.setAttribute("type", "float")
            accoutpy.appendChild(paroutpy)
            tcoutpy.appendChild(accoutpy)
            soutpy.appendChild(outpyfa)
            soutpy.appendChild(tcoutpy)
            # interpolation
            sintpy = doc.createElement("source")
            sintpy.setAttribute("id", "%s_location_Y-interpolation" % (i.name))
            intpyfa = doc.createElement("Name_array")
            intpyfa.setAttribute("id", "%s_location_Y-interpolation-array"
                                 % (i.name))
            intpyfa.setAttribute("count", "%s" % (ii))
            sintpydat = doc.createTextNode("%s" % (inty))
            intpyfa.appendChild(sintpydat)
            tcintpy = doc.createElement("technique_common")
            accintpy = doc.createElement("accessor")
            accintpy.setAttribute("source",
                                  "#%s_location_Y-interpolation-array"
                                  % (i.name))
            accintpy.setAttribute("count", "%s" % (ii))
            accintpy.setAttribute("stride", "1")
            parintpy = doc.createElement("param")
            parintpy.setAttribute("name", "INTERPOLATION")
            parintpy.setAttribute("type", "name")
            accintpy.appendChild(parintpy)
            tcintpy.appendChild(accintpy)
            sintpy.appendChild(intpyfa)
            sintpy.appendChild(tcintpy)
            # intangent
            sintangpy = doc.createElement("source")
            sintangpy.setAttribute("id", "%s_location_Y-intangent" % (i.name))
            intangpyfa = doc.createElement("float_array")
            intangpyfa.setAttribute("id", "%s_location_Y-intangent-array"
                                    % (i.name))
            intangpyfa.setAttribute("count", "%s" % ((ii) * 2))
            sintangpydat = doc.createTextNode("%s" % (intangy))
            intangpyfa.appendChild(sintangpydat)
            tcintangpy = doc.createElement("technique_common")
            accintangpy = doc.createElement("accessor")
            accintangpy.setAttribute("source", "#%s_location_Y-intangent-array"
                                     % (i.name))
            accintangpy.setAttribute("count", "%s" % (ii))
            accintangpy.setAttribute("stride", "2")
            parintangpy = doc.createElement("param")
            parintangpy.setAttribute("name", "X")
            parintangpy.setAttribute("type", "float")
            parintangpyy = doc.createElement("param")
            parintangpyy.setAttribute("name", "Y")
            parintangpyy.setAttribute("type", "float")
            accintangpy.appendChild(parintangpy)
            accintangpy.appendChild(parintangpyy)
            tcintangpy.appendChild(accintangpy)
            sintangpy.appendChild(intangpyfa)
            sintangpy.appendChild(tcintangpy)
            # outtangent
            soutangpy = doc.createElement("source")
            soutangpy.setAttribute("id", "%s_location_Y-outtangent" % (i.name))
            outangpyfa = doc.createElement("float_array")
            outangpyfa.setAttribute("id", "%s_location_Y-outtangent-array"
                                    % (i.name))
            outangpyfa.setAttribute("count", "%s" % ((ii) * 2))
            soutangpydat = doc.createTextNode("%s" % (outtangy))
            outangpyfa.appendChild(soutangpydat)
            tcoutangpy = doc.createElement("technique_common")
            accoutangpy = doc.createElement("accessor")
            accoutangpy.setAttribute("source",
                                     "#%s_location_Y-outtangent-array"
                                     % (i.name))
            accoutangpy.setAttribute("count", "%s" % (ii))
            accoutangpy.setAttribute("stride", "2")
            paroutangpy = doc.createElement("param")
            paroutangpy.setAttribute("name", "X")
            paroutangpy.setAttribute("type", "float")
            paroutangpyy = doc.createElement("param")
            paroutangpyy.setAttribute("name", "Y")
            paroutangpyy.setAttribute("type", "float")
            accoutangpy.appendChild(paroutangpy)
            accoutangpy.appendChild(paroutangpyy)
            tcoutangpy.appendChild(accoutangpy)
            soutangpy.appendChild(outangpyfa)
            soutangpy.appendChild(tcoutangpy)
            # sampler
            samy = doc.createElement("sampler")
            samy.setAttribute("id", "%s_location_Y-sampler" % (i.name))
            semip = doc.createElement("input")
            semip.setAttribute("semantic", "INPUT")
            semip.setAttribute("source", "#%s_location_Y-input" % (i.name))
            semop = doc.createElement("input")
            semop.setAttribute("semantic", "OUTPUT")
            semop.setAttribute("source", "#%s_location_Y-output" % (i.name))
            seminter = doc.createElement("input")
            seminter.setAttribute("semantic", "INTERPOLATION")
            seminter.setAttribute("source", "#%s_location_Y-interpolation"
                                  % (i.name))
            semintang = doc.createElement("input")
            semintang.setAttribute("semantic", "IN_TANGENT")
            semintang.setAttribute("source", "#%s_location_Y-intangent"
                                   % (i.name))
            semoutang = doc.createElement("input")
            semoutang.setAttribute("semantic", "OUT_TANGENT")
            semoutang.setAttribute("source", "#%s_location_Y-outtangent"
                                   % (i.name))
            samy.appendChild(semip)
            samy.appendChild(semop)
            samy.appendChild(seminter)
            samy.appendChild(semintang)
            samy.appendChild(semoutang)
            chany = doc.createElement("channel")
            chany.setAttribute("source", "#%s_location_Y-sampler" % (i.name))
            chany.setAttribute("target", "%s/translation.Y" % (i.name))
            anmly.appendChild(sinpy)
            anmly.appendChild(soutpy)
            anmly.appendChild(sintpy)
            anmly.appendChild(sintangpy)
            anmly.appendChild(soutangpy)
            anmly.appendChild(samy)
            anmly.appendChild(chany)
            # libanm.appendChild(anmly)
            print(ii)
            print(inpy)
            print(outpy)
            print(inty)
            print(intangy)
            print(outtangy)
            print("doney")
    return anmly


def extract_anilz(self, i):
    fcus = {}
    for fcu in curves:
        # Z
        if fcu.data_path == 'location'and fcu.array_index == 2:
            anmlz = doc.createElement("animation")
            anmlz.setAttribute("id", "%s_location_Z" % (i.name))
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
                intz += ("%s " % (key.interpolation))
                inpz += ("%s " % (time))
                outpz += ("%s " % (value))
                intangfirst = convert_time(khlx)
                outangfirst = convert_time(khrx)
                intangz += ("%s %s " % (intangfirst, khly))
                outtangz += ("%s %s " % (outangfirst, khry))
                ii += 1
            # input
            sinpz = doc.createElement("source")
            sinpz.setAttribute("id", "%s_location_Z-input" % (i.name))
            inpzfa = doc.createElement("float_array")
            inpzfa.setAttribute("id", "%s_location_Z-input-array" % (i.name))
            inpzfa.setAttribute("count", "%s" % (ii))
            sinpzdat = doc.createTextNode("%s" % (inpz))
            inpzfa.appendChild(sinpzdat)
            tcinpz = doc.createElement("technique_common")
            accinpz = doc.createElement("accessor")
            accinpz.setAttribute("source", "#%s_location_Z-input-array"
                                 % (i.name))
            accinpz.setAttribute("count", "%s" % (ii))
            accinpz.setAttribute("stride", "1")
            parinpz = doc.createElement("param")
            parinpz.setAttribute("name", "TIME")
            parinpz.setAttribute("type", "float")
            accinpz.appendChild(parinpz)
            tcinpz.appendChild(accinpz)
            sinpz.appendChild(inpzfa)
            sinpz.appendChild(tcinpz)
            # output
            soutpz = doc.createElement("source")
            soutpz.setAttribute("id", "%s_location_Z-output" % (i.name))
            outpzfa = doc.createElement("float_array")
            outpzfa.setAttribute("id", "%s_location_Z-output-array" % (i.name))
            outpzfa.setAttribute("count", "%s" % (ii))
            soutpzdat = doc.createTextNode("%s" % (outpz))
            outpzfa.appendChild(soutpzdat)
            tcoutpz = doc.createElement("technique_common")
            accoutpz = doc.createElement("accessor")
            accoutpz.setAttribute("source", "#%s_location_Z-output-array"
                                  % (i.name))
            accoutpz.setAttribute("count", "%s" % (ii))
            accoutpz.setAttribute("stride", "1")
            paroutpz = doc.createElement("param")
            paroutpz.setAttribute("name", "VALUE")
            paroutpz.setAttribute("type", "float")
            accoutpz.appendChild(paroutpz)
            tcoutpz.appendChild(accoutpz)
            soutpz.appendChild(outpzfa)
            soutpz.appendChild(tcoutpz)
            # interpolation
            sintpz = doc.createElement("source")
            sintpz.setAttribute("id", "%s_location_Z-interpolation" % (i.name))
            intpzfa = doc.createElement("Name_array")
            intpzfa.setAttribute("id", "%s_location_Z-interpolation-array"
                                 % (i.name))
            intpzfa.setAttribute("count", "%s" % (ii))
            sintpzdat = doc.createTextNode("%s" % (intz))
            intpzfa.appendChild(sintpzdat)
            tcintpz = doc.createElement("technique_common")
            accintpz = doc.createElement("accessor")
            accintpz.setAttribute("source",
                                  "#%s_location_Z-interpolation-array"
                                  % (i.name))
            accintpz.setAttribute("count", "%s" % (ii))
            accintpz.setAttribute("stride", "1")
            parintpz = doc.createElement("param")
            parintpz.setAttribute("name", "INTERPOLATION")
            parintpz.setAttribute("type", "name")
            accintpz.appendChild(parintpz)
            tcintpz.appendChild(accintpz)
            sintpz.appendChild(intpzfa)
            sintpz.appendChild(tcintpz)
            # intangent
            sintangpz = doc.createElement("source")
            sintangpz.setAttribute("id", "%s_location_Z-intangent" % (i.name))
            intangpzfa = doc.createElement("float_array")
            intangpzfa.setAttribute("id", "%s_location_Z-intangent-array"
                                    % (i.name))
            intangpzfa.setAttribute("count", "%s" % ((ii) * 2))
            sintangpzdat = doc.createTextNode("%s" % (intangz))
            intangpzfa.appendChild(sintangpzdat)
            tcintangpz = doc.createElement("technique_common")
            accintangpz = doc.createElement("accessor")
            accintangpz.setAttribute("source", "#%s_location_Z-intangent-array"
                                     % (i.name))
            accintangpz.setAttribute("count", "%s" % (ii))
            accintangpz.setAttribute("stride", "2")
            parintangpz = doc.createElement("param")
            parintangpz.setAttribute("name", "X")
            parintangpz.setAttribute("type", "float")
            parintangpyz = doc.createElement("param")
            parintangpyz.setAttribute("name", "Y")
            parintangpyz.setAttribute("type", "float")
            accintangpz.appendChild(parintangpz)
            accintangpz.appendChild(parintangpyz)
            tcintangpz.appendChild(accintangpz)
            sintangpz.appendChild(intangpzfa)
            sintangpz.appendChild(tcintangpz)
            # outtangent
            soutangpz = doc.createElement("source")
            soutangpz.setAttribute("id", "%s_location_Z-outtangent" % (i.name))
            outangpzfa = doc.createElement("float_array")
            outangpzfa.setAttribute("id", "%s_location_Z-outtangent-array"
                                    % (i.name))
            outangpzfa.setAttribute("count", "%s" % ((ii) * 2))
            soutangpzdat = doc.createTextNode("%s" % (outtangz))
            outangpzfa.appendChild(soutangpzdat)
            tcoutangpz = doc.createElement("technique_common")
            accoutangpz = doc.createElement("accessor")
            accoutangpz.setAttribute("source",
                                     "#%s_location_Z-outtangent-array"
                                     % (i.name))
            accoutangpz.setAttribute("count", "%s" % (ii))
            accoutangpz.setAttribute("stride", "2")
            paroutangpz = doc.createElement("param")
            paroutangpz.setAttribute("name", "X")
            paroutangpz.setAttribute("type", "float")
            paroutangpyz = doc.createElement("param")
            paroutangpyz.setAttribute("name", "Y")
            paroutangpyz.setAttribute("type", "float")
            accoutangpz.appendChild(paroutangpz)
            accoutangpz.appendChild(paroutangpyz)
            tcoutangpz.appendChild(accoutangpz)
            soutangpz.appendChild(outangpzfa)
            soutangpz.appendChild(tcoutangpz)
            # sampler
            samz = doc.createElement("sampler")
            samz.setAttribute("id", "%s_location_Z-sampler" % (i.name))
            semip = doc.createElement("input")
            semip.setAttribute("semantic", "INPUT")
            semip.setAttribute("source", "#%s_location_Z-input" % (i.name))
            semop = doc.createElement("input")
            semop.setAttribute("semantic", "OUTPUT")
            semop.setAttribute("source", "#%s_location_Z-output" % (i.name))
            seminter = doc.createElement("input")
            seminter.setAttribute("semantic", "INTERPOLATION")
            seminter.setAttribute("source", "#%s_location_Z-interpolation"
                                  % (i.name))
            semintang = doc.createElement("input")
            semintang.setAttribute("semantic", "IN_TANGENT")
            semintang.setAttribute("source", "#%s_location_Z-intangent"
                                   % (i.name))
            semoutang = doc.createElement("input")
            semoutang.setAttribute("semantic", "OUT_TANGENT")
            semoutang.setAttribute("source", "#%s_location_Z-outtangent"
                                   % (i.name))
            samz.appendChild(semip)
            samz.appendChild(semop)
            samz.appendChild(seminter)
            samz.appendChild(semintang)
            samz.appendChild(semoutang)
            chanz = doc.createElement("channel")
            chanz.setAttribute("source", "#%s_location_Z-sampler" % (i.name))
            chanz.setAttribute("target", "%s/translation.Z" % (i.name))
            anmlz.appendChild(sinpz)
            anmlz.appendChild(soutpz)
            anmlz.appendChild(sintpz)
            anmlz.appendChild(sintangpz)
            anmlz.appendChild(soutangpz)
            anmlz.appendChild(samz)
            anmlz.appendChild(chanz)
            # libanm.appendChild(anmlz)
            print(ii)
            print(inpz)
            print(outpz)
            print(intz)
            print(intangz)
            print(outtangz)
            print("donez")
    return anmlz


def extract_anirx(self, i):
    fcus = {}
    for fcu in curves:
# rotation_euler
        # X
        if fcu.data_path == 'rotation_euler'and fcu.array_index == 0:
            anmrx = doc.createElement("animation")
            anmrx.setAttribute("id", "%s_rotation_euler_X" % (i.name))
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
                intx += ("%s " % (keyx.interpolation))
                inpx += ("%s " % (time))
                outpx += ("%s " % (value * utils.toD))
                intangfirst = convert_time(khlx)
                outangfirst = convert_time(khrx)
                intangx += ("%s %s " % (intangfirst, khly))
                outtangx += ("%s %s " % (outangfirst, khry))
                ii += 1
            # input
            sinpx = doc.createElement("source")
            sinpx.setAttribute("id", "%s_rotation_euler_X-input" % (i.name))
            inpxfa = doc.createElement("float_array")
            inpxfa.setAttribute("id", "%s_rotation_euler_X-input-array"
                                % (i.name))
            inpxfa.setAttribute("count", "%s" % (ii))
            sinpxdat = doc.createTextNode("%s" % (inpx))
            inpxfa.appendChild(sinpxdat)
            tcinpx = doc.createElement("technique_common")
            accinpx = doc.createElement("accessor")
            accinpx.setAttribute("source", "#%s_rotation_euler_X-input-array"
                                 % (i.name))
            accinpx.setAttribute("count", "%s" % (ii))
            accinpx.setAttribute("stride", "1")
            parinpx = doc.createElement("param")
            parinpx.setAttribute("name", "TIME")
            parinpx.setAttribute("type", "float")
            accinpx.appendChild(parinpx)
            tcinpx.appendChild(accinpx)
            sinpx.appendChild(inpxfa)
            sinpx.appendChild(tcinpx)
            # output
            soutpx = doc.createElement("source")
            soutpx.setAttribute("id", "%s_rotation_euler_X-output" % (i.name))
            outpxfa = doc.createElement("float_array")
            outpxfa.setAttribute("id", "%s_rotation_euler_X-output-array"
                                 % (i.name))
            outpxfa.setAttribute("count", "%s" % (ii))
            soutpxdat = doc.createTextNode("%s" % (outpx))
            outpxfa.appendChild(soutpxdat)
            tcoutpx = doc.createElement("technique_common")
            accoutpx = doc.createElement("accessor")
            accoutpx.setAttribute("source", "#%s_rotation_euler_X-output-array"
                                  % (i.name))
            accoutpx.setAttribute("count", "%s" % (ii))
            accoutpx.setAttribute("stride", "1")
            paroutpx = doc.createElement("param")
            paroutpx.setAttribute("name", "VALUE")
            paroutpx.setAttribute("type", "float")
            accoutpx.appendChild(paroutpx)
            tcoutpx.appendChild(accoutpx)
            soutpx.appendChild(outpxfa)
            soutpx.appendChild(tcoutpx)
            # interpolation
            sintpx = doc.createElement("source")
            sintpx.setAttribute("id", "%s_rotation_euler_X-interpolation"
                                % (i.name))
            intpxfa = doc.createElement("Name_array")
            intpxfa.setAttribute("id",
                                 "%s_rotation_euler_X-interpolation-array"
                                 % (i.name))
            intpxfa.setAttribute("count", "%s" % (ii))
            sintpxdat = doc.createTextNode("%s" % (intx))
            intpxfa.appendChild(sintpxdat)
            tcintpx = doc.createElement("technique_common")
            accintpx = doc.createElement("accessor")
            accintpx.setAttribute("source",
                                  "#%s_rotation_euler_X-interpolation-array"
                                  % (i.name))
            accintpx.setAttribute("count", "%s" % (ii))
            accintpx.setAttribute("stride", "1")
            parintpx = doc.createElement("param")
            parintpx.setAttribute("name", "INTERPOLATION")
            parintpx.setAttribute("type", "name")
            accintpx.appendChild(parintpx)
            tcintpx.appendChild(accintpx)
            sintpx.appendChild(intpxfa)
            sintpx.appendChild(tcintpx)
            # intangent
            sintangpx = doc.createElement("source")
            sintangpx.setAttribute("id", "%s_rotation_euler_X-intangent"
                                   % (i.name))
            intangpxfa = doc.createElement("float_array")
            intangpxfa.setAttribute("id", "%s_rotation_euler_X-intangent-array"
                                    % (i.name))
            intangpxfa.setAttribute("count", "%s" % ((ii) * 2))
            sintangpxdat = doc.createTextNode("%s" % (intangx))
            intangpxfa.appendChild(sintangpxdat)
            tcintangpx = doc.createElement("technique_common")
            accintangpx = doc.createElement("accessor")
            accintangpx.setAttribute("source",
                                     "#%s_rotation_euler_X-intangent-array"
                                     % (i.name))
            accintangpx.setAttribute("count", "%s" % (ii))
            accintangpx.setAttribute("stride", "2")
            parintangpx = doc.createElement("param")
            parintangpx.setAttribute("name", "X")
            parintangpx.setAttribute("type", "float")
            parintangpxy = doc.createElement("param")
            parintangpxy.setAttribute("name", "Y")
            parintangpxy.setAttribute("type", "float")
            accintangpx.appendChild(parintangpx)
            accintangpx.appendChild(parintangpxy)
            tcintangpx.appendChild(accintangpx)
            sintangpx.appendChild(intangpxfa)
            sintangpx.appendChild(tcintangpx)
            # outtangent
            soutangpx = doc.createElement("source")
            soutangpx.setAttribute("id", "%s_rotation_euler_X-outtangent"
                                   % (i.name))
            outangpxfa = doc.createElement("float_array")
            outangpxfa.setAttribute("id",
                                    "%s_rotation_euler_X-outtangent-array"
                                    % (i.name))
            outangpxfa.setAttribute("count", "%s" % ((ii) * 2))
            soutangpxdat = doc.createTextNode("%s" % (outtangx))
            outangpxfa.appendChild(soutangpxdat)
            tcoutangpx = doc.createElement("technique_common")
            accoutangpx = doc.createElement("accessor")
            accoutangpx.setAttribute("source",
                                     "#%s_rotation_euler_X-outtangent-array"
                                     % (i.name))
            accoutangpx.setAttribute("count", "%s" % (ii))
            accoutangpx.setAttribute("stride", "2")
            paroutangpx = doc.createElement("param")
            paroutangpx.setAttribute("name", "X")
            paroutangpx.setAttribute("type", "float")
            paroutangpxy = doc.createElement("param")
            paroutangpxy.setAttribute("name", "Y")
            paroutangpxy.setAttribute("type", "float")
            accoutangpx.appendChild(paroutangpx)
            accoutangpx.appendChild(paroutangpxy)
            tcoutangpx.appendChild(accoutangpx)
            soutangpx.appendChild(outangpxfa)
            soutangpx.appendChild(tcoutangpx)
            # sampler
            samx = doc.createElement("sampler")
            samx.setAttribute("id", "%s_rotation_euler_X-sampler" % (i.name))
            semip = doc.createElement("input")
            semip.setAttribute("semantic", "INPUT")
            semip.setAttribute("source", "#%s_rotation_euler_X-input"
                               % (i.name))
            semop = doc.createElement("input")
            semop.setAttribute("semantic", "OUTPUT")
            semop.setAttribute("source", "#%s_rotation_euler_X-output"
                               % (i.name))
            seminter = doc.createElement("input")
            seminter.setAttribute("semantic", "INTERPOLATION")
            seminter.setAttribute("source",
                                  "#%s_rotation_euler_X-interpolation"
                                  % (i.name))
            semintang = doc.createElement("input")
            semintang.setAttribute("semantic", "IN_TANGENT")
            semintang.setAttribute("source", "#%s_rotation_euler_X-intangent"
                                   % (i.name))
            semoutang = doc.createElement("input")
            semoutang.setAttribute("semantic", "OUT_TANGENT")
            semoutang.setAttribute("source", "#%s_rotation_euler_X-outtangent"
                                   % (i.name))
            samx.appendChild(semip)
            samx.appendChild(semop)
            samx.appendChild(seminter)
            samx.appendChild(semintang)
            samx.appendChild(semoutang)
            chanx = doc.createElement("channel")
            chanx.setAttribute("source", "#%s_rotation_euler_X-sampler"
                               % (i.name))
            chanx.setAttribute("target", "%s/rotation_x.ANGLE" % (i.name))
            anmrx.appendChild(sinpx)
            anmrx.appendChild(soutpx)
            anmrx.appendChild(sintpx)
            anmrx.appendChild(sintangpx)
            anmrx.appendChild(soutangpx)
            anmrx.appendChild(samx)
            anmrx.appendChild(chanx)
            # libanm.appendChild(anmrx)
            print(ii)
            print(inpx)
            print(outpx)
            print(intx)
            print(intangx)
            print(outtangx)
            print("donerotx")
    return anmrx


def extract_aniry(self, i):
    fcus = {}
    for fcu in curves:
            # Y
        if fcu.data_path == 'rotation_euler'and fcu.array_index == 1:
            anmry = doc.createElement("animation")
            anmry.setAttribute("id", "%s_rotation_euler_Y" % (i.name))
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
                inty += ("%s " % (key.interpolation))
                inpy += ("%s " % (time))
                outpy += ("%s " % (value * utils.toD))
                intangfirst = convert_time(khlx)
                outangfirst = convert_time(khrx)
                intangy += ("%s %s " % (intangfirst, khly))
                outtangy += ("%s %s " % (outangfirst, khry))
                ii += 1
            # input
            sinpy = doc.createElement("source")
            sinpy.setAttribute("id", "%s_rotation_euler_Y-input" % (i.name))
            inpyfa = doc.createElement("float_array")
            inpyfa.setAttribute("id", "%s_rotation_euler_Y-input-array"
                                % (i.name))
            inpyfa.setAttribute("count", "%s" % (ii))
            sinpydat = doc.createTextNode("%s" % (inpy))
            inpyfa.appendChild(sinpydat)
            tcinpy = doc.createElement("technique_common")
            accinpy = doc.createElement("accessor")
            accinpy.setAttribute("source", "#%s_rotation_euler_Y-input-array"
                                 % (i.name))
            accinpy.setAttribute("count", "%s" % (ii))
            accinpy.setAttribute("stride", "1")
            parinpy = doc.createElement("param")
            parinpy.setAttribute("name", "TIME")
            parinpy.setAttribute("type", "float")
            accinpy.appendChild(parinpy)
            tcinpy.appendChild(accinpy)
            sinpy.appendChild(inpyfa)
            sinpy.appendChild(tcinpy)
            # output
            soutpy = doc.createElement("source")
            soutpy.setAttribute("id", "%s_rotation_euler_Y-output" % (i.name))
            outpyfa = doc.createElement("float_array")
            outpyfa.setAttribute("id", "%s_rotation_euler_Y-output-array"
                                 % (i.name))
            outpyfa.setAttribute("count", "%s" % (ii))
            soutpydat = doc.createTextNode("%s" % (outpy))
            outpyfa.appendChild(soutpydat)
            tcoutpy = doc.createElement("technique_common")
            accoutpy = doc.createElement("accessor")
            accoutpy.setAttribute("source", "#%s_rotation_euler_Y-output-array"
                                  % (i.name))
            accoutpy.setAttribute("count", "%s" % (ii))
            accoutpy.setAttribute("stride", "1")
            paroutpy = doc.createElement("param")
            paroutpy.setAttribute("name", "VALUE")
            paroutpy.setAttribute("type", "float")
            accoutpy.appendChild(paroutpy)
            tcoutpy.appendChild(accoutpy)
            soutpy.appendChild(outpyfa)
            soutpy.appendChild(tcoutpy)
            # interpolation
            sintpy = doc.createElement("source")
            sintpy.setAttribute("id", "%s_rotation_euler_Y-interpolation"
                                % (i.name))
            intpyfa = doc.createElement("Name_array")
            intpyfa.setAttribute("id",
                                 "%s_rotation_euler_Y-interpolation-array"
                                 % (i.name))
            intpyfa.setAttribute("count", "%s" % (ii))
            sintpydat = doc.createTextNode("%s" % (inty))
            intpyfa.appendChild(sintpydat)
            tcintpy = doc.createElement("technique_common")
            accintpy = doc.createElement("accessor")
            accintpy.setAttribute("source",
                                  "#%s_rotation_euler_Y-interpolation-array"
                                  % (i.name))
            accintpy.setAttribute("count", "%s" % (ii))
            accintpy.setAttribute("stride", "1")
            parintpy = doc.createElement("param")
            parintpy.setAttribute("name", "INTERPOLATION")
            parintpy.setAttribute("type", "name")
            accintpy.appendChild(parintpy)
            tcintpy.appendChild(accintpy)
            sintpy.appendChild(intpyfa)
            sintpy.appendChild(tcintpy)
            # intangent
            sintangpy = doc.createElement("source")
            sintangpy.setAttribute("id", "%s_rotation_euler_Y-intangent"
                                   % (i.name))
            intangpyfa = doc.createElement("float_array")
            intangpyfa.setAttribute("id", "%s_rotation_euler_Y-intangent-array"
                                    % (i.name))
            intangpyfa.setAttribute("count", "%s" % ((ii) * 2))
            sintangpydat = doc.createTextNode("%s" % (intangy))
            intangpyfa.appendChild(sintangpydat)
            tcintangpy = doc.createElement("technique_common")
            accintangpy = doc.createElement("accessor")
            accintangpy.setAttribute("source",
                                     "#%s_rotation_euler_Y-intangent-array"
                                     % (i.name))
            accintangpy.setAttribute("count", "%s" % (ii))
            accintangpy.setAttribute("stride", "2")
            parintangpy = doc.createElement("param")
            parintangpy.setAttribute("name", "X")
            parintangpy.setAttribute("type", "float")
            parintangpyy = doc.createElement("param")
            parintangpyy.setAttribute("name", "Y")
            parintangpyy.setAttribute("type", "float")
            accintangpy.appendChild(parintangpy)
            accintangpy.appendChild(parintangpyy)
            tcintangpy.appendChild(accintangpy)
            sintangpy.appendChild(intangpyfa)
            sintangpy.appendChild(tcintangpy)
            # outtangent
            soutangpy = doc.createElement("source")
            soutangpy.setAttribute("id", "%s_rotation_euler_Y-outtangent"
                                   % (i.name))
            outangpyfa = doc.createElement("float_array")
            outangpyfa.setAttribute("id",
                                    "%s_rotation_euler_Y-outtangent-array"
                                    % (i.name))
            outangpyfa.setAttribute("count", "%s" % ((ii) * 2))
            soutangpydat = doc.createTextNode("%s" % (outtangy))
            outangpyfa.appendChild(soutangpydat)
            tcoutangpy = doc.createElement("technique_common")
            accoutangpy = doc.createElement("accessor")
            accoutangpy.setAttribute("source",
                                     "#%s_rotation_euler_Y-outtangent-array"
                                     % (i.name))
            accoutangpy.setAttribute("count", "%s" % (ii))
            accoutangpy.setAttribute("stride", "2")
            paroutangpy = doc.createElement("param")
            paroutangpy.setAttribute("name", "X")
            paroutangpy.setAttribute("type", "float")
            paroutangpyy = doc.createElement("param")
            paroutangpyy.setAttribute("name", "Y")
            paroutangpyy.setAttribute("type", "float")
            accoutangpy.appendChild(paroutangpy)
            accoutangpy.appendChild(paroutangpyy)
            tcoutangpy.appendChild(accoutangpy)
            soutangpy.appendChild(outangpyfa)
            soutangpy.appendChild(tcoutangpy)
            # sampler
            samy = doc.createElement("sampler")
            samy.setAttribute("id", "%s_rotation_euler_Y-sampler" % (i.name))
            semip = doc.createElement("input")
            semip.setAttribute("semantic", "INPUT")
            semip.setAttribute("source", "#%s_rotation_euler_Y-input"
                               % (i.name))
            semop = doc.createElement("input")
            semop.setAttribute("semantic", "OUTPUT")
            semop.setAttribute("source", "#%s_rotation_euler_Y-output"
                               % (i.name))
            seminter = doc.createElement("input")
            seminter.setAttribute("semantic", "INTERPOLATION")
            seminter.setAttribute("source",
                                  "#%s_rotation_euler_Y-interpolation"
                                  % (i.name))
            semintang = doc.createElement("input")
            semintang.setAttribute("semantic", "IN_TANGENT")
            semintang.setAttribute("source", "#%s_rotation_euler_Y-intangent"
                                   % (i.name))
            semoutang = doc.createElement("input")
            semoutang.setAttribute("semantic", "OUT_TANGENT")
            semoutang.setAttribute("source", "#%s_rotation_euler_Y-outtangent"
                                   % (i.name))
            samy.appendChild(semip)
            samy.appendChild(semop)
            samy.appendChild(seminter)
            samy.appendChild(semintang)
            samy.appendChild(semoutang)
            chany = doc.createElement("channel")
            chany.setAttribute("source", "#%s_rotation_euler_Y-sampler"
                               % (i.name))
            chany.setAttribute("target", "%s/rotation_y.ANGLE" % (i.name))
            anmry.appendChild(sinpy)
            anmry.appendChild(soutpy)
            anmry.appendChild(sintpy)
            anmry.appendChild(sintangpy)
            anmry.appendChild(soutangpy)
            anmry.appendChild(samy)
            anmry.appendChild(chany)
            # libanm.appendChild(anmry)
            print(ii)
            print(inpy)
            print(outpy)
            print(inty)
            print(intangy)
            print(outtangy)
            print("doneroty")
    return anmry


def extract_anirz(self, i):
    fcus = {}
    for fcu in curves:
        # Z
        if fcu.data_path == 'rotation_euler'and fcu.array_index == 2:
            anmrz = doc.createElement("animation")
            anmrz.setAttribute("id", "%s_rotation_euler_Z" % (i.name))
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
                intz += ("%s " % (key.interpolation))
                inpz += ("%s " % (time))
                outpz += ("%s " % (value * utils.toD))
                intangfirst = convert_time(khlx)
                outangfirst = convert_time(khrx)
                intangz += ("%s %s " % (intangfirst, khly))
                outtangz += ("%s %s " % (outangfirst, khry))
                ii += 1
            # input
            sinpz = doc.createElement("source")
            sinpz.setAttribute("id", "%s_rotation_euler_Z-input" % (i.name))
            inpzfa = doc.createElement("float_array")
            inpzfa.setAttribute("id", "%s_rotation_euler_Z-input-array"
                                % (i.name))
            inpzfa.setAttribute("count", "%s" % (ii))
            sinpzdat = doc.createTextNode("%s" % (inpz))
            inpzfa.appendChild(sinpzdat)
            tcinpz = doc.createElement("technique_common")
            accinpz = doc.createElement("accessor")
            accinpz.setAttribute("source", "#%s_rotation_euler_Z-input-array"
                                 % (i.name))
            accinpz.setAttribute("count", "%s" % (ii))
            accinpz.setAttribute("stride", "1")
            parinpz = doc.createElement("param")
            parinpz.setAttribute("name", "TIME")
            parinpz.setAttribute("type", "float")
            accinpz.appendChild(parinpz)
            tcinpz.appendChild(accinpz)
            sinpz.appendChild(inpzfa)
            sinpz.appendChild(tcinpz)
            # output
            soutpz = doc.createElement("source")
            soutpz.setAttribute("id", "%s_rotation_euler_Z-output" % (i.name))
            outpzfa = doc.createElement("float_array")
            outpzfa.setAttribute("id", "%s_rotation_euler_Z-output-array"
                                 % (i.name))
            outpzfa.setAttribute("count", "%s" % (ii))
            soutpzdat = doc.createTextNode("%s" % (outpz))
            outpzfa.appendChild(soutpzdat)
            tcoutpz = doc.createElement("technique_common")
            accoutpz = doc.createElement("accessor")
            accoutpz.setAttribute("source", "#%s_rotation_euler_Z-output-array"
                                  % (i.name))
            accoutpz.setAttribute("count", "%s" % (ii))
            accoutpz.setAttribute("stride", "1")
            paroutpz = doc.createElement("param")
            paroutpz.setAttribute("name", "VALUE")
            paroutpz.setAttribute("type", "float")
            accoutpz.appendChild(paroutpz)
            tcoutpz.appendChild(accoutpz)
            soutpz.appendChild(outpzfa)
            soutpz.appendChild(tcoutpz)
            # interpolation
            sintpz = doc.createElement("source")
            sintpz.setAttribute("id", "%s_rotation_euler_Z-interpolation"
                                % (i.name))
            intpzfa = doc.createElement("Name_array")
            intpzfa.setAttribute("id",
                                 "%s_rotation_euler_Z-interpolation-array"
                                 % (i.name))
            intpzfa.setAttribute("count", "%s" % (ii))
            sintpzdat = doc.createTextNode("%s" % (intz))
            intpzfa.appendChild(sintpzdat)
            tcintpz = doc.createElement("technique_common")
            accintpz = doc.createElement("accessor")
            accintpz.setAttribute("source",
                                  "#%s_rotation_euler_Z-interpolation-array"
                                  % (i.name))
            accintpz.setAttribute("count", "%s" % (ii))
            accintpz.setAttribute("stride", "1")
            parintpz = doc.createElement("param")
            parintpz.setAttribute("name", "INTERPOLATION")
            parintpz.setAttribute("type", "name")
            accintpz.appendChild(parintpz)
            tcintpz.appendChild(accintpz)
            sintpz.appendChild(intpzfa)
            sintpz.appendChild(tcintpz)
            # intangent
            sintangpz = doc.createElement("source")
            sintangpz.setAttribute("id", "%s_rotation_euler_Z-intangent"
                                   % (i.name))
            intangpzfa = doc.createElement("float_array")
            intangpzfa.setAttribute("id", "%s_rotation_euler_Z-intangent-array"
                                    % (i.name))
            intangpzfa.setAttribute("count", "%s" % ((ii) * 2))
            sintangpzdat = doc.createTextNode("%s" % (intangz))
            intangpzfa.appendChild(sintangpzdat)
            tcintangpz = doc.createElement("technique_common")
            accintangpz = doc.createElement("accessor")
            accintangpz.setAttribute("source",
                                     "#%s_rotation_euler_Z-intangent-array"
                                     % (i.name))
            accintangpz.setAttribute("count", "%s" % (ii))
            accintangpz.setAttribute("stride", "2")
            parintangpz = doc.createElement("param")
            parintangpz.setAttribute("name", "X")
            parintangpz.setAttribute("type", "float")
            parintangpyz = doc.createElement("param")
            parintangpyz.setAttribute("name", "Y")
            parintangpyz.setAttribute("type", "float")
            accintangpz.appendChild(parintangpz)
            accintangpz.appendChild(parintangpyz)
            tcintangpz.appendChild(accintangpz)
            sintangpz.appendChild(intangpzfa)
            sintangpz.appendChild(tcintangpz)
            # outtangent
            soutangpz = doc.createElement("source")
            soutangpz.setAttribute("id", "%s_rotation_euler_Z-outtangent"
                                   % (i.name))
            outangpzfa = doc.createElement("float_array")
            outangpzfa.setAttribute("id",
                                    "%s_rotation_euler_Z-outtangent-array"
                                    % (i.name))
            outangpzfa.setAttribute("count", "%s" % ((ii) * 2))
            soutangpzdat = doc.createTextNode("%s" % (outtangz))
            outangpzfa.appendChild(soutangpzdat)
            tcoutangpz = doc.createElement("technique_common")
            accoutangpz = doc.createElement("accessor")
            accoutangpz.setAttribute("source",
                                     "#%s_rotation_euler_Z-outtangent-array"
                                     % (i.name))
            accoutangpz.setAttribute("count", "%s" % (ii))
            accoutangpz.setAttribute("stride", "2")
            paroutangpz = doc.createElement("param")
            paroutangpz.setAttribute("name", "X")
            paroutangpz.setAttribute("type", "float")
            paroutangpyz = doc.createElement("param")
            paroutangpyz.setAttribute("name", "Y")
            paroutangpyz.setAttribute("type", "float")
            accoutangpz.appendChild(paroutangpz)
            accoutangpz.appendChild(paroutangpyz)
            tcoutangpz.appendChild(accoutangpz)
            soutangpz.appendChild(outangpzfa)
            soutangpz.appendChild(tcoutangpz)
            # sampler
            samz = doc.createElement("sampler")
            samz.setAttribute("id", "%s_rotation_euler_Z-sampler" % (i.name))
            semip = doc.createElement("input")
            semip.setAttribute("semantic", "INPUT")
            semip.setAttribute("source", "#%s_rotation_euler_Z-input"
                               % (i.name))
            semop = doc.createElement("input")
            semop.setAttribute("semantic", "OUTPUT")
            semop.setAttribute("source", "#%s_rotation_euler_Z-output"
                               % (i.name))
            seminter = doc.createElement("input")
            seminter.setAttribute("semantic", "INTERPOLATION")
            seminter.setAttribute("source",
                                  "#%s_rotation_euler_Z-interpolation"
                                  % (i.name))
            semintang = doc.createElement("input")
            semintang.setAttribute("semantic", "IN_TANGENT")
            semintang.setAttribute("source", "#%s_rotation_euler_Z-intangent"
                                   % (i.name))
            semoutang = doc.createElement("input")
            semoutang.setAttribute("semantic", "OUT_TANGENT")
            semoutang.setAttribute("source", "#%s_rotation_euler_Z-outtangent"
                                   % (i.name))
            samz.appendChild(semip)
            samz.appendChild(semop)
            samz.appendChild(seminter)
            samz.appendChild(semintang)
            samz.appendChild(semoutang)
            chanz = doc.createElement("channel")
            chanz.setAttribute("source", "#%s_rotation_euler_Z-sampler"
                               % (i.name))
            chanz.setAttribute("target", "%s/rotation_z.ANGLE" % (i.name))
            anmrz.appendChild(sinpz)
            anmrz.appendChild(soutpz)
            anmrz.appendChild(sintpz)
            anmrz.appendChild(sintangpz)
            anmrz.appendChild(soutangpz)
            anmrz.appendChild(samz)
            anmrz.appendChild(chanz)
            # libanm.appendChild(anmrz)
            print(ii)
            print(inpz)
            print(outpz)
            print(intz)
            print(intangz)
            print(outtangz)
            print("donerotz")
    return anmrz
