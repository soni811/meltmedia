#!/bin/bash

if [ -e "bin/setenv.sh" ];
then
  . bin/setenv.sh
fi

#python main.py $@
python3 main.py -e local
# python3 main.py -e develop
#python3 main.py -e prod