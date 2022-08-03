from MergeTreeGenerator import MergeTreeGenerator
from GeneratorUtils import generateComponentInstantiation, generateSignalMap, generateAssignments

class ShiftMergerGenerator:
    def __init__(self, depth, wseed, wvalue, woffset, neutral, ug, edvg, prefix=""):
        self.entity_name = F"{prefix}shift_merger"
        self.depth = depth
        self.wseed = wseed
        self.wvalue = wvalue
        self.woffset = woffset
        self.ug = ug
        self.edvg = edvg
        self.mtg = MergeTreeGenerator(depth, ug, wvalue, wseed, neutral, prefix=prefix)
        self.neutral = neutral

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
        signals += [("seed", "in", F"std_logic_vector({self.wseed}-1 downto 0)")]

        signals += [("offset_in", "in", F"std_logic_vector({self.woffset}-1 downto 0)")]
        signals += [("value_in", "in", F"std_logic_vector({self.wvalue}-1 downto 0)")]

        signals += [("offset_out", "out", F"std_logic_vector({self.woffset}-1 downto 0)")]
        signals += [("value_out", "out", F"std_logic_vector({self.wvalue}-1 downto 0)")]

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
        # Most of the code here is static.
        decl = ""
        #Declarations
        ## Memory component according to provided sizes
        decl += self.mtg.generateComponentDeclaration()
        decl += self.edvg.generateComponentDeclaration()

        # Generate connecting signals
        for signal in self.mtg.generateDeclarationSignals():
            if "clk" == signal[0]:
                continue
            decl += "\nsignal mt_{} : {};".format(signal[0],signal[2])

        for signal in self.edvg.getEntitySignals():
            if "clk" == signal[0]:
                continue
            dec = "\nsignal edv_{} : {};".format(signal[0],signal[2])
            decl += dec.replace("WIDTH", str(self.woffset))

        bhv = ""
        signal_map = generateSignalMap(self.mtg.generateDeclarationSignals(), "mt_")
        bhv += generateComponentInstantiation("mt", self.mtg.entity_name, signal_map, None)

        signal_map = generateSignalMap(self.edvg.getEntitySignals(), "edv_")
        generic_map = {"STAGES" : self.mtg.computeLatency(), "WIDTH" : self.woffset}
        bhv += generateComponentInstantiation("edv", self.edvg.entity_name, signal_map, generic_map)

        s = {
            "mt_enable": "enable",
            "mt_seed": "seed",
            "value_out": "mt_val_out"
        }
        s |= {
            "edv_enable": "enable",
            "offset_out": "edv_data_out"
        }

        for i in range(self.depth):
            s |= {F"mt_val{i}_in": F"mt_value_in({i})"}
        assignments = generateAssignments(s)

        bhv += assignments
        return F"""
architecture rtl of {self.entity_name} is

{decl}

type avalue is array ({self.depth} downto 0) of std_logic_vector({self.wvalue} - 1 downto 0);
type aoffset is array ({self.depth} downto 0) of std_logic_vector({self.woffset} - 1 downto 0);

signal mt_value_in : avalue :=(others => {self.neutral});   --memory for queue.

begin

{bhv}
process(clk)
    variable offset_mem : aoffset :=(others => (others => '0'));   --memory for queue.
    variable value_mem : avalue :=(others => {self.neutral});   --memory for queue.
    variable neutral_mem : std_logic_vector({self.depth} downto 0) :=(others => '0');   --memory for queue.
begin
    if rising_edge(clk) then
        if enable = '1' then
        -- If there is no enable, we have to leave everything as it is to avoid overfilling the queue. The merger will be halted as well.
            -- Step 1: Shift the values
            for i in {self.depth}-1 downto 0 loop
                offset_mem(i+1) := offset_mem(i);
                value_mem(i+1) := value_mem(i);
                neutral_mem(i+1) := neutral_mem(i);
            end loop;
            offset_mem(0) := offset_in;
            value_mem(0) := value_in; 

            if value_in = {self.neutral} then
                neutral_mem(0) := '1'; 
            else
                neutral_mem(0) := '0'; 
            end if;
            

            -- Step 2: 
            -- Decide which values go into the merger and which ones will be the neutral element
            -- And reset the internal data structures to the neutral element, so no element is processed twice            
            for i in 1 to {self.depth} loop
                if offset_mem({self.depth}) = offset_mem(i) and neutral_mem({self.depth}) = '0' and neutral_mem(i) = '0' then
                    mt_value_in(i-1) <= value_mem(i); 
                    neutral_mem(i) := '1';
                else 
                    mt_value_in(i-1) <= {self.neutral}; 
                end if;
            end loop;
            edv_data_in <= offset_mem({self.depth});
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

        self.mtg.generateFile(folder)

if __name__ == "__main__":
    pass
