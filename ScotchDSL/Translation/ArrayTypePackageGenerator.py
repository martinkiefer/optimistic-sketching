class ArrayTypePackageGenerator:
    def __init__(self, num, mux_factor, data_width, prefix):
        self.pkg_name = F"{prefix}array_type_pkg"
        self.content = F"""
library ieee;
use ieee.std_logic_1164.all;

package {self.pkg_name} is
	constant NUM : natural := {num};
    constant MUX_FACTOR : natural := {mux_factor};
    constant DATA_WIDTH : natural := {data_width};
    type data_array_type is array (natural range <>) of std_logic_vector (DATA_WIDTH-1 downto 0);
    type natural_array_type is array(natural range <>) of natural;
	function get_stages(b : natural; n : natural) return natural;
end package;

package body array_type_pkg is

	function get_stages(b : natural; n : natural) return natural is
	
    	variable factor : natural := n - 1;
      variable r : natural := 0;
       
		begin  

		while factor > 0 loop
			factor := factor / b;
			r := r + 1;
		end loop;
		
		return r;
    end function get_stages;
end package body;
"""

    def generateFile(self, folder):
        f = open("{}/{}".format(folder, F"{self.pkg_name}.vhd"), "w")
        f.write(self.content)
        f.close()