from __future__ import print_function
import os,sys,subprocess,hashlib
import ROOT
from samplesclass import Sample
import time
import glob
from copytreePSI import filelist as getSampleFileList  # to avoid name conflict with filelist variable
from BetterConfigParser import BetterConfigParser
from sample_parser import ParseInfo
from optparse import OptionParser
import zlib
import base64

class MultiCache:
    def __init__(self, regions, sampleList, path, config, filelist=None, sample_to_merge=None, mergeCachingPart=-1):
        ROOT.gROOT.SetBatch(True)
        self.verbose = False
        self.path = path
        self.config = config
        self.regions = regions if type(regions) == list else [x.strip() for x in regions.split(',')]
        self.remove_sys = True

        # DEBUG
        #self.verbose = True

        try:
            self.__tmpPath = os.environ["TMPDIR"]
            print('The TMPDIR is ', os.environ["TMPDIR"])
        except KeyError:
            print("\x1b[32;5m %s \x1b[0m" %open('%s/data/vhbb.txt' %config.get('Directories','vhbbpath')).read())
            print("\x1b[31;5;1m\n\t>>> %s: Please set your TMPDIR and try again... <<<\n\x1b[0m" %os.getlogin())
            sys.exit(-1)

        if os.path.exists("../../interface/VHbbNameSpace_h.so"):
            print ('ROOT.gROOT.LoadMacro("../../interface/VHbbNameSpace_h.so")')
            ROOT.gROOT.LoadMacro("../../interface/VHbbNameSpace_h.so")
        elif os.path.exists("../interface/VHbbNameSpace_h.so"):
            print ('ROOT.gROOT.LoadMacro("../interface/VHbbNameSpace_h.so")')
            ROOT.gROOT.LoadMacro("../interface/VHbbNameSpace_h.so")


        if config.has_option('Directories','tmpSamples'):
            self.__cachedPath = config.get('Directories','tmpSamples')

        self.__hashDict = {}

        # samples info
        samplesinfo = config.get('Directories','samplesinfo')
        info = ParseInfo(samplesinfo, self.path) #creates a list of Samples by reading the info in samples_nosplit.cfg and the conentent of the path.

        # MC background
        mc = eval(config.get('Plot_general','samples'))

        # check if data samples are the same for all regions (required!)
        dataSamplesPerRegion = []
        dataSamples = []
        for region in self.regions:
            section = 'Plot:%s'%region
            dataSamples = eval(config.get(section, 'Datas'))
            dataSamplesString = ','.join(dataSamples)
            if dataSamplesString not in dataSamplesPerRegion:
                dataSamplesPerRegion.append(dataSamplesString)
        if len(dataSamplesPerRegion) > 1:
            print ("\x1b[32mERROR: these regions can't be cached together because data samples differ!!! \x1b[0m")
            print (dataSamplesPerRegion)
            exit(-1)
        elif len(dataSamplesPerRegion) < 1:
            print ("\x1b[32mWARNING: no data samples!! \x1b[0m")
        data = dataSamples if len(dataSamplesPerRegion) > 0 else []

        # check if signal
        isSignalPerRegion = []
        for region in self.regions:
            section = 'Plot:%s'%region
            isSignal = config.has_option(section, 'Signal')
            if isSignal not in isSignalPerRegion:
                isSignalPerRegion.append(isSignal)
        if len(isSignalPerRegion) > 1:
            print ("\x1b[32mERROR: these regions can't be cached together because isSignal differs!! \x1b[0m")
            exit(-6)

        # check if mc signal samples are the same for all regions (required!)
        mcSignalSamplesPerRegion = []
        mcSignalSamples = []
        for region in self.regions:
            section = 'Plot:%s'%region
            mcSignalSamples = eval(config.get(section,'Datas'))
            mcSignalSamplesString = ','.join(mcSignalSamples)
            if mcSignalSamplesString not in mcSignalSamplesPerRegion:
                mcSignalSamplesPerRegion.append(mcSignalSamplesString)
        if len(mcSignalSamplesPerRegion) > 1:
            print ("\x1b[32mERROR: these regions can't be cached together because mc signal samples differ!!! \x1b[0m")
            print (mcSignalSamplesPerRegion)
            exit(-3)

        # MC signal
        if isSignalPerRegion[0]:
            if len(mcSignalSamplesPerRegion)<1:
                print ("\x1b[32mERROR: defined as signal region, but not signal given! \x1b[0m")
                exit(-5)
            section = 'Plot:%s'%self.regions[0]
            mc.append(config.get(section, 'Signal'))

        total_lumi = eval(config.get('Plot_general','lumi'))
        print ('-'*60)
        print (" (%d) MC:   %r"%(len(mc),mc))
        print (" (%d) DATA: %r"%(len(data),data))
        print ('-'*60)
        datasamples = info.get_samples(data)
        mcsamples = info.get_samples(mc)
        sampleList = mcsamples + datasamples

        self.__sampleList = sampleList
        self.sample_to_merge = sample_to_merge

        # number of the chunk that should be processed
        self.mergeCachingPart = mergeCachingPart

        print('\n\t>>> MultiCaching FILES <<<\n')
        self.__cache_samples(filelist, self.mergeCachingPart)


    def __cache_samples(self, filelist=None, mergeCachingPart=-1):
        print ('__cache_samples (v2)')
        if self.sample_to_merge:
            print ('prepare to __cache_samples: %s'%self.sample_to_merge)

            # check if supplied sample name corresponds to existing sample
            sampleDictionary = {}
            matchedSample = None
            for sample in self.__sampleList:

                # compare extension
                extMatch = ('_ext' in str(sample)) == ('_ext' in self.sample_to_merge)
                if extMatch and '_ext' in str(sample):

                    # compare ext number
                    extToMerge = self.sample_to_merge.split('_ext')[1].strip()
                    extCompare = str(sample).split('_ext')[1].strip()
                    extMatch = extMatch and (extToMerge==extCompare)

                    pureSampleName = str(sample).split('_ext')[0]
                    pureSampleLongName = sample.identifier.split('_ext')[0]
                    pureNameSampleToMerge = self.sample_to_merge.split('_ext')[0]
                else:
                    pureSampleName = str(sample)
                    pureSampleLongName = sample.identifier
                    pureNameSampleToMerge = self.sample_to_merge

                # compare name
                sampleMatch = pureNameSampleToMerge.strip() == pureSampleName.strip()
                if extMatch and sampleMatch:
                    matchedSample = sample
                    print ('matching sample found:'+str(matchedSample))
                    break

            if matchedSample:
                self._trim_tree(sample=matchedSample, filelist=filelist, mergeplot=False, forceReDo=False, mergeCachingPart=mergeCachingPart)
            else:
                print ('not in list of samples!')
                for sample in self.__sampleList:
                    print ("--"+str(sample))

    def _get_cuts(self, region):
        section = 'Plot:%s'%region
        if config.has_option('Cuts',region):
            cut = config.get('Cuts',region)
        elif config.has_option(section, 'Datacut'):
            cut = cut=config.get(section, 'Datacut')
        else:
            cut = ''
        return [cut]

    def _minimum_cut(self, cutList):

     #  if config.has_option('Cuts',region):
     #       cut = config.get('Cuts',region)
     #   else:
     #       cut = None
     #       #print ("''Cuts' section doesn't contain any ",region)
     #   if config.has_option(section, 'Datacut'):
     #       cut=config.get(section, 'Datacut')
     cuts = []
     for cut in cutList:
        mcut = '(%s)'%cut.replace(' ','')
        if mcut not in cuts:
            cuts.append(mcut)
     return '||'.join(cuts)

    def _trim_tree(self, sample, filelist, mergeplot = False, forceReDo = False, mergeCachingPart = -1):

        # DEBUG
        #forceReDo = True

        start_time = time.time()
        print("Caching the sample")
        print("==================\n")

        sampleName = sample.name
        inputfiles = []
        outputfiles = []
        tmpfiles = []
        # prefix
        tmpCache = ''
        tmpSource = ''
        theHash = ''

        # regions
        regionDict = {}
        for region in self.regions:
            regionDict[region] = {}
            regionDict[region]['cut'] = self._minimum_cut(self._get_cuts(region))
            regionDict[region]['hashString'] = '%s_%s_split%d' %(sample, regionDict[region]['cut'], sample.mergeCachingSize)
            regionDict[region]['hash'] = hashlib.sha224(regionDict[region]['hashString']).hexdigest()
            regionDict[region]['tmpfileName'] = '%s/tmp_%s_%d.root'%(self.__tmpPath, regionDict[region]['hash'], mergeCachingPart)
            regionDict[region]['outputfileName'] = '%s/tmp_%s_%d.root'%(self.__cachedPath, regionDict[region]['hash'], mergeCachingPart)

        # filelist
        print ("#files:", len(filelist))
        if self.verbose:
            print ('-'*60)
            print (regionDict)
            print ("FILES:", filelist, mergeCachingPart)
            print ('-'*60)


        # check for existence of the individual tree INPUT files
        inputfile = ''
        if filelist and mergeCachingPart > -1:
            filelistCopied = []
            for inputFile in filelist:
                try:
                    subfolder = inputFile.split('/')[-4]
                    filename = inputFile.split('/')[-1]
                    filename = filename.split('_')[0]+'_'+subfolder+'_'+filename.split('_')[1]
                    hash = hashlib.sha224(filename).hexdigest()
                    inputFileNew = "%s/%s/%s" %(self.path,sample.identifier,filename.replace('.root','')+'_'+str(hash)+'.root')
                    if self.verbose:
                        print('inputFile2',inputFileNew,'isfile',os.path.isfile(inputFileNew.replace('root://t3dcachedb03.psi.ch:1094/','')))
                    filelistCopied.append(inputFileNew)
                except Exception as e:
                    print ('Exception:'+str(e))
                    print ('ERROR occured for "'+inputFile+'"')
            inputfile = ';'.join(filelistCopied)

        if self.verbose:
            print ("inputfiles:",inputfiles)

        #------------------------------------------------------------------------------------------------------------
        # check if CACHED file is existing
        #------------------------------------------------------------------------------------------------------------
        for region in self.regions:
            regionDict[region]['outputfileExists'] = self.file_valid(regionDict[region]['outputfileName'])

        # skip if ALL of the files exist
        if all([regionDict[region]['outputfileExists'] for region in self.regions]):
            print ('-'*60)
            print (' all cache files exist! => skipped')
            print ('-'*60)
            return True

        print("==================================================================")
        print ('The cuts are ')
        for region in self.regions:
            print ("  %s\t\t%s"%(region, regionDict[region]['cut']))
        print("==================================================================\n")

        # open OUTPUT files
        try:
            for region in self.regions:
                if not regionDict[region]['outputfileExists']:
                    regionDict[region]['tmpfile'] = ROOT.TFile.Open(regionDict[region]['tmpfileName'], 'recreate') # if forceReDo else 'create')
                else:
                    regionDict[region]['tmpfile'] = None

                print("Writing: ",regionDict[region]['tmpfile'])
        except Exception as e:
            print ('EXCEPTION',e)
            ## in case there are problems go to the next dataset [probably another process is working on this dataset]
            if len(filelist) == 0: return (theName,theHash)
            else:
                print('PROBLEM WITH FILE!!',tmpfile)
        if ';' in inputfile:
            print ('reading inputfiles...')
        else:
            print ('reading inputfile',inputfile)

        treeEmpty = True
        # ----------------------------------------------------------------------------------------------------------
        #  READ INPUT files
        # ----------------------------------------------------------------------------------------------------------
        # list -> TChain
        if ';' in inputfile:
            tree = ROOT.TChain(sample.tree)
            histograms = {}
            time1=time.time()
            nFilesChained = 0
            for rootFileName in inputfile.split(';'):
                # check root file existence
                if os.path.isfile(rootFileName.replace('root://t3dcachedb03.psi.ch:1094/','')):
                    obj = None
                    input = ROOT.TFile.Open(rootFileName,'read')
                    if input and not input.IsZombie():

                        # add count histograms, since they are not in the tchain
                        for key in input.GetListOfKeys():
                            obj = key.ReadObj()
                            if obj.GetName() == 'tree':
                                continue
                            for region in self.regions:
                                histogramName = obj.GetName()+region

                                if histogramName in histograms:
                                    if histograms[histogramName]:
                                        histograms[histogramName].Add(obj.Clone(obj.GetName()))
                                    else:
                                        print ("ERROR: histogram object was None!!!")
                                else:
                                    # copy count histogram to the appropriate output file
                                    histograms[histogramName] = obj.Clone(obj.GetName())
                                    histograms[histogramName].SetDirectory(regionDict[region]['tmpfile'])
                        input.Close()

                        # add file to chain
                        chainTree = '%s/%s'%(rootFileName, sample.tree)
                        if self.verbose:
                            print ('chaining '+chainTree)
                        statusCode = tree.Add(chainTree)

                        # check for errors in chaining the file
                        if statusCode != 1 or not tree:
                            print ('ERROR: failed to chain ' + chainTree + ', returned: ' + str(statusCode),'tree:',tree)
                            raise Exception("TChain method Add failure")
                        else:
                            treeEmpty = False
                            nFilesChained += 1
                    else:
                        print ('ERROR: Cant open file:'+chainTree)
            assert type(tree) is ROOT.TChain
            time2=time.time()

            print ('adding %d files to chain took %f seconds.'%(nFilesChained, time2-time1))
            assert nFilesChained > 0
            input = None

            if self.verbose:
                print ("HISTOGRAMS: %r"%histograms)
            #output.cd()
            #for histogramName, histogram in histograms.iteritems():
            #    histogram.SetDirectory(output)

        # single input file -> read it as TFile
        else:
            print ("I am reading")
            input = ROOT.TFile.Open(inputfile,'read')
            input.Print()
            print ("I read the tree")
            tree = input.Get(sample.tree)
            assert type(tree) is ROOT.TTree
            treeEmpty = False
            input.cd()

            obj = ROOT.TObject
            for key in ROOT.gDirectory.GetListOfKeys():
                input.cd()
                obj = key.ReadObj()
                if obj.GetName() == 'tree':
                    continue
                output.cd()
                obj.Write(key.GetName())

        # ----------------------------------------------------------------------------------------------------------
        #  CUTS
        # ----------------------------------------------------------------------------------------------------------
        if not treeEmpty:
            time1 = time.time()

            subcutExists = sample.subcut and sample.subcut.strip() != "1"

            # remove branches from tree
            if self.remove_sys:
                print ('INFO: useless branches will be removed!')
                tree.SetBranchStatus("*Down",0)
                tree.SetBranchStatus("*Up",0)

                removeBranches = []
                try:
                    removeBranches += eval(self.config.get('Branches','useless_after_sys'))
                except:
                    pass
                try:
                    removeBranches += eval(self.config.get('Branches','useless_branch'))
                except:
                    pass
                nBranchesRemoved = 0
                branchList = tree.GetListOfBranches()
                for branch in removeBranches:
                    try:
                        if branchList.FindObject(branch):
                            tree.SetBranchStatus(branch,0)
                            nBranchesRemoved += 1
                    except:
                        pass
                print ("# of branches removed:", nBranchesRemoved)

            # add branches to cache
            tree.AddBranchToCache("*")

            time2 = time.time()
            if self.verbose:
                print ('DEBUG: tree=',tree)

            # only process regions for which OUTPUT file is not existing
            self.regionsToProcess = [x for x in self.regions if regionDict[x]['tmpfile']]
            self.regionsSkipped = [x for x in self.regions if not regionDict[x]['tmpfile']]

            for region in self.regionsToProcess:
                regionDict[region]['cutFormula'] = ROOT.TTreeFormula("cutFormula_"+region, regionDict[region]['cut'], tree)
                regionDict[region]['subcutFormula'] = ROOT.TTreeFormula("subcutFormula_"+region, sample.subcut if subcutExists else '1', tree)
                regionDict[region]['cutTree'] = tree.CloneTree(0)
                regionDict[region]['cutTree'].SetDirectory(regionDict[region]['tmpfile'])
                regionDict[region]['filledEntries'] = 0

            print ('region dictionary created, now looping over the events')
            sys.stdout.flush()

            if self.verbose:
                print (regionDict)

            i = 0
            s = 0
            s2 = 0
            oldTreeNum = -1
            totalEntries = 0

            timeLoopStart = time.time()
            # loop over all events in tree/tchain
            for event in tree:
                tree.LoadTree(i)

                # if file changes in chain, UpdateFormulaLeaves() has to be called
                treeNum = tree.GetTreeNumber()
                if treeNum != oldTreeNum:
                    for region in self.regionsToProcess:
                        regionDict[region]['cutFormula'].UpdateFormulaLeaves()
                        regionDict[region]['subcutFormula'].UpdateFormulaLeaves()
                    oldTreeNum = treeNum

                # the GetNdata() here is used because of its side-effects!
                for region in self.regionsToProcess:
                    n1 = regionDict[region]['cutFormula'].GetNdata()
                    s = regionDict[region]['cutFormula'].EvalInstance()
                    passed = 0
                    if s:
                        n2 = regionDict[region]['subcutFormula'].GetNdata()
                        s2 = regionDict[region]['subcutFormula'].EvalInstance()
                        if s and s2:
                           regionDict[region]['cutTree'].Fill()
                           regionDict[region]['filledEntries'] += 1
                           passed = 1
                totalEntries += 1
                i += 1

                # output status
                if i % 10000 == 0:
                    timeNow = time.time()
                    eventsPerSecond = i/(timeNow-timeLoopStart) if timeNow-timeLoopStart > 0 else 0
                    timeETA = (timeNow-timeLoopStart)/(1.0*treeNum/nFilesChained)*(1-1.0*treeNum/nFilesChained) if treeNum > 0 else 0
                    print ('%d %%, tree: %d, event number: %d, ETA: %1.1f min'%(int(100.0*treeNum/nFilesChained), treeNum, i, timeETA/60.0))
                    if self.verbose and i % 100000:
                        print (' region\t\t\t#')
                        for region in self.regionsToProcess:
                            print (' %s\t\t\t%d'%(region, regionDict[region]['filledEntries']))
                    sys.stdout.flush()


            time3 = time.time()
            print ('cut done in ' + str(time3-time2) + ' s' + ' events: ' + str(totalEntries))
            print ('-------------------------------------------------------------------------')
            print ('  region\t\t\tentries\tpercent\tfile')
            for region in self.regionsToProcess:
                outputFileNameShort = regionDict[region]['outputfileName'].split('/')[-1]
                print ("  %s\t\t%d\t%1.3f\t%s"%(region, regionDict[region]['filledEntries'], (100.0* regionDict[region]['filledEntries']/totalEntries) if totalEntries>0 else 0, outputFileNameShort))
            print ('-------------------------------------------------------------------------')

            if len(self.regionsSkipped) > 0:
                print ('skipped:')
                for region in self.regionsSkipped:
                    print (' '+region)

        # ----------------------------------------------------------------------------------------------------------
        #  write OUTPUT
        # ----------------------------------------------------------------------------------------------------------
        print ('write to files...')
        for region in self.regions:
            if regionDict[region]['tmpfile']:
                regionDict[region]['tmpfile'].Write()

        print ('having written all files to disk fills you with determination')

        if input:
            input.Close()
            #del input
