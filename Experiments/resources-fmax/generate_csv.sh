dir=$(pwd)

cd $1
for d in */; do 
    d=${d::-1}
    if test -f "$d/utilization_hierarchy.rpt"; then
        c=$(echo $d | tr " " ,)
        c=$(echo $c | tr . ,)
        t=$(python ${dir}/timing_to_csv.py "$d/cproject.runs/impl_1/tl_timing_summary_routed.rpt")
        for l in $(python ${dir}/util_to_csv.py "$d/utilization_hierarchy.rpt"); do
            echo $c,$l,$t
        done
    fi
done
cd $dir
