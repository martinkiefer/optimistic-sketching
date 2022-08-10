GPU_ARCH ?= "sm_75"

all : ./replicated ./row-by-row ../../../Data/wc98_keys.bin ../../../Data/nyt_keys.bin ../../../Data/caida_keys.bin  ../../../Data/uniform_keys.bin ../../../Data/zipf_1.05_keys.bin ../../../Data/zipf_1.1_keys.bin ../../../Data/zipf_1.5_keys.bin


./replicated :
	${CUDA_PREFIX}/bin/nvcc -arch ${GPU_ARCH} ../../../Application-Sketching/CUDA/Replicated/cm-app.cu -o ./replicated

./row-by-row :
	${CUDA_PREFIX}/bin/nvcc -arch ${GPU_ARCH} ../../../Application-Sketching/CUDA/Row-by-Row/cm-app.cu -o ./row-by-row

../../../Data/nyt_keys.bin : 
	cd ../../../Data/; bash generate_nyt.sh 

../../../Data/caida_keys.bin : 
	cd ../../../Data/; bash generate_caida.sh 

../../../Data/wc98_keys.bin : 
	cd ../../../Data/; bash generate_wc98.sh 

../../../Data/uniform_keys.bin : 
	cd ../../../Data/; bash generate_uniform.sh 

../../../Data/zipf_1.05_keys.bin : 
	cd ../../../Data/; bash generate_zipf.sh 1.05

../../../Data/zipf_1.1_keys.bin : 
	cd ../../../Data/; bash generate_zipf.sh 1.1

../../../Data/zipf_1.5_keys.bin : 
	cd ../../../Data/; bash generate_zipf.sh 1.5
