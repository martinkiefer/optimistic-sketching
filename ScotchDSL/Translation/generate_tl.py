from math import ceil, log2, floor
from ForwardingUpdateFunctionGenerator import ForwardingUpdateFunctionGenerator
from OptimisticMatrixSketchGenerator import OptimisticMatrixSketchGenerator
from GeneratorUtils import generateComponentInstantiation, generateSignalMap, generateAssignments

class TlGenerator:
    def __init__(self, sketchg):
        self.entity_name = "tl"
        self.sketchg = sketchg

    def generateIncludes(self):
        return """
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use WORK.functions_pkg.all;
    """

    def getEntitySignals(self):
        signals = []
        signals += [("clk", "in", "std_logic")]
        signals += [("sin1", "in", "std_logic")]
        signals += [("sout1", "out", "std_logic")]
        return signals

    def generateArchitectureDefinition(self):
        outputxor = " xor ".join(map(lambda x : F"parity(rd_data{x}_out)", range(self.sketchg.banks)))
        pmap = ["\nclk => clk", "\nready => open", "\nrd_en_in => rd_en_in"]
        pmap += list(map(lambda x: F"\nrd_data{x}_out => rd_data{x}_out", range(self.sketchg.banks)))
        pmap += list(map(lambda x: F"\nval{x}_in => val{x}_in", range(self.sketchg.n_inputs)))
        pmap += list(map(lambda x: F"\nval_en{x}_in => val_en{x}_in", range(self.sketchg.n_inputs)))

        decl = self.sketchg.generateComponentDeclaration()
        for signal in ssg.generateDeclarationSignals():
            if not signal[0] == "clk":
                decl += F"signal {signal[0]} : {signal[2]};\n"

        signal_map = generateSignalMap(ssg.generateDeclarationSignals(), F"")
        cmap = generateComponentInstantiation(F"s", ssg.entity_name, signal_map, None)

        input_chain = []
        idx = 0
        input_chain += [F"\nrd_en_in <= input_chain({idx})"]
        idx += 1
        for i in range(self.sketchg.n_inputs):
            input_chain += [F"\nval_en{i}_in <= input_chain({idx})"]
            idx += 1
            input_chain += [F"\nval{i}_in <= input_chain({idx+self.sketchg.wvalue-1} downto {idx})"]
            idx += self.sketchg.wvalue


        return F"""
architecture rtl of {self.entity_name} is
{decl}
signal input_chain : std_logic_vector({(self.sketchg.wvalue+1)*self.sketchg.n_inputs} downto 0);
begin
{cmap}
{";".join(input_chain)};
process(clk)
begin
    if rising_edge(clk) then
        input_chain(0) <= sin1;
        for i in 0 to input_chain'LENGTH-2 loop
                input_chain(i+1) <= input_chain(i);
        end loop;
    end if;
end process;
        
sout1 <= {outputxor};      

end rtl;
        """


    def generateEntityDeclaration(self):
        frame = """
    ENTITY {} IS
    PORT (
    {}
    );
    END {};"""
        signals = map(lambda x: "{} : {} {}".format(x[0], x[1], x[2]), self.getEntitySignals())
        return frame.format(self.entity_name, ";\n".join(signals), self.entity_name)


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


if __name__ == "__main__":

    from ParserInterface import *
    from Functions import SelectorFunctionGenerator, UpdateFunctionGenerator

    with open(sys.argv[1]) as f:
        data = json.load(f)

        if len(sys.argv) == 12:
            outdir = sys.argv[11]
        else:
            outdir = "./output"

        if not os.path.exists(outdir):
            os.makedirs(outdir)

        cwd = os.getcwd()
        os.chdir(os.path.dirname(sys.argv[1]))

        selector_list = create_selector_function_statement_list(data)
        update_list = create_cupdate_function_statement_list(data)
        map_list = create_compute_function_statement_list(data)

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

        fpg = FunctionPackageGenerator()
        fpg.generateFile(outdir)

        sfg = SelectorFunctionGenerator(selector_list, data["value_size"], data["selector_seed_size"], data["offset_max_size"], True, True)
        sfg.generateFile(outdir)

        ufg = ForwardingUpdateFunctionGenerator(update_list, data["compute_out_size"], data["update_seed_size"], data["state_size"], wbaddr, True)
        ufg.generateFile(outdir)

        ufgp = UpdateFunctionGenerator(update_list, data["compute_out_size"], data["update_seed_size"], data["state_size"], True)
        ufgp.generateFile(outdir)

        cfg = SelectorFunctionGenerator(map_list, data["value_size"], data["update_seed_size"], data["compute_out_size"], True, True, "mapx")
        cfg.generateFile(outdir)

        if not "effective_increment_size" in data:
            data["effective_increment_size"] = None

        if not "level_value_increment" in data:
            data["level_value_increment"] = 0

        ssg = OptimisticMatrixSketchGenerator(n_inputs, banks, nrows, segsize, total_segments,
                                              data["selector_seed_size"], data["update_seed_size"], data["value_size"],
                                              data["state_size"], sfg, ufg, cfg, ufgp, data["compute_neutral"], qsize,
                                              with_mt, with_mqt, smg_depth, data["effective_increment_size"], data["level_value_increment"])

        ssg.generateFile(outdir)

        tlg = TlGenerator(ssg)
        tlg.generateFile(outdir)
