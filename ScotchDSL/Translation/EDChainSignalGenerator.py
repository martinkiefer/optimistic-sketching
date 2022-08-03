from DChainSignalGenerator import DChainSignalGenerator

class EDChainSignalGenerator(DChainSignalGenerator):
    def __init__(self, prefix=""):
        self.entity_name = F"{prefix}edchain_signal"

    def getEntitySignals(self):
        signals = []
        signals += [("clk", "in", "std_logic")]
        signals += [("data_in", "in", "std_logic")]
        signals += [("enable", "in", "std_logic")]
        signals += [("data_out", "out", "std_logic := '0'")]
        return signals

    def generateDeclarationSignals(self):
        return self.getEntitySignals()

    def generateArchitectureDefinition(self):
        return """
architecture rtl of {} is
type pipeline_type is array(STAGES-1 downto 0) of std_logic;
begin
	process(clk)
    variable pipeline : pipeline_type := (others=>'0');
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
""".format(self.entity_name)


if __name__ == "__main__":
    hcg = EDChainSignalGenerator()
    hcg.generateFile("./")
