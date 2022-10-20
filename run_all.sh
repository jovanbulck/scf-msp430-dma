#! /bin/bash

JSON=$(ls testcase/*.json)

for j in $JSON; do
    echo ... Running $j
    ./main.py $j
    RV=$?

    if grep -q "nemdef" <<< "$j"; then
        if [ $RV -ge 4 ]; then
            echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
            echo "!!                Nemesis leak in hardened program                        !"
            echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
        fi
    fi
done
