################################################################################
# Vivado tcl script for building RedPitaya FPGA in non project mode
#
# Usage:
# vivado -mode tcl -source red_pitaya_vivado.tcl
################################################################################

################################################################################
# define paths
################################################################################

set path_rtl rtl
set path_ip  ip
set path_sdc sdc

set path_out out
set path_sdk sdk

file mkdir $path_out
file mkdir $path_sdk

################################################################################
# setup an in memory project
################################################################################

set part xc7z010clg400-1

create_project -in_memory -part $part

# experimental attempts to avoid a warning
#get_projects
#get_designs
#list_property  [current_project]
#set_property FAMILY 7SERIES [current_project]
#set_property SIM_DEVICE 7SERIES [current_project]

################################################################################
# create PS BD (processing system block design)
################################################################################

# file was created from GUI using "write_bd_tcl -force ip/system_bd.tcl"
# create PS BD
source                            $path_ip/system_bd.tcl

# generate SDK files
generate_target all [get_files    system.bd]
write_hwdef              -file    $path_sdk/red_pitaya.hwdef

################################################################################
# read files:
# 1. RTL design sources
# 2. IP database files
# 3. constraints
################################################################################

# template
#read_verilog                      $path_rtl/...

read_verilog                      .gen/sources_1/bd/system/hdl/system_wrapper.v

read_verilog                      $path_rtl/axi_master.v
read_verilog                      $path_rtl/axi_slave.v
read_verilog                      $path_rtl/axi_wr_fifo.v

read_verilog                      $path_rtl/red_pitaya_ams.v
read_verilog                      $path_rtl/red_pitaya_asg_ch.v
read_verilog                      $path_rtl/red_pitaya_asg.v
read_verilog                      $path_rtl/red_pitaya_dfilt1.v
read_verilog                      $path_rtl/red_pitaya_hk.v
read_verilog                      $path_rtl/red_pitaya_pid_block.v
read_verilog                      $path_rtl/red_pitaya_pid.v
read_verilog                      $path_rtl/red_pitaya_pll.sv
read_verilog                      $path_rtl/red_pitaya_ps.v
read_verilog                      $path_rtl/red_pitaya_pwm.sv
read_verilog                      $path_rtl/red_pitaya_scope.v
read_verilog                      $path_rtl/red_pitaya_top.v

read_verilog                      $path_rtl/lock.v
read_verilog                      $path_rtl/lock/aDACdecoder.v
read_verilog                      $path_rtl/lock/LP_filter.v
read_verilog                      $path_rtl/lock/LP_filter2.v
#read_verilog                      $path_rtl/lock/LP_filter2_pipe.v
read_verilog                      $path_rtl/lock/LP_filter3.v
#read_verilog                      $path_rtl/lock/LP_filter3_pipe.v
read_verilog                      $path_rtl/lock/sq_mult.v
read_verilog                      $path_rtl/lock/muxer3.v
read_verilog                      $path_rtl/lock/muxer4.v
read_verilog                      $path_rtl/lock/muxer5.v
read_verilog                      $path_rtl/lock/muxer_reg3.v

read_verilog                      $path_rtl/lock/muxer_reg4.v
read_verilog                      $path_rtl/lock/muxer_reg5.v
#read_verilog                      $path_rtl/lock/gen_mod.v
read_verilog                      $path_rtl/lock/gen_mod_h.v
read_verilog                      $path_rtl/lock/gen_ramp.v
read_verilog                      $path_rtl/lock/gen_ramp_relock.v
read_verilog                      $path_rtl/lock/lock_ctrl.v
read_verilog                      $path_rtl/lock/lock_pid_block.v
read_verilog                      $path_rtl/lock/slope9.v
read_verilog                      $path_rtl/lock/sat14.v
read_verilog                      $path_rtl/lock/satprotect.v
read_verilog                      $path_rtl/lock/satprotect2.v
#read_verilog                      $path_rtl/lock/UniversalCounter.v
read_verilog                      $path_rtl/lock/debounce.v
read_verilog                      $path_rtl/lock/trigger_input.v
read_verilog                      $path_rtl/lock/jump_control.v
#read_verilog                      $path_rtl/lock/sum_2N.v
read_verilog                      $path_rtl/lock/sum_2N2.v
read_verilog                      $path_rtl/lock/pipe_mult.v





read_xdc                          $path_sdc/red_pitaya.xdc

################################################################################
# run synthesis
# report utilization and timing estimates
# write checkpoint design
################################################################################

#synth_design -top red_pitaya_top
#synth_design -top red_pitaya_top -flatten_hierarchy none -bufg 16 -keep_equivalent_registers

synth_design -top red_pitaya_top -flatten_hierarchy none -bufg 16 -keep_equivalent_registers -fanout_limit 100


#synth_design -top red_pitaya_top \
#             -flatten_hierarchy none \
#             -bufg 16 \
#             -keep_equivalent_registers \
#             -fanout_limit 400 \
#             -fsm_extraction  one_hot \
#             -resource_sharing off \
#             -no_lc \
#             -shreg_min_size 5

# Last good one
#synth_design -top red_pitaya_top \
             #-flatten_hierarchy rebuilt \
             #-bufg 12 \
             #-fanout_limit 400 \
             #-fsm_extraction  one_hot \
             #-keep_equivalent_registers \
             #-resource_sharing off \
             #-no_lc \
             #-shreg_min_size 5



write_checkpoint         -force   $path_out/post_synth
report_timing_summary    -file    $path_out/post_synth_timing_summary.rpt
report_power             -file    $path_out/post_synth_power.rpt

################################################################################
# run placement and logic optimization
# report utilization and timing estimates
# write checkpoint design
################################################################################

opt_design
power_opt_design
place_design
phys_opt_design
write_checkpoint         -force   $path_out/post_place
report_timing_summary    -file    $path_out/post_place_timing_summary.rpt
#write_hwdef              -file    $path_sdk/red_pitaya.hwdef

################################################################################
# run router
# report actual utilization and timing,
# write checkpoint design
# run drc, write verilog and xdc out
################################################################################

route_design
write_checkpoint         -force   $path_out/post_route
report_timing_summary    -file    $path_out/post_route_timing_summary.rpt
report_timing            -file    $path_out/post_route_timing.rpt -sort_by group -max_paths 100 -path_type summary
report_clock_utilization -file    $path_out/clock_util.rpt
report_utilization       -file    $path_out/post_route_util.rpt
report_power             -file    $path_out/post_route_power.rpt
report_drc               -file    $path_out/post_imp_drc.rpt
#write_verilog            -force   $path_out/bft_impl_netlist.v
#write_xdc -no_fixed_only -force   $path_out/bft_impl.xdc

################################################################################
# generate a bitstream
################################################################################

set_property BITSTREAM.GENERAL.COMPRESS TRUE [current_design]

write_bitstream -force $path_out/red_pitaya.bit

################################################################################
# generate system definition
################################################################################

write_sysdef             -hwdef   $path_sdk/red_pitaya.hwdef \
                         -bitfile $path_out/red_pitaya.bit \
                         -file    $path_sdk/red_pitaya.sysdef

exit
