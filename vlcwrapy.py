import pickle
import os
import sys
import pythoncom, pyHook 
import win32api
import subprocess
import ctypes
import threading
from multiprocessing import *
import time
import natsort
import atexit
import logging

def log_uncaught_exceptions(ex_cls, ex, tb):

    logging.critical(''.join(traceback.format_tb(tb)))
    logging.critical('{0}: {1}'.format(ex_cls, ex))


class vlc(object):
    def __init__(self,filepath,vlcp,scriptpath):
        self.fn=filepath
        self.vlcpath=vlcp        
        self.process=None
        self.restart(filepath)
        atexit.register(self.savestate,scriptpath)
        
    def kill(self):
        p, self.process = self.process, None
        if p is not None and p.poll() is None:
            p.kill() 
            p.wait()
            
    def is_alive(self):
        if self.process is not None and self.process.poll() is  None:
            return True
        else:
            return False
    
    def restart(self,filepath):
        self.kill()
        self.process = subprocess.Popen([self.vlcpath,filepath],close_fds=True)
        self.fn=filepath
                
    def play_next(self):        
        f=self.get_new_file(1)
        self.restart(f)
                
    def play_prev(self):
        
        f=self.get_new_file(-1)
        self.restart(f)      

    def play_from_record(self):
        f=self.get_record()
        # print f
        if f:
            self.restart( os.path.join(os.path.split(self.fn)[0],f) )
    
    def get_new_file(self,switch):        
        dirname= os.path.dirname(self.fn)    
        supplist=['.mkv','.flv','.avi','.mpg','.wmv','.ogm','.mp4','.rmvb']        
        files = [os.path.join(dirname,f) for f in os.listdir(dirname) if (os.path.isfile(os.path.join(dirname,f)) and os.path.splitext(f)[-1]in supplist)]
        files=natsort.natsorted(files)
        #print files
        try: currentindex=files.index(self.fn)
        except: currentindex=0
        i=0
        if switch==1:
            if currentindex<(len(files)-1):i=currentindex+1            
        else:
            if currentindex>0:i=currentindex-1  
        return files[i] 

    def get_record(self):
        dirname=os.path.split(self.fn)[0]

        dbase=pickle.load(open('d:/vlcdatabase.p')) if os.path.isfile('d:/vlcdatabase.p') else {}
        return dbase.get(dirname,None)

    def savestate(self,scriptpath):
        f=open(os.path.join(scriptpath,'lastfile.txt'),'w')
        f.write(self.fn)
        f.close()
        dbase=pickle.load(open('d:/vlcdatabase.p')) if os.path.isfile('d:/vlcdatabase.p') else {}
        dbase[os.path.split(self.fn)[0]]=os.path.split(self.fn)[1]
        pickle.dump(dbase,open('d:/vlcdatabase.p','w'))
        print "state saved"   

class vlcThread(threading.Thread):
    def __init__(self,filepath,vlcp,fl,scriptpath):
        threading.Thread.__init__(self)
        self.fn,self.vlcpath,self.flag=filepath,vlcp,fl
        self.daemon=True 
        self.scriptpath=scriptpath
            
    def run(self):
        vlcinstance=vlc(self.fn,self.vlcpath,self.scriptpath)
        last_alive=time.time()
        while True:            
            time.sleep(0.3)
            if vlcinstance.is_alive(): last_alive=time.time()
            else: 
                print time.time()-last_alive
                if (time.time()-last_alive)>1:
                    sys.exit(0)
                    break
            if(self.flag.value==1):
                vlcinstance.play_next()
                self.flag.value=0
            if(self.flag.value==-1):
                vlcinstance.play_prev()
                self.flag.value=0
            if(self.flag.value==2):
                vlcinstance.play_from_record()
                self.flag.value=0
                
class hookThread(threading.Thread):
    def __init__(self,flag):
        threading.Thread.__init__(self)
        self.flag=flag
        self.daemon=True       
        
    def kbeventhandler(self,event):    
        if event.Key=='Home' and 'vlc' in event.WindowName.lower():
            self.flag.value =-1
            return False
        if event.Key=='End' and 'vlc' in event.WindowName.lower():
            self.flag.value =1
            return False
        if event.Key=='F2'  and 'vlc' in event.WindowName.lower():
            self.flag.value =2
            return False
        return True
    def run(self):
        hm = pyHook.HookManager()
        hm.KeyDown = self.kbeventhandler
        hm.HookKeyboard()    
        pythoncom.PumpMessages()

class LoggerWriter:
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level

    def write(self, message):
        if message != '\n':
            self.logger.log(self.level, message)


def main():
    logging.basicConfig(
            level=logging.DEBUG,
            filename='D:/vlc.log',
            filemode='w')
    logger = logging.getLogger("demo")
    # sys.excepthook = log_uncaught_exceptions
    # logging.debug('About to do f().')
    sys.stderr=LoggerWriter(logger, logging.DEBUG)
    scriptpath=os.path.dirname(sys.argv[0])
    #print scriptpath
    vlcpath='vlc'
    flag=Value('i')
    flag.value=0
    if os.name=='nt': vlcpath='C:/Program Files (x86)/VideoLAN/VLC/vlc.exe'
    fn='H:\\Anime\\needless\\Needless_[E-D]\\[Exiled-Destiny]_Needless_Ep11v2_(04B16479).mkv'
    if "lastfile.txt" in os.listdir(scriptpath):
        fn=open(os.path.join(scriptpath,'lastfile.txt')).read()
    
    if len(sys.argv)>1:
        fn=sys.argv[1] #use argument if available or else use default file    
    t=vlcThread(fn,vlcpath,flag,scriptpath)
    print t.fn
    
    h=hookThread(flag)
    t.start()
    h.start()
    t.join()
    print "bye bye"


    
if __name__ == '__main__':
    main() 
