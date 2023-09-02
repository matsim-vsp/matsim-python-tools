#!/bin/bash --login
#$ -l h_rt=700000
#$ -j y
#$ -m a
#$ -o ./logfile/logfile_$JOB_NAME.log
#$ -cwd
#$ -pe mp 3
#$ -l mem_free=3G
#$ -N sumo

date
hostname

source env/bin/activate

ENV=$(realpath "env")

export LD_LIBRARY_PATH="$ENV/lib64:$ENV/lib:$LD_LIBRARY_PATH"
export SUMO_HOME="$ENV/share/sumo/"

# use with -t 1-10
idx=$((SGE_TASK_ID - 1))
total=$SGE_TASK_LAST

mode="routes"
scenario="base"
network="sumo.net.xml"

f="output-${mode}/scenario-$scenario"

command="python -u -m matsim.scenariogen sumo-${mode} ${mode}.txt --scenario $scenario --network $network --output $f --runner runner/${JOB_ID}${SGE_TASK_ID} --runner-index $idx --runner-total $total"

echo ""
echo "command is $command"
echo ""

$command
python -u -m matsim.scenariogen sumo-collect-results $mode --input $f