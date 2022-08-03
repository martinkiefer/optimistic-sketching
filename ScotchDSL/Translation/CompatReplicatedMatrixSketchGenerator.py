from math import ceil, log2, floor
from MemoryComponentGenerator import MemoryComponentGenerator
from HashConverterGenerator import HashConverterGenerator
from DFUGenerator import DFUGenerator
from GeneratorUtils import generateComponentInstantiation, generateSignalMap, generateAssignments
from ForwardingUpdateFunctionGenerator import ForwardingUpdateFunctionGenerator
from DChainVectorGenerator import DChainVectorGenerator
from DChainSignalGenerator import DChainSignalGenerator
from RowSuperStageGenerator import RowSuperStageGenerator
from FunctionPackageGenerator import FunctionPackageGenerator
from SeedGenerator import SeedGenerator
from MuxGenerator import MuxGenerator
from DemuxGenerator import DemuxGenerator
from DemuxConfigPackageGenerator import DemuxConfigPackageGenerator
from MuxConfigPackageGenerator import MuxConfigPackageGenerator
from MemorySegmentGenerator import MemorySegmentGenerator
from GlobalConfigPackageGenerator import GlobalConfigPackageGenerator
from MatrixSketchGenerator import MatrixSketchGenerator

import math
import os

def is_power_of_two(n):
    return n > 0 and (n & (n - 1)) == 0

