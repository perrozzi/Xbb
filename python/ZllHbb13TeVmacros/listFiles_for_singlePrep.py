import glob, sys, os, re

vetoed_datasets = [
                   "BulkGravTohhTohbbhbb_narrow_M",
                   "DYBJetsToNuNu_Zpt",
                   "DYJetsToNuNu_TuneCUETP8M1_13TeV",
                   "DYJetsToQQ_HT180_13TeV",
                   "GluGluHToBB_M120_13TeV_powheg_pythia8",
                   "GluGluToBulkGravitonToHHTo4B_M",
                   "GluGluToHHTo4B_node_",
                   "MuEnrichedPt5",
                   "QCD_Pt_",
                   ]

VHBBHeppy_version = 'VHBBHeppyV21bis'

# intput_file = str(VHBBHeppy_version)+'.txt'
#intput_file = 'DYB.txt'
intput_file = 'V21bis.txt'

das = "../das_client.py"

def cleanList(l):
    l = [w.strip() for w in l]
    l = filter(lambda x: len(x)>0, l)
    return l

def getFiles(dataset):
    files = os.popen('python {0} --query=\"file dataset={1} instance=prod/phys03\" --limit=0'.format(das, dataset)).read().split("\n")
    return sorted(cleanList(files))

if __name__ == "__main__":
    datasets = open(intput_file).readlines()
    datasets = cleanList(datasets)
    counter=1

    if not os.path.isdir(VHBBHeppy_version+"_files"): os.system("mkdir "+VHBBHeppy_version+"_files")

    for dataset in datasets:

        # for vetoed_dataset in vetoed_datasets:
            # vetoed = re.search(vetoed_dataset,dataset)
            # break
        # if vetoed:
            # # print 'dataset',dataset,'vetoed',vetoed
            # continue

        # print 'dataset',dataset,'vetoed',vetoed
        # continue

        filename = (dataset[1:]).split("/")[0].replace("/","_")
        # print 'step1',filename

        ext = ''
        if '_ext' in dataset:
            filename = filename+'_ext'+(dataset[1:]).split("_ext")[1][:1]
        # print 'step2',filename

        # add customization string (not needed so far)
        # filename = filename+'__'+(dataset[1:]).split("/")[1].split(filename[:10])[0].replace("/","_")[:-1]
        # print 'step3',filename

        if 'Run' in dataset:
            filename = (dataset[1:]).split("/")[0].replace("/","_")+(dataset[1:])[:-38].split((dataset[1:]).split("/")[0].replace("/","_"))[2]
        # print 'step4',filename

        if os.path.isfile(VHBBHeppy_version+"_files/"+filename+".txt"):
            print "TERREMOTO E TRAGEDIA, "+VHBBHeppy_version+"_files/"+filename+".txt from dataset ",dataset,"already exists!!!"
            # os.system("sleep 30")

        outfile = open(VHBBHeppy_version+"_files/"+filename+".txt", "w")
        files = getFiles(dataset)
        print 'retrieving info on dataset',dataset,'txt filename',filename,'counter '+str(counter)+'/'+str(len(datasets))
        counter=counter+1
        for file in files:
            outfile.write(str(file)+'\n')
        outfile.close()
