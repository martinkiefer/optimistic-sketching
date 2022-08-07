all : ./evaluator ../../Data/nyt_key.bin ../../Data/caida_key.bin ../../Data/wc98_key.bin ../../Data/gt/nyt/gt_count.bin ../../Data/gt/caida/gt_count.bin ../../Data/gt/wc98/gt_count.bin   

./evaluator :
	${CUDA_PREFIX}/bin/nvcc -arch sm_75 ../../Evaluator/evaluator.cu -o evaluator


../../Data/nyt_key.bin : 
	cd ../../Data/; bash generate_nyt.sh 

../../Data/caida_key.bin : 
	cd ../../Data/; bash generate_caida.sh 

../../Data/wc98_key.bin : 
	cd ../../Data/; bash generate_wc98.sh 

../../Data/gt/nyt/gt_count.bin : 
	cd ../../Data/gt/nyt; bash generate.sh 

../../Data/gt/caida/gt_count.bin : 
	cd ../../Data/gt/caida; bash generate.sh 

../../Data/gt/wc98/gt_count.bin : 
	cd ../../Data/gt/wc98; bash generate.sh 
