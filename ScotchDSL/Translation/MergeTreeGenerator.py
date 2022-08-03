from Functions import UpdateFunctionGenerator, FunctionGenerator
from GeneratorUtils import generateComponentInstantiation, generateSignalMap, generateAssignments


class MergeTreeGenerator(FunctionGenerator):
    def __init__(self, n_inputs, ug, value_width, seed_width, neutral_element, prefix=""):
        # The seed width doesn't matter, because
        self.ug = ug
        self.value_width = value_width
        self.seed_width = seed_width
        self.n_inputs = n_inputs
        self.neutral_element = neutral_element
        self.prefix = prefix

        self.entity_name = F"{prefix}merge_tree{self.n_inputs}"
        self.signals = self.generateDeclarationSignals()
        self.levels = None

        self.architecture_frame = """
ARCHITECTURE a{} OF {} IS
{}
BEGIN
{}
END a{};
"""
        self.entity_frame = """
ENTITY {} IS
PORT (
    {}
);
END {};"""

    def generateArchitecture(self):
        aux_signals = ""
        update_declaration = self.ug.generateComponentDeclaration()

        # First, we generate the component instantiations for all binary mergers in the tree.
        # And add the requiret auxilliary signals
        update_components = ""
        n_elems = self.n_inputs
        l = 0
        while True:
            for i in range(0, n_elems, 2):
                update_signal_map = {
                    "clk": "clk",
                    "v": F"s{l}_{i//2}_op0_in",
                    "seed": "seed",
                    "state": F"s{l}_{i//2}_op1_in",
                    "outstate": F"s{l}_{i//2}_res_out"
                }
                update_components += generateComponentInstantiation(F"u_{l}_{i//2}", self.ug.entity_name, update_signal_map, None)

                # Create auxiliary signals for each component
                aux_signals += F"\nsignal s{l}_{i//2}_op0_in : std_logic_vector({self.value_width-1} downto 0);"
                aux_signals += F"\nsignal s{l}_{i//2}_op1_in : std_logic_vector({self.value_width-1} downto 0);"
                aux_signals += F"\nsignal s{l}_{i//2}_res_out : std_logic_vector({self.value_width-1} downto 0);"

            n_elems = (n_elems - 1) // 2 + 1
            l += 1
            if n_elems == 1:
                break



        bhv = ""
        n_elems = self.n_inputs
        l = 0
        clocked_assignments = ""
        unclocked_assignments = ""
        while True:
            for i in range(0, n_elems, 2):
                if l == 0 and i + 1 < n_elems:
                    assignments = {
                        F"s{l}_{i//2}_op0_in" : F"val{i}_in",
                        F"s{l}_{i//2}_op1_in": F"val{i+1}_in"
                    }
                    unclocked_assignments += generateAssignments(assignments)
                elif l == 0 and i + 1 == n_elems:
                    assignments = {
                        F"s{l}_{i//2}_op0_in" : F"val{i}_in",
                        F"s{l}_{i//2}_op1_in": self.neutral_element
                    }
                    clocked_assignments += generateAssignments(assignments)
                elif l > 0 and i + 1 < n_elems:
                    assignments = {
                        F"s{l}_{i//2}_op0_in" : F"s{l-1}_{i}_res_out",
                        F"s{l}_{i//2}_op1_in": F"s{l-1}_{i+1}_res_out"
                    }
                    clocked_assignments += generateAssignments(assignments)
                elif l > 0 and i + 1 == n_elems:
                    assignments = {
                        F"s{l}_{i//2}_op0_in" : F"s{l-1}_{i}_res_out",
                        F"s{l}_{i//2}_op1_in": self.neutral_element
                    }
                    clocked_assignments += generateAssignments(assignments)

            n_elems = (n_elems - 1) // 2 + 1
            l += 1
            if n_elems == 1:
                break

        self.levels = l
        # Assign the output of the last level
        assignments = {
            "val_out" : F"s{l-1}_{0}_res_out"
        }
        clocked_assignments += generateAssignments(assignments)

        bhv = F'''

{unclocked_assignments}

process(clk)
begin
    if rising_edge(clk) then
        if enable = '1' then
            {clocked_assignments}
        end if;
    end if;
end process;        
        '''

        return self.architecture_frame.format(self.entity_name, self.entity_name, update_declaration + aux_signals,
                                              update_components + bhv, self.entity_name)

    def generateDeclarationSignals(self):
        clk = [("clk","in","std_logic")]
        enable = [("enable","in","std_logic")]
        valin = [(F"val{x}_in","in",F"std_logic_vector({self.value_width-1} downto 0)") for x in range(self.n_inputs)]
        seed = [("seed","in",F"std_logic_vector({self.seed_width-1} downto 0)")]
        valout = [("val_out", "out", F"std_logic_vector({self.value_width - 1} downto 0)")]
        return clk+enable+valin+seed+valout

    def computeLatency(self):
        if self.levels is None:
            self.generateArchitecture()
        return self.levels

    def generateFile(self, folder):
        f = open("{}/{}.vhd".format(folder, self.entity_name), "w")
        f.write(self.generateFunctionFile())
        f.close()


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

            if not "initial_state" in data:
                data["initial_state"] = "(others => '0')"

            mtg = MergeTreeGenerator(int(data["inter_ss_parallelism"]), ufg, data["state_size"], data["update_seed_size"], data["compute_neutral"])
            mtg.generateFile(outdir)
