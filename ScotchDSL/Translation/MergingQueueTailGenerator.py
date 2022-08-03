"""
The regular queue tail has one job: Making sure neutral elements do not clog the queue.
"""
from QueueTailGenerator import QueueTailGenerator
from GeneratorUtils import generateComponentInstantiation, generateSignalMap


class MergingQueueTailGenerator(QueueTailGenerator):
    def __init__(self, wseed, woffset, wvalue, ug, neutral, prefix=""):
        self.ug = ug
        super(MergingQueueTailGenerator, self).__init__(wseed, woffset, wvalue, neutral)
        self.entity_name = F"{prefix}merging_queue_tail"

    def generateArchitectureDefinition(self):
        decl = ""
        # Declarations
        # Memory component according to provided sizes
        decl += self.ug.generateComponentDeclaration()

        for signal in self.ug.generateDeclarationSignals():
            if "clk" == signal[0]:
                continue
            decl += "\nsignal u_{} : {};".format(signal[0], signal[2])

        bhv = ""
        signal_map = generateSignalMap(self.ug.generateDeclarationSignals(), "u_")
        bhv += generateComponentInstantiation("u", self.ug.entity_name, signal_map, None)

        return F"""
architecture rtl of {self.entity_name} is
    signal offset_state : std_logic_vector({self.woffset} - 1 downto 0) :=  (others => '0');
    signal value_state : std_logic_vector({self.wvalue} - 1 downto 0) := {self.neutral};
    
{decl}

begin

{bhv}

u_state <= value_state;
u_v <= value_in;
u_seed <= seed;

process(clk)
begin
    if rising_edge(clk) then
        if enable = '1' then
            -- If the current offsets are equal, we simply use the state coming out of the merger (update)
            value_out <= value_state;
            offset_out <= offset_state;
            
            if (offset_state /= offset_in and value_in /= {self.neutral}) or eject = '1'  then
                value_state <= value_in;
                offset_state <= offset_in;
                
                -- Neutral elements are not pushed to the queue
                if value_state /= {self.neutral} then
                    push_out <= '1';  
                else
                    push_out <= '0';
                end if;
            elsif offset_state = offset_in then
                value_state <= u_outstate;
                push_out <= '0';
            else
                push_out <= '0';
            end if;
        end if;
    end if;
end process;
end rtl;
"""


if __name__ == "__main__":
    pass
