from math import ceil, log2

import DChainVectorGenerator
import EDChainVectorGenerator
import MergeTreeGenerator
import FifoQueueGenerator
import DemuxNeutralGenerator
import DemuxConfigPackageGenerator
import ShiftMergerGenerator
import QueueTailGenerator
import MergingQueueTailGenerator
from GeneratorUtils import generateComponentInstantiation, generateSignalMap, generateAssignments

# Generators that must be passed from outside:
# UpdateGenerator
# DvectorGenerator
class ConcurrencyControllerGenerator:
    def __init__(self, with_mt, smg_depth, with_mqt, wuseed, wstate, waddr, n_inputs, banks, neutral_element,
                 ug, dvector_generator, qsize, demuxfactor, effective_increment_size=None, level_increment=0, frontend_latency=0, prefix=""):
        self.prefix = prefix
        self.banks = banks
        self.waddr = waddr
        self.wbaddr = waddr - int(ceil(log2(self.banks)))
        self.n_inputs = n_inputs
        self.wuseed = wuseed
        self.wstate = wstate
        self.neutral_element = neutral_element
        self.ug = ug
        self.qsize = qsize
        self.dvg = dvector_generator
        self.demuxfactor = demuxfactor

        self.demuxnc = None
        self.demuxng = None
        self.qafsize = qsize - frontend_latency - 3 - 1
        if self.banks > 1:
            self.demuxnc = DemuxConfigPackageGenerator.DemuxConfigPackageGenerator(self.banks, demuxfactor, self.wstate, "demuxn_config_pkg", prefix=prefix)
            self.demuxng = DemuxNeutralGenerator.DemuxNeutralGenerator(self.neutral_element, prefix=prefix)
            self.qafsize -= self.demuxnc.computeLatency()  
        if smg_depth > 0:
            self.qafsize -= smg_depth + int(ceil(log2(smg_depth)))  
        assert(self.qafsize > 0)

        if effective_increment_size is None or with_mqt:
            effective_increment_size = wstate
            
        if smg_depth > 0:
            level_increase = int(ceil(log2(smg_depth)))
        else:
            level_increase = 0

        effective_increment_size = min(effective_increment_size+level_increase*level_increment, wstate) 
        self.qg = FifoQueueGenerator.FifoQueueGenerator(self.qsize, self.qafsize, self.wbaddr, self.wstate, effective_increment_size, prefix=prefix)

        if with_mqt:
            self.qtg = MergingQueueTailGenerator.MergingQueueTailGenerator(self.wuseed, self.wbaddr, self.wstate, self.ug, self.neutral_element, prefix=prefix)
        else:
            self.qtg = QueueTailGenerator.QueueTailGenerator(self.wuseed, self.wbaddr, self.wstate, self.neutral_element, prefix=prefix)

        self.mtg = None
        if with_mt:
            self.mtg = MergeTreeGenerator.MergeTreeGenerator(self.n_inputs, self.ug, self.wstate, self.wuseed, self.neutral_element, prefix=prefix)

        self.smg = None
        if smg_depth is not None and smg_depth > 0:
            self.smg = ShiftMergerGenerator.ShiftMergerGenerator(smg_depth, self.wuseed, self.wstate, self.waddr, self.neutral_element, self.ug, dvector_generator, prefix=prefix)

        self.entity_name = F"{prefix}concurrency_controller"

        self.signals = self.generateDeclarationSignals()


    def computeLatency(self):
        latency = 0
        return latency

    def generateIncludes(self):
        return F"""
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use WORK.{self.prefix}demuxn_config_pkg.all;
"""

    def generateDeclarationSignals(self):
        signals = []
        signals += [("clk", "in", "std_logic")]

        # Signals for value processing
        signals += [("enable", "in", "std_logic")]
        signals += [(F"useed", "in", F"std_logic_vector({self.wuseed - 1} downto 0)")]
        signals += [(F"almost_full", "out", F"std_logic := '0'")]
        for i in range(self.n_inputs):
            signals += [(F"val{i}_in", "in", F"std_logic_vector({self.wstate - 1} downto 0)")]
            signals += [(F"offset{i}_in", "in", F"std_logic_vector({self.waddr - 1} downto 0)")]

        for i in range(self.banks):
            signals += [(F"val{i}_out", "out", F"std_logic_vector({self.wstate - 1} downto 0)")]
            signals += [(F"offset{i}_out", "out", F"std_logic_vector({self.wbaddr - 1} downto 0)")]

        return signals

    def generateEntityDeclaration(self):
        frame = """
ENTITY {} IS
PORT (
{}
);
END {};"""
        signals = map(lambda x: "{} : {} {}".format(x[0], x[1], x[2]), self.signals)
        return frame.format(self.entity_name, ";\n".join(signals), self.entity_name)

    def generateArchitectureDefinition(self):
        frame = """
ARCHITECTURE a{} OF {} IS
{}
BEGIN
{}
END a{};
"""

        bhv = ""
        decl = ""
        # Declarations
        ## Update component for the replace logic
        """
        - Demux w. default value (d times, hits b banks), broadcast for offset
        - (Optional) Shift merger
        - Queue tail (with or without merger)
        - Queues
        - Counter, selects the offset based on a case statement. Nah, make it two stages. Comparison + queue mechanism
        Asserting the correct value.
        - Isolate the comparison from the insertion of the neutral value?
        """
        ## MergeTree generator
        if self.mtg is not None:
            decl += self.mtg.generateComponentDeclaration()

        ## Demuxn generator
        if self.banks > 1:
            decl += self.demuxng.generateComponentDeclaration()

        ## Queue generator
        decl += self.qg.generateComponentDeclaration()

        ## Queue tail generator
        decl += self.qtg.generateComponentDeclaration()

        ## Shift merger generator
        if self.smg is not None:
            decl += self.smg.generateComponentDeclaration()

        # Offset buffer while offsets are merged in tree.
        decl += self.dvg.generateComponentDeclaration()

        for b in range(self.banks):
            decl += F"\nsignal almost_full_{b} : std_logic := '0';"
            decl += F"\nsignal next_offset_{b} : std_logic_vector({self.wbaddr-1} downto 0);"
            decl += F"\nsignal cur_of_{b}: integer range 0 to {self.n_inputs-1} := 0;"

        # Every input value gets a demux (if banks != 1)
        if self.banks > 1:
            for b in range(self.n_inputs):
                for signal in self.demuxng.generateDeclarationSignals():
                    if "clk" == signal[0]:
                        continue
                    decl += F"\nsignal dm_{b}_{signal[0]} : {signal[2]};"
                signal_map = generateSignalMap(self.demuxng.generateDeclarationSignals(), F"dm_{b}_")
                bhv += generateComponentInstantiation(F"dm_{b}", self.demuxng.entity_name, signal_map, None)


                for signal in self.dvg.getEntitySignals():
                    if "clk" == signal[0]:
                        continue
                    dec = F"\nsignal odv1_{b}_{signal[0]} : {signal[2]};"
                    decl += dec.replace("WIDTH", str(self.wbaddr))

                signal_map = generateSignalMap(self.dvg.getEntitySignals(), F"odv1_{b}_")
                generic_map = {"STAGES": self.demuxnc.computeLatency(), "WIDTH": self.wbaddr}
                bhv += generateComponentInstantiation(F"odv1_{b}", self.dvg.entity_name, signal_map, generic_map)

        # Every bank gets a shift merger for every input value if desired
        if self.smg is not None:
            for i in range(self.n_inputs):
                for signal in self.smg.generateDeclarationSignals():
                    if "clk" == signal[0]:
                        continue
                    decl += F"\nsignal sm_{i}_{signal[0]} : {signal[2]};"
                signal_map = generateSignalMap(self.smg.generateDeclarationSignals(), F"sm_{i}_")
                bhv += generateComponentInstantiation(F"sm_{i}", self.smg.entity_name, signal_map, None)

        # Every bank gets a merge tree (if desired)
        if self.mtg is not None:
            for b in range(self.banks):
                for signal in self.mtg.generateDeclarationSignals():
                    if "clk" == signal[0]:
                        continue
                    decl += F"\nsignal mt_{b}_{signal[0]} : {signal[2]};"
                signal_map = generateSignalMap(self.mtg.generateDeclarationSignals(), F"mt_{b}_")
                bhv += generateComponentInstantiation(F"mt_{b}", self.mtg.entity_name, signal_map, None)

        # Every bank gets one queue per input value
        for b in range(self.banks):
            for i in range(self.n_inputs):
                for signal in self.qg.generateDeclarationSignals():
                    if "clk" == signal[0]:
                        continue
                    dec = F"\nsignal q_{b}_{i}_{signal[0]} : {signal[2]};"
                    dec = dec.replace("depth", str(self.qsize))
                    dec = dec.replace("almost_full_depth", str(self.qafsize))
                    dec = dec.replace("offset_width", str(self.wbaddr))
                    dec = dec.replace("value_width", str(self.wstate))
                    decl += dec

                signal_map = generateSignalMap(self.qg.generateDeclarationSignals(), F"q_{b}_{i}_")
                bhv += generateComponentInstantiation(F"q_{b}_{i}", self.qg.entity_name, signal_map, None)
                decl += F"\nsignal qin_{b}_{i}_value : std_logic_vector({self.wstate-1} downto 0);"
                decl += F"\nsignal qin_{b}_{i}_offset : std_logic_vector({self.wbaddr-1} downto 0);"

        # Every bank gets one queue tail per input value
        for b in range(self.banks):
            for i in range(self.n_inputs):
                for signal in self.qtg.generateDeclarationSignals():
                    if "clk" == signal[0]:
                        continue
                    decl += F"\nsignal qt_{b}_{i}_{signal[0]} : {signal[2]};"
                signal_map = generateSignalMap(self.qtg.generateDeclarationSignals(), F"qt_{b}_{i}_")
                bhv += generateComponentInstantiation(F"qt_{b}_{i}", self.qtg.entity_name, signal_map, None)

        # Okay let's do connecting signals.
        # First, let's compute the ready signal. The ready signal will be one cycle delayed.



        # Connect input / muxes to queue / queue tail
        # Queue tail to queue

        if self.mtg is not None:
            for b in range(self.banks):
                for signal in self.dvg.getEntitySignals():
                    if "clk" == signal[0]:
                        continue
                    dec = F"\nsignal odv2_{b}_{signal[0]} : {signal[2]};"
                    decl += dec.replace("WIDTH", str(self.wbaddr))

                signal_map = generateSignalMap(self.dvg.getEntitySignals(), F"odv2_{b}_")
                generic_map = {"STAGES": self.mtg.computeLatency(), "WIDTH": self.wbaddr}
                bhv += generateComponentInstantiation(F"odv2_{b}", self.dvg.entity_name, signal_map, generic_map)

        # Architecture behavior
        # Connect inputs to resepctive demuxes / queues
        # Connect muxes to queue tails / shift mergers
        # Connect shift merges to queue tails (if necessary)
        # Connect queue tails to queues
        # Don't forget to connect enable logic to full
        # Connect inputs to mux (if we need a mux)

        #We need to delay the offset while

        s = {}
        if self.banks > 1:
            # Connect to demux and offset delay chain 1
            for i in range(self.n_inputs):
                #Connect inputs to shift merger first, if necessary
                if self.smg is not None:
                    # Connect queue entrance to shift merger
                    s |= {
                        F"sm_{i}_enable": "'1'",
                        F"sm_{i}_seed": "useed",
                        F"sm_{i}_value_in": F"val{i}_in",
                        F"sm_{i}_offset_in": F"offset{i}_in"
                    }

                    s |= {
                        F"odv1_{i}_enable": "'1'",
                        F"odv1_{i}_data_in": F"sm_{i}_offset_out({self.waddr-1} downto {self.waddr-self.wbaddr})",
                        F"dm_{i}_enable_in": "'1'",
                        F"dm_{i}_data_in": F"sm_{i}_value_out",
                        F"dm_{i}_index_in": F"sm_{i}_offset_out({self.waddr-self.wbaddr-1} downto 0)"
                    }
                else:
                    s |= {
                        F"odv1_{i}_enable": "'1'",
                        F"odv1_{i}_data_in": F"offset{i}_in({self.waddr-1} downto {self.waddr-self.wbaddr})",
                        F"dm_{i}_enable_in": "'1'",
                        F"dm_{i}_data_in": F"val{i}_in",
                        F"dm_{i}_index_in": F"offset{i}_in({self.waddr-self.wbaddr-1} downto 0)"
                    }
                    # Connect offset delay chain 1 and demux to queue entrance signals
                    for b in range(self.banks):
                        s |= {
                            F"qin_{b}_{i}_value": F"dm_{i}_data_out({b})",
                            F"qin_{b}_{i}_offset": F"odv1_{i}_data_out"
                        }
                    

                # Connect offset delay chain 1 and demux to queue entrance signals
                for b in range(self.banks):
                    s |= {
                        F"qin_{b}_{i}_value": F"dm_{i}_data_out({b})",
                        F"qin_{b}_{i}_offset": F"odv1_{i}_data_out"
                    }
        else:
            # Connect inputs directly to queue entrance signals
            b = 0
            for i in range(self.n_inputs):
                if self.smg is None:
                    s |= {
                        F"qin_{b}_{i}_value": F"val{i}_in",
                        F"qin_{b}_{i}_offset": F"offset{i}_in"
                    }
                else:
                    s |= {
                        F"sm_{i}_enable": "'1'",
                        F"sm_{i}_seed": "useed",
                        F"sm_{i}_value_in": F"val{i}_in",
                        F"sm_{i}_offset_in": F"offset{i}_in"
                    }
                    s |= {
                        F"qin_{b}_{i}_value": F"sm_{i}_value_out",
                        F"qin_{b}_{i}_offset": F"sm{i}_offset_out"
                    }


        # Connect queue entrance directly to queue tail
        for b in range(self.banks):
            for i in range(self.n_inputs):
                s |= {
                    F"qt_{b}_{i}_value_in": F"qin_{b}_{i}_value",
                    F"qt_{b}_{i}_offset_in":F"qin_{b}_{i}_offset"
                }

        # Connect queue tail to queue
        for b in range(self.banks):
            for i in range(self.n_inputs):
                s |= {
                    F"qt_{b}_{i}_enable": F"'1'",
                    F"qt_{b}_{i}_seed": F"useed",
                    F"qt_{b}_{i}_eject": F"q_{b}_{i}_empty",
                    F"q_{b}_{i}_push": F"qt_{b}_{i}_push_out",
                    F"q_{b}_{i}_value_in": F"qt_{b}_{i}_value_out",
                    F"q_{b}_{i}_offset_in": F"qt_{b}_{i}_offset_out"
                }
        bhv += generateAssignments(s)

        #Logic telling the outside world whether this controller needs a break
        for b in range(self.banks):
            bhv += F"""
process(clk) is
begin
    if rising_edge(clk) then
        almost_full_{b} <= {" or ".join([F"q_{b}_{i}_almost_full" for i in range(self.n_inputs)])};
    end if;
end process;
        """

        # Logic connecting the queue to the outside world
        bhv += F"""
        process(clk) is
        begin
            if rising_edge(clk) then
                almost_full <= {" or ".join([F"almost_full_{i}" for i in range(self.banks)])};
            end if;
        end process;
                """
        # Create offset computation logic and output assignments
        for b in range(self.banks):
            forwards = ""
            offsets = ""
            noclk = ""
            if self.mtg is not None:
                s = {
                    F"mt_{b}_enable": F"'1'",
                }
                bhv += generateAssignments(s)
            for i in range(self.n_inputs):
                if self.mtg is not None:
                    forwards += F"""
                        odv2_{b}_data_in <= next_offset_{b};
                        if q_{b}_{i}_pop = '1' then
                            mt_{b}_val{i}_in <= q_{b}_{i}_value_out;
                        else 
                            mt_{b}_val{i}_in <= {self.neutral_element};
                        end if;
                    """
                    noclk += F"""
                            q_{b}_{i}_pop <= '1' when q_{b}_{i}_offset_out = next_offset_{b} and q_{b}_{i}_empty = '0' else '0';
                    """
                    offsets += F"""
                        if cur_of_{b} = {i} then
                            next_offset_{b} <= q_{b}_{i}_offset_out; 
                        end if;        
                    """
                else:
                    noclk += F"""
                            q_{b}_{i}_pop <= '1' when cur_of_{b} = {i} and q_{b}_{i}_empty = '0' else '0';
                    """
                    forwards += F"""
                        if cur_of_{b} = {i} then
                            if q_{b}_{i}_pop = '1' then 
                                val{b}_out <= q_{b}_{i}_value_out; 
                                offset{b}_out <= q_{b}_{i}_offset_out; 
                            else
                                val{b}_out <= {self.neutral_element}; 
                                offset{b}_out <= (others => '0'); 
                            end if;
                        end if;        
                    """

            outputs = ""
            if self.mtg is not None:
                outputs += F"""
                    odv2_{b}_enable <= '1';
                    offset{b}_out <= odv2_{b}_data_out; 
                    val{b}_out <= mt_{b}_val_out;
                    mt_{b}_seed <= useed;
                """
            noclk += outputs
            bhv += F"""
process(clk) is
begin
    if rising_edge(clk) then
            -- Compute the next offset for every bank 
{offsets}
            if cur_of_{b} = {self.n_inputs-1} then
                cur_of_{b} <= 0;
            else
                cur_of_{b} <= cur_of_{b} + 1;
            end if;
            -- Forward value
{forwards}
    end if;
end process;
{noclk}
"""


        return frame.format(self.entity_name, self.entity_name, decl, bhv, self.entity_name)

    def generateComponentDeclaration(self):
        entity_declaration = self.generateEntityDeclaration()
        component_declaration = entity_declaration.replace("ENTITY {}".format(self.entity_name),
                                                           "COMPONENT {}".format(self.entity_name))
        component_declaration = component_declaration.replace("END {}".format(self.entity_name),
                                                              "END COMPONENT {}".format(self.entity_name))
        return component_declaration

    def generateFile(self, folder):
        f = open("{}/{}.vhd".format(folder, self.entity_name), "w")
        content = self.generateIncludes()
        content += self.generateEntityDeclaration()
        content += self.generateArchitectureDefinition()
        f.write(content)
        f.close()
        self.qtg.generateFile(folder)
        self.qg.generateFile(folder)

        if self.demuxnc is not None:
            self.demuxnc.generateFile(folder)

        if self.demuxng is not None:
            self.demuxng.generateFile(folder)

        if self.mtg is not None:
            self.mtg.generateFile(folder)

        if self.smg is not None:
            self.smg.generateFile(folder)


if __name__ == "__main__":
    from ParserInterface import *
    from Functions import SelectorFunctionGenerator, UpdateFunctionGenerator

    with open(sys.argv[1]) as f:
        data = json.load(f)

        if len(sys.argv) == 3:
            outdir = sys.argv[2]
        else:
            outdir = "./output"

        if not os.path.exists(outdir):
            os.makedirs(outdir)

        cwd = os.getcwd()
        os.chdir(os.path.dirname(sys.argv[1]))
        update_list = create_update_function_statement_list(data)
        os.chdir(cwd)

        ufg = UpdateFunctionGenerator(update_list, data["state_size"], data["update_seed_size"],
                                      data["state_size"], True)
        ufg.generateFile(outdir)

        fpk = FunctionPackageGenerator()
        fpk.generateFile(outdir)

        if "initial_state" not in data:
            data["initial_state"] = "(others => '0')"

        dvg = EDChainVectorGenerator.EDChainVectorGenerator()
        dvg.generateFile(outdir)
        ccg = ConcurrencyControllerGenerator(True, 8, True, data["update_seed_size"], data["state_size"], data["offset_max_size"], 4, 2, data["compute_neutral"], ufg, dvg, 30, 4)
        ccg.generateFile(outdir)
