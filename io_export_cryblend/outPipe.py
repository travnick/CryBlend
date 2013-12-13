#------------------------------------------------------------------------------
# License:   GPLv2+
#------------------------------------------------------------------------------


from io_export_cryblend import exceptions
from logging import basicConfig, info, debug, warning, DEBUG


# Clear the log file
# try:
#    f = open(
#        'C:\Program Files\Blender Foundation\Blender\CryBlend Export.log', 'w')
#    fPath = 'C:\Program Files\Blender Foundation\Blender\CryBlend Export.log'
# except:
#    f = open('CryBlend Export.log', 'w')
#    fPath = 'CryBlend Export.log'
# f.close()

# basicConfig(filename=fPath,level=DEBUG,format='%(asctime)s %(message)s')


class outPipe():
    def __init__(self):
        pass

    def pump(self, message, message_type='info'):
        if message_type == 'info':
            print("[Info] CryBlend: {!r}".format(message))

        elif message_type == 'debug':
            print("[Debug] CryBlend: {!r}".format(message))

        elif message_type == 'warning':
            print("[Warning] CryBlend: {!r}".format(message))

        elif message_type == 'error':
            print("[Error] CryBlend: {!r}".format(message))

        else:
            raise exceptions.CryBlendException("No such message type {!r}".
                                    format(message_type))

oP = outPipe()


def cbPrint(msg, message_type='info'):
    oP.pump(msg, message_type)
