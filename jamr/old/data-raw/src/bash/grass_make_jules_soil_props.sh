#!/bin/bash

export GRASS_MESSAGE_FORMAT=plain

r.mask -r

# ========================================================= #
# Read in soil texture maps
# ========================================================= #

g.region region=globe_0.008333Deg
g.region -p

SOILGRID_VARS=(CLYPPT SNDPPT SLTPPT BLDFIE CECSOL ORCDRC PHIHOX)
HWSD_VARS=(clay sand silt bulk_density cec_soil oc ph_h2o)

# Read HWSD maps, which we use to fill gaps in the
# SoilGrids data
for i in `seq 0 6`
do
    VARIABLE=${HWSD_VARS[i]}
    SOILGRID_VARIABLE=${SOILGRID_VARS[i]}
    for LAYER in t s
    do	
	r.in.gdal \
	    -a \
	    input=${HWSDDIR}/hwsd_sg_"${LAYER}"_"${VARIABLE}".tif \
	    output=hwsd_"${LAYER}"_"${VARIABLE}" \
	    $OVERWRITE
    done
    r.mapcalc \
    	"hwsd_${SOILGRID_VARIABLE}_sl1 = hwsd_t_${VARIABLE}" \
    	$OVERWRITE
    r.mapcalc \
    	"hwsd_${SOILGRID_VARIABLE}_sl2 = hwsd_t_${VARIABLE}" \
    	$OVERWRITE
    r.mapcalc \
    	"hwsd_${SOILGRID_VARIABLE}_sl3 = hwsd_t_${VARIABLE}" \
    	$OVERWRITE
    r.mapcalc \
    	"hwsd_${SOILGRID_VARIABLE}_sl4 = hwsd_s_${VARIABLE}" \
    	$OVERWRITE
    r.mapcalc \
    	"hwsd_${SOILGRID_VARIABLE}_sl5 = hwsd_s_${VARIABLE}" \
    	$OVERWRITE
    r.mapcalc \
    	"hwsd_${SOILGRID_VARIABLE}_sl6 = hwsd_s_${VARIABLE}" \
    	$OVERWRITE
    r.mapcalc \
    	"hwsd_${SOILGRID_VARIABLE}_sl7 = hwsd_s_${VARIABLE}" \
    	$OVERWRITE
done

# Read SoilGrids1km maps
RGN_STR=globe_0.008333Deg
g.region region=${RGN_STR}
for HORIZON in sl1 sl2 sl3 sl4 sl5 sl6 sl7
do
    for VARIABLE in CLYPPT SNDPPT SLTPPT BLDFIE CECSOL ORCDRC PHIHOX TEXMHT
    do
	# import data
	r.in.gdal \
	    -a \
	    input=${SOILGRIDDIR}/${VARIABLE}_M_${HORIZON}_1km_ll.tif \
	    output=${VARIABLE}_${HORIZON}_init \
	    $OVERWRITE	
	r.mask raster=esacci_land_frac_${RGN_STR}
	if [[ ${VARIABLE} == TEXMHT ]]
	then
	    r.mapcalc \
		"${VARIABLE}_${HORIZON} = ${VARIABLE}_${HORIZON}_init" \
		${OVERWRITE}
	else
	    r.mapcalc \
		"${VARIABLE}_${HORIZON} = if(isnull(${VARIABLE}_${HORIZON}_init), hwsd_${VARIABLE}_${HORIZON}, ${VARIABLE}_${HORIZON}_init)" \
		${OVERWRITE}
	fi	
	r.mask -r 
	g.remove -f type=raster name=${VARIABLE}_${HORIZON}_init
    done
done

# ========================================================= #
# Apply pedotransfer functions
# ========================================================= #

