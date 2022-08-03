from math import ceil, log2, floor
from ForwardingUpdateFunctionGenerator import ForwardingUpdateFunctionGenerator
from CompatReplicatedMatrixSketchGenerator import ReplicatedMatrixSketchGenerator
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
        outputxor = " xor ". join(map(lambda i: F" parity(rd_data{i}_out) xor rd_valid{i}_out ",range(self.sketchg.n_parallel)))
        pmap = ["\nclk => clk", "\nready => open", "\nrd_en_in => rd_en_in"]
        pmap += [F"\nrd_data_out => rd_data_out"]
        pmap += list(map(lambda x: F"\nval{x}_in => val{x}_in", range(self.sketchg.n_parallel)))
        pmap += list(map(lambda x: F"\nval_en{x}_in => val_en{x}_in", range(self.sketchg.n_parallel)))

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
        for i in range(self.sketchg.n_parallel):
            input_chain += [F"\nval_en{i}_in <= input_chain({idx})"]
            idx += 1
            input_chain += [F"\nval{i}_in <= input_chain({idx+self.sketchg.wvalue-1} downto {idx})"]
            idx += self.sketchg.wvalue


        return F"""
architecture rtl of {self.entity_name} is
{decl}
signal input_chain : std_logic_vector({(self.sketchg.wvalue+1)*self.sketchg.n_parallel} downto 0);
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

        if len(sys.argv) >= 9:
            outdir = sys.argv[8]
        else:
            outdir = "./output"

        if not os.path.exists(outdir):
            os.makedirs(outdir)

        cwd = os.getcwd()
        os.chdir(os.path.dirname(sys.argv[1]))
        selector_list = create_selector_function_statement_list(data)
        update_list = create_update_function_statement_list(data)
        os.chdir(cwd)

        sfg = SelectorFunctionGenerator(selector_list, data["value_size"], data["selector_seed_size"], data["offset_max_size"], True)
        sfg.generateFile(outdir)

        matrix = [[int(sys.argv[2])]*int(sys.argv[4])]*int(sys.argv[3])
        waddr = int(ceil(log2(sum(matrix[0]))))
        ufg = ForwardingUpdateFunctionGenerator(update_list, data["value_size"], data["update_seed_size"], data["state_size"], waddr, True)
        ufg.generateFile(outdir)

        ssg = ReplicatedMatrixSketchGenerator(int(sys.argv[7]), matrix, data["selector_seed_size"], data["update_seed_size"], data["value_size"], data["state_size"], sfg, ufg, 1, int(sys.argv[5]), int(sys.argv[6]))
        ssg.generateFile(outdir)

        tlg = TlGenerator(ssg)
        tlg.generateFile(outdir)
