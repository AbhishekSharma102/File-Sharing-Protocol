import binascii, sys, errno, stat
import commands, os, time, hashlib
import re
from stat import *
import socket
from threading import Thread, Timer
from SocketServer import ThreadingMixIn

TCP_IP = ''
TCP_PORT = 12345
BUFFER_SIZE = 2048
arrow = True
syncLock = False
t = None
class ClientThread(Thread):

    def __init__(self,ip,port,sock):
        Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.sock = sock
        self.data = ''
        self.readFlag = True
        self.readData = False
        self.readCommand = True
        self.downloadFlag = False
        self.gotData = ''
        self.sync = False
        if port != 0:
            print " New thread started for "+ip+":"+str(port)
        else:
            print " Connected to server "

    def run(self):
        self.gotData = ''
        while self.readFlag:
            temp = self.sock.recv(BUFFER_SIZE)
            self.gotData += temp
            if ('END DATA' in re.split('\n', self.gotData)[-1] or 'END DOWNLOAD' in re.split('\n', self.gotData)[-1] or 'END COMMAND' in re.split('\n', self.gotData)[-1]):# and self.sync == False:
                l = self.gotData
                #print l
                if len(l) > 0 and re.split('\n', l)[0] == 'DATA':
                    toprint = re.split('DATA\n', l)[1]
                    toprint = re.split('\nEND DATA', toprint)[0]
                    toprint = re.split('\n', toprint)
                    tempprint = []
                    for i in toprint:
                        oneline = re.split('\t', i)
                        oneline = oneline[0:len(oneline)-1]
                        oneline = '\t'.join(oneline)
                        tempprint.append(oneline)
                    print '\n'.join(tempprint)
                    global arrow
                    arrow = True
                elif len(l) > 0 and re.split('\n', l)[0] == 'DOWNLOAD':
                    tomake = re.split('DOWNLOAD\n', l)[1]
                    tomake = re.split('\nEND DOWNLOAD', tomake)[0]
                    filedata = re.split('\n', tomake)[1]
                    filename = re.split('\n', tomake)[1]
                    filename = re.split('\t', filename)[0]
                    if re.split('\n', tomake)[0] == 'UDP':        #means UDP
                        sock1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        sock1.bind(('', 12346))
                        recvd = ''
                        sock1.settimeout(0.5)
                        while True:
                            try:
                                message, address = sock1.recvfrom(1024)
                            except socket.timeout:
                                break
                            recvd += message
                        sock1.close()
                        try:
                            fp = open(filename, 'w')
                            fp.write(recvd)
                            fp.close()
                        except:
                            print 'error downloading file'
                            continue
                        fp = open(filename, 'r')
                        fp = fp.read()
                        m = hashlib.md5()
                        m.update(fp)
                        hashedvalue = binascii.hexlify(m.digest())
                        filedata = re.split('\t', filedata)
                        print '\t'.join(filedata[0:4])
                        print filename + '\tsaved: ' + str(hashedvalue) + '\trecvd: ' + filedata[-1]
                    else:
                        tomake = re.split('\n', tomake)[2:]
                        tomake = '\n'.join(tomake)
                        try:
                            fp = open(filename, 'w')
                        except:
                            print 'error downloading file'
                            continue
                        fp.write(tomake)
                        filedata = re.split('\t', filedata)
                        fp.close()
                        m = hashlib.md5()
                        m.update(tomake)
                        hashedvalue = binascii.hexlify(m.digest())
                        filedatalen = len(filedata)
                        fileperm = filedata[4]
                        self.setPerm(filename, fileperm)
                        print '\t'.join(filedata[0:4]) + '\t' + hashedvalue
                            
                    arrow = True
                elif len(l) > 0 and re.split('\n', l)[0] == 'COMMAND':
                    l = re.split('COMMAND\n', l)[1]
                    l = re.split('\nEND COMMAND', l)[0]
                    temp = re.split(' +', l)
                    if temp[0] == 'index':
                        self.indexCalled(temp)
                    elif temp[0] == 'hash':
                        self.hashCalled(temp)
                    elif temp[0] == 'download':
                        self.downloadCalled(temp)
                self.gotData = ''
            if len(self.gotData) > 0 and 'END SYNC' in re.split('\n', self.gotData)[-1] and self.sync == False:
                self.sync = True
                #print self.gotData
                dataBlock = re.split('SYNC START\n', self.gotData)[1]
                dataBlock = re.split('\nEND SYNC', dataBlock)[0]
                indFiles = re.split('FILE START\n', dataBlock)[1:]
                files = []
                for i in indFiles:
                    temp = re.split('FILE END\n', i)[0]
                    files.append(temp)
                fileinfo = []
                filedata = []
                filename = []
                for i in files:
                    tempdata = re.split('FILE DATA START\n', i)[1]
                    tempdata = re.split('\nFILE DATA END\n', tempdata)[0]
                    filedata.append(tempdata)
                    tempinfo = re.split('FILE INFO START\n', i)[1]
                    tempinfo = re.split('\nFILE INFO END\n', tempinfo)[0]
                    fileinfo.append(tempinfo)
                    tempname = re.split('FILE NAME START\n', i)[1]
                    tempname = re.split('\nFILE NAME END\n', tempname)[0]
                    filename.append(tempname)
                itemlen = len(filename)
                for i in range(itemlen):
                    if not filename[i] == './server2.py':
                        try:
                            fp = open(filename[i], 'r')
                            fp = fp.read()
                            #file exists, check hash and create new if different
                            m = hashlib.md5()
                            m.update(fp)
                            hashedvalue = m.digest()
                            hashedvalue = str(binascii.hexlify(hashedvalue))
                            if not re.split('\t', fileinfo[i])[0] == hashedvalue:
                                fpc = open(filename[i], 'w')
                                fpc.write(filedata[i])
                                perm = re.split('\t', fileinfo[i])[1]
                                self.setPerm(filename[i], perm)
                                #print 'new file saved'
                        except:
                            try:                                    #create directory
                                dirname = re.split('/', filename[i])
                                dirname = dirname[0:len(dirname)-1]
                                dirname = '/'.join(dirname)
                                os.makedirs(dirname)
                            except OSError as exc:
                                if exc.errno == errno.EEXIST and os.path.isdir(dirname):
                                    pass
                                else:
                                    print 'unable to create directory %s' % (dirname)
                                    continue
                            fpc = open(filename[i], 'w')
                            fpc.write(filedata[i])
                            fpc.close()
                            perm = re.split('\t', fileinfo[i])[1]
                            self.setPerm(filename[i], perm)
                self.gotData = ''
                self.sync = False
                
    def setPerm(self, name, perm):
        perm = int(perm)
        temp = 0
        if (perm & stat.S_IRUSR):
            temp = temp | stat.S_IRUSR
        if (perm & stat.S_IWUSR):
            temp = temp | stat.S_IWUSR
        if (perm & stat.S_IXUSR):
            temp = temp | stat.S_IXUSR
        if (perm & stat.S_IRGRP):
            temp = temp | stat.S_IRGRP
        if (perm & stat.S_IWGRP):
            temp = temp | stat.S_IWGRP
        if (perm & stat.S_IXGRP):
            temp = temp | stat.S_IXGRP
        if (perm & stat.S_IROTH):
            temp = temp | stat.S_IROTH
        if (perm & stat.S_IWOTH):
            temp = temp | stat.S_IWOTH
        if (perm & stat.S_IXOTH):
            temp = temp | stat.S_IXOTH
        #print temp
        os.chmod(name, temp)


    def indexCalled(self, arguments):
        if len(arguments) == 1 or len(arguments) > 4:
            self.sendData('DATA\ninvalid arguments\nEND DATA')
        else:
            if arguments[1] == 'longlist' and len(arguments) == 2:
                toReturn = "DATA\n"
                output = commands.getoutput("ls")
                output = re.split('\n', output)
                for i in output:
                    info = os.stat(i)
                    toReturn += self.fileDetails(i, info)
                toReturn += '\nEND DATA'
                self.sendData(toReturn)
            elif arguments[1] == 'shortlist' and len(arguments) > 2 and len(arguments) < 5:
                startTime = 0
                endTime = 0
                if len(arguments) == 3:
                    startTime = float(arguments[2])
                    toReturn = "DATA\n"
                    output = commands.getoutput("ls")
                    output = re.split('\n', output)
                    for i in output:
                        info = os.stat(i)
                        if info.st_mtime >= startTime:
                            toReturn += self.fileDetails(i, info)
                    toReturn += '\nEND DATA'
                    self.sendData(toReturn)
                elif len(arguments) == 4:
                    startTime = float(arguments[2])
                    endTime = float(arguments[3])
                    toReturn = "DATA\n"
                    output = commands.getoutput("ls")
                    output = re.split('\n', output)
                    for i in output:
                        info = os.stat(i)
                        if info.st_mtime >= startTime and info.st_mtime <= endTime:
                            toReturn += self.fileDetails(i, info)
                    toReturn += '\nEND DATA'
                    self.sendData(toReturn)
            elif arguments[1] == 'regex' and len(arguments) == 3:
                toReturn = "DATA\n"
                output = commands.getoutput("ls")
                output = re.split('\n', output)
                for i in output:
                    if bool(re.search(arguments[2], i)):
                        info = os.stat(i)
                        toReturn += self.fileDetails(i, info)
                toReturn += '\nEND DATA'
                self.sendData(toReturn)
            else:
                self.sendData('DATA\ninvalid command or arguments\nEND DATA')

    def fileDetails(self, name, info):
        toReturn = ''
        toReturn += name + "\t"
        if S_ISDIR(info.st_mode):
            toReturn += "direc\t"
        else:
            toReturn += "file\t"
        tempTime = time.ctime(info.st_mtime)
        toReturn += str(info.st_size) + "\t"
        toReturn += str(tempTime) + "\t"
        toReturn += str(info.st_mode)
        toReturn += "\n"
        return toReturn

    def hashCalled(self, arguments):
        if len(arguments) > 3 or len(arguments) == 1:
            self.sendData('DATA\ninvalid arguments\nEND DATA')
        elif arguments[1] == 'verify':
            fp = 0
            try:
                fp = open(arguments[2], 'r')
                fp = fp.read()
            except:
                self.sendData('DATA\ninvalid filename\nEND DATA')
            m = hashlib.md5()
            m.update(fp)
            hashedvalue = m.digest()
            hashedvalue = binascii.hexlify(hashedvalue)
            info = time.ctime(os.stat(arguments[2]).st_mtime)
            toReturn = 'DATA\n' + arguments[2] + '\t' + str(hashedvalue) + '\t' + str(info) + '\n'
            toReturn += '\nEND DATA'
            self.sendData(toReturn)
        elif arguments[1] == 'checkall' and len(arguments) == 2:
            toReturn = "DATA\n"
            output = commands.getoutput("ls")
            output = re.split('\n', output)
            for i in output:
                info = os.stat(i)
                if not S_ISDIR(info.st_mode):
                    fp = open(i, 'r')
                    fp = fp.read()
                    m = hashlib.md5()
                    m.update(fp)
                    hashedvalue = binascii.hexlify(m.digest())
                    infoMTime = time.ctime(info.st_mtime)
                    toReturn += i + '\t' + str(hashedvalue) + '\t' + str(infoMTime) + '\n'
            toReturn += '\nEND DATA'
            self.sendData(toReturn)
        else:
            self.sendData('DATA\ninvalid command or arguments\nEND DATA')

    def downloadCalled(self, arguments):
        if arguments[1] == 'TCP' and len(arguments) == 3:
            fp = 0
            try:
                fp = open(arguments[2], 'r')
                fp = fp.read()
                info = os.stat(arguments[2])
                info = self.fileDetails(arguments[2], info)
            except:
                self.sendData('DATA\ninvalid filename\nEND DATA')
                return
            fp = 'DOWNLOAD\nTCP\n' + info + fp + '\nEND DOWNLOAD'
            self.sendData(fp)
        elif arguments[1] == 'UDP' and len(arguments) == 3:
            fp = 0
            try:
                fp = open(arguments[2], 'r')
                fp = fp.read()
                info = os.stat(arguments[2])
                info = self.fileDetails(arguments[2], info)
                m = hashlib.md5()
                m.update(fp)
                hashedvalue = m.digest()
                hashedvalue = binascii.hexlify(hashedvalue)
                info = re.split('\n', info)[0]
                info += '\t' + str(hashedvalue) + '\n'
            except:
                self.sendData('DATA\ninvalid filename\nEND DATA')
                return
            self.sendData('DOWNLOAD\nUDP\n' + info + '\nEND DOWNLOAD')
            time.sleep(0.04)
            self.sendDataUdp(fp)
        else:
            self.sendData('DATA\ninvalid command or arguments\nEND DATA')

    def sendDataUdp(self, toSend):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        addr = (self.ip, 12346)
        msglen = len(toSend)
        sent = 0
        while(sent < msglen):
            temp = s.sendto(toSend[sent:sent+1024], addr)
            sent += temp
        s.close()
        #print 'udp msg sent'

    def closeConnection(self):
        print 'closing connection'
        self.readFlag = False
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
            self.sock.close()
        except:
            print 'there seemed to be an error closing client. Maybe it\'s already closed'

    def sendRequest(self, typeString):
        self.logcmd(typeString)
        typeString = 'COMMAND\n' + typeString + '\nEND COMMAND'
        self.sendData(typeString)

    def logcmd(self, tolog):
        fp = open('.logfile.log', 'a', 0664)
        fp.write(tolog + '\n')
        fp.close()
        os.chmod('.logfile.log', 0664)

    def sendData(self, toSend):
        i = 0
        #print toSend
        msglen = len(toSend)
        while i < msglen:
            sent = self.sock.send(toSend[i:])
            if sent == 0:
                print 'Socket connection broken'
                self.closeConnection()
            i = i + sent
        #print 'data sent'

    def genPermissions(self, info):
        return str(info.st_mode)


    def syncAll(self):
        toReturn = 'SYNC START\n'
        for root, dirs, files in os.walk('.', topdown=False):
            for names in files:
                if names != 'server2.py' and names != '.logfile.log':
                    toReturn += 'FILE START\n'
                    filename = os.path.join(root, names)
                    filedata = open(filename, 'r')
                    filedata = filedata.read()
                    fileinfo = os.stat(filename)
                    m = hashlib.md5()
                    m.update(filedata)
                    hashedvalue = binascii.hexlify(m.digest())
                    finfo = str(hashedvalue) + '\t' + self.genPermissions(fileinfo) + '\n'
                    toReturn += 'FILE NAME START\n' + str(filename) + '\nFILE NAME END\n'
                    toReturn += 'FILE DATA START\n' + str(filedata) + '\nFILE DATA END\n'
                    toReturn += 'FILE INFO START\n' + finfo + 'FILE INFO END\n'
                    toReturn += 'FILE END\n'
        toReturn += 'END SYNC'
        global syncLock
        syncLock = False
        self.sendData(toReturn)


