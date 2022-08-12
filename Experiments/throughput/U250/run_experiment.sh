
for df in zipf_1.05 zipf_1.1 zipf_1.5 nyt wc98 caida uniform; do
    for i in {1..10}; do
        ./sketch_app oversubscribed.xclbin ../../../Data/${df}.bin >> oversubscribed_${df}.csv 
        ./sketch_app regular.xclbin ../../../Data/${df}.bin >> regular_${df}.csv 
        ./sketch_app pessimistic.xclbin ../../../Data/${df}.bin >> pessimistic_${df}.csv 
    done
done
