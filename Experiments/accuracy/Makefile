all : ./evaluator ../../Data/nyt_keys.bin ../../Data/caida_keys.bin ../../Data/wc98_keys.bin ../../Data/gt/nyt/gt_count.bin ../../Data/gt/caida/gt_count.bin ../../Data/gt/wc98/gt_count.bin   

GPU_ARCH ?= "sm_75"

./evaluator :
	${CUDA_PREFIX}/bin/nvcc -arch ${GPU_ARCH} ../../Evaluator/evaluator.cu -o evaluator


../../Data/nyt_keys.bin : 
	cd ../../Data/; bash generate_nyt.sh 

../../Data/caida_keys.bin : 
	cd ../../Data/; bash generate_caida.sh 

../../Data/wc98_keys.bin : 
	cd ../../Data/; bash generate_wc98.sh 

../../Data/gt/nyt/gt_count.bin : 
	cd ../../Data/gt/nyt; bash generate.sh 

../../Data/gt/caida/gt_count.bin : 
	cd ../../Data/gt/caida; bash generate.sh 

../../Data/gt/wc98/gt_count.bin : 
	cd ../../Data/gt/wc98; bash generate.sh 
