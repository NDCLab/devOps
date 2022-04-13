#!/bin/bash
# A script to generate a job and submit for some R script

# USAGE: sh /home/data/NDClab/tools/lab-devOps/scripts/rrun.sh <file_name>.R
usage() { echo "Usage: sh rmat.sh [--parallel] <file_name>.m" 1>&2; exit 1; }

file_name=$2

if [ ! -f $2 || "$file_name" == "*.m" ] 
then
    echo "File $2 does not exist or is not a matlab file." 
    exit 9999 
fi

# Generate sub file
sub_file="${file_name}.sub"

if [[ $* == *--parallel* ]]; then
    exec_line="matlab -nodisplay -nosplash -r ${file_name}"
    cpus="4"
else
    exec_line="matlab -singleCompThread -nodisplay -nosplash -r ${file_name}"
    cpus="1"
fi

echo -e  "#!/bin/bash\\n
#SBATCH --nodes=1\\n
#SBATCH --ntasks=1\\n
#SBATCH --time=01:00:00\\n
#SBATCH --cpus-per-task=${cpus}\\n
module load matlab-2018b\\n
${exec_line}" >| $sub_file

# Submit sub file
echo "Submitting $sub_file as job"
sbatch $sub_file

# Give confirmation message and instructions
echo -e "Job submitted. To rerun again, execute \\'sbatch $sub_file \\'"
