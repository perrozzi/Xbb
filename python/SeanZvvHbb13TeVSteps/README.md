##Instructions for ZvvHbb on LXPLUS

*Disclaimer: This package is under active development. The default branch, V20_from_silvio, is guaranteed to run at PSI or Pisa. The version that David uses runs on LXPLUS, but may or may not be synchronized with the default branch. The default branch is being tested on LXPLUS and, pending potential modifications and updates, should be verified to run on LXPLUS by the end of next week.*

*My dream is to run this within an IPython notebook in some sort of packaged distribution so that the code is frozen and the results easily reproducible. It's a lofty goal, but it'd be a great way to demonstrate open science.*

###Installation
  
Checkout a CMSSW_7_1_X (X >= 5) release and clone the [Xbb](https://github.com/perrozzi/Xbb) repository within its src/ directory. The [HiggsAnalysis-CombinedLimit](https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit) package used by the analysis is only validated for use with those versions of CMSSW according to [documentation](https://twiki.cern.ch/twiki/bin/view/CMS/SWGuideHiggsAnalysisCombinedLimit).
  
```bash
export SCRAM_ARCH=slc6_amd64_gcc481
cmsrel CMSSW_7_1_5
# To checkout the CMSSW release under a different name
# scram project -n some_name CMSSW_7_1_5
cd CMSSW_7_1_5/src; cmsenv
# SSH
git clone git@github.com:perrozzi/Xbb.git
# HTTPS
# git clone https://github.com/perrozzi/Xbb.git
```

The configuration files are located in [SeanZvvHbb13TeVconfig/](../SeanZvvHbb13TeVconfig). The relevant configuration options will be referenced as we move through the steps, but feel free to peruse those files for a sense of their use. My intention is to leave the bulk of the documentation within the configuration files when it is sensible to do so, such that they document themselves.

Unlike Python 3, Python 2's ConfigParser module does not support interpolation of options across sections. This is addressed by the [BetterConfigParser](../myutils/BetterConfigParser.py) class, which provides support for such extended interpolation using the `<!section|option!>` syntax.

The steps to run are located in [SeanZvvHbb13TeVSteps/](../SeanZvvHbb13TeVSteps). All of the commands and steps mentioned should be run from within the Xbb/python/ directory.

###1. Set Up the Working Environment

Set the options in the **[Configuration]** section and **Working Environment** subsection of [**paths.ini**](../SeanZvvHbb13TeVconfig/paths.ini).

While there are eight cores available on LXPLUS, it is better to lower the number of processes when testing and debugging. From browsing other users' configuration files, I've seen directory paths end with and without a trailing slash. I've adopted the convention to omit the trailing slash.
  
###2. **Prepare the Samples**
  
The ntuples for the samples are stored at INFN's Tier2 computing center in Pisa (grazie a Andrea). The large size of these ntuples makes them unwieldy to repeatedly process when optimizing an analysis strategy, so they are first skimmed with a selection cut to reduce their size and copied locally for convenience.

Set the options in the **Preparation Step** subsection of [**paths.ini**](../SeanZvvHbb13TeVconfig/paths.ini).

Set the options in the **[General]** section of [**samples_nosplit.ini**](../SeanZvvHbb13TeVconfig/samples_nosplit.ini) and, below the **[Samples_running]** section, create or modify the sample sections.

Run the [das_query.py](../das_query.py) script, which will query the [CMS Data Aggregation System](https://cmsweb.cern.ch/das/) (DAS) to locate the sample (or dataset) and its corresponding ntuples (or files).
```bash
./das_query.py SeanZvvHbb13TeVconfig
```
The script should finish in under ten minutes. There should be a new directory within SeanZvvHbb13TeVconfig/ which contains files filled with logical file names (LFNs) for each sample.

To skim and copy a sample, run the [prep.py](../prep.py) script.
```bash
# Create a valid GRID proxy to access remote files.
voms-proxy-init -voms cms
./prep.py SeanZvvHbb13TeVconfig sampleName
```
The [TreeCopier](../utils/treecopier.py) class will skim and copy ntuples using eight processes. The time it takes to finish varies based on the number of ntuples to prepare, the skimming selection, and the connection to the remote server.

Otherwise, run the [Step0_prep.sh](Step0_prep.sh) script to skim and copy all the samples.
```bash
# Create a valid GRID proxy to access remote files.
voms-proxy-init -voms cms
bash SeanZvvHbb13TeVSteps/Step0_prep.sh
```
This will definitely take a lot of time to finish, on the order of half a day.

If you want to run this script from within a screen or tmux session so you don't have to worry about disconnecting from LXPLUS, see this [article](https://cern.service-now.com/service-portal/article.do?n=KB0002408). Here's an example bash function that I use to create a tmux session with kerberos authentication renewal, where the first command line argument is the name given to the session.
```bash
ktmux () {
    AKLOG=/usr/bin/aklog krenew -b -t -- tmux new-session -d -s $1; tmux send-keys -t $1:0.0 "cd $(pwd)" C-m
}
```
**Remember the LXPLUS node on which you launched the tmux session!**
