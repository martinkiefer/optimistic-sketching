class HashConverterGenerator:
    def __init__(self, enable=False, prefix=""):
        self.entity_name = F"{prefix}hash_converter"
        self.enable = enable

    def generateIncludes(self):
        return """
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
"""

    def getEntitySignals(self):
        signals = []
        signals += [("clk", "in", "std_logic")]
        if self.enable:
            signals += [("enable", "in", "std_logic")]

        signals += [("addr_in", "in", "std_logic_vector(ADDR_WIDTH-1 downto 0)")]
        signals += [("addr_out", "out", "std_logic_vector(ADDR_WIDTH-1 downto 0)")] 
        return signals

    def getEntityGenericVariables(self):
        signals = []
        signals += [("MAX_VAL", "natural")]
        signals += [("ADDR_WIDTH", "natural")] 
        return signals

    def generateEntityDeclaration(self):
        generics = []
        for signal in self.getEntityGenericVariables():
            generics += ["\n{} : {}".format(signal[0], signal[1])]

        signals = []
        for signal in self.getEntitySignals():
            signals += ["\n{} : {} {}".format(signal[0], signal[1], signal[2])]
        return F"""
            entity {self.entity_name} is
            generic (
                {";".join(generics)}
            );
            port (
                {";".join(signals)}
            );
            end {self.entity_name};
        """


    def generateComponentDeclaration(self):
        entity_declaration = self.generateEntityDeclaration()
        component_declaration = entity_declaration.replace("entity {}".format(self.entity_name), "component {}".format(self.entity_name))
        component_declaration = component_declaration.replace("end {}".format(self.entity_name), "end component {}".format(self.entity_name))
        return component_declaration

    def generateArchitectureDefinition(self):
        if self.enable:
            return F"""
architecture rtl of {self.entity_name} is
begin
    process(clk)
    begin
        if rising_edge(clk) then
            if enable = '1' then
                if to_integer(unsigned(addr_in)) >= MAX_VAL then
                    addr_out <= std_logic_vector(to_unsigned(to_integer(unsigned(addr_in))-MAX_VAL, addr_out'length));
                else
                    addr_out <= addr_in;
                end if;
            end if;
        end if;
    end process;
end rtl;
"""
        else:
            return F"""
architecture rtl of {self.entity_name} is
begin
    process(clk)
    begin
        if rising_edge(clk) then
            if to_integer(unsigned(addr_in)) >= MAX_VAL then
                addr_out <= std_logic_vector(to_unsigned(to_integer(unsigned(addr_in))-MAX_VAL, addr_out'length));
            else
                addr_out <= addr_in;
            end if;
        end if;
    end process;
end rtl;
    """

    def generateFile(self, folder):
        f = open("{}/{}.vhd".format(folder, self.entity_name), "w")
        content = self.generateIncludes()
        content += self.generateEntityDeclaration()
        content += self.generateArchitectureDefinition()
        f.write(content)
        f.close()

if __name__ == "__main__":
    hcg = HashConverterGenerator()
    hcg.generateFile("./")
