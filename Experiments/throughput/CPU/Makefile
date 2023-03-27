all : ./seed.bin ./one-per-thread ./one-per-core ../../../Data/wc98_keys.bin ../../../Data/nyt_keys.bin ../../../Data/caida_keys.bin  ../../../Data/uniform_keys.bin ../../../Data/zipf_1.05_keys.bin ../../../Data/zipf_1.1_keys.bin ../../../Data/zipf_1.5_keys.bin


./one-per-thread :
	g++ -O2 -std=c++17 ../../../Application-Sketching/SIMD+OpenMP/cm-app.cpp -march=native -mtune=native -shared-libgcc -fopenmp -DREPLICAS=256 -o one-per-thread

./one-per-core :
	g++ -O2 -std=c++17 ../../../Application-Sketching/SIMD+OpenMP/cm-app.cpp -march=native -mtune=native -shared-libgcc -fopenmp -DREPLICAS=128 -o one-per-core

./seed.bin :
	head -c 1M </dev/urandom >  seed.bin

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