for HORIZON in sl1 sl2 sl3 sl4 sl5 sl6 sl7
do
    # ###########################
    # (i) Cosby pedotransfer funs
    # ###########################
    RGN_STR=globe_0.008333Deg
    g.region region=${RGN_STR}

    # These PTFs use the Brooks and Corey (1964) model
    
    # Pore size distribution index, dimensionless
    r.mapcalc \
    	"lambda_cosby_${HORIZON}_${RGN_STR} = 1 / (3.10 + 0.157 * CLYPPT_${HORIZON} - 0.003 * SNDPPT_${HORIZON})" \
    	$OVERWRITE

    # Inverted pore size distribution index, dimensionless [b]
    #
    # NB this is the Brooks & Corey (aka Clapp & Hornberger) "b" coefficient
    r.mapcalc \
    	"b_cosby_${HORIZON}_${RGN_STR} = 1 / lambda_cosby_${HORIZON}_${RGN_STR}" \
    	$OVERWRITE

    # Air-entry pressure, Pascal
    r.mapcalc \
    	"psi_pa_cosby_${HORIZON}_${RGN_STR} = -0.01 * (10 ^ (2.17 - (0.0063 * CLYPPT_${HORIZON}) - (0.0158 * SNDPPT_${HORIZON}))) * (1000 * 9.80665)" \
    	$OVERWRITE

    # Air-entry pressure, metres head [sathh]
    r.mapcalc \
    	"psi_m_cosby_${HORIZON}_${RGN_STR} = -psi_pa_cosby_${HORIZON}_${RGN_STR} / (1000 * 9.80665)" \
    	$OVERWRITE

    # Saturated hydraulic conductivity, mm s-1 [satcon]
    r.mapcalc \
    	"k_sat_cosby_${HORIZON}_${RGN_STR} = (25.4 / (60 * 60)) * (10 ^ (-0.60 - (0.0064 * CLYPPT_${HORIZON}) + (0.0126 * SNDPPT_${HORIZON})))" \
    	$OVERWRITE

    # Saturated water content, cm3 cm-3 [sm_sat]
    r.mapcalc \
    	"theta_sat_cosby_${HORIZON}_${RGN_STR} = 0.01 * (50.5 - 0.037 * CLYPPT_${HORIZON} - 0.142 * SNDPPT_${HORIZON})" \
    	$OVERWRITE

    # To calculate soil water content at critical point and 
    # wilting point we use Eqn 1 from Clapp and Hornberger 
    # (1978):
    #     psi = psi_s * W ^ (-b)
    # N.B:
    # - after Dharssi et al (2009),
    #   * soil suction at critical point is 3.364m (=33kPa)
    #   * soil suction at wilting point is 152.9m (=1500kPa)
    # - assume theta_res = 0 (consistent with JULES)
    # - see Zulkafli (2013) [PhD thesis], p75 for more info
    # - also see https://www.tobymarthews.com/soilwat.html

    # Critical water content, cm3 cm-3 [sm_crit]
    r.mapcalc \
    	"theta_crit_cosby_${HORIZON}_${RGN_STR} = theta_sat_cosby_${HORIZON}_${RGN_STR} * (psi_m_cosby_${HORIZON}_${RGN_STR} / 3.364) ^ lambda_cosby_${HORIZON}_${RGN_STR}" \
    	$OVERWRITE

    # Assume soil suction at wilting point = 152.9m, after
    # Dharssi et al (2009) (=-1500000Pa)
    # Water content at wilting point, cm3 cm-3 [sm_wilt]
    r.mapcalc \
    	"theta_wilt_cosby_${HORIZON}_${RGN_STR} = theta_sat_cosby_${HORIZON}_${RGN_STR} * (psi_m_cosby_${HORIZON}_${RGN_STR} / 152.9) ^ lambda_cosby_${HORIZON}_${RGN_STR}" \
    	$OVERWRITE

    # Assume that residual water content is zero
    r.mapcalc \
    	"theta_res_cosby_${HORIZON}_${RGN_STR} = 0" \
    	$OVERWRITE

    # #######################################
    # (ii) Tomasella and Hodnett (2002, 2004)
    # #######################################

    g.region region=globe_0.008333Deg
    
    # These PTFs use the van Genuchten (1980) model
    
    # nM, dimensionless
    r.mapcalc \
    	"nM_tomas_${HORIZON}_${RGN_STR} = exp((62.986 - (0.833 * CLYPPT_${HORIZON}) - (0.529 * (ORCDRC_${HORIZON} / 10)) + (0.593 * PHIHOX_${HORIZON} / 10) + (0.007 * CLYPPT_${HORIZON} * CLYPPT_${HORIZON}) - (0.014 * SNDPPT_${HORIZON} * SLTPPT_${HORIZON})) / 100)" \
    	$OVERWRITE

    # alpha, Pascal
    r.mapcalc \
    	"alpha_pa_tomas_${HORIZON}_${RGN_STR} = 0.001 * exp((-2.294 - (3.526 * SLTPPT_${HORIZON}) + (2.440 * (ORCDRC_${HORIZON} / 10)) - (0.076 * CECSOL_${HORIZON}) - (11.331 * PHIHOX_${HORIZON} / 10) + (0.019 * SLTPPT_${HORIZON} * SLTPPT_${HORIZON})) / 100)" \
    	$OVERWRITE

    # alpha, metres head
    r.mapcalc \
    	"alpha_m_tomas_${HORIZON}_${RGN_STR} = (1000 * 9.80665) * alpha_pa_tomas_${HORIZON}_${RGN_STR}" \
    	$OVERWRITE

    # Saturated water content, cm3 cm-3
    r.mapcalc \
    	"theta_sat_tomas_${HORIZON}_${RGN_STR} = 0.01 * (81.799 + (0.099 * CLYPPT_${HORIZON}) - (31.42 * BLDFIE_${HORIZON} * 0.001) + (0.018 * CECSOL_${HORIZON}) + (0.451 * PHIHOX_${HORIZON} / 10) - (0.0005 * SNDPPT_${HORIZON} * CLYPPT_${HORIZON}))" \
    	$OVERWRITE

    # Residual water content, cm3 cm-3
    r.mapcalc \
    	"theta_res_tomas_${HORIZON}_${RGN_STR} = 0.01 * (22.733 - (0.164 * SNDPPT_${HORIZON}) + (0.235 * CECSOL_${HORIZON}) - (0.831 * PHIHOX_${HORIZON} / 10) + (0.0018 * CLYPPT_${HORIZON} * CLYPPT_${HORIZON}) + (0.0026 * SNDPPT_${HORIZON} * CLYPPT_${HORIZON}))" \
    	$OVERWRITE

    # From JULES docs (http://jules-lsm.github.io/vn5.4/namelists/ancillaries.nml.html#list-of-soil-parameters) 
    # sathh = 1 / alpha, where alpha has units m-1
    # Air-entry pressure, metres head [sathh]
    r.mapcalc \
    	"psi_m_tomas_${HORIZON}_${RGN_STR} = 1 / alpha_m_tomas_${HORIZON}_${RGN_STR}" \
    	$OVERWRITE

    # Inverted pore size distribution index, dimensionless [b]
    r.mapcalc \
    	"b_tomas_${HORIZON}_${RGN_STR} = 1 / (nM_tomas_${HORIZON}_${RGN_STR} - 1)" \
    	$OVERWRITE

    # We can use the V-G model to calculate water content at
    # field capacity and critical point

    # Critical point (assume suction=3.364m)
    r.mapcalc \
    	"A_crit_tomas_${HORIZON}_${RGN_STR} = (alpha_m_tomas_${HORIZON}_${RGN_STR} * 3.364) ^ nM_tomas_${HORIZON}_${RGN_STR}" \
    	$OVERWRITE

    r.mapcalc \
    	"Se_crit_tomas_${HORIZON}_${RGN_STR} = (1 + A_crit_tomas_${HORIZON}_${RGN_STR}) ^ ((1 / nM_tomas_${HORIZON}_${RGN_STR}) - 1)" \
    	$OVERWRITE

    # [sm_crit]
    r.mapcalc \
    	"theta_crit_tomas_${HORIZON}_${RGN_STR} = (Se_crit_tomas_${HORIZON}_${RGN_STR} * (theta_sat_tomas_${HORIZON}_${RGN_STR} - theta_res_tomas_${HORIZON}_${RGN_STR})) + theta_res_tomas_${HORIZON}_${RGN_STR}" \
    	$OVERWRITE

    # Wilting point (assume suction=152.9m)
    r.mapcalc \
    	"A_wilt_tomas_${HORIZON}_${RGN_STR} = (alpha_m_tomas_${HORIZON}_${RGN_STR} * 152.9) ^ nM_tomas_${HORIZON}_${RGN_STR}" \
    	$OVERWRITE

    r.mapcalc \
    	"Se_wilt_tomas_${HORIZON}_${RGN_STR} = (1 + A_wilt_tomas_${HORIZON}_${RGN_STR}) ^ ((1 / nM_tomas_${HORIZON}_${RGN_STR}) - 1)" \
    	$OVERWRITE

    # [sm_wilt]
    r.mapcalc \
    	"theta_wilt_tomas_${HORIZON}_${RGN_STR} = (Se_wilt_tomas_${HORIZON}_${RGN_STR} * (theta_sat_tomas_${HORIZON}_${RGN_STR} - theta_res_tomas_${HORIZON}_${RGN_STR})) + theta_res_tomas_${HORIZON}_${RGN_STR}" \
    	$OVERWRITE

    # No PTF for saturated conductivity, so use Cosby instead [satcon]
    r.mapcalc \
    	"k_sat_tomas_${HORIZON}_${RGN_STR} = k_sat_cosby_${HORIZON}_${RGN_STR}" \
    	$OVERWRITE
    
    # #######################################
    # Zhang & Schaap (2017)
    # #######################################

    RGN_STR=globe_0.008333Deg
    g.region region=${RGN_STR}

    # Set mask
    r.mapcalc "MASK = TEXMHT_${HORIZON}" $OVERWRITE

    # Create maps
    # r.mapcalc "Cl = if(TEXMHT_${HORIZON}==1,1,0)" $OVERWRITE
    # r.mapcalc "SiCl = if(TEXMHT_${HORIZON}==2,1,0)" $OVERWRITE
    # r.mapcalc "SaCl = if(TEXMHT_${HORIZON}==3,1,0)" $OVERWRITE
    # r.mapcalc "ClLo = if(TEXMHT_${HORIZON}==4,1,0)" $OVERWRITE
    # r.mapcalc "SiClLo = if(TEXMHT_${HORIZON}==5,1,0)" $OVERWRITE
    # r.mapcalc "SaClLo = if(TEXMHT_${HORIZON}==6,1,0)" $OVERWRITE
    # r.mapcalc "Lo = if(TEXMHT_${HORIZON}==7,1,0)" $OVERWRITE
    # r.mapcalc "SiLo = if(TEXMHT_${HORIZON}==8,1,0)" $OVERWRITE
    # r.mapcalc "SaLo = if(TEXMHT_${HORIZON}==9,1,0)" $OVERWRITE
    # r.mapcalc "Si = if(TEXMHT_${HORIZON}==10,1,0)" $OVERWRITE
    # r.mapcalc "LoSa = if(TEXMHT_${HORIZON}==11,1,0)" $OVERWRITE
    # r.mapcalc "Sa = if(TEXMHT_${HORIZON}==12,1,0)" $OVERWRITE    
    echo "1         = 1
    2 thru 12       = 0" > Cl_rules.txt
    echo "1         = 0
    2               = 1
    3 thru 12       = 0" > SiCl_rules.txt
    echo "1 2       = 0
    3               = 1
    4 thru 12       = 0" > SaCl_rules.txt
    echo "1 thru 3  = 0
    4               = 1
    5 thru 12       = 0" > ClLo_rules.txt
    echo "1 thru 4  = 0
    5               = 1
    6 thru 12       = 0" > SiClLo_rules.txt
    echo "1 thru 5  = 0
    6               = 1
    7 thru 12       = 0" > SaClLo_rules.txt
    echo "1 thru 6  = 0
    7               = 1
    8 thru 12       = 0" > Lo_rules.txt
    echo "1 thru 7  = 0
    8               = 1
    9 thru 12       = 0" > SiLo_rules.txt
    echo "1 thru 8  = 0
    9               = 1
    10 thru 12      = 0" > SaLo_rules.txt
    echo "1 thru 9  = 0
    10              = 1
    11 12           = 0" > Si_rules.txt
    echo "1 thru 10 = 0
    11              = 1
    12              = 0" > LoSa_rules.txt
    echo "1 thru 11 = 0
    12              = 1" > Sa_rules.txt
    # reclass maps to binary form
    for CLS in Cl SiCl SaCl ClLo SiClLo SaClLo Lo SiLo SaLo Si LoSa Sa
    do
    	echo "running reclass for ${CLS}..."
    	r.reclass \
    	    input=TEXMHT_${HORIZON} \
    	    output=${CLS} \
    	    rules=${CLS}_rules.txt \
    	    $OVERWRITE
    	rm -f ${CLS}_rules.txt
    done

    # 1-Cl     | 0.1309948472 | 0.4574695264 | 0.0085736519 | 1.2547490134 | 14.7500629329
    # 2-SiCl   | 0.1236437112 | 0.4729208221 | 0.0101142735 | 1.273204146  | 9.6136374341    
    # 3-SaCl   | 0.147392179  | 0.3818242427 | 0.0250359697 | 1.2366347276 | 11.3533844849    
    # 4-ClLo   | 0.1072850999 | 0.4287550719 | 0.0099478343 | 1.3908612189 | 7.0635116122    
    # 5 SiClLo | 0.1196643822 | 0.4702973434 | 0.0055563345 | 1.4341667317 | 11.108435216    
    # 6 SaClLo | 0.0933631331 | 0.3800973379 | 0.0124256821 | 1.3051970186 | 13.2312093416    
    # 7 Lo     | 0.0902482845 | 0.4017669217 | 0.0063582607 | 1.4214753311 | 13.3386286706    
    # 8 SiLo   | 0.083186447  | 0.4269400175 | 0.0034302367 | 1.5517801798 | 18.4713576853    
    # 9 SaLo   | 0.0606397155 | 0.3808945256 | 0.0164037225 | 1.4569557234 | 37.4503675019    
    # 10 Si    | 0.0650483449 | 0.4724838864 | 0.0060396053 | 1.5771727061 | 43.7471157565
    # 11 LoSa  | 0.0581702395 | 0.3830712622 | 0.024619742  | 1.6968969844 | 108.1993376227
    # 12 Sa    | 0.0545506462 | 0.3633494968 | 0.0328446188 | 2.8953059015 | 642.9544642258
    
    # *BUT* - see https://jules.jchmr.org/sites/default/files/McGuireEtAl_soils_JULESAnnualMeeting_20200907v2b.pdf
    # "The K0 & n-exponent values for Sa=Sand are too extreme for JULES to
    # handle, causing gridded JULES to hang without crashing, so we replaced
    # the Sa values with the LoSa values."
    
    # [theta_res]
    r.mapcalc \
	"theta_res_rosetta3_${HORIZON}_${RGN_STR} = Cl * 0.1309948472 + SiCl * 0.1236437112 + SaCl * 0.147392179 + ClLo * 0.1072850999 + SiClLo * 0.1196643822 + SaClLo * 0.0933631331 + Lo * 0.0902482845 + SiLo * 0.083186447 + SaLo * 0.0606397155 + Si * 0.0650483449 + LoSa * 0.0581702395 + Sa * 0.0581702395" \
	$OVERWRITE

    # [theta_sat]
    r.mapcalc \
	"theta_sat_rosetta3_${HORIZON}_${RGN_STR} = Cl * 0.4574695264 + SiCl * 0.4729208221 + SaCl * 0.3818242427 + ClLo * 0.4287550719 + SiClLo * 0.4702973434 + SaClLo * 0.3800973379 + Lo * 0.4017669217 + SiLo * 0.4269400175 + SaLo * 0.3808945256 + Si * 0.4724838864 + LoSa * 0.3830712622 + Sa * 0.3830712622" \
	$OVERWRITE
    
    # alpha (*100 because values given in 1/cm)
    r.mapcalc \
	"alpha_m_rosetta3_${HORIZON}_${RGN_STR} = 100 * (Cl * 0.0085736519 + SiCl * 0.0101142735 + SaCl * 0.0250359697 + ClLo * 0.0099478343 + SiClLo * 0.0055563345 + SaClLo * 0.0124256821 + Lo * 0.0063582607 + SiLo * 0.0034302367 + SaLo * 0.0164037225 + Si * 0.0060396053 + LoSa * 0.024619742 + Sa * 0.024619742)" \
	$OVERWRITE

    # n - same order of magnitude as tomas
    r.mapcalc \
	"nM_rosetta3_${HORIZON}_${RGN_STR} = Cl * 1.2547490134 + SiCl * 1.273204146 + SaCl * 1.2366347276 + ClLo * 1.3908612189 + SiClLo * 1.4341667317 + SaClLo * 1.3051970186 + Lo * 1.4214753311 + SiLo * 1.5517801798 + SaLo * 1.4569557234 + Si * 1.5771727061 + LoSa * 1.6968969844 + Sa * 1.6968969844" \
	$OVERWRITE

    # [satcon] cm/day -> kg m-2 s-1
    r.mapcalc \
	"k_sat_rosetta3_${HORIZON}_${RGN_STR} = (Cl * 14.7500629329 + SiCl * 9.6136374341 + SaCl * 11.3533844849 + ClLo * 7.0635116122 + SiClLo * 11.108435216 + SaClLo * 13.2312093416 + Lo * 13.3386286706 + SiLo * 18.4713576853 + SaLo * 37.4503675019 + Si * 43.7471157565 + LoSa * 108.1993376227 + Sa * 108.1993376227) * 10 / 24 / 60 / 60" \
	$OVERWRITE
    
    # Now compute the remaining parameters using van Genuchten relationship
    
    # Air-entry pressure, metres head [sathh]
    r.mapcalc \
	"psi_m_rosetta3_${HORIZON}_${RGN_STR} = 1 / alpha_m_rosetta3_${HORIZON}_${RGN_STR}" \
	$OVERWRITE

    # Inverted pore size distribution index, dimensionless
    # (based on Morel-Seytoux et al (1996) - see Marthews et al. (2014) [b]    
    r.mapcalc \
	"b_rosetta3_${HORIZON}_${RGN_STR} = 1 / (nM_rosetta3_${HORIZON}_${RGN_STR} - 1)" \
	$OVERWRITE

    # Use van Genuchten model to calculate water content at
    # field capacity and critical point

    # Critical point (assume suction=3.364m)
    r.mapcalc \
	"A_crit_rosetta3_${HORIZON}_${RGN_STR} = (alpha_m_rosetta3_${HORIZON}_${RGN_STR} * 3.364) ^ nM_rosetta3_${HORIZON}_${RGN_STR}" \
	$OVERWRITE

    r.mapcalc \
	"Se_crit_rosetta3_${HORIZON}_${RGN_STR} = (1 + A_crit_rosetta3_${HORIZON}_${RGN_STR}) ^ ((1 / nM_rosetta3_${HORIZON}_${RGN_STR}) - 1)" \
	$OVERWRITE
    
    # [sm_crit]
    r.mapcalc \
	"theta_crit_rosetta3_${HORIZON}_${RGN_STR} = (Se_crit_rosetta3_${HORIZON}_${RGN_STR} * (theta_sat_rosetta3_${HORIZON}_${RGN_STR} - theta_res_rosetta3_${HORIZON}_${RGN_STR})) + theta_res_rosetta3_${HORIZON}_${RGN_STR}" \
	$OVERWRITE

    # Wilting point (assume suction=152.9m)
    r.mapcalc \
	"A_wilt_rosetta3_${HORIZON}_${RGN_STR} = (alpha_m_rosetta3_${HORIZON}_${RGN_STR} * 152.9) ^ nM_rosetta3_${HORIZON}_${RGN_STR}" \
	$OVERWRITE

    r.mapcalc \
	"Se_wilt_rosetta3_${HORIZON}_${RGN_STR} = (1 + A_wilt_rosetta3_${HORIZON}_${RGN_STR}) ^ ((1 / nM_rosetta3_${HORIZON}_${RGN_STR}) - 1)" \
	$OVERWRITE

    # [sm_wilt]
    r.mapcalc \
	"theta_wilt_rosetta3_${HORIZON}_${RGN_STR} = (Se_wilt_rosetta3_${HORIZON}_${RGN_STR} * (theta_sat_rosetta3_${HORIZON}_${RGN_STR} - theta_res_rosetta3_${HORIZON}_${RGN_STR})) + theta_res_rosetta3_${HORIZON}_${RGN_STR}" \
	$OVERWRITE

    # Remove mask
    r.mask -r
    
    # # Reset resolution
    # NATIVE_RGN_STR=globe_0.002083Deg
    # RGN_STR=globe_0.008333Deg
    # g.region region=${RGN_STR}

    # # Resample rosetta3 maps to 1k resolution
    # for VARIABLE in b k_sat psi_m theta_crit theta_sat theta_wilt
    # do
    # 	r.resamp.stats \
    # 	    input=${VARIABLE}_rosetta3_${HORIZON}_${NATIVE_RGN_STR}.tif \
    # 	    output=${VARIABLE}_rosetta3_${HORIZON}_${RGN_STR}.tif \
    # 	    method=average \
    # 	    $OVERWRITE
    # done            
