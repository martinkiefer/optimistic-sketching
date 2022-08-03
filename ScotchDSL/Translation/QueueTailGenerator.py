"""
The regular queue tail has one job: Making sure neutral elements do not clog the queue.
"""


class QueueTailGenerator:
    def __init__(self, wseed, woffset, wvalue, neutral, prefix=""):
        self.entity_name = F"{prefix}queue_tail"
        self.wseed = wseed
        self.neutral = neutral
        self.woffset = woffset
        self.wvalue = wvalue

    def generateIncludes(self):
        return """
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
"""

    def generateDeclarationSignals(self):
        signals = []
        signals += [("clk", "in", "std_logic")]
        signals += [("enable", "in", "std_logic")]
        signals += [("eject", "in", "std_logic")]
        signals += [("seed", "in", F"std_logic_vector({self.wseed} - 1 downto 0)")]

        signals += [("offset_in", "in", F"std_logic_vector({self.woffset} - 1 downto 0)")]
        signals += [("value_in", "in", F"std_logic_vector({self.wvalue} - 1 downto 0)")]

        signals += [("offset_out", "out", F"std_logic_vector({self.woffset} - 1 downto 0)")]
        signals += [("value_out", "out", F"std_logic_vector({self.wvalue} - 1 downto 0) := {self.neutral}")]

        signals += [("push_out", "out", "std_logic")]

        return signals

    def generateEntityDeclaration(self):
        frame = """
entity {} is
port (
    {}
);
end {};
"""

        signals = []
        for signal in self.generateDeclarationSignals():
            signals += ["\n{} : {} {}".format(signal[0], signal[1], signal[2])]
        return frame.format(self.entity_name, ";".join(signals), self.entity_name)

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

process(clk)
begin
    if rising_edge(clk) then
        if enable = '1' then
            offset_out <= offset_in;
            value_out <= value_in;

            if value_in = {self.neutral} then
                push_out <= '0';
            else 
                push_out <= '1';
            end if;
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
    pass
