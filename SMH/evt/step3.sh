for i in /eos/uscms//store/user/lpchbb/cmantill//pfbits-v15.03-all/*root ; do

    python infer_on_root.py  --ifile $i --json root.json --h5 ../../../SubtLeNet/train/smh/models/evt/v0/weights.h5

done

