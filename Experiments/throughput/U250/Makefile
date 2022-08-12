#
# this file was created by a computer. trust it.
#

# compiler tools
#XILINX_VITIS ?= /data/Xilinx/Vitis/2022.1
XILINX_XRT ?= /opt/xilinx/xrt

HOST_CXX ?= g++
RM = rm -f
RMDIR = rm -rf

VITIS_PLATFORM = xilinx_u250_gen3x16_xdma_shell_4_1
VITIS_PLATFORM_PATH = $(VITIS_PLATFORM)

# host compiler global settings
CXXFLAGS += -std=c++1y -DVITIS_PLATFORM=$(VITIS_PLATFORM) -D__USE_XOPEN2K8 -I$(XILINX_XRT)/include/ -O2 -g -Wall -c -fmessage-length=0
LDFLAGS += -lxilinxopencl -lpthread -lrt -lstdc++ -L$(XILINX_XRT)/lib/ -Wl,-rpath-link,$(XILINX_XRT)/lib

#
# host files
#

HOST_OBJECTS += src/host_sketch.o

HOST_EXE = sketch_app

BUILD_SUBDIRS += src/

#
# primary build targets
#

.PHONY: all clean
all:  $(HOST_EXE) ../../../Data/wc98.bin ../../../Data/nyt.bin ../../../Data/caida.bin  ../../../Data/uniform.bin ../../../Data/zipf_1.05.bin ../../../Data/zipf_1.1.bin ../../../Data/zipf_1.5.bin

clean:
	-$(RM) $(HOST_EXE) $(HOST_OBJECTS)

.PHONY: incremental
incremental: all


nothing:

#
# host rules
#

src/host_sketch.o: ../../../Application-Sketching/Vitis-U250/host/host_sketch.cpp $(XILINX_XRT)/include/xclhal2.h
	-@mkdir -p $(@D)
	$(HOST_CXX) $(CXXFLAGS) -o "$@" "$<"

$(HOST_EXE): $(HOST_OBJECTS)
	$(HOST_CXX) -o "$@" $(+) $(LDFLAGS)

../../../Data/nyt.bin :
	cd ../../../Data/; bash generate_nyt.sh

../../../Data/caida.bin :
	cd ../../../Data/; bash generate_caida.sh

../../../Data/wc98.bin :
	cd ../../../Data/; bash generate_wc98.sh

../../../Data/uniform.bin :
	cd ../../../Data/; bash generate_uniform.sh

../../../Data/zipf_1.05.bin :
	cd ../../../Data/; bash generate_zipf.sh 1.05

../../../Data/zipf_1.1.bin :
	cd ../../../Data/; bash generate_zipf.sh 1.1

../../../Data/zipf_1.5.bin :
	cd ../../../Data/; bash generate_zipf.sh 1.5
