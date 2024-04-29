#!/bin/bash

export GRASS_MESSAGE_FORMAT=plain

r.mask -r

# GLEAM
GLEAMDIR=/mnt/scratch/scratch/data/GLEAM/data/v3.3b
g.region region=globe_0.250000Deg
g.region -p