def syncData(flag):
    global t
    if flag == 's' and not t:
        t = Timer(30, syncData, [flag])
        t.start()
    elif not t:
        t = Timer(60, syncData, [flag])
        t.start()
        #time.sleep(30)
    global syncLock
    syncLock = True
    print '\nsync in progress...'
    newthread.syncAll()
    #syncLock = False

isServer = raw_input('run as server/client?(s/c)')
correctInput = False
automation = ''
if isServer == 's':
    tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcpsock.bind((TCP_IP, TCP_PORT))
    tcpsock.listen(5)
    print "Waiting for incoming connections..."
    (conn, (ip,port)) = tcpsock.accept()
    print 'Got connection from ', (ip,port)
    newthread = ClientThread(ip,port,conn)
    newthread.start()
    correctInput = True
    automation = Timer(15, syncData, ['s'])

elif isServer == 'c':
    tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ip = raw_input('please enter the ip to connect to?\n$>')
    tcpsock.connect((ip, TCP_PORT))
    newthread = ClientThread(ip, 0, tcpsock)
    newthread.start()
    correctInput = True
    automation = Timer(1000, syncData, ['c'])
else:
    print 'incorrect input, exiting'
    sys.exit(0)

#automation.start()
syncData(isServer)

started = False

while correctInput:
    getInput = ""
    if arrow and syncLock == False:
        getInput = raw_input('$>')
        if (isServer == 's' and not started):
            #t.start()
            started = True
        getInput = re.split(" +", getInput)
        if getInput[0] == 'close' and syncLock == False:
            newthread.closeConnection()
            t.cancel()
            #automation.cancel()
            break
        elif getInput[0] == 'index' and len(getInput) > 1 and syncLock == False:
            if getInput[1] == 'longlist':
                newthread.sendRequest(' '.join(getInput))
                arrow = False
            elif getInput[1] == 'shortlist':
                if len(getInput) == 3:
                    newthread.sendRequest(' '.join(getInput))
                    arrow = False
                elif len(getInput) == 4:
                    newthread.sendRequest(' '.join(getInput))
                    arrow = False
                else:
                    print 'invalid command or arguments'
            elif getInput[1] == 'regex' and len(getInput) == 3:
                newthread.sendRequest(' '.join(getInput))
                arrow = False
            else:
                print 'invalid command or arguments'
        elif getInput[0] == 'hash' and len(getInput) > 1 and syncLock == False:
            if getInput[1] == 'verify' and len(getInput) == 3:
                newthread.sendRequest(' '.join(getInput))
                arrow = False
            elif getInput[1] == 'checkall' and len(getInput) == 2:
                newthread.sendRequest(' '.join(getInput))
                arrow = False
            else:
                print 'invalid command or arguments'
        elif getInput[0] == 'download' and len(getInput) == 3 and syncLock == False:
            newthread.sendRequest(' '.join(getInput))
            arrow = False
            newthread.downloadFlag = True
        elif syncLock == False:
            print 'invalid command or arguments'
        elif syncLock:
        	print 'not allowed, sync in progress'
