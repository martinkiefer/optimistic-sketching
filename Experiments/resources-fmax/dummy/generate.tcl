package require fileutil
set project_name cproject

set outputdir ./
create_project -part xcvu13p-fhga2104-3-e $project_name $outputdir
add_files [glob ./sketch/*.vhd]
add_files -fileset constrs_1 ./constraints.xdc 
set_property top tl [current_fileset]
set_property STEPS.SYNTH_DESIGN.ARGS.KEEP_EQUIVALENT_REGISTERS true [get_runs synth_1]
set_property STEPS.SYNTH_DESIGN.ARGS.FLATTEN_HIERARCHY none [get_runs synth_1]

if { "[lindex $argv 0]" == "1" } {
    set_property strategy Congestion_SSI_SpreadLogic_high [get_runs impl_1]
} elseif { "[lindex $argv 0]" == "2" } {
    set_property strategy Performance_ExplorePostRoutePhysOpt [get_runs impl_1]
} elseif { "[lindex $argv 0]" == "3" } {
    set_property strategy Area_Explore  [get_runs impl_1]
} elseif { "[lindex $argv 0]" == "4" } {
    set_property strategy Congestion_SSI_SpreadLogic_low [get_runs impl_1]
} else {
    set_property strategy Performance_RefinePlacement [get_runs impl_1]
}


foreach file [fileutil::findByPattern ./sketch *.tcl] {
    source $file
}

launch_runs synth_1 -jobs 20
wait_on_run synth_1
launch_runs impl_1 -jobs 20
wait_on_run impl_1
open_run impl_1
report_utilization -hierarchical  -file utilization_hierarchy.rpt