done

# ========================================================= #
# Compute dry heat capacity, dry thermal conductivity
# ========================================================= #

RGN_STR=globe_0.008333Deg
g.region region=${RGN_STR}

# See Zed Zulkafli's PhD thesis for equations

# Units: J m-3 K-1
cc=2373000
cs=2133000
csi=2133000
lambda_air=0.025
lambda_clay=1.16025
lambda_sand=1.57025
lambda_silt=1.57025
for HORIZON in sl1 sl2 sl3 sl4 sl5 sl6 sl7
do
    for METHOD in cosby tomas rosetta3
    do
	r.mapcalc \
	    "hcap_${METHOD}_${HORIZON}_${RGN_STR} = (1 - theta_sat_${METHOD}_${HORIZON}_${RGN_STR}) * (CLYPPT_${HORIZON} * 0.01 * $cc + SNDPPT_${HORIZON} * 0.01 * $cs + SLTPPT_${HORIZON} * 0.01 * $csi)" \
	    $OVERWRITE

	r.mapcalc \
	    "hcon_${METHOD}_${HORIZON}_${RGN_STR} = ($lambda_air ^ theta_sat_${METHOD}_${HORIZON}_${RGN_STR}) * ($lambda_clay ^ ((1 - theta_sat_${METHOD}_${HORIZON}_${RGN_STR}) * CLYPPT_${HORIZON} * 0.01)) * ($lambda_sand ^ ((1 - theta_sat_${METHOD}_${HORIZON}_${RGN_STR}) * SNDPPT_${HORIZON} * 0.01)) * ($lambda_silt ^ ((1 - theta_sat_${METHOD}_${HORIZON}_${RGN_STR}) * SLTPPT_${HORIZON} * 0.01))" \
	    $OVERWRITE
    done
