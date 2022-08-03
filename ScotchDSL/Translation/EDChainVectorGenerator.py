from DChainVectorGenerator import DChainVectorGenerator

class EDChainVectorGenerator(DChainVectorGenerator):
    def __init__(self, neutral="(others=>'0')", prefix=""):
        self.entity_name = F"{prefix}edchain_vector"
        self.neutral = neutral

    def getEntitySignals(self):
        signals = []
        signals += [("clk", "in", "std_logic")]
        signals += [("enable", "in", "std_logic")]
        signals += [("data_in", "in", "std_logic_vector(WIDTH-1 downto 0)")]
        signals += [("data_out", "out", F"std_logic_vector(WIDTH-1 downto 0) := {self.neutral}")]
        return signals


    def generateArchitectureDefinition(self):
        return F"""
architecture rtl of {self.entity_name} is
type pipeline_type is array(STAGES-1 downto 0) of std_logic_vector(WIDTH-1 downto 0);
begin
	process(clk)
    variable pipeline : pipeline_type := (others => {self.neutral});
    begin
	if rising_edge(clk) then
	    if enable = '1' then
            for i in STAGES-1 downto 1 loop
                 pipeline(i) := pipeline(i-1);
            end loop;
            pipeline(0) := data_in;
            data_out <= pipeline(STAGES-1);
        end if;
    end if;
    end process;
end rtl;
"""

if __name__ == "__main__":
    hcg = EDChainVectorGenerator()
    hcg.generateFile("./")
