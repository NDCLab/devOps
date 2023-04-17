#!/bin/bash
IFS=$'\n'
TOOL_PATH="/home/data/NDClab/tools"
DATA_PATH="/home/data/NDClab/datasets"
ANA_PATH="/home/data/NDClab/analyses"
LOG_PATH="/home/data/NDClab/other/logs/repo-updates"
LAB_MGR="ndclab"
LAB_TECH=$(grep "technician" $TOOL_PATH/lab-devOps/scripts/configs/config-leads.json | cut -d":" -f2 | tr -d '"",')
repoarr=()

echo "Checking repos in tools"
for REPO in `ls $TOOL_PATH`
do
  echo "Checking $REPO"
  if [ -e "$TOOL_PATH/$REPO/.git" ]
    then
      cd "$TOOL_PATH/$REPO"
      git fetch
      MSG=$(git pull 2>&1)
      echo $MSG # make sure to output (possible) error message to log file
      [[ $MSG =~ "error: Your local changes" ]] && repoarr+=("$REPO")
    else
      echo "Not a git repo. Skipping."
  fi
done

echo "Checking repos in datasets"
for REPO in `ls $DATA_PATH`
do
  echo "Checking $REPO"
  if [ -e "$DATA_PATH/$REPO/.git" ]
    then
      cd "$DATA_PATH/$REPO"
      git fetch
      MSG=$(git pull 2>&1)
      echo $MSG
      [[ $MSG =~ "error: Your local changes" ]] && repoarr+=("$REPO")
    else
      echo "Not a git repo. Skipping."
   fi
done

echo "Checking repos in analyses"
for REPO in `ls $ANA_PATH`
do
  echo "Checking $REPO"
  if [ -e "$ANA_PATH/$REPO/.git" ]
    then
      cd "$ANA_PATH/$REPO"
      git fetch
      MSG=$(git pull 2>&1)
      echo $MSG
      [[ $MSG =~ "error: Your local changes" ]] && repoarr+=("$REPO")
    else
      echo "Not a git repo. Skipping."
   fi
done

if [ ${#repoarr[@]} -gt 0 ]
then
    for repo in ${repoarr[@]}
    do
        PROJ_LEAD=$(grep "$repo" $TOOL_PATH/lab-devOps/scripts/configs/config-leads.json | cut -d":" -f2 | tr -d '"",')
        if [[ $PROJ_LEAD == "" ]]; then
            echo "Can't find proj lead for $repo, emailing lab tech"
            echo "git pull failed for $repo, no project lead found in config-leads.json." | mail -s \
            "$repo needs re-sync with Github" "$LAB_TECH@fiu.edu"
        else
            # email proj lead
            echo "As project lead, you are being notified that there are changes on the HPC in the $repo repo that have not " \
            "been pushed to the GitHub remote. Please identify the source of these changes and complete the git sequence to re-sync " \
            "with the GitHub remote." | mail -s "$repo needs to be re-synced with Github" "$PROJ_LEAD@fiu.edu"
        fi
    done
    # escalation after > 3 days
    last_week=`date -d "3 days ago" +%m_%d_%Y`
    for log in $(ls $LOG_PATH/$last_week* 2>/dev/null); do
        repos=($(cat $log | grep -B 1 "error: Your local changes")) # Previous line should contain name of repo
        for line in ${repos[@]}; do
            if [[ "$line" =~ "Checking" ]]; then
                # email lab mgr
                repo=$(echo "$line" | cut -d" " -f2)
                PROJ_LEAD=$(grep "$repo" $TOOL_PATH/lab-devOps/scripts/configs/config-leads.json | cut -d":" -f2 | tr -d '"",')
                if [[ "${repoarr[*]}" =~ "$repo" ]]; then
                    echo "$repo has not been synced with Github remote since at least $last_week. Please follow up with project lead " \
                    "${PROJ_LEAD:-\"unknown\"} about committing unsaved changes." | mail -s "$repo needs re-sync" "$LAB_MGR@fiu.edu"
                fi
            fi
        done
    done
fi
