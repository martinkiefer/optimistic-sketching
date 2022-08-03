from math import ceil, log2, floor

from EDChainSignalGenerator import EDChainSignalGenerator
from EDChainVectorGenerator import EDChainVectorGenerator
from MemoryComponentGenerator import MemoryComponentGenerator
from HashConverterGenerator import HashConverterGenerator
from DFUGenerator import DFUGenerator
from GeneratorUtils import generateComponentInstantiation, generateSignalMap, generateAssignments
from ForwardingUpdateFunctionGenerator import ForwardingUpdateFunctionGenerator
from DChainVectorGenerator import DChainVectorGenerator
from DChainSignalGenerator import DChainSignalGenerator
from MemoryBufferGenerator import MemoryBufferGenerator
from MemorySegmentGenerator import MemorySegmentGenerator
from ConcurrenyControllerGenerator import ConcurrencyControllerGenerator

def is_power_of_two(n):
    return n > 0 and (n & (n - 1)) == 0

#Okay, let's put an end to the idea that each super stage is something unique
class OptimisticRowSuperStageGenerator:
    def __init__(self, banks, n_inputs, memseg_size, total_segments, wsseed, wuseed, wvalue,
    wstate, selector_generator, forwarding_update_generator, plain_update_generator,
    map_generator, neutral_element, qsize, with_mt, with_mqt, smg_depth, effective_increment_size=None, level_increment=0, prefix=""):
        self.n_inputs = n_inputs
        self.banks = banks
        self.total_segments = total_segments
        self.total_size = memseg_size*self.total_segments
        assert(self.total_segments % self.banks == 0)
        self.bank_size = self.total_size//self.banks
        self.waddr = int(ceil(log2(self.total_size)))
        self.wbaddr = self.waddr - int(ceil(log2(self.banks)))
        self.wsseed = wsseed
        self.wuseed = wuseed
        self.wvalue = wvalue
        self.wstate= wstate
        self.neutral_element = neutral_element
        self.dvg = DChainVectorGenerator(prefix=prefix)
        self.dsg = DChainSignalGenerator(prefix=prefix)
        self.edvg = EDChainVectorGenerator(prefix=prefix)

        self.edsg = EDChainSignalGenerator(prefix=prefix)
        self.pug = plain_update_generator

        self.mbg = MemoryBufferGenerator(prefix=prefix)
        self.msg = MemorySegmentGenerator(prefix=prefix)
        self.mcg = MemoryComponentGenerator([memseg_size]*(total_segments//self.banks), self.wstate, self.wvalue, self.msg, self.mbg, "0", prefix=prefix)
        self.sg = selector_generator
        self.mapg = map_generator
        self.ug = forwarding_update_generator
        self.hcg = None
        hcg_lat = 0
        if not is_power_of_two(self.bank_size):
            self.hcg = HashConverterGenerator(True, prefix=prefix)
            hcg_lat += 1
        frontend_latency = max(self.mapg.computeLatency(), self.sg.computeLatency() + hcg_lat)
        self.ccg = ConcurrencyControllerGenerator(with_mt, smg_depth, with_mqt, self.wuseed, self.wstate, self.waddr, self.n_inputs, self.banks, self.neutral_element, self.pug, self.edvg, qsize, 4, effective_increment_size, level_increment, frontend_latency=frontend_latency, prefix=prefix)
        self.dfug = DFUGenerator(prefix=prefix)

        self.entity_name = F"{prefix}super_stage"

        self.signals = self.generateDeclarationSignals()

    def computeMemoryLatency(self):
        return self.total_segments//self.banks+1

    def computeDFULatency(self):
        return self.computeMemoryLatency()+1

    def computeEnablePipelineLatency(self):
        latency = 0
        if not self.hcg is None:
            latency += 1
        latency += self.sg.computeLatency()
        latency += self.computeDFULatency()
        latency += self.computeMemoryLatency()
        latency += 1 #For the update stage
        return latency

    def computeValuePipelineLatency(self):
        latency = 0
        latency += self.computeDFULatency()
        latency += self.computeMemoryLatency()
        return latency
        
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
        signals += [("almost_full", "out", "std_logic := '0'")]

        for b in range(self.banks):
            #Signals for direct reading from read stage overrides value_enable
            signals += [(F"rd_en{b}_in", "in", "std_logic")]
            signals += [(F"rd_addr{b}_in", "in", "std_logic_vector({} downto 0)".format(self.wbaddr-1))]
            signals += [(F"rd_data{b}_out", "out", "std_logic_vector({} downto 0)".format(self.wstate-1))]
            signals += [(F"rd_valid{b}_out", "out", "std_logic")]

        #Signals for value processing
        for i in range(self.n_inputs):
            signals += [(F"val_en{i}_in", "in", "std_logic")]
            signals += [(F"val{i}_in", "in", "std_logic_vector({} downto 0)".format(self.wvalue-1))]


        signals += [("sseed_in", "in", "std_logic_vector({} downto 0)".format(self.wsseed-1))]
        signals += [("useed_in", "in", "std_logic_vector({} downto 0)".format(self.wuseed-1))]

        return signals


    def generateEntityDeclaration(self):
        frame = """
ENTITY {} IS
PORT (
{}
);
END {};"""
        signals = map(lambda x : "{} : {} {}".format(x[0], x[1], x[2]), self.signals)
        return frame.format(self.entity_name, ";\n".join(signals), self.entity_name)

    def generateComponentDeclarations(self):
        decl = ""
        ## Selector Stage
        decl += self.sg.generateComponentDeclaration()
        for i in range(self.n_inputs):
            for signal in self.sg.generateDeclarationSignals():
                if "clk" == signal[0]:
                    continue
                decl += F"\nsignal s_{i}_{signal[0]} : {signal[2]};"
        if self.hcg is not None:
            decl += self.hcg.generateComponentDeclaration()
            for i in range(self.n_inputs):
                for signal in self.hcg.getEntitySignals():
                    if "clk" == signal[0]:
                        continue
                    dec = F"\nsignal hc_{i}_{signal[0]} : {signal[2]};"
                    dec = dec.replace("ADDR_WIDTH", str(self.waddr))
                    decl += dec

        ## Mapper
        decl += self.mapg.generateComponentDeclaration()
        for i in range(self.n_inputs):
            for signal in self.mapg.generateDeclarationSignals():
                if "clk" == signal[0]:
                    continue
                decl += F"\nsignal map_{i}_{signal[0]} : {signal[2]};"

        decl += self.edsg.generateComponentDeclaration()
        for i in range(self.n_inputs):
            for signal in self.edsg.generateDeclarationSignals():
                if "clk" == signal[0]:
                    continue
                dec = F"\nsignal eds_{i}_{signal[0]} : {signal[2]};"
                decl += dec.replace("WIDTH", str(self.wstate))
        ## Mapper

        hcg_lat = 0 if self.hcg is None else 1

        if self.mapg.computeLatency() > self.sg.computeLatency() + hcg_lat:
            decl += self.edvg.generateComponentDeclaration()
            for i in range(self.n_inputs):
                for signal in self.edvg.generateDeclarationSignals():
                    if "clk" == signal[0]:
                        continue
                    dec = F"\nsignal edv_{i}_{signal[0]} : {signal[2]};"
                    decl += dec.replace("WIDTH", str(self.wbaddr))

            # We need a buffer for the intermediate (with enable)
            # We need a buffer for the valid bit (with enable)
        elif self.mapg.computeLatency() < self.sg.computeLatency() + hcg_lat:
            decl += self.edvg.generateComponentDeclaration()
            for i in range(self.n_inputs):
                for signal in self.edvg.generateDeclarationSignals():
                    if "clk" == signal[0]:
                        continue
                    dec = F"\nsignal edv_{i}_{signal[0]} : {signal[2]};"
                    decl += dec.replace("WIDTH", str(self.wstate))
            # We need a buffer for the offset (with enable)
        else:
            #We can connect directly to the cc with both functions which is obviously barely ever going to be the case
            pass

        decl += self.ccg.generateComponentDeclaration()
        for signal in self.ccg.generateDeclarationSignals():
            if "clk" == signal[0]:
                continue
            decl += F"\nsignal cc_{signal[0]} : {signal[2]};"

        #Here comes the memory
        decl += self.mcg.generateComponentDeclaration()
        for b in range(self.banks):
            for signal in self.mcg.generateDeclarationSignals():
                if "clk" == signal[0]:
                    continue
                decl += F"\nsignal mc_{b}_{signal[0]} : {signal[2]};"

        # Next: The DFU
        decl += self.dfug.generateComponentDeclaration()
        for b in range(self.banks):
            for signal in self.dfug.getEntitySignals():
                if "clk" == signal[0]:
                    continue
                dec = F"\nsignal dfu_{b}_{signal[0]} : {signal[2]};"
                dec = dec.replace("ADDR_WIDTH", str(self.wbaddr))
                dec = dec.replace("MEM_WIDTH", str(self.wstate))
                decl += dec

        # Next: The atomic update
        decl += self.ug.generateComponentDeclaration()
        for b in range(self.banks):
            for signal in self.ug.generateDeclarationSignals():
                if "clk" == signal[0]:
                    continue
                decl += F"\nsignal u_{b}_{signal[0]} : {signal[2]};"

        # And the delay chain that carries the state:
        decl += self.dvg.generateComponentDeclaration()
        for b in range(self.banks):
            for signal in self.dvg.getEntitySignals():
                if "clk" == signal[0]:
                    continue
                dec = F"\nsignal vdv_{b}_{signal[0]} : {signal[2]};"
                decl += dec.replace("WIDTH", str(self.wstate))

        # And the enable for the read
        decl += self.dsg.generateComponentDeclaration()
        for b in range(self.banks):
            for signal in self.dsg.getEntitySignals():
                if "clk" == signal[0]:
                    continue
                decl += F"\nsignal rds_{b}_{signal[0]} : {signal[2]};"

        return decl

    def generateComponentInstantiations(self):
        bhv = ""
        ## Selector Stage
        for i in range(self.n_inputs):
            signal_map = generateSignalMap(self.sg.generateDeclarationSignals(), F"s_{i}_")
            bhv += generateComponentInstantiation(F"s_{i}", self.sg.entity_name, signal_map, None)

        ## HashConverter
        if not self.hcg is None:
            for i in range(self.n_inputs):
                signal_map = generateSignalMap(self.hcg.getEntitySignals(), F"hc_{i}_")
                generic_map = {"ADDR_WIDTH" : self.waddr, "MAX_VAL" : self.bank_size}
                bhv += generateComponentInstantiation(F"hc_{i}", self.hcg.entity_name, signal_map, generic_map)

        ## Map Stage
        for i in range(self.n_inputs):
            signal_map = generateSignalMap(self.mapg.generateDeclarationSignals(), F"map_{i}_")
            bhv += generateComponentInstantiation(F"map_{i}", self.mapg.entity_name, signal_map, None)

            signal_map = generateSignalMap(self.edsg.getEntitySignals(), F"eds_{i}_")
            generic_map = {"STAGES": self.mapg.computeLatency()}
            bhv += generateComponentInstantiation(F"eds_{i}", self.edsg.entity_name, signal_map, generic_map)

        hcg_lat = 0 if self.hcg is None else 1

        for i in range(self.n_inputs):
            if self.mapg.computeLatency() > self.sg.computeLatency() + hcg_lat:
                signal_map = generateSignalMap(self.edvg.getEntitySignals(), F"edv_{i}_")
                generic_map = {"STAGES": self.mapg.computeLatency() - self.sg.computeLatency() + hcg_lat, "WIDTH:": self.wbaddr}
                bhv += generateComponentInstantiation(F"edv_{i}", self.edvg.entity_name, signal_map, generic_map)
            elif self.mapg.computeLatency() < self.sg.computeLatency() + hcg_lat:
                signal_map = generateSignalMap(self.edvg.getEntitySignals(), F"edv_{i}_")
                generic_map = {"STAGES": self.sg.computeLatency() + hcg_lat - self.mapg.computeLatency(), "WIDTH": self.wstate}
                bhv += generateComponentInstantiation(F"edv_{i}", self.edvg.entity_name, signal_map, generic_map)

        # Concurrency controller
        signal_map = generateSignalMap(self.ccg.generateDeclarationSignals(), F"cc_")
        bhv += generateComponentInstantiation(F"cc", self.ccg.entity_name, signal_map, None)

        for b in range(self.banks):
            signal_map = generateSignalMap(self.dfug.getEntitySignals(), F"dfu_{b}_")
            generic_map = {"MEM_WIDTH" : self.wstate, "ADDR_WIDTH" : self.wbaddr, "DFU_WIDTH" : self.computeDFULatency()}
            bhv += generateComponentInstantiation(F"dfu_{b}", self.dfug.entity_name, signal_map, generic_map)

        for b in range(self.banks):
            signal_map = generateSignalMap(self.ug.generateDeclarationSignals(), F"u_{b}_")
            bhv += generateComponentInstantiation(F"u_{b}", self.ug.entity_name, signal_map, None)

        for b in range(self.banks):
            signal_map = generateSignalMap(self.mcg.generateDeclarationSignals(), F"mc_{b}_")
            bhv += generateComponentInstantiation(F"mc_{b}", self.mcg.entity_name, signal_map, None)

        vdv_latency = self.computeMemoryLatency() + self.computeDFULatency()
        for b in range(self.banks):
            signal_map = generateSignalMap(self.dvg.getEntitySignals(), F"vdv_{b}_")
            generic_map = {"STAGES" : vdv_latency, "WIDTH" : self.wstate}
            bhv += generateComponentInstantiation(F"vdv_{b}", self.dvg.entity_name, signal_map, generic_map)

        for b in range(self.banks):
            signal_map = generateSignalMap(self.dsg.getEntitySignals(), F"rds_{b}_")
            generic_map = {"STAGES" : self.computeMemoryLatency()}
            bhv += generateComponentInstantiation(F"rds_{b}", self.dsg.entity_name, signal_map, generic_map)

        ## HashComponentGenerator
        return bhv

    def generateConnections(self):
        bhv = ""
        assignments = {
            F"almost_full": "cc_almost_full"
        }
        bhv += generateAssignments(assignments)
        for i in range(self.n_inputs):
            assignments = {
                f"s_{i}_v": f"val{i}_in",
                f"s_{i}_enable": f"'1'",
                F"s_{i}_seed" : "sseed_in",

            }
            bhv += generateAssignments(assignments)

            assignments = {
                f"map_{i}_v": f"val{i}_in",
                f"map_{i}_enable": f"'1'",
                f"map_{i}_seed": f"useed_in",
                f"eds_{i}_data_in": F"val_en{i}_in",
                f"eds_{i}_enable": f"'1'",
            }
            bhv += generateAssignments(assignments)

            hcg_lat = None
            if self.hcg is None:
                hcg_lat = 0
            else:
                hcg_lat = 1

                assignments = {
                    F"hc_{i}_addr_in": F"s_{i}_offset({self.waddr-1} downto 0)",
                    F"hc_{i}_enable": f"'1'",
                }
                bhv += generateAssignments(assignments)

            assignments = {
                F"cc_useed": F"useed_in",
                F"cc_enable": F"'1'"
            }
            bhv += generateAssignments(assignments)
            # Okay, next come the optional data and enable vectors + connections to the cc
            if self.mapg.computeLatency() == self.sg.computeLatency() + 1 and self.hcg is not None:
                # Connect map and hcg to concurrency controller
                assignments = {
                    F"cc_offset{i}_in": F"hc_{i}_addr_out",
                }
                assignments |= {
                    F"cc_val{i}_in": F"map_{i}_offset when eds_{i}_data_out = '1' else {self.neutral_element}"
                }
                bhv += generateAssignments(assignments)
            elif self.mapg.computeLatency() == self.sg.computeLatency() and self.hcg is None:
                # Connect map and sel to concurrency controller
                assignments = {
                    F"cc_offset{i}_in": F"s_{i}_offset({self.waddr-1} downto 0)",
                }
                assignments |= {
                    F"cc_val{i}_in": F"map_{i}_offset when eds_{i}_data_out = '1' else {self.neutral_element}"
                }
                bhv += generateAssignments(assignments)
            elif self.mapg.computeLatency() < self.sg.computeLatency() + 1 and self.hcg is not None:
                # Map to edv, enable to eds, hcg to concurrency controller
                assignments = {
                    f"cc_offset{i}_in": f"hc_{i}_addr_out",
                }
                assignments |= {
                    f"edv_{i}_enable": f"'1'",
                    f"edv_{i}_data_in": f"map_{i}_offset when eds_{i}_data_out = '1' else {self.neutral_element}",
                    f"cc_val{i}_in": f"edv_{i}_data_out"
                }
                bhv += generateAssignments(assignments)
            elif self.mapg.computeLatency() < self.sg.computeLatency()  and self.hcg is None:
                # Map to edv, enable to eds, hcg to concurrency controller
                assignments = {
                    f"cc_offset{i}_in": f"s_{i}_offset({self.waddr-1} downto 0)",
                }
                assignments |= {
                    f"edv_{i}_enable": f"'1'",
                    f"edv_{i}_data_in": f"map_{i}_offset when eds_{i}_data_out = '1' else {self.neutral_element}",
                    f"cc_val{i}_in": f"edv_{i}_data_out"
                }
                bhv += generateAssignments(assignments)
            elif self.mapg.computeLatency() > self.sg.computeLatency() + 1 and self.hcg is not None:
                # hcg to edv, map to cc
                assignments = {
                    f"edv_{i}_enable": f"'1'",
                    F"edv_{i}_data_in": F"hc_{i}_addr_out",
                    F"cc_offset{i}_in": F"edv_{i}_data_out"
                }
                assignments |= {
                    F"cc_val{i}_in": F"map_{i}_offset when eds_{i}_data_out = '1' else {self.neutral_element}"
                }
                bhv += generateAssignments(assignments)
            elif self.mapg.computeLatency() > self.sg.computeLatency()  and self.hcg is None:
                # hcg to edv, map to cc
                assignments = {
                    f"edv_{i}_enable": f"'1'",
                    F"edv_{i}_data_in": F"s_{i}_addr_out({self.waddr-1} downto 0)",
                    F"cc_offset{i}_in": F"edv_{i}_data_out"
                }
                assignments |= {
                    F"cc_val{i}_in": F"map_{i}_offset when eds_{i}_data_out = '1' else {self.neutral_element}"
                }
                bhv += generateAssignments(assignments)
            else:
                assert(False)

        for b in range(self.banks):
            assignments = {
                F"rds_{b}_data_in" : F"rd_en{b}_in",
                F"vdv_{b}_data_in" : F"cc_val{b}_out",
            }
            bhv += generateAssignments(assignments)

            assignments = {
                F"mc_{b}_rd_addr_in" : F"cc_offset{b}_out when rd_en{b}_in = '0' else rd_addr{b}_in"
            }
            bhv += generateAssignments(assignments)

            assignments = {
                F"dfu_{b}_addr_in" : F"mc_{b}_rd_addr_out",
                F"dfu_{b}_data_in" : F"mc_{b}_rd_data_out"
            }
            bhv += generateAssignments(assignments)

            assignments = {
                F"u_{b}_v": F"vdv_{b}_data_out",
                F"u_{b}_seed": F"useed_in",
                F"u_{b}_state": F"dfu_{b}_data_out",
                F"u_{b}_addr_in": F"dfu_{b}_addr_out",
                F"u_{b}_fwd_enable_in": F"'1'",
                F"u_{b}_cmp_in": F"dfu_{b}_cmp_out"
            }
            bhv += generateAssignments(assignments)

            assignments = {
                F"mc_{b}_wr_en_in": "'1'",
                F"mc_{b}_wr_addr_in": F"u_{b}_addr_out",
                F"mc_{b}_wr_data_in": F"u_{b}_outstate",
                F"dfu_{b}_enable_r_in": "'1'",
                F"dfu_{b}_addr_r_in": F"u_{b}_addr_out",
                F"dfu_{b}_data_r_in": F"u_{b}_outstate"
            }
            bhv += generateAssignments(assignments)

        return bhv

    def generateArchitectureDefinition(self):
        # One select per input value
        # One mapper per input value
        # + additional delay per input value if necessary
        # One concurrency controller
        # Per bank: Memory Read + DFU + AU + Memory Write

        bhv = ""
        for b in range(self.banks):
            assignments = {
                F"rd_data{b}_out" : F"mc_{b}_rd_data_out",
                F"rd_valid{b}_out" : F"rds_{b}_data_out"
            }
            bhv += generateAssignments(assignments)
        frame = F"""
ARCHITECTURE a{self.entity_name} OF {self.entity_name} IS
{self.generateComponentDeclarations()}
BEGIN
{self.generateComponentInstantiations()}
{self.generateConnections()}

OUT_PROC : process(clk)
begin
    if rising_edge(clk) then
{bhv}
    end if;
end process;

END a{self.entity_name};
"""        

        return frame

    def generateComponentDeclaration(self):
        entity_declaration = self.generateEntityDeclaration()
        component_declaration = entity_declaration.replace("ENTITY {}".format(self.entity_name), "COMPONENT {}".format(self.entity_name))
        component_declaration = component_declaration.replace("END {}".format(self.entity_name), "END COMPONENT {}".format(self.entity_name))
        return component_declaration

    def generateFile(self, folder):
        f = open("{}/{}.vhd".format(folder, self.entity_name), "w")
        content = self.generateIncludes()
        content += self.generateEntityDeclaration()
        content += self.generateArchitectureDefinition()
        f.write(content)
        f.close()

        genlist = [self.dvg, self.dsg, self.edvg, self.edsg, self.mbg, self.msg,
                   self.mcg, self.ccg, self.hcg, self.dfug]
        for g in genlist:
            if g is not None:
                g.generateFile(folder)



if __name__ == "__main__":

    from ParserInterface import *
    from Functions import SelectorFunctionGenerator, UpdateFunctionGenerator
    from FunctionPackageGenerator import FunctionPackageGenerator

    with open(sys.argv[1]) as f:
        data = json.load(f)

        outdir = "./output"
        if not os.path.exists(outdir):
            os.makedirs(outdir)

        cwd = os.getcwd()
        os.chdir(os.path.dirname(sys.argv[1]))

        selector_list = create_selector_function_statement_list(data)
        update_list = create_cupdate_function_statement_list(data)
        map_list = create_compute_function_statement_list(data)

        os.chdir(cwd)



        segsize = 4
        total_segs = 16
        banks = 2
        waddr = int(ceil(log2(segsize*total_segs)))
        wbaddr = waddr - int(ceil(log2(banks)))

        fpg = FunctionPackageGenerator()
        fpg.generateFile("./output")

        sfg = SelectorFunctionGenerator(selector_list, data["value_size"], data["selector_seed_size"], data["offset_max_size"], True, True)
        sfg.generateFile("./output")

        ufg = ForwardingUpdateFunctionGenerator(update_list, data["compute_out_size"], data["update_seed_size"], data["state_size"], wbaddr, True)
        ufg.generateFile("./output")

        ufgp = UpdateFunctionGenerator(update_list, data["compute_out_size"], data["update_seed_size"], data["state_size"], True)
        ufgp.generateFile("./output")

        cfg = SelectorFunctionGenerator(map_list, data["value_size"], data["update_seed_size"], data["compute_out_size"], True, True, "mapx")
        cfg.generateFile("./output")

        ssg = OptimisticRowSuperStageGenerator(banks, 4, segsize, total_segs, data["selector_seed_size"], data["update_seed_size"],
                                               data["value_size"], data["state_size"], sfg, ufg, ufgp,
                                               cfg, data["compute_neutral"], 30, True, True, 8)
        ssg.generateFile("./output")

        #print(ssg.generateComponentDeclaration())
        #for signal in ssg.generateDeclarationSignals():
        #    print(F"signal {signal[0]}: {signal[2]};")

        #signal_map = generateSignalMap(ssg.generateDeclarationSignals(), F"")
        #print(generateComponentInstantiation(F"ss", ssg.entity_name, signal_map, None))
