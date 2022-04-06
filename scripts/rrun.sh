#!/bin/bash
# A script to generate a job and submit for some R script

# USAGE: sh /home/data/NDClab/tools/lab-devOps/scripts/rrun.sh <file_name>.R
usage() { echo "Usage: sh rrun.sh <file_name>.R" 1>&2; exit 1; }

file_name=$2

if [ ! -f $2 || "$file_name" == "*.R" ] 
then
    echo "File $2 does not exist or is not an R file." 
    exit 9999 
fi

# Generate sub file
sub_file="${file_name}.sub"

echo -e  "#!/bin/bash\\n
#SBATCH --nodes=1\\n
#SBATCH --ntasks=1\\n
#SBATCH --time=01:00:00\\n
module load r-4.0.2-gcc-8.2.0-tf4pnwr\\n
Rscript ${file_name}.R" >| $sub_file

# Submit sub file
echo "Submitting $sub_file as job"
sbatch $sub_file

# Give confirmation message and instructions
echo "Job submitted. To rerun again, execute \'sbatch $sub_file \'"
