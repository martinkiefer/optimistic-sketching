class DemuxNeutralSingleGenerator:
    def __init__(self, neutral, prefix=""):
        self.entity_name = F"{prefix}demuxn_single"
        self.neutral = neutral
        self.prefix = prefix

    def generateIncludes(self):
        return F"""
library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;
use WORK.{self.prefix}demuxn_config_pkg.all;
"""

    def getEntitySignals(self):
        signals = []
        signals += [("clk", "in", "std_logic")]
        signals += [("enable_in", "in", "std_logic")]
        signals += [("index_in", "in", "std_logic_vector(DEMUX_INDEX_WIDTH-1 downto 0)")]
        signals += [("data_in", "in", "std_logic_vector(DEMUX_DATA_WIDTH-1 downto 0)")]
        signals += [("data_out", "out", F"demux_data_array_type(0 to DEMUX_FACTOR-1) := (others => {self.neutral})")]
        signals += [("rest_out", "out", "demux_index_array_type(0 to DEMUX_FACTOR-1)")]

        return signals

    def getEntityGenericVariables(self):
        signals = []
        signals += [("STAGE_FACTOR", "integer")]
        return signals

    def generateEntityDeclaration(self):
        frame = """
entity {} is
generic (
    {}
);
port (
    {}
);
end {};
"""
        generics = []
        for signal in self.getEntityGenericVariables():
            generics += ["\n{} : {}".format(signal[0], signal[1])]

        signals = []
        for signal in self.getEntitySignals():
            signals += ["\n{} : {} {}".format(signal[0], signal[1], signal[2])]
        return frame.format(self.entity_name, ";".join(generics), ";".join(signals), self.entity_name)

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
begin
process(clk, enable_in, index_in, data_in)
	variable factor : natural;
    variable index_in_nat : natural;
    variable index_out_nat : natural;
    variable rest : natural;
	begin
    if rising_edge(clk) then
        if enable_in = '1' then
            factor := DEMUX_FACTOR ** STAGE_FACTOR;
            index_in_nat := to_integer(unsigned(index_in));
		    index_out_nat := index_in_nat / factor;
            rest := index_in_nat mod factor;

            data_out <= (others => {self.neutral});
            data_out(index_out_nat) <= data_in;
		rest_out <= (others => std_logic_vector(to_unsigned(rest, DEMUX_INDEX_WIDTH)));
        end if;
	end if;
end process;
end rtl;
""".format(self.entity_name)

    def generateFile(self, folder):
        f = open("{}/{}.vhd".format(folder, self.entity_name), "w")
        content = self.generateIncludes()
        content += self.generateEntityDeclaration()
        content += self.generateArchitectureDefinition()
        f.write(content)
        f.close()


if __name__ == "__main__":
    msg = DemuxNeutralSingleGenerator()
    msg.generateFile("./output")
