rm -rf caida_keys.* caida_values.*
wget https://tubcloud.tu-berlin.de/s/CypXyJbkb2yK4Yp/download/caida_keys.bin.gz  -O ./caida_keys.bin.gz
gunzip caida_keys.bin.gz
head -c 8G caida_keys.bin > tmp.bin
mv tmp.bin caida_keys.bin

wget https://tubcloud.tu-berlin.de/s/Jor96j5zCb882HA/download/caida_values.bin.gz  -O ./caida_values.bin.gz
gunzip caida_values.bin.gz
head -c 8G caida_values.bin > tmp.bin
mv tmp.bin caida_values.bin


python rowify.py caida_keys.bin caida_values.bin caida.bin
