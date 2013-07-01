#-------------------------------------------------------------------------------
# License:   GPLv2+
#-------------------------------------------------------------------------------
from logging import basicConfig, info, debug, warning, DEBUG

#Clear the log file
#try:
#    f = open('C:\Program Files\Blender Foundation\Blender\CryBlend Export.log', 'w')
#    fPath = 'C:\Program Files\Blender Foundation\Blender\CryBlend Export.log'
#except:
#    f = open('CryBlend Export.log', 'w')
#    fPath = 'CryBlend Export.log'
#f.close()

#basicConfig(filename=fPath,level=DEBUG,format='%(asctime)s %(message)s')

class outPipe():
    def __init__(self):
        pass

    def pump(self, msg, type='info'):
        if type == 'info':
            print("CryBlend Exporter: {!r}".format(msg))
            
        elif type == 'debug':
            print("CryBlend Debug: {!r}".format(msg))

        elif type == 'warning':
            print("CryBlend Exporter Warning: {!r}".format(msg))

        elif type == 'error':
            print("CryBlend Exporter Error: {!r}".format(msg))
        
oP = outPipe()

def cbPrint(msg, type='info'):
    oP.pump(msg, type)
