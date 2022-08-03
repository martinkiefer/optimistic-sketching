class EnableDemuxConfigPackageGenerator:
    def __init__(self, num, mux_factor, prefix=""):
        self.pkg_name = F"{prefix}enable_demux_config_pkg"
        self.content = F"""
library IEEE;
USE IEEE.std_logic_1164.all;
USE WORK.{prefix}functions_pkg.all;

package {self.pkg_name} is
	constant ENABLE_DEMUX_NUM : natural := {num};
    constant ENABLE_DEMUX_FACTOR : natural := {mux_factor};

    constant ENABLE_DEMUX_STAGES : natural := ceil_log_n(ENABLE_DEMUX_FACTOR, ENABLE_DEMUX_NUM);
    constant ENABLE_DEMUX_INDEX_WIDTH : natural := ceil_log_n(2, ENABLE_DEMUX_NUM);
    
    type enable_demux_index_array_type is array (natural range <>) of std_logic_vector(ENABLE_DEMUX_INDEX_WIDTH-1 downto 0);
end package;
"""

    def generateFile(self, folder):
        f = open("{}/{}".format(folder, F"{self.pkg_name}.vhd"), "w")
        f.write(self.content)
        f.close()