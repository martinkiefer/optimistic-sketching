curdir=$(pwd)

i=$1
s=$2
echo "-- $i $s--"
rm -rf "$i.$s"
#Create a working copy of the IO template
cp -r ../../dummy "$i.$s"
cd "$i.$s"
#Call scripts, create source folder
python ../../../../../ScotchDSL/Translation/generate_tl_pessimistic.py ../../../../../Sketches/Select-Update/count-key32-novalue-state64/descriptor.json $i ./sketch
#Run script
bash compile.sh $VIVADO_DIR $s
#Boom, done.
cd $curdir