#        tmpSourceFile = ROOT.TFile.Open(tmpSource,'read')
#        if tmpSourceFile.IsZombie():
#            print("@ERROR: Zombie file")
        #del output
        print ("debug4")
        theName = '<thejob>'
        print ("I've done " + theName + " in " + str(time.time() - start_time) + " s.")

        # ----------------------------------------------------------------------------------------------------------
        # copy files TMP -> STORAGE
        # ----------------------------------------------------------------------------------------------------------
        copyTime0 = time.time()
        print ("Copying file to the tmp folder.")
        for region in self.regions:
            if not regionDict[region]['outputfileExists']:
                tmpfile = regionDict[region]['tmpfileName']
                outputFile = regionDict[region]['outputfileName']
                print('outputFile',outputFile)
                command = 'xrdcp -d 1 ' + tmpfile + ' ' + outputFile
                print('the command is', command)
                subprocess.call([command], shell=True)
                if '/scratch/' in  tmpfile: command = 'rm %s' %(tmpfile)
                else: command = 'gfal-rm %s' %(tmpfile)
                if not filelist or len(filelist) == 0: return (theName,theHash)
        copyTime1 = time.time()
        print ("Copy of files to cache dir is complete, that fills you with determination")
        print ("Copy files took " + str(copyTime1 - copyTime0) + " s.")

    def file_valid(self, file):
        #print ('Will now check if the file exists and is valid')
        #print ('==============================================\n')

        file_exists = False
        file_dummy = file
        file_dummy = file_dummy.replace('root://t3dcachedb03.psi.ch:1094/','')
        file_dummy = file_dummy.replace('srm://t3se01.psi.ch:8443/srm/managerv2?SFN=','')

        if self.verbose:
            print ('The command is', 'os.path.isfile(',file_dummy,')', os.path.isfile(file_dummy))

        if os.path.isfile(file_dummy):
            if self.verbose:
                print(file_dummy, 'exists.')
            f = ROOT.TFile.Open(file,'read')

            if not f or (f.GetNkeys() == 0 or f.TestBit(ROOT.TFile.kRecovered) or f.IsZombie()):
                if f:
                    print ('f.GetNkeys()',f.GetNkeys(),'f.TestBit(ROOT.TFile.kRecovered)',f.TestBit(ROOT.TFile.kRecovered),'f.IsZombie()',f.IsZombie())
                print ('File', file_dummy, 'already exists but is buggy, gonna delete and rewrite it.')
                del_protocol = file.replace('gsidcap://t3se01.psi.ch:22128/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=').replace('dcap://t3se01.psi.ch:22125/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=').replace('root://t3dcachedb03.psi.ch:1094/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=')
                if '/scratch/' in  del_protocol: command = 'rm %s' %(del_protocol)
                else: command = 'gfal-rm %s' %(del_protocol)
                subprocess.call([command], shell=True)
                print(command)
            else:
                file_exists = True
                #print ("E:"+file_dummy)

        return file_exists


