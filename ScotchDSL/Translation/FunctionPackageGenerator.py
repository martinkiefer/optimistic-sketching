class FunctionPackageGenerator:
    def __init__(self, prefix = ""):
        self.package_name = F"{prefix}functions_pkg"
        self.content = F"""
library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

package {self.package_name} is
        function parity(v: std_logic_vector) return std_logic;
        function minmax(l: std_logic_vector; r: std_logic_vector) return std_logic_vector;
        function maxmax(l: std_logic_vector; r: std_logic_vector) return std_logic_vector;
        function ceil_log_n(val : natural; n : natural) return natural;
end package;

package body {self.package_name} is

        function parity(v: std_logic_vector) return std_logic is

                constant n: natural := v'length;
                constant t: std_logic_vector(n - 1 downto 0) := v;

                begin
                if n = 0 then
                        return '0';
                elsif n = 1 then
                        return t(0);
                else
                        return parity(t(n - 1 downto n / 2)) xor parity(t(n / 2 - 1 downto 0));
                end if;
        end function parity;

        function minmax(l: std_logic_vector; r: std_logic_vector) return std_logic_vector is
                constant n: natural := l'length;
                variable t: std_logic_vector(n - 1 downto 0) := l;
        begin
                if unsigned(l(n/2-1 downto 0)) >  unsigned(r(n/2-1 downto 0)) then
                    t(n/2-1 downto 0) := r(n/2-1 downto 0);
                end if;
                
                if unsigned(l(n-1 downto n/2)) <  unsigned(r(n-1 downto n/2)) then
                    t(n-1 downto n/2) := r(n-1 downto n/2);
                end if;
                
                return t;
        end function minmax;

        function maxmax(l: std_logic_vector; r: std_logic_vector) return std_logic_vector is
                constant n: natural := l'length;
                variable t: std_logic_vector(n - 1 downto 0) := l;
        begin
                if unsigned(l(n/2-1 downto 0)) <  unsigned(r(n/2-1 downto 0)) then
                    t(n/2-1 downto 0) := r(n/2-1 downto 0);
                end if;
                
                if unsigned(l(n-1 downto n/2)) <  unsigned(r(n-1 downto n/2)) then
                    t(n-1 downto n/2) := r(n-1 downto n/2);
                end if;
                
                return t;
        end function maxmax;

        function ceil_log_n(val : natural; n : natural) return natural is
    	        variable factor : natural := n - 1;
                variable r : natural := 0;
                        begin  
                        while factor > 0 loop
                                factor := factor / val;
                                r := r + 1;
                        end loop;
                        return r;
        end function ceil_log_n;

end package body;
"""

    def generateFile(self, folder):
        f = open("{}/{}".format(folder, F"{self.package_name}.vhd"), "w")
        f.write(self.content)
        f.close()



