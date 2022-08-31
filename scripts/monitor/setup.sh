#!/bin/bash
# A script to set up data monitoring & preprocessing in your project

usage() { echo "Usage: setup.sh [-t] <project-path> [datatype1,datatype2,datatype3] [id-standard] [task1,task2,task3]" 1>&2; exit 1; }

datam_path="data-monitoring"
code_path="code"
labpath="/home/data/NDClab/tools/lab-devOps/scripts/monitor"

# TODO: include ndc colors
cat << "EOF"
 .__   __.  _______   ______  __          ___      .______
 |  \ |  | |       \ /      ||  |        /   \     |   _  \
 |   \|  | |  .--.  |  ,----'|  |       /  ^  \    |  |_)  |
 |  . `  | |  |  |  |  |     |  |      /  /_\  \   |   _  <
 |  |\   | |  '--'  |  `----.|  `----./  _____  \  |  |_)  |
 |__| \__| |_______/ \______||_______/__/     \__\ |______/
EOF

echo -e "data monitoring setting up ... \\n"
sleep 2

# interpret optional t flag to construct tracker
if [ "$1" = "-t" ]; then 
    project=$2
    datatypes=$3
    ids=$4
    # Optional tasks arg 
    tasks=${5:-0}
    echo "Setting up central tracker"
    python "${labpath}/gen-tracker.py" "${project}${datam_path}/central-tracker_${project::-1}.csv" $datatypes $ids \$2 
    chmod +x "${project}/${datam_path}/central-tracker_${project::-1}.csv"
else
    project=$1
    datatypes=$2
    ids=$3
    # Optional tasks arg 
    tasks=${4:-0}
fi

#TODO: loop through a list, collect list from dir.

echo "Setting up hallMonitor helper files"
# delete if previously written
if [ -f "${project}/${datam_path}/rename-cols.py" ]; then
    rm -f "${project}/${datam_path}/rename-cols.py"
fi
if [ -f "${project}/${datam_path}/update-tracker.py" ]; then
    rm -f "${project}/${datam_path}/update-tracker.py"
fi
if [ -f "${project}/${datam_path}/check-id.py" ]; then
    rm -f "${project}/${datam_path}/update-tracker.py"
fi
cp "${labpath}/template/rename-cols.py" "${project}/${datam_path}"
cp "${labpath}/template/update-tracker.py" "${project}/${datam_path}"
cp "${labpath}/template/check-id.py" "${project}/${datam_path}"

# give permissions for all copied files
chmod +x "${project}/${datam_path}/rename-cols.py"
chmod +x "${project}/${datam_path}/update-tracker.py"

echo "Setting up hallMonitor.sh"
# delete if previously written
if [ -f "${project}/${datam_path}/hallMonitor.sh" ]; then
    rm -f "${project}/${datam_path}/hallMonitor.sh"
fi
if [ -f "${project}/${datam_path}/hallMonitor.sub" ]; then
    rm -f "${project}/${datam_path}/hallMonitor.sub"
fi
# set up hallMonitor sh file with preset tasks instead of simply copying
sh "${labpath}/constructMonitor.sh" "/home/data/NDClab/datasets/${project}" $datatypes $tasks
# sets up hallMonitor sub file without any default mapping or replacement
cp "${labpath}/template/hallMonitor.sub" "${project}/${datam_path}"

# give permissions for all copied files
chmod +x "${project}/${datam_path}/hallMonitor.sh"
chmod +x "${project}/${datam_path}/hallMonitor.sub"

echo "Setting up preprocess.sub"
# delete if previously written
if [ -f "${project}/${datam_path}/inst-tracker.py" ]; then
    rm -f "${project}/${datam_path}/inst-tracker.py"
fi
if [ -f "${project}/${datam_path}/preprocess.sub" ]; then
    rm -f "${project}/${datam_path}/preprocess.sub"
fi
cp "${labpath}/template/preprocess.sub" "${project}/${datam_path}"
cp "${labpath}/template/inst-tracker.py" "${project}/${datam_path}"

# give permissions for all copied files
chmod +x "${project}/${datam_path}/preprocess.sub"
chmod +x "${project}/${datam_path}/inst-tracker.py"
chmod +x "${project}/${datam_path}/check-id.py"