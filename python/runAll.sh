#!/bin/bash
#====================================================================
#
#        FILE: runAll.sh
#
#       USAGE: runAll.sh sample energy task
#
# DESCRIPTION: Script to be launched in the batch system.
#              Can also be used, with some care, to run locally.
#
#      AUTHOR: VHbb team
#              ETH Zurich
#
#=====================================================================



# fix for python escape sequence bug:
export TERM=""

#Input argument:
sample=$1           # sample you want to run on. It has to match the naming in sample.info.
energy=$2           # sqrt(s) you want to run
task=$3             # the task 
nprocesses=$4       # Dummy variable, used to shift the other parameters by +1
job_id=$5           # needed for split step and train optimisation. @TO FIX: it does not have a unique meaning
additional_arg=$6   # needed for train optimisation
optional_filelist=$7 # needed to run the prep and sys step with limited number of files per job

# echo '1:'${1}' 2:'${2}' 3:'${3}' 4:'${4}' 5:'${5}' 6:'${6}
echo 
echo 'Reading ./'${energy}'config'
echo 'task'$task
echo 

whereToLaunch=`python << EOF 
import os
from myutils import BetterConfigParser
config = BetterConfigParser()
config.read('./${energy}config/paths.ini')
print config.get('Configuration','whereToLaunch')
EOF`
echo 'whereToLaunch= '$whereToLaunch

#-------------------------------------------------
# Read debug variable
#-------------------------------------------------

DEBUG=`python << EOF 
import os
from myutils import BetterConfigParser
config = BetterConfigParser()
config.read('./${energy}config/general.ini')
print config.get('General','Debug')
EOF`

echo "Debug is " $DEBUG

#-------------------------------------------------
# Check the number of input arguments
#-------------------------------------------------

if [[ $DEBUG -eq "True" ]]
  then
  echo ""
  echo "Checking the number of input arguments"
  echo ""
fi

if [ $# -lt 3 ]
    then
    echo "ERROR: You passed " $# "arguments while the script needs at least 3 arguments."
    echo "Exiting..."
    echo " ---------------------------------- "
    echo " Usage : ./runAll.sh sample energy task"
    echo " ---------------------------------- "
    exit
fi

#------------------------------------------------
# get the log dir from the config and create it
#------------------------------------------------
logpath=`python << EOF 
import os
from myutils import BetterConfigParser
config = BetterConfigParser()
config.read('./${energy}config/paths.ini')
print config.get('Directories','logpath')
EOF`
if [ ! -d $logpath ]
    then
    mkdir -p $logpath
fi

if [[ $whereToLaunch == "pisa" ]]; then
    export TMPDIR=$CMSSW_BASE/src/tmp
fi

MVAList=`python << EOF 
import os
from myutils import BetterConfigParser
config = BetterConfigParser()
config.read('./${energy}config/training.ini')
print config.get('MVALists','List_for_submitscript')
EOF`


#----------------------------------------------
# load from the paths the configs to be used
#----------------------------------------------
input_configs=`python << EOF 
import os
from myutils import BetterConfigParser
config = BetterConfigParser()
config.read('./${energy}config/paths.ini')
print config.get('Configuration','List')
EOF`
required_number_of_configs=7                                             # set the number of required cconfig
input_configs_array=( $input_configs )                                   # create an array to count the number of elements
if [ ${#input_configs_array[*]} -lt $required_number_of_configs ]        # check if the list contains the right number of configs
    then 
    #echo "@ERROR : The number of the elements in the config list is not correct"
    #exit
    echo "@LOG : The number of config files you are using is"
    echo ${#input_configs_array[*]}
fi
configList=${input_configs// / -C ${energy}config\/}                     # replace the spaces with ' -C '
echo "@LOG : The config list you are using is"
echo ${configList}
echo "task is"
echo ${task}


#------------------------------------
#Run the scripts
#------------------------------------

echo "============================"
echo "Will Lauch the script"
echo "============================"
echo "The command is"

if [ $task = "prep" ]; then
    echo "./prepare_environment_with_config.py --samples $sample --config ${energy}config/${configList} --config ${energy}config/samples_nosplit.ini"
    ./prepare_environment_with_config.py --samples $sample --config ${energy}config/${configList} --config ${energy}config/samples_nosplit.ini
fi

if [ $task = "singleprep" ]; then
    echo './prepare_environment_with_config.py --samples $sample --config ${energy}config/${configList} --config ${energy}config/samples_nosplit.ini --filelist "${optional_filelist}"'
    ./prepare_environment_with_config.py --samples $sample --config ${energy}config/${configList} --config ${energy}config/samples_nosplit.ini --filelist "${optional_filelist}"
fi

if [ $task = "mergesingleprep" ]; then
    echo './myutils/mergetreePSI.py --samples $sample --config ${energy}config/${configList} --config ${energy}config/samples_nosplit.ini --filelist "${optional_filelist}"'
    ./myutils/mergetreePSI.py --samples $sample --config ${energy}config/${configList} --config ${energy}config/samples_nosplit.ini --filelist "${optional_filelist}"
fi

if [ $task = "trainReg" ]; then
    echo "./trainRegression.py --config ${energy}config/${configList} --config ${energy}config/regression.ini"
    ./trainRegression.py --config ${energy}config/${configList} --config ${energy}config/regression.ini
fi

if [ $task = "singlesys" ]; then
    echo "singlesys: ./write_regression_systematics.py --samples $sample --config ${energy}config/${configList} --filelist ${optional_filelist}"
    ./write_regression_systematics.py --samples $sample --config ${energy}config/${configList} --filelist ${optional_filelist}
fi

if [ $task = "sys" ]; then
    echo "./write_regression_systematics.py --samples $sample --config ${energy}config/${configList}"
    ./write_regression_systematics.py --samples $sample --config ${energy}config/${configList}
fi

if [ $task = "mergesinglesys" ]; then
    echo './myutils/mergetreePSI.py --samples $sample --config ${energy}config/${configList} --config ${energy}config/samples_nosplit.ini --filelist "${optional_filelist}"'
    ./myutils/mergetreePSI.py --samples $sample --config ${energy}config/${configList} --config ${energy}config/samples_nosplit.ini --filelist "${optional_filelist}" --mergesys "True"
fi

if [ $task = "reg" ]; then
    ./only_regression.py --samples $sample --config ${energy}config/${configList}
fi

if [ $task = "eval" ]; then
    echo "./evaluateMVA.py --discr $MVAList --samples $sample --config ${energy}config/${configList}"
    ./evaluateMVA.py --discr $MVAList --samples $sample --config ${energy}config/${configList}
fi

if [ $task = "syseval" ]; then
    echo "./write_regression_systematics.py --samples $sample --config ${energy}config/${configList}"
    ./write_regression_systematics.py --samples $sample --config ${energy}config/${configList}
    echo "./evaluateMVA.py --discr $MVAList --samples $sample --config ${energy}config/${configList}"
    ./evaluateMVA.py --discr $MVAList --samples $sample --config ${energy}config/${configList}
fi

if [ $task = "train" ]; then
    echo "./train.py --training $sample --config ${energy}config/${configList} --local True"
    python train.py --training $sample --config ${energy}config/${configList} --local True
fi

if [ $task = "plot" ]; then
    echo "./tree_stack.py --region $sample --config ${energy}config/${configList}"
    ./tree_stack.py --region $sample --config ${energy}config/${configList}
fi

if [ $task = "singleplot" ]; then
    echo "./prepare_plot_trees.py --samples $sample --config ${energy}config/${configList} --filelist ${optional_filelist}"
    ./prepare_plot_trees.py --samples $sample --config ${energy}config/${configList} --filelist "${optional_filelist}"
fi

if [ $task = "dc" ]; then
    echo "./workspace_datacard.py --variable $sample --config ${energy}config/${configList}  --config ${energy}config/datacards.ini"
    ./workspace_datacard.py --variable $sample --config ${energy}config/${configList}  --config ${energy}config/datacards.ini
fi

if [ $task = "split" ]; then
    echo "./split_tree.py --samples $sample --config ${energy}config/${configList} --max-events $job_id"
    ./split_tree.py --samples $sample --config ${energy}config/${configList} --max-events $job_id
fi

if [ $task = "stack" ]; then
    echo "./manualStack.py --config ${energy}config/${configList}"
    ./manualStack.py --config ${energy}config/${configList}
fi

if [ $task = "plot_sys" ]; then
    ./plot_systematics.py --config ${energy}config/${configList}
fi
if [ $task = "mva_opt" ]; then
    if [ $# -lt 5 ]
  then
  echo "@ERROR: You passed " $# "arguments while BDT optimisation needs at least 5 arguments."
  echo "Exiting..."
  echo " ---------------------------------- "
  echo " Usage : ./runAll.sh sample energy task jo_id bdt_factory_settings"
  echo " ---------------------------------- "
  exit
    fi
    echo "BDT factory settings"
    echo $additional_arg
    echo "Runnning"
    python -u train.py --name ${sample} --training ${job_id} --config ${energy}config/${configList} --setting ${additional_arg} --local True
fi
if [ $task = "mva_opt_eval" ]; then
    ./evaluateMVA.py --discr $MVAList --samples $sample --config ${energy}config/${configList} --weight ${additional_arg}
fi
#Work in progress
if [ $task = "mva_opt_dc" ]; then
    echo "python -u workspace_datacard.py --variable $sample --config ${energy}config/${configList}  --config ${energy}config/datacards.ini --optimisation ${additional_arg}"
    python -u workspace_datacard.py --variable $sample --config ${energy}config/${configList}  --config ${energy}config/datacards.ini --optimisation ${additional_arg}
fi

echo "end runAll.sh"
