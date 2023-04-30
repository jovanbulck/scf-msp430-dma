#! /bin/bash

JSON=$(ls testcase/*.nemdef.json)

for j in $JSON; do
    ./main.py $j $@
    RV=$?

    # if grep -q "nemdef" <<< "$j"; then
    #     if [ $RV -ge 2 ]; then
    #         echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    #         echo "!!                SCA leak in hardened program                            !"
    #         echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    #     fi
    # fi
done
