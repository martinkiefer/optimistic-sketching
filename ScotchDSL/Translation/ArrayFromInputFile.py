import sys 

class SeedGenerator:
    def __init__(self, f, package_name, constant_name, nseeds, width, prefix=""):
        self.package_name = F"{prefix}{package_name}"
        self.constant_name = constant_name
        self.nseeds = nseeds
        self.width = width
        self.f = open(f, "rb")

    def generateIncludes(self):
        return """
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
"""

    def generatePackage(self):
        frame = """
package {} is
    type {} is array({} downto 0) of std_logic_vector({} downto 0) ;
    constant {} : {} := (
       {}
    );
end package;
"""

        ba = self.f.read(self.nseeds*self.width//8)
        vectors = []
        for ns in range(0, self.nseeds):
            v = F"{ns} => "
            v += "\""
            v += bin(int.from_bytes(ba[ns*self.width//8:(ns+1)*self.width//8],byteorder="little",signed=False))[2:].zfill(self.width)
            v += "\""
            vectors.append(v)
        vectors_string = ",\n       ".join(vectors)
        return frame.format(self.package_name, self.constant_name+"_type",
         self.nseeds-1, self.width-1, self.constant_name, self.constant_name+"_type",
         vectors_string)

    def generateFile(self, folder):
        f = open("{}/{}.vhd".format(folder, self.package_name), "w")
        content = self.generateIncludes()
        content += self.generatePackage()
        f.write(content)
        f.close()

if __name__ == "__main__":
    sfg = SeedGenerator(sys.argv[1], "binary_pkg", "idata", int(sys.argv[2]), int(sys.argv[3]))
    sfg.generateFile("./")
