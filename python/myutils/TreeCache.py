from __future__ import print_function
import os,sys,subprocess,hashlib
import ROOT
from samplesclass import Sample
import time

class TreeCache:
    def __init__(self, cutList, sampleList, path, config):
        ROOT.gROOT.SetBatch(True)
        self.path = path
        self.config = config
        print("Init path",path," sampleList",sampleList)
        self._cutList = []
        #! Make the cut lists from inputs
        for cut in cutList:
            self._cutList.append('(%s)'%cut.replace(' ',''))
        try:
            self.__tmpPath = os.environ["TMPDIR"]
            print('The TMPDIR is ', os.environ["TMPDIR"])
            
        except KeyError:
            print("\x1b[32;5m %s \x1b[0m" %open('%s/data/vhbb.txt' %config.get('Directories','vhbbpath')).read())
            print("\x1b[31;5;1m\n\t>>> %s: Please set your TMPDIR and try again... <<<\n\x1b[0m" %os.getlogin())
            sys.exit(-1)

        self.whereToLaunch = config.get('Configuration','whereToLaunch')):

        self.__doCache = True
        if config.has_option('Directories','tmpSamples'):
            self.__tmpPath = config.get('Directories','tmpSamples')
        self.__hashDict = {}
        self.minCut = None
        self.__find_min_cut()# store the cut list as one string in minCut, using ROOT syntax (i.e. || to separate between each cut) 
        self.__sampleList = sampleList
        print('\n\t>>> Caching FILES <<<\n')
        self.__cache_samples()
        
    def putOptions(self):
        return (self.__sampleList,self.__doCache,self.__tmpPath,self._cutList,self.__hashDict,self.minCut,self.path)
    
    def _mkdir_recursive(self, path):
        sub_path = os.path.dirname(path)
        if not os.path.exists(sub_path):
            self._mkdir_recursive(sub_path)
        if not os.path.exists(path):
            os.mkdir(path)

    def __find_min_cut(self):
        effective_cuts = []
        for cut in self._cutList:
            if not cut in effective_cuts:
                effective_cuts.append(cut)
        self._cutList = effective_cuts
        self.minCut = '||'.join(self._cutList)

    def _trim_tree(self, sample, forceReDo = False):

        start_time = time.time()
        print("Caching the sample")
        print("==================\n")

        ''' Create temporary file for each sample '''
        theName = sample.name
        print('Reading sample <<<< %s' %sample)
        source = '%s/%s' %(self.path,sample.get_path)
        checksum = self.get_checksum(source)
        theHash = hashlib.sha224('%s_s%s_%s' %(sample,checksum,self.minCut)).hexdigest()
        self.__hashDict[theName] = theHash
        if not self.whereToLaunch == 'PSI':
            tmpSource = '%s/tmp_%s.root'%(self.__tmpPath,theHash)
        else:
            tmpSource = os.environ["TMPDIR"]+'/'+'tmp_'+theHash+'.root'

        print('the tmp source is ', tmpSource)
        #print ('self.__doCache',self.__doCache,'self.file_exists(tmpSource)',self.file_exists(tmpSource))
        print("==================================================================")
        print ('The cut is ', self.minCut)
        print("==================================================================\n")
        if self.__doCache and self.file_exists(tmpSource) and not forceReDo:
            print('sample',theName,'skipped, filename=',tmpSource)
            return (theName,theHash)
        print ('trying to create',tmpSource)
        print ('self.__tmpPath',self.__tmpPath)
        if self.__tmpPath.find('root://t3dcachedb03.psi.ch:1094/') != -1:
            mkdir_command = self.__tmpPath.replace('root://t3dcachedb03.psi.ch:1094/','srm://t3se01.psi.ch/')
            print('mkdir_command',mkdir_command)
            # RECURSIVELY CREATE REMOTE FOLDER ON PSI SE, but only up to 3 new levels
            mkdir_command1 = mkdir_command.rsplit('/',1)[0]
            mkdir_command2 = mkdir_command1.rsplit('/',1)[0]
            mkdir_command3 = mkdir_command2.rsplit('/',1)[0]
            my_user = os.popen("whoami").read().strip('\n').strip('\r')+'/'
            if my_user in mkdir_command3:
              print ('mkdir_command3',mkdir_command3)
              subprocess.call(['srmmkdir '+mkdir_command3], shell=True)# delete the files already created ?     
            if my_user in mkdir_command2:
              print ('mkdir_command2',mkdir_command2)
              subprocess.call(['srmmkdir '+mkdir_command2], shell=True)# delete the files already created ?     
            if my_user in mkdir_command1:
              print ('mkdir_command1',mkdir_command1)
              subprocess.call(['srmmkdir '+mkdir_command1], shell=True)# delete the files already created ?     
            if my_user in mkdir_command:
              print ('mkdir_command',mkdir_command)
              subprocess.call(['srmmkdir '+mkdir_command], shell=True)# delete the files already created ?     
        else:
            mkdir_command = self.__tmpPath
            print('mkdir_command',mkdir_command)
            # RECURSIVELY CREATE REMOTE FOLDER ON PSI SE, but only up to 3 new levels
            mkdir_command1 = mkdir_command.rsplit('/',1)[0]
            mkdir_command2 = mkdir_command1.rsplit('/',1)[0]
            mkdir_command3 = mkdir_command2.rsplit('/',1)[0]
            my_user = os.popen("whoami").read().strip('\n').strip('\r')+'/'
            if my_user in mkdir_command and not os.path.exists(mkdir_command):
              print ('mkdir_command',mkdir_command)
              subprocess.call(['mkdir '+mkdir_command], shell=True)# delete the files already created ?     

        try:
            #! read the tree from the input
            if forceReDo:
                output = ROOT.TFile.Open(tmpSource,'recreate')
            else:
                output = ROOT.TFile.Open(tmpSource,'create')
            output.cd()
        except:
            ## in case there are problems go to the next dataset [probably another process is working on this dataset]
            return (theName,theHash)
        print ('reading',source)
        print ("I am reading")
        input = ROOT.TFile.Open(source,'read')
        print ("I read")
        tree = input.Get(sample.tree)
        assert type(tree) is ROOT.TTree
        print ("debug1")
        input.cd()
        obj = ROOT.TObject
        for key in ROOT.gDirectory.GetListOfKeys():
            input.cd()
            obj = key.ReadObj()
            if obj.GetName() == 'tree':
                continue
            output.cd()
            obj.Write(key.GetName())
        output.cd()
        theCut = self.minCut
        if sample.subsample:
            theCut += '& (%s)' %(sample.subcut)
        print ("the cut is", theCut)
        #Problem here: not working when empty tree
        cuttedTree=tree.CopyTree(theCut)
        cuttedTree.Write()
        output.Write()
        input.Close()
        del input
        output.Close()
#        tmpSourceFile = ROOT.TFile.Open(tmpSource,'read')
#        if tmpSourceFile.IsZombie():
#            print("@ERROR: Zombie file")

        if self.whereToLaunch == 'PSI':
            srmpathOUT = tmpSource.replace('gsidcap://t3se01.psi.ch:22128/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=').replace('dcap://t3se01.psi.ch:22125/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=').replace('root://t3dcachedb03.psi.ch:1094/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=')
            command = 'srmcp -2 -globus_tcp_port_range 20000,25000 file:///'+tmpSource+' '+srmpathOUT.replace('root://t3dcachedb03.psi.ch:1094/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=')
            print(command)
            subprocess.call([command], shell=True)

        del output
        print ("debug4")
        print ("I've done " + theName + " in " + str(time.time() - start_time) + " s.")
        return (theName,theHash)


    def __cache_samples(self):
        inputs=[]
        for job in self.__sampleList:
            inputs.append((self,"_trim_tree",(job)))
        multiprocess=0
        multiprocess=int(self.config.get('Configuration','nprocesses'))
        outputs = []
        print('launching __cache_samples with ',multiprocess,' processes')
        if multiprocess>1:
            from multiprocessing import Pool
            from myutils import GlobalFunction
            p = Pool(multiprocess)
            outputs = p.map(GlobalFunction, inputs)
        else:
            for input_ in inputs:
                outputs.append(getattr(input_[0],input_[1])(input_[2])) #ie. self._trim_tree(job)
        
        for output in outputs:
            (theName,theHash) = output
            self.__hashDict[theName]=theHash

    def get_tree(self, sample, cut):
        print('input file %s/tmp_%s.root'%(self.__tmpPath,self.__hashDict[sample.name]))
        # print ('Opening %s/tmp_%s.root'%(self.__tmpPath,self.__hashDict[sample.name]))
        input = ROOT.TFile.Open('%s/tmp_%s.root'%(self.__tmpPath,self.__hashDict[sample.name]),'read')
        print ('Opening %s/tmp_%s.root'%(self.__tmpPath,self.__hashDict[sample.name]))
        try:
            tree = input.Get(sample.tree)
            assert type(tree) is ROOT.TTree
        except:
            print ("%s/tmp_%s.root is corrupted. I'm relaunching _trim_tree"%(self.__tmpPath,self.__hashDict[sample.name]))
            self._trim_tree(sample, forceReDo=True)
            input = ROOT.TFile.Open('%s/tmp_%s.root'%(self.__tmpPath,self.__hashDict[sample.name]),'read')
            tree = input.Get(sample.tree)
            print("Type of sample.tree ROOT.TTree? (again) ", type(tree) is ROOT.TTree)


        #fill all Count* histos as lists, like self.CountWeighted = [123.23]
        for obj in input.GetListOfKeys():
            name = obj.GetName()
            if "Count" in name:
                obj = obj.ReadObj()
                assert(type(obj) is ROOT.TH1F)
                counts = []
                for i in range(obj.GetNbinsX()):
                    value = obj.GetBinContent(i+1)
                    if value<=0:
                        print("WARNING: bin ",i+1," of ",name," is ",value,". I'm forcing it to be 1.")
                        value=1
                    counts.append(value)

                setattr(self,name,counts)

        if sample.subsample:
            cut += '& (%s)' %(sample.subcut)
        print('cut is', cut)
        ROOT.gROOT.cd()
        print('getting the tree after applying cuts')
        cuttedTree=tree.CopyTree(cut)
        # cuttedTree.SetDirectory(0)
        input.Close()
        del input
        del tree
        return cuttedTree

    @staticmethod
    def get_slc_version():
        command = 'uname -a'
        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,shell=True)
        lines = p.stdout.readlines()
        line = lines[0].split()[2]
        if 'el5' in line:
            return 'SLC5'
        elif 'el6' in line:
            return 'SLC6'
        else:
            sys.exit(-1)

    @staticmethod
    def get_scale(sample, config, lumi = None, count=1):
#        print float(sample.lumi)
        try: sample.xsec = sample.xsec[0]
        except: pass
        anaTag=config.get('Analysis','tag')
        theScale = 1.
        lumi = float(sample.lumi)
        theScale = lumi*sample.xsec*sample.sf/(count)
        print("sample: ",sample,"lumi: ",lumi,"xsec: ",sample.xsec,"sample.sf: ",sample.sf,"count: ",count," ---> using scale: ", theScale)
        return theScale

    @staticmethod
    def get_checksum(file):
        if 'gsidcap://t3se01.psi.ch:22128' in file:
            srmPath = 'srm://t3se01.psi.ch:8443/srm/managerv2?SFN='
            command = 'srmls -l %s' %file.replace('gsidcap://t3se01.psi.ch:22128/','%s/'%srmPath)
            p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,shell=True)
            lines = p.stdout.readlines()
            if any('does not exist' in line for line in lines):
                print('File not found')
                print(command)
            checksum = lines[6].replace('- Checksum value:','')
            checksum = checksum.strip()
            #srmPath = 'srm://t3se01.psi.ch'
            #command = 'gfal-sum %s ADLER32' %file.replace('gsidcap://t3se01.psi.ch:22128/','%s/'%srmPath)
            #print(command)
            #p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,shell=True)
            #lines = p.stdout.readlines()
            #if any('No such' in line for line in lines):
            #    print('File not found')
            #    print(command)
            #checksum = lines[0].split()[1]

        else:
            command = 'md5sum %s' %file
            p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,shell=True)
            lines = p.stdout.readlines()
            checksum = lines[0]
        return checksum
    
    @staticmethod
    def file_exists(file):
        print ('Will now check if the file exists')
        print ('=================================\n')

        file_exists = False

        file_dummy = file
        #srmPath = 'srm://t3se01.psi.ch:8443/srm/managerv2?SFN='
        file_dummy = file_dummy.replace('root://t3dcachedb03.psi.ch:1094/','')
        file_dummy = file_dummy.replace('srm://t3se01.psi.ch:8443/srm/managerv2?SFN=','')

        print ('The command is', 'os.path.isfile(',file_dummy,')', os.path.isfile(file_dummy))
        if os.path.isfile(file_dummy):
            print(file_dummy, 'exists.')
            f = ROOT.TFile.Open(file,'read')
            if not f:
                print ('File is null. Gonna redo it.')
            elif f.GetNkeys() == 0 or f.TestBit(ROOT.TFile.kRecovered) or f.IsZombie():
                print ('f.GetNkeys()',f.GetNkeys(),'f.TestBit(ROOT.TFile.kRecovered)',f.TestBit(ROOT.TFile.kRecovered),'f.IsZombie()',f.IsZombie())
                print ('File', file_dummy, 'already exists but is buggy, gonna delete and rewrite it.')
                del_protocol = file.replace('gsidcap://t3se01.psi.ch:22128/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=').replace('dcap://t3se01.psi.ch:22125/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=').replace('root://t3dcachedb03.psi.ch:1094/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=')
                command = 'srmrm %s' %(del_protocol)
                subprocess.call([command], shell=True)
                print(command)
            else:
                file_exists = True

        #exist = os.path.exists(file_dummy)
        #print('os.path.exists(',file_dummy,')',exist)
        #return os.path.exists(file_dummy)
        return file_exists


