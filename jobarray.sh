#!/usr/bin/env bash
#
#SBATCH -J vary_num  # give the job a name   
#
# 1 node, 12 CPUs per node (total 12 CPUs), no GPU, wall clock time of hours
#
#SBATCH -N 1                     ## Node count
#SBATCH --ntasks=1              ## Tasks
#SBATCH --cpus-per-task=12        ## CPUs per task; number of threads of each task
#SBATCH -t 56:00:00              ## Walltime
#SBATCH --mem=40GB
#SBATCH -p research              ## Partition
#SBATCH --error=./eulerlog/array_job_slurm_%A_%a.err
#SBATCH --output=./eulerlog/array_job_slurm_%A_%a.out


source ~/.bashrc

echo "SLURM_JOBID: " $SLURM_JOBID
echo "SLURM_ARRAY_TASK_ID: " $SLURM_ARRAY_TASK_ID
echo "SLURM_ARRAY_JOB_ID: " $SLURM_ARRAY_JOB_ID

conda activate py39

echo "======== testing CPU available ========"
echo "running on machine: " $(hostname -s)

lscpu | grep '^CPU(s):'
lscpu | grep 'Model name'
lscpu | grep 'MHz'
lscpu | grep 'Architecture'
echo "======== run with different inputs ========"

python ticker_selecter_parallel.py --idx $( awk "NR==$SLURM_ARRAY_TASK_ID" config/sequence.txt ) 

	#| tee ./output_folder/output_$(awk "NR==$SLURM_ARRAY_TASK_ID" config/sequence.txt).txt 

# sbatch --array=1-20 jobarray.sh