if __name__ == "__main__":
    print ("Read Parameters")
    print ("===================\n")
    parser = OptionParser()
    parser.add_option("-R", "--region", dest="region", default="",
                          help="region to plot")
    parser.add_option("-C", "--config", dest="config", default=[], action="append",
                          help="configuration file")
    parser.add_option("-f", "--filelist", dest="filelist", default="",
                                  help="list of files you want to run on")
    parser.add_option("-m", "--mergeplot", dest="mergeplot", default=False,
                                  help="option to merge")
    parser.add_option("-M", "--mergecachingplot", dest="mergecachingplot", default=False, action='store_true', help="use files from mergecaching")
    parser.add_option("-s", "--settings", dest="settings", default=False,
                                  help="co ntains sample you want to merge, as well as the subcut bin")
    (opts, args) = parser.parse_args(sys.argv)
    if opts.config =="":
            opts.config = "config"

    # to avoid argument size limits, filelist can be encoded with 'base64:' + base64(zlib(.)), decode it first in this case
    if opts.filelist.startswith('base64:'):
        opts.filelist = zlib.decompress(base64.b64decode(opts.filelist[7:]))

    # config
    vhbbPlotDef=opts.config[0].split('/')[0]+'/vhbbPlotDef.ini'
    opts.config.append(vhbbPlotDef)#adds it to the config list
    config = BetterConfigParser()
    config.read(opts.config)

    # input/output files
    path = config.get('Directories','plottingSamples')
    filelist = filter(None,opts.filelist.replace(' ', '').split(';'))
    mergeCachingPart = int(opts.settings[opts.settings.find('CACHING')+7:].split('__')[0].split('_')[-1])
    sampleToMerge = '__'.join(opts.settings[opts.settings.find('CACHING')+7:].split('__')[1:])
    samples = None
    mc = MultiCache(regions=opts.region, sampleList=samples, path=path, config=config, filelist=filelist, sample_to_merge=sampleToMerge, mergeCachingPart=mergeCachingPart)



