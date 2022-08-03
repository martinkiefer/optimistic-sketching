from math import ceil, log2, floor
from MemoryComponentGenerator import MemoryComponentGenerator
from HashConverterGenerator import HashConverterGenerator
from DFUGenerator import DFUGenerator
from GeneratorUtils import generateComponentInstantiation, generateSignalMap, generateAssignments
from ForwardingUpdateFunctionGenerator import ForwardingUpdateFunctionGenerator
from DChainVectorGenerator import DChainVectorGenerator
from DChainSignalGenerator import DChainSignalGenerator
from OptimisticRowSuperStageGenerator import OptimisticRowSuperStageGenerator
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

class OptimisticMatrixSketchGenerator:
    def __init__(self, n_inputs, banks, nrows, memseg_size, total_segments, wsseed, wuseed, wvalue, wstate,
     selector_generator, update_generator, map_generator, plain_update_generator, neutral_element,
                 qsize, with_mt, with_mqt, smg_depth, effective_increment_size=None, level_increment=0, dfactor=4, cfactor=2, prefix=""):
        self.entity_name = F"{prefix}sketch"
        self.n_inputs = n_inputs
        self.nrows = nrows
        self.banks = banks
        self.memseg_size = memseg_size
        self.total_segments = total_segments
        self.neutral_element = neutral_element
        self.total_size = self.memseg_size*self.total_segments
        self.waddr = int(ceil(log2(self.total_size)))
        self.wbaddr = self.waddr - int(ceil(log2(self.banks)))

        self.wseed = wsseed
        self.wuseed = wuseed
        self.wvalue = wvalue
        self.wstate = wstate

        self.n_sstages = self.nrows

        self.selector_generator = selector_generator
        self.map_generator = map_generator
        self.update_generator = update_generator
        self.plain_update_generator = plain_update_generator

        # I think, we are gonna need several of these beauties
        self.mux_pkg = MuxConfigPackageGenerator(self.nrows, cfactor, self.wstate, prefix=prefix)
        self.demux_pkg = DemuxConfigPackageGenerator(self.nrows, dfactor, self.wbaddr, prefix=prefix)

        self.usg = SeedGenerator("update_seed_pkg", "update_seeds", self.nrows, self.wuseed, prefix=prefix)
        self.ssg = SeedGenerator("selector_seed_pkg", "selector_seeds", self.nrows, self.wseed, prefix=prefix)

        self.demuxg = DemuxGenerator(prefix)
        self.muxg = MuxGenerator(prefix)

        # Set up the OptimisticRowSuperStage
        self.sg = OptimisticRowSuperStageGenerator(banks, n_inputs, memseg_size, total_segments, wsseed, wuseed,
                                                    wvalue, wstate, selector_generator, update_generator,
                                                    plain_update_generator, map_generator, self.neutral_element,
                                                    qsize, with_mt, with_mqt, smg_depth, effective_increment_size, level_increment, prefix=prefix)

        self.gcpg = GlobalConfigPackageGenerator("optimistic", self.wstate, self.wvalue, memseg_size, n_inputs, self.wseed, self.wuseed,
    dfactor, cfactor, self.banks, 1, self.nrows, self.total_size, prefix=prefix)

        self.signals = self.generateDeclarationSignals()

    def generateIncludes(self):
        return F"""
    library ieee;
    use ieee.std_logic_1164.all;
    use ieee.numeric_std.all;
    use work.{self.usg.package_name}.all;
    use work.{self.ssg.package_name}.all;
    use WORK.{self.mux_pkg.pkg_name}.all;
    use WORK.{self.demux_pkg.pkg_name}.all;
    """


    def generateDeclarationSignals(self):
        signals = []
        signals += [("clk", "in", "std_logic")]
        signals += [("ready", "out", "std_logic")]
        signals += [(F"rd_en_in", "in", "std_logic")]

        for b in range(self.banks):
            signals += [(F"rd_data{b}_out", "out", F"std_logic_vector({self.wstate-1} downto 0)")]
            signals += [(F"rd_valid{b}_out", "out", "std_logic")]

        for i in range(self.n_inputs):
            #Signals for value processing
            signals += [(F"val_en{i}_in", "in", "std_logic")]
            signals += [(F"val{i}_in", "in", F"std_logic_vector({self.wvalue - 1} downto 0)")]

        return signals


    def generateArchitectureDefinition(self):

        decl = ""
        #Declarations
        decl += self.sg.generateComponentDeclaration()

        # One mux, demux pair per input value connecting to each row
        # Connect inputs directly to rows. If this becomes an issue, we'll use the big fat demux

        decl += self.demuxg.generateComponentDeclaration()
        decl += self.muxg.generateComponentDeclaration()

        ## Connecting signals
        for i in range(self.nrows):
            for signal in self.sg.generateDeclarationSignals():
                if signal[0] != "enable":
                    decl += F"\nsignal ss{i}_{signal[0]} : {signal[2]};"
                else:
                    decl += F"\nsignal ss{i}_{signal[0]} : {signal[2]} := '1';"

        decl += F"\nsignal tmp_ready : std_logic := '1';"

        for b in range(self.banks):
            for signal in self.muxg.generateDeclarationSignals():
                decl += F"\nsignal smux{b}_{signal[0]} : {signal[2]};"

            for signal in self.demuxg.generateDeclarationSignals():
                decl += F"\nsignal sdemux{b}_{signal[0]} : {signal[2]};"

        decl += "\nsignal addr : std_logic_vector({}-1 downto 0) := (others => '0');".format(self.wbaddr)
        decl += "\nsignal index : std_logic_vector({}-1 downto 0) := (others => '0');".format(int(math.ceil(math.log2(self.nrows))))

        #Architecture behavior
        ## Generate component instanciations
        bhv = ""
        for i in range(self.nrows):
            signal_map = generateSignalMap(self.sg.generateDeclarationSignals(), F"ss{i}_")
            bhv += generateComponentInstantiation(F"ss{i}", self.sg.entity_name, signal_map, None)


        for b in range(self.banks):
            signal_map = generateSignalMap(self.muxg.generateDeclarationSignals(), F"smux{b}_")
            bhv += generateComponentInstantiation(F"smux{b}", self.muxg.entity_name, signal_map, None)

            signal_map = generateSignalMap(self.demuxg.generateDeclarationSignals(), F"sdemux{b}_")
            bhv += generateComponentInstantiation(F"sdemux{b}", self.demuxg.entity_name, signal_map, None)

        seed_map = {}
        for i in range(self.nrows):
            seed_map[F"ss{i}_sseed_in"] = F"selector_seeds({i})"
            seed_map[F"ss{i}_useed_in"] = F"update_seeds({i})"
        bhv += generateAssignments(seed_map)

        for b in range(self.banks):
            demux_inmap = {
                F"sdemux{b}_data_in" : "addr",
                F"sdemux{b}_enable_in" : "rd_en_in",
                F"sdemux{b}_index_in" : "index"
            }
            bhv += generateAssignments(demux_inmap)

            mux_outmap = {
                F"rd_data{b}_out" : F"smux{b}_data_out",
                F"rd_valid{b}_out" : F"smux{b}_enable_out"
            }
            bhv += generateAssignments(mux_outmap)

        assignments = ""
        for i in range(self.n_inputs):
            for r in range(self.nrows):
                bhv += F"        ss{r}_val_en{i}_in <= val_en{i}_in and tmp_ready;\n"
                bhv += F"        ss{r}_val{i}_in <= val{i}_in;\n"

        for r in range(self.nrows):
            for b in range(self.banks):
                #Connect demux output to read inputs
                bhv += F"ss{r}_rd_en{b}_in <= sdemux{b}_enable_out({r});\n"
                bhv += F"ss{r}_rd_addr{b}_in <= sdemux{b}_data_out({r});\n"

                #Connect demux output to read inputs
                bhv += F"smux{b}_data_in({r}) <= ss{r}_rd_data{b}_out ;\n"
                bhv += F"smux{b}_enable_in({r}) <= ss{r}_rd_valid{b}_out;\n"


        bhv += F"""
	process(clk)
    begin
    if rising_edge(clk) then
        if rd_en_in = '1' then
            if to_integer(unsigned(addr)) >= {self.total_size//self.banks-1} then
                addr <= (others => '0');
                if to_integer(unsigned(index)) >= {self.nrows} then
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
"""

        bhv += F"""
    process(clk) is
    begin
        if rising_edge(clk) then
            tmp_ready <= not ({" or ".join([F"ss{i}_almost_full" for i in range(self.nrows)])});
        end if;
    end process;
            """

        for r in range(self.nrows):
            bhv += F"""
            process(clk) is
            begin
                if rising_edge(clk) then
                    ss{r}_enable <= not ({" or ".join([F"ss{i}_almost_full" for i in range(self.nrows)])});
                end if;
            end process;
                    """

        frame = F"""
    ARCHITECTURE a{self.entity_name} OF {self.entity_name} IS
    {decl}
    BEGIN
    {bhv}
    ready <= tmp_ready;
    END a{self.entity_name};
        """
        return frame

    def generateEntityDeclaration(self):
        frame = """
    ENTITY {} IS
    PORT (
    {}
    );
    END {};"""
        signals = map(lambda x: "{} : {} {}".format(x[0], x[1], x[2]), self.signals)
        return frame.format(self.entity_name, ";\n".join(signals), self.entity_name)

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

        self.sg.generateFile(folder)
        self.gcpg.generateFile(folder)
        self.demuxg.generateFile(folder)
        self.muxg.generateFile(folder)
        self.mux_pkg.generateFile(folder)
        self.demux_pkg.generateFile(folder)
        self.usg.generateFile(folder)
        self.ssg.generateFile(folder)



if __name__ == "__main__":

    from ParserInterface import *
    from Functions import SelectorFunctionGenerator, UpdateFunctionGenerator

    with open(sys.argv[1]) as f:
        data = json.load(f)

        if len(sys.argv) >= 12:
            outdir = sys.argv[11]
        else:
            outdir = "./output"

        if len(sys.argv) == 13:
            prefix = sys.argv[12]
        else:
            prefix = ""

        if not os.path.exists(outdir):
            os.makedirs(outdir)

        cwd = os.getcwd()
        os.chdir(os.path.dirname(sys.argv[1]))

        selector_list = create_selector_function_statement_list(data, prefix=prefix)
        update_list = create_cupdate_function_statement_list(data, prefix=prefix)
        map_list = create_compute_function_statement_list(data, prefix=prefix)

        os.chdir(cwd)
        nrows = int(sys.argv[2])
        n_inputs = int(sys.argv[3])
        banks = int(sys.argv[4])
        segsize = int(sys.argv[5])
        total_segments = int(sys.argv[6])
        qsize = int(sys.argv[7])
        with_mt = (int(sys.argv[8]) > 0)
        with_mqt = (int(sys.argv[9]) > 0)
        smg_depth = int(sys.argv[10])

        waddr = int(ceil(log2(segsize*total_segments)))
        wbaddr = waddr - int(ceil(log2(banks)))

        fpg = FunctionPackageGenerator(prefix)
        fpg.generateFile(outdir)

        sfg = SelectorFunctionGenerator(selector_list, data["value_size"], data["selector_seed_size"], data["offset_max_size"], True, True, prefix=prefix)
        sfg.generateFile(outdir)

        ufg = ForwardingUpdateFunctionGenerator(update_list, data["compute_out_size"], data["update_seed_size"], data["state_size"], wbaddr, True, prefix=prefix)
        ufg.generateFile(outdir)

        ufgp = UpdateFunctionGenerator(update_list, data["compute_out_size"], data["update_seed_size"], data["state_size"], True, prefix=prefix)
        ufgp.generateFile(outdir)

        cfg = SelectorFunctionGenerator(map_list, data["value_size"], data["update_seed_size"], data["compute_out_size"], True, True, "mapx", prefix=prefix)
        cfg.generateFile(outdir)

        if not "effective_increment_size" in data:
            data["effective_increment_size"] = None

        if not "level_value_increment" in data:
            data["level_value_increment"] = 0

        ssg = OptimisticMatrixSketchGenerator(n_inputs, banks, nrows, segsize, total_segments,
                                              data["selector_seed_size"], data["update_seed_size"], data["value_size"],
                                              data["state_size"], sfg, ufg, cfg, ufgp, data["compute_neutral"], qsize,
                                              with_mt, with_mqt, smg_depth, data["effective_increment_size"], data["level_value_increment"], prefix=prefix)
        ssg.generateFile(outdir)

        #print(ssg.generateComponentDeclaration())

        #for signal in ssg.generateDeclarationSignals():
        #    print(F"signal {signal[0]} : {signal[2]};")

        #signal_map = generateSignalMap(ssg.generateDeclarationSignals(), F"")
        #print(generateComponentInstantiation(F"s", ssg.entity_name, signal_map, None))
