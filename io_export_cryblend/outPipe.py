#------------------------------------------------------------------------------
# License:   GPLv2+
#------------------------------------------------------------------------------


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
            print("CryBlend Exporter: {!r}".format(message))

        elif message_type == 'debug':
            print("CryBlend Debug: {!r}".format(message))

        elif message_type == 'warning':
            print("CryBlend Exporter Warning: {!r}".format(message))

        elif message_type == 'error':
            print("CryBlend Exporter Error: {!r}".format(message))

oP = outPipe()


def cbPrint(msg, message_type='info'):
    oP.pump(msg, message_type)
