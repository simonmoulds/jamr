#!/bin/bash

# This script creates various lookup tables for processing ESA LC maps

# ========================================================= #
# 1. Implement Table 2 in Poulter et al. (2015)
# ========================================================= #

# Poulter et al. (2015) Plant functional type classification for earth
# system models. Geosci. Model Dev. 8, 2315--2328

echo "30 = 50
40       = 50
50       = 900
100      = 100
110      = 50
150      = 10 
160      = 300
170      = 600
*        = 0
" > $AUXDIR/tree_broadleaf_evergreen_reclass.txt

echo "30 = 50
40       = 50
60       = 700
61       = 700
62       = 300
90       = 300
100      = 200
110      = 100
150      = 30
151      = 20
160      = 300
180      = 50
190      = 25
*        = 0
" > $AUXDIR/tree_broadleaf_deciduous_reclass.txt

echo "70 = 700
71       = 700
72       = 300
90       = 200
100      = 50
110      = 50
150      = 10
151      = 60
180      = 100
190      = 25
*        = 0
" > $AUXDIR/tree_needleleaf_evergreen_reclass.txt

echo "80 = 700
81       = 700
82       = 300
90       = 100
100      = 50
151      = 20
*        = 0
" > $AUXDIR/tree_needleleaf_deciduous_reclass.txt

echo "30 = 50
40       = 75
50       = 50
70       = 50
71       = 50
80       = 50
81       = 50
90       = 50
100      = 50
110      = 50
120      = 200
121      = 300
150      = 10
152      = 20
170      = 200
*        = 0
" > $AUXDIR/shrub_broadleaf_evergreen_reclass.txt

echo "12 = 500
30       = 50
40       = 100
50       = 50
60       = 150
61       = 150
62       = 250
70       = 50
71       = 50
72       = 50
80       = 50
81       = 50
82       = 50
90       = 50
100      = 100
110      = 100
120      = 200
122      = 600
150      = 30
152      = 60
180      = 100
*        = 0
" > $AUXDIR/shrub_broadleaf_deciduous_reclass.txt

echo "30 = 50
40       = 75
70       = 50
71       = 50
72       = 50
80       = 50
81       = 50
82       = 50
90       = 50
100      = 50
110      = 50
120      = 200
121      = 300
150      = 10
152      = 20
180      = 50
*        = 0
" > $AUXDIR/shrub_needleleaf_evergreen_reclass.txt

echo "*  = 0
" > $AUXDIR/shrub_needleleaf_deciduous_reclass.txt

echo "30 = 150
40       = 250
60       = 150
61       = 150
62       = 350
70       = 150
71       = 150
72       = 300
80       = 150
81       = 150
82       = 300
90       = 150
100      = 400
110      = 600
120      = 200
121      = 200
122      = 200
130      = 600
140      = 600
150      = 50
151      = 50
152      = 50
153      = 150
160      = 200
180      = 400
190      = 150
*        = 0
" > $AUXDIR/natural_grass_reclass.txt

echo "10 = 1000
11       = 1000
12       = 500
20       = 1000
30       = 600
40       = 400
*        = 0
" > $AUXDIR/managed_grass_reclass.txt

echo "190 = 750
*         = 0
" > $AUXDIR/urban_reclass.txt

echo "62 = 100
72       = 300
82       = 300
90       = 100
120      = 200
121      = 200
122      = 200
130      = 400
140      = 400
150      = 850
151      = 850
152      = 850
153      = 850
200      = 1000
201      = 1000
202      = 1000
*        = 0
" > $AUXDIR/bare_soil_reclass.txt

echo "160 = 200
170       = 200
180       = 300
190       = 50
210       = 1000
*         = 0
" > $AUXDIR/water_reclass.txt

echo "220 = 1000
*         = 0
" > $AUXDIR/snow_ice_reclass.txt

echo "0 = 1000
*       = 0
" > $AUXDIR/nodata_reclass.txt

# THIS IS NO LONGER THE RECOMMENDED METHOD - SEE ANTS

# # ========================================================= #
# # 1. Implement Table B1/2 in Wiltshire et al. (2020)
# # ========================================================= #

# cp $AUXDIR/natural_grass_reclass.txt $AUXDIR/c3_natural_grass_reclass.txt
# cp $AUXDIR/natural_grass_reclass.txt $AUXDIR/c4_natural_grass_reclass.txt
# cp $AUXDIR/managed_grass_reclass.txt $AUXDIR/c3_managed_grass_reclass.txt
# cp $AUXDIR/managed_grass_reclass.txt $AUXDIR/c4_managed_grass_reclass.txt

# # Wiltshire et al. (2020) JULES-GL7: the Global Land configuration of
# # the Joint UK Land Environment Simulator version 7.0 and 7.2. Geosci.
# # Model Dev. 13, 483--505.

# # Note that Table B2 corresponds with IGBP classes; here, we use the
# # equivalent CCI classes according to the following crosswalk table:

# # TODO

# # Broadleaf tree (evergreen and deciduous)
# echo "10 = 5
# 20       = 5
# 30       = 5
# 40       = 5
# 50       = 9
# 60       = 5
# 61       = 5
# 62       = 5
# 90       = 5
# 100      = 5
# 110      = 5
# 140      = 9
# 150      = 9
# 160      = 9
# 170      = 9
# 180      = 9
# *        = 0
# " > $AUXDIR/tree_broadleaf_evergreen_balanced_lai_reclass.txt

# cp $AUXDIR/tree_broadleaf_evergreen_balanced_lai_reclass.txt $AUXDIR/tree_broadleaf_deciduous_balanced_lai_reclass.txt

# # Needleleaf tree (broadleaf and evergreen)
# echo "10 = 6
# 30       = 6
# 40       = 6
# 70       = 6
# 71       = 6
# 72       = 6
# 80       = 4
# 81       = 4
# 82       = 4
# 90       = 6
# *        = 0
# " > $AUXDIR/tree_needleleaf_evergreen_balanced_lai_reclass.txt   

# cp $AUXDIR/tree_needleleaf_evergreen_balanced_lai_reclass.txt $AUXDIR/tree_needleleaf_deciduous_balanced_lai_reclass.txt

# # C3 grass (natural and managed)
# echo "10 = 4
# 11       = 3
# 12       = 2
# 20       = 5
# 30       = 4
# 40       = 4
# 50 thru 122 = 2
# 130      = 3
# 140      = 4
# 160      = 3
# 170      = 3
# 180      = 3
# *        = 0
# " > $AUXDIR/c3_natural_grass_balanced_lai_reclass.txt

# cp $AUXDIR/c3_natural_grass_balanced_lai_reclass.txt $AUXDIR/c3_managed_grass_balanced_lai_reclass.txt

# # C4 grass (natural and managed)
# echo "10 = 4
# 11       = 4
# 20 thru 62 = 4
# 100      = 4
# 110      = 4
# 130      = 4
# 150      = 4
# *        = 0
# " > $AUXDIR/c4_natural_grass_balanced_lai_reclass.txt

# cp $AUXDIR/c4_natural_grass_balanced_lai_reclass.txt $AUXDIR/c4_managed_grass_balanced_lai_reclass.txt

# # Shrub (broadleaf and needleleaf, evergreen and deciduous)
# echo "10 thru 40 = 3
# 60       = 3
# 61       = 3
# 62       = 3
# 100      = 2
# 110      = 2
# 120 thru 130 = 3
# 140      = 2
# *        = 0
# " > $AUXDIR/shrub_broadleaf_evergreen_balanced_lai_reclass.txt

# cp $AUXDIR/shrub_broadleaf_evergreen_balanced_lai_reclass.txt $AUXDIR/shrub_broadleaf_deciduous_balanced_lai_reclass.txt
# cp $AUXDIR/shrub_broadleaf_evergreen_balanced_lai_reclass.txt $AUXDIR/shrub_needleleaf_evergreen_balanced_lai_reclass.txt
# cp $AUXDIR/shrub_broadleaf_evergreen_balanced_lai_reclass.txt $AUXDIR/shrub_needleleaf_deciduous_balanced_lai_reclass.txt
