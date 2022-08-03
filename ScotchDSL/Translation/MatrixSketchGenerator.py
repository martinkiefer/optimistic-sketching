from math import ceil, log2, floor
from HashConverterGenerator import HashConverterGenerator
from DFUGenerator import DFUGenerator
from GeneratorUtils import generateComponentInstantiation, generateSignalMap, generateAssignments
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
from MemoryBufferGenerator import MemoryBufferGenerator

import math

def is_power_of_two(n):
    return n > 0 and (n & (n - 1)) == 0

class MatrixSketchGenerator:
    def __init__(self, size_matrix, wsseed, wuseed, wvalue, 
    wstate, selector_generator, update_generator, ss_factor, dfactor, cfactor, prefix=""):
        self.prefix = prefix
        self.size_matrix = size_matrix
        self.n_rows = len(self.size_matrix)
        self.total_size = sum(self.size_matrix[0])
        self.waddr = int(ceil(log2(self.total_size)))
        self.wsseed = wsseed
        self.wuseed = wuseed
        self.wvalue = wvalue
        self.wstate= wstate
        self.usg = SeedGenerator("update_seed_pkg", "update_seeds", self.n_rows, self.wuseed, prefix=prefix)
        self.ssg = SeedGenerator("selector_seed_pkg", "selector_seeds", self.n_rows, self.wsseed, prefix=prefix)

        self.dvg = DChainVectorGenerator(prefix=prefix)
        self.dsg = DChainSignalGenerator(prefix=prefix)
        self.fpg = FunctionPackageGenerator(prefix=prefix)
        
        self.gcpg = GlobalConfigPackageGenerator("select-update", self.wstate, self.wvalue, self.size_matrix[0][0], 1, self.wsseed, self.wuseed, 
    dfactor, cfactor, 1, 1, self.n_rows, self.total_size, prefix=prefix)

        self.msg = MemorySegmentGenerator(prefix)
        self.mbg = MemoryBufferGenerator(prefix)
        self.sg = selector_generator
        self.ug = update_generator
        self.hcg = HashConverterGenerator(prefix)
        self.dfug = DFUGenerator(prefix)
        self.ss_factor = ss_factor

        self.demuxg = DemuxGenerator(prefix)
        self.muxg = MuxGenerator(prefix)

        self.mux_pkg = MuxConfigPackageGenerator(self.n_rows, cfactor, self.wstate, prefix=prefix)
        self.demux_pkg = DemuxConfigPackageGenerator(self.n_rows, dfactor, self.waddr, prefix=prefix)

        self.entity_name = F"{prefix}sketch"

        self.signals = self.generateDeclarationSignals()

        self.ssgl = []
        for i, rowsizes in enumerate(self.size_matrix):
            self.ssgl.append(RowSuperStageGenerator(rowsizes,self.wsseed, self.wuseed, self.wvalue, self.wstate, 
            self.msg, self.mbg, self.sg, self.dvg, self.dsg, self.ug, self.dfug, self.hcg, i, prefix=prefix))

        self.nss_per_package = int(math.ceil(self.n_rows / self.ss_factor))

        
    def generateIncludes(self):
        return F"""
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use work.{self.prefix}update_seed_pkg.all;
use work.{self.prefix}selector_seed_pkg.all;
use WORK.{self.prefix}mux_config_pkg.all;
use WORK.{self.prefix}demux_config_pkg.all;
"""


    def generateDeclarationSignals(self):
        signals = []
        signals += [("clk", "in", "std_logic")]

        #Signals for direct reading from read stage overrides value_enable
        signals += [("rd_en_in", "in", "std_logic")]
        signals += [("rd_data_out", "out", "std_logic_vector({} downto 0)".format(self.wstate-1))]
        signals += [("rd_valid_out", "out", "std_logic")]

        #Signals for value processing
        signals += [("val_en_in", "in", "std_logic")]
        signals += [("val_in", "in", "std_logic_vector({} downto 0)".format(self.wvalue-1))]

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
        for ssg in self.ssgl:
            for signal in ssg.generateDeclarationSignals():
                decl += "\nsignal ss{}_{} : {};".format(ssg.identifier, signal[0],signal[2])       

        for signal in self.muxg.generateDeclarationSignals():
            decl += "\nsignal smux_{} : {};".format(signal[0],signal[2])    

        for signal in self.demuxg.generateDeclarationSignals():
            decl += "\nsignal sdemux_{} : {};".format(signal[0],signal[2])  

        decl += "\nsignal addr : std_logic_vector({}-1 downto 0) := (others => '0');".format(self.waddr)
        decl += "\nsignal index : std_logic_vector({}-1 downto 0) := (others => '0');".format(int(math.ceil(math.log2(self.n_rows))))
        decl += "\ntype mem_type is array({} downto 0) of std_logic_vector({} downto 0);".format(self.nss_per_package-1, self.wvalue-1)

        #Architecture behavior
        ## Generate component instanciations
        bhv = ""
        for ssg in self.ssgl:
            signal_map = generateSignalMap(ssg.generateDeclarationSignals(), "ss{}_".format(ssg.identifier))
            bhv += generateComponentInstantiation("ss{}".format(ssg.identifier), ssg.entity_name, signal_map, None)


        signal_map = generateSignalMap(self.muxg.generateDeclarationSignals(), "smux_")
        bhv += generateComponentInstantiation("smux", self.muxg.entity_name, signal_map, None)

        signal_map = generateSignalMap(self.demuxg.generateDeclarationSignals(), "sdemux_")
        bhv += generateComponentInstantiation("sdemux", self.demuxg.entity_name, signal_map, None)


        clk_map = {}
        clk_map["smux_clk"] = "clk"
        clk_map["sdemux_clk"] = "clk"

        seed_map = {}
        for ssg in self.ssgl:
            clk_map["ss{}_clk".format(ssg.identifier)] = "clk" 
            seed_map["ss{}_sseed_in".format(ssg.identifier)] = "selector_seeds({})".format(ssg.identifier)
            seed_map["ss{}_useed_in".format(ssg.identifier)] = "update_seeds({})".format(ssg.identifier)
        bhv += generateAssignments(clk_map) 
        bhv += generateAssignments(seed_map)

        demux_inmap = {
            "sdemux_data_in" : "addr",
            "sdemux_enable_in" : "rd_en_in",
            "sdemux_index_in" : "index"
        }
        bhv += generateAssignments(demux_inmap)

        mux_outmap = {
            "rd_data_out" : "smux_data_out",
            "rd_valid_out" : "smux_enable_out"
        }
        bhv += generateAssignments(mux_outmap)

        assignments = ""
        for ssg in self.ssgl:
            assignments += "        ss{}_val_en_in <= enable_pipe({});\n".format(ssg.identifier, ssg.identifier // self.ss_factor)
            assignments += "        ss{}_val_in <= value_pipe({});\n".format(ssg.identifier, ssg.identifier // self.ss_factor)

        for ssg in self.ssgl:
            #Connect demux output to read inputs
            bhv += "ss{}_rd_en_in <= sdemux_enable_out({});\n".format(ssg.identifier, ssg.identifier)
            bhv += "ss{}_rd_addr_in <= sdemux_data_out({});\n".format(ssg.identifier, ssg.identifier)

            #Connect demux output to read inputs
            bhv += "smux_data_in({}) <= ss{}_rd_data_out ;\n".format(ssg.identifier, ssg.identifier)
            bhv += "smux_enable_in({}) <= ss{}_rd_valid_out;\n".format(ssg.identifier, ssg.identifier)

        bhv += """
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
        variable enable_pipe : std_logic_vector({} downto 0) := (others => '0');
        variable value_pipe : mem_type;
	begin
    if rising_edge(clk) then
        enable_pipe(0) := val_en_in;
        value_pipe(0) := val_in;
{}
        for i in {} downto 0 loop
            enable_pipe(i+1) := enable_pipe(i);
            value_pipe(i+1) := value_pipe(i);
        end loop;
    end if;
    end process;
        """.format(self.total_size-1, self.n_rows-1, self.nss_per_package-1, assignments, self.nss_per_package-2)

        return frame.format(self.entity_name, self.entity_name, decl, bhv, self.entity_name)

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

        for ssg in self.ssgl:
            ssg.generateFile(folder)

        self.dvg.generateFile(folder)
        self.dsg.generateFile(folder)
        self.hcg.generateFile(folder)
        self.dfug.generateFile(folder)
        self.msg.generateFile(folder)
        self.fpg.generateFile(folder)
        self.usg.generateFile(folder)
        self.ssg.generateFile(folder)
        self.demuxg.generateFile(folder)
        self.muxg.generateFile(folder)
        self.demux_pkg.generateFile(folder)
        self.mux_pkg.generateFile(folder)
        self.gcpg.generateFile(folder)
        self.mbg.generateFile(folder)