class ReplicatedMatrixSketchGenerator(MatrixSketchGenerator):
    def __init__(self, n_parallel, size_matrix, wsseed, wuseed, wvalue, 
    wstate, selector_generator, update_generator, ss_factor, dfactor, cfactor, prefix=""):
        self.n_parallel = n_parallel

        super().__init__(size_matrix, wsseed, wuseed, wvalue, 
        wstate, selector_generator, update_generator, ss_factor, dfactor, cfactor, prefix=prefix)

        self.n_sstages = n_parallel*self.n_rows
        self.mux_pkg = MuxConfigPackageGenerator(self.n_rows, cfactor, self.wstate, prefix=prefix)
        self.demux_pkg = DemuxConfigPackageGenerator(self.n_rows, dfactor, self.waddr, prefix=prefix)
        self.gcpg = GlobalConfigPackageGenerator("select-update", self.wstate, self.wvalue, self.size_matrix[0][0], 1, self.wsseed, self.wuseed, 
    dfactor, cfactor, n_parallel, 1, self.n_rows, self.total_size, prefix=prefix)



    def generateDeclarationSignals(self):
        signals = []
        signals += [("clk", "in", "std_logic")]

        #Signals for direct reading from read stage overrides value_enable
        signals += [("rd_en_in", "in", "std_logic")]
        signals += [("ready", "out", "std_logic")]

        for i in range(0,self.n_parallel):
            #Signals for value processing
            signals += [("val_en{}_in".format(i), "in", "std_logic")]
            signals += [("val{}_in".format(i), "in", "std_logic_vector({} downto 0)".format(self.wvalue-1))]
            signals += [(F"rd_data{i}_out", "out", "std_logic_vector({} downto 0)".format(self.wstate-1))]
            signals += [(F"rd_valid{i}_out", "out", "std_logic")]

        return signals


    def generateArchitectureDefinition(self):
        frame = """
ARCHITECTURE a{} OF {} IS
{}
BEGIN
{}
END a{};
"""        

        decl = ""
        #Declarations
        for ssg in self.ssgl:
            decl += ssg.generateComponentDeclaration()

        decl += self.demuxg.generateComponentDeclaration()
        decl += self.muxg.generateComponentDeclaration()

        ## Connecting signals
        for i in range(0,self.n_parallel):
            for ssg in self.ssgl:
                for signal in ssg.generateDeclarationSignals():
                    decl += "\nsignal ss{}_{}_{} : {};".format(ssg.identifier, i, signal[0],signal[2])       

            for signal in self.muxg.generateDeclarationSignals():
                decl += "\nsignal smux{}_{} : {};".format(i,signal[0],signal[2])    

            for signal in self.demuxg.generateDeclarationSignals():
                decl += "\nsignal sdemux{}_{} : {};".format(i,signal[0],signal[2])  

        decl += "\nsignal addr : std_logic_vector({}-1 downto 0) := (others => '0');".format(self.waddr)
        decl += "\nsignal index : std_logic_vector({}-1 downto 0) := (others => '0');".format(int(math.ceil(math.log2(self.n_rows))))
        decl += "\ntype mem_type is array({} downto 0) of std_logic_vector({} downto 0);".format(self.nss_per_package-1, self.wvalue-1)

        #Architecture behavior
        ## Generate component instanciations
        bhv = ""
        for i in range(0, self.n_parallel):
            for ssg in self.ssgl:
                signal_map = generateSignalMap(ssg.generateDeclarationSignals(), "ss{}_{}_".format(ssg.identifier,i))
                bhv += generateComponentInstantiation("ss{}_{}".format(ssg.identifier,i), ssg.entity_name, signal_map, None)


            signal_map = generateSignalMap(self.muxg.generateDeclarationSignals(), F"smux{i}_")
            bhv += generateComponentInstantiation(F"smux{i}", self.muxg.entity_name, signal_map, None)

            signal_map = generateSignalMap(self.demuxg.generateDeclarationSignals(), F"sdemux{i}_")
            bhv += generateComponentInstantiation(F"sdemux{i}", self.demuxg.entity_name, signal_map, None)


        clk_map = {}

        seed_map = {}
        for i in range(0,self.n_parallel):
            clk_map[F"smux{i}_clk"] = "clk"
            clk_map[F"sdemux{i}_clk"] = "clk"

            for ssg in self.ssgl:
                clk_map["ss{}_{}_clk".format(ssg.identifier, i)] = "clk" 
                seed_map["ss{}_{}_sseed_in".format(ssg.identifier, i)] = "selector_seeds({})".format(ssg.identifier)
                seed_map["ss{}_{}_useed_in".format(ssg.identifier, i)] = "update_seeds({})".format(ssg.identifier)
            demux_inmap = {
                F"sdemux{i}_data_in" : "addr",
                F"sdemux{i}_enable_in" : "rd_en_in",
                F"sdemux{i}_index_in" : "index"
            }

            bhv += generateAssignments(demux_inmap)
        bhv += generateAssignments(clk_map) 
        bhv += generateAssignments(seed_map)



        for i in range(0, self.n_parallel):
            mux_outmap = {
                F"rd_data{i}_out" : F"smux{i}_data_out",
                F"rd_valid{i}_out" : F"smux{i}_enable_out"
            }
            bhv += generateAssignments(mux_outmap)

        assignments = ""
        loop_assignments = ""
        for i in range(0, self.n_parallel):
            loop_assignments += "enable_pipe{}(i+1) := enable_pipe{}(i);\n".format(i, i)
            loop_assignments += "value_pipe{}(i+1) := value_pipe{}(i);\n".format(i, i)

            assignments += "enable_pipe{}(0) := val_en{}_in;\n".format(i,i)
            assignments += "value_pipe{}(0) := val{}_in;\n".format(i,i)
            
        for i in range(0, self.n_parallel):
            for ssg in self.ssgl:
                assignments += "        ss{}_{}_val_en_in <= enable_pipe{}({});\n".format(ssg.identifier, i, i, ssg.identifier // self.ss_factor)
                assignments += "        ss{}_{}_val_in <= value_pipe{}({});\n".format(ssg.identifier, i, i, ssg.identifier // self.ss_factor)

        for i in range(0, self.n_parallel):
            for ssg in self.ssgl:
                #Connect demux output to read inputs
                bhv += "ss{}_{}_rd_en_in <= sdemux{}_enable_out({});\n".format(ssg.identifier, i, i, ssg.identifier)
                bhv += "ss{}_{}_rd_addr_in <= sdemux{}_data_out({});\n".format(ssg.identifier, i, i, ssg.identifier)

                #Connect demux output to read inputs
                bhv += "smux{}_data_in({}) <= ss{}_{}_rd_data_out ;\n".format(i, ssg.identifier, ssg.identifier, i)
                bhv += "smux{}_enable_in({}) <= ss{}_{}_rd_valid_out;\n".format(i, ssg.identifier, ssg.identifier, i)

        process_declaration = ""
        for i in range(0, self.n_parallel):
            process_declaration += "variable enable_pipe{} : std_logic_vector({} downto 0) := (others => '0');\n".format(i, self.nss_per_package-1)
            process_declaration += "variable value_pipe{} : mem_type;\n".format(i)


        bhv += """
    ready <= '1';

	process(clk)
    begin
    if rising_edge(clk) then
        if rd_en_in = '1' then
            if to_integer(unsigned(addr)) >= {} then
                addr <= (others => '0');
                if to_integer(unsigned(index)) >= {} then
                    index <= (others => '0');
                else
                    index <= std_logic_vector(to_unsigned(to_integer(unsigned(index)) + 1, index'LENGTH));
                end if;
            else
                addr <= std_logic_vector(to_unsigned(to_integer(unsigned(addr)) + 1, addr'LENGTH));
            end if;
        end if;
    end if;
    end process;

    process(clk)
{}
    begin
    if rising_edge(clk) then
{}
        for i in {} downto 0 loop
{}
        end loop;
    end if;
    end process;
        """.format(self.total_size-1, self.n_rows-1, process_declaration, assignments, self.nss_per_package-2, loop_assignments)

        return frame.format(self.entity_name, self.entity_name, decl, bhv, self.entity_name)

    def generateComponentDeclaration(self):
        entity_declaration = self.generateEntityDeclaration()
        component_declaration = entity_declaration.replace("ENTITY {}".format(self.entity_name), "COMPONENT {}".format(self.entity_name))
        component_declaration = component_declaration.replace("END {}".format(self.entity_name), "END COMPONENT {}".format(self.entity_name))
        return component_declaration


if __name__ == "__main__":

    from ParserInterface import *
    from Functions import SelectorFunctionGenerator, UpdateFunctionGenerator

    with open(sys.argv[1]) as f:
        data = json.load(f)

        if len(sys.argv) >= 9:
            outdir = sys.argv[8]
        else:
            outdir = "./output"

        if len(sys.argv) >= 10:
            prefix = sys.argv[9]
        else:
            prefix = ""

        if not os.path.exists(outdir):
            os.makedirs(outdir)

        cwd = os.getcwd()
        os.chdir(os.path.dirname(sys.argv[1]))
        selector_list = create_selector_function_statement_list(data, prefix=prefix)
        update_list = create_update_function_statement_list(data, prefix=prefix)
        os.chdir(cwd)

        sfg = SelectorFunctionGenerator(selector_list, data["value_size"], data["selector_seed_size"], data["offset_max_size"], True, prefix=prefix)
        sfg.generateFile(outdir)

        matrix = [[int(sys.argv[2])]*int(sys.argv[4])]*int(sys.argv[3])
        waddr = int(ceil(log2(sum(matrix[0]))))
        ufg = ForwardingUpdateFunctionGenerator(update_list, data["value_size"], data["update_seed_size"], data["state_size"], waddr, True, prefix=prefix)
        ufg.generateFile(outdir)

        ssg = ReplicatedMatrixSketchGenerator(int(sys.argv[7]), matrix, data["selector_seed_size"], data["update_seed_size"], data["value_size"], data["state_size"], sfg, ufg, 1, int(sys.argv[5]), int(sys.argv[6]), prefix=prefix)
        ssg.generateFile(outdir)

