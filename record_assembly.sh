#!/bin/bash
#
source "/home/igor/.cache/pypoetry/virtualenvs/linux-speech-to-text-V1ZZoUsK-py3.12/bin/activate"
echo "Activated"
/home/igor/linux-speech-to-text/record_assembly.py > /tmp/record_log.txt 2>&1
