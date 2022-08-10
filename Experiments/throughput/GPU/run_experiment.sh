
for df in zipf_1.05 zipf_1.1 zipf_1.5 nyt wc98 caida uniform; do
    for i in {1..10}; do
        ./row-by-row 2 $(( 4096*32 )) ../../../Data/${df}_keys.bin ../../../Data/${df}_values.bin >> ${df}.csv
        ./row-by-row 2 $(( 4096*16 )) ../../../Data/${df}_keys.bin ../../../Data/${df}_values.bin >> ${df}.csv

        for p in {0..14}; do 
            ./replicated 2 $(( 4096*32 )) $((2 ** $p)) ../../../Data/${df}_keys.bin ../../../Data/${df}_values.bin >> ${df}.csv
            ./replicated 2 $(( 4096*16 )) $((2 ** $p)) ../../../Data/${df}_keys.bin ../../../Data/${df}_values.bin >> ${df}.csv
        done
    done
done
