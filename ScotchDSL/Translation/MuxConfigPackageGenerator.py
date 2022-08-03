class MuxConfigPackageGenerator:
    def __init__(self, num, mux_factor, data_width, pkg_name="mux_config_pkg", prefix=""):
        self.pkg_name = F"{prefix}{pkg_name}"
        self.prefix = prefix
        self.content = F"""
library IEEE;
use IEEE.std_logic_1164.all;
use WORK.{self.prefix}functions_pkg.all;

package {self.pkg_name} is
	constant MUX_NUM : natural := {num};
    constant MUX_FACTOR : natural := {mux_factor};
    constant MUX_DATA_WIDTH : natural := {data_width};

    constant MUX_STAGES : natural := ceil_log_n(MUX_FACTOR, MUX_NUM);
    constant MUX_INDEX_WIDTH : natural := ceil_log_n(2, MUX_NUM);

    type mux_data_array_type is array (natural range <>) of std_logic_vector (MUX_DATA_WIDTH-1 downto 0);
    type mux_index_array_type is array(natural range <>) of std_logic_vector (MUX_INDEX_WIDTH-1 downto 0);
end package;
"""

    def generateFile(self, folder):
        f = open("{}/{}.vhd".format(folder, self.pkg_name), "w")
        f.write(self.content)
        f.close()
