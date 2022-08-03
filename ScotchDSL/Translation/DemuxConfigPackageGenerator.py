from math import log, ceil

class DemuxConfigPackageGenerator:
    def __init__(self, num, mux_factor, data_width, pkg_name="demux_config_pkg", prefix=""):
        self.mux_factor = mux_factor
        self.num = num
        self.pkg_name = F"{prefix}{pkg_name}"
        self.content = F"""
library IEEE;
USE IEEE.std_logic_1164.all;
USE WORK.{prefix}functions_pkg.all;

package {self.pkg_name} is
	constant DEMUX_NUM : natural := {num};
    constant DEMUX_FACTOR : natural := {mux_factor};
    constant DEMUX_DATA_WIDTH : natural := {data_width};

    constant DEMUX_STAGES : natural := ceil_log_n(DEMUX_FACTOR, DEMUX_NUM);
    constant DEMUX_INDEX_WIDTH : natural := ceil_log_n(2, DEMUX_NUM);
    
    type demux_data_array_type is array (natural range <>) of std_logic_vector (DEMUX_DATA_WIDTH-1 downto 0);  
    type demux_index_array_type is array (natural range <>) of std_logic_vector(DEMUX_INDEX_WIDTH-1 downto 0);
end package;
"""


    def computeLatency(self):
        return int(ceil(log(self.num, self.mux_factor)))


    def generateFile(self, folder):
        f = open("{}/{}".format(folder, F"{self.pkg_name}.vhd"), "w")
        f.write(self.content)
        f.close()