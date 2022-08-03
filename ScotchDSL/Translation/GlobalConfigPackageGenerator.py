import os

class GlobalConfigPackageGenerator:
    def __init__(self, model, ssize, vsize, memdepth, ivals, sseedsizem, useedsize, 
    dfactor, cfactor, drepfactor, srepfactor, rows, cols, prefix=""):
        self.package_name = F"{prefix}global_config_pkg"
        version_file = open(os.path.dirname(os.path.realpath(__file__))+"/../VERSION", "r")
        version = version_file.read().rstrip()
        version_file.close()

        self.content = F'''
library ieee;
use ieee.std_logic_1164.all;

package {self.package_name} is
    -- Global parameters
    constant MODEL : string := "{model}";
    constant STATE_WIDTH : natural := {ssize};
    constant VALUE_WIDTH : natural := {vsize};
    constant MEMORY_SEGMENT_DEPTH : natural := {memdepth};
    constant INPUT_VALUES : natural := {ivals};

    constant SELECT_SEED_WIDTH : natural := {sseedsizem};
    constant UPDATE_SEED_WIDTH : natural := {useedsize};

    constant DISPATCH_FACTOR : natural := {dfactor};
    constant COLLECT_FACTOR : natural := {cfactor};

    constant DATA_REPLICATION_FACTOR : natural := {drepfactor};
    constant STREAMING_REPLICATION_FACTOR : natural := {srepfactor};

    -- Per-Replica Parameters
    constant ROWS : natural := {rows};
    constant COLS : natural := {cols};
    
    -- Total number of sketches (over all data-parallel replicas, does not include streaming replicas)
    constant N_SKETCHES : natural := {rows*cols*drepfactor};
    constant GEN_VERSION : string := "{version}";

end package;
'''

    def generateFile(self, folder):
        f = open("{}/{}".format(folder, F"{self.package_name}.vhd"), "w")
        f.write(self.content)
        f.close()
