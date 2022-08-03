import sys
from math import log2

class FifoQueueGenerator:
    def __init__(self, depth, almost_full_depth, offset_width, value_width, effective_value_width=None, prefix=""):
        self.entity_name = F"{prefix}fifo_queue"
        self.depth = depth
        self.almost_full_depth = almost_full_depth
        self.offset_width = offset_width
        self.value_width = value_width
        if effective_value_width:
            self.effective_value_width = effective_value_width
        else:
            self.effective_value_width = value_width
        self.full_size=self.offset_width + self.effective_value_width
        self.ip_name = F"fifo_generator_{self.depth}_{self.full_size}"
        
        

    def generateIncludes(self):
        return """
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
"""

    def getEntitySignals(self):
        signals = []
        signals += [("clk", "in", "std_logic")]
        signals += [("pop", "in", "std_logic")]
        signals += [("push", "in", "std_logic")]

        signals += [("offset_in", "in", F"std_logic_vector({self.offset_width}-1 downto 0)")]
        signals += [("value_in", "in", F"std_logic_vector({self.value_width}-1 downto 0)")]

        signals += [("offset_out", "out", F"std_logic_vector({self.offset_width}-1 downto 0)")]
        signals += [("value_out", "out", F"std_logic_vector({self.value_width}-1 downto 0)")]

        signals += [("empty", "out", "std_logic")]
        signals += [("full", "out", "std_logic")]
        signals += [("almost_full", "out", "std_logic")]

        return signals

    def generateDeclarationSignals(self):
        return self.getEntitySignals()

    def generateEntityDeclaration(self):
        signals = []
        for signal in self.getEntitySignals():
            signals += ["\n{} : {} {}".format(signal[0], signal[1], signal[2])]

        frame = F"""
entity {self.entity_name} is
port (
    {";".join(signals)}
);
end {self.entity_name};
"""

        return frame

    def generateComponentDeclaration(self):
        entity_declaration = self.generateEntityDeclaration()
        component_declaration = entity_declaration.replace("entity {}".format(self.entity_name),
                                                           "component {}".format(self.entity_name))
        component_declaration = component_declaration.replace("end {}".format(self.entity_name),
                                                              "end component {}".format(self.entity_name))
        return component_declaration

    def generateArchitectureDefinition(self):
        return F"""
architecture rtl of {self.entity_name} is

signal joint_in : STD_LOGIC_VECTOR({self.full_size-1} DOWNTO 0);
signal joint_out : STD_LOGIC_VECTOR({self.full_size-1} DOWNTO 0);

Component {self.ip_name} IS
  PORT (
    clk : IN STD_LOGIC;
    srst : IN STD_LOGIC;
    din : IN STD_LOGIC_VECTOR({self.full_size-1} DOWNTO 0);
    wr_en : IN STD_LOGIC;
    rd_en : IN STD_LOGIC;
    dout : OUT STD_LOGIC_VECTOR({self.full_size-1} DOWNTO 0);
    full : OUT STD_LOGIC;
    empty : OUT STD_LOGIC;
    prog_full : OUT STD_LOGIC;
    wr_rst_busy : OUT STD_LOGIC;
    rd_rst_busy : OUT STD_LOGIC
  );
END component {self.ip_name};

begin

joint_in({self.offset_width-1} downto 0) <= offset_in;
joint_in({self.full_size-1} downto {self.offset_width}) <= value_in({self.effective_value_width-1} downto 0);

offset_out <= joint_out({self.offset_width-1} downto 0);
value_out <= ({self.value_width-1} downto {self.effective_value_width} => '0') & joint_out( {self.full_size-1} downto {self.offset_width});

q: {self.ip_name}
PORT MAP(
clk => clk,
srst => '0',
din => joint_in,
dout => joint_out,
wr_en => push,
rd_en => pop,
empty => empty,
full => full,
prog_full => almost_full,
wr_rst_busy => open,
rd_rst_busy => open
);


end rtl;
"""

    def generateFile(self, folder):
        f = open("{}/{}.vhd".format(folder, self.entity_name), "w")
        content = self.generateIncludes()
        content += self.generateEntityDeclaration()
        content += self.generateArchitectureDefinition()
        f.write(content)
        f.close()

        f = open("{}/{}.tcl".format(folder, self.ip_name), "w")
        f.write(F"update_compile_order -fileset sources_1")
        f.write(F"\n")
        f.write(F"create_ip -name fifo_generator -vendor xilinx.com -library ip -version 13.2 -module_name {self.ip_name}")
        f.write(F"\n")
        if self.depth >= 512:
            #f.write(F"set_property -dict [list CONFIG.Performance_Options First_Word_Fall_Through CONFIG.Input_Data_Width {self.full_size} CONFIG.Input_Depth {self.depth} CONFIG.Output_Data_Width {self.full_size} CONFIG.Output_Depth {self.depth} CONFIG.Data_Count_Width {int(log2(self.depth))} CONFIG.Write_Data_Count_Width {int(log2(self.depth))} CONFIG.Read_Data_Count_Width {int(log2(self.depth))} CONFIG.Programmable_Full_Type Single_Programmable_Full_Threshold_Constant CONFIG.Full_Threshold_Assert_Value {self.almost_full_depth} CONFIG.Full_Threshold_Negate_Value {self.almost_full_depth-1} CONFIG.Empty_Threshold_Assert_Value 4 CONFIG.Empty_Threshold_Negate_Value 5] [get_ips {self.ip_name}]")
            f.write(F"set_property -dict [list CONFIG.Performance_Options First_Word_Fall_Through CONFIG.Input_Data_Width {self.full_size} CONFIG.Input_Depth {self.depth} CONFIG.Output_Data_Width {self.full_size} CONFIG.Output_Depth {self.depth} CONFIG.Programmable_Full_Type Single_Programmable_Full_Threshold_Constant CONFIG.Full_Threshold_Assert_Value {self.almost_full_depth} CONFIG.Full_Threshold_Negate_Value {self.almost_full_depth-1}] [get_ips {self.ip_name}]")
        else:
            f.write(F"set_property -dict [list CONFIG.Fifo_Implementation Common_Clock_Distributed_RAM CONFIG.Performance_Options First_Word_Fall_Through CONFIG.Input_Data_Width {self.full_size} CONFIG.Input_Depth {self.depth} CONFIG.Output_Data_Width {self.full_size} CONFIG.Output_Depth {self.depth} CONFIG.Use_Embedded_Registers false CONFIG.Use_Extra_Logic true CONFIG.Programmable_Full_Type Single_Programmable_Full_Threshold_Constant CONFIG.Full_Threshold_Assert_Value {self.almost_full_depth} CONFIG.Full_Threshold_Negate_Value {self.almost_full_depth-1}] [get_ips {self.ip_name}]")
        f.write(F"\n")
        f.write("update_compile_order -fileset sources_1")
        f.write(F"\n")
        f.write(F"set_property generate_synth_checkpoint false [get_files ./${{project_name}}.srcs/sources_1/ip/{self.ip_name}/{self.ip_name}.xci]")
        f.write(F"\n")
        f.write(F"generate_target all [get_files ./${{project_name}}.srcs/sources_1/ip/{self.ip_name}/{self.ip_name}.xci]")
        f.write(F"\n")
        f.write(F"export_ip_user_files -of_objects [get_files {{{{./${{project_name}}.srcs/sources_1/ip/{self.ip_name}/{self.ip_name}.xci}}}}] -no_script -sync -force -quiet")
        f.write(F"\n")
        f.write("update_compile_order -fileset sources_1")
        f.write(F"\n")



if __name__ == '__main__':
    ffqg = FifoQueueGenerator(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]))
    ffqg.generateFile("./")