done    

# ========================================================= #
# Read VARIABLEs which are included in the SoilGrids data
# ========================================================= #

g.region region=${RGN_STR}

# PHIHOX, CLYPPT
for HORIZON in sl1 sl2 sl3 sl4 sl5 sl6 sl7
do
    r.mapcalc \
	"ph_${HORIZON}_${RGN_STR} = PHIHOX_${HORIZON} / 10" \
	$OVERWRITE
    r.mapcalc \
	"clay_${HORIZON}_${RGN_STR} = CLYPPT_${HORIZON}" \
	$OVERWRITE
done

# ========================================================= #
# Soil albedo
# ========================================================= #

# Use dataset of Houldcroft et al. (2009) (downloaded from JASMIN)
g.region region=${RGN_STR}

ncks -O --msa -d longitude,180.,360. -d longitude,0.,180. ../data/soil_albedo.nc tmp.nc
ncap2 -O -s 'where(longitude > 180) longitude=longitude-360' tmp.nc $AUXDIR/soil_albedo_corr_long.nc
rm -f tmp.nc

# use GDAL tools to convert netCDF to geotiff
gdal_translate \
    -co "compress=lzw" \
    NETCDF:\"$AUXDIR/soil_albedo_corr_long.nc\":soil_albedo tmp.tif

# resample to match globe_0.008333Deg region, using nearest-neighbour resampling
gdalwarp \
    -overwrite \
    -t_srs EPSG:4326 \
    -co "compress=lzw" \
    -te -180 -90 180 90 \
    -ts 43200 21600 \
    -r near \
    tmp.tif $AUXDIR/soil/background_soil_albedo_${RGN_STR}.tif

# clean up
rm -f tmp.tif

# import data to GRASS
r.in.gdal \
    -a \
    input=$AUXDIR/soil/background_soil_albedo_${RGN_STR}.tif \
    output=background_soil_albedo_${RGN_STR} \
    $OVERWRITE
