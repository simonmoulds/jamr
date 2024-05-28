
from jamr.landfraction import LandFraction, ESALandFraction
from jamr.landcover import ESACCILC, ESACCIWB, TerrestrialEcoregions, C4Fraction, Poulter2015PFT, Poulter2015FivePFT, Poulter2015NinePFT
from jamr.soil import SoilGrids
from jamr.elevation import MERITDEM


class LandFractionFactory:
    @staticmethod
    def create_land_fraction(method,
                             config,
                             inputdata,
                             region,
                             overwrite):
        if method == 'ESA':
            return ESALandFraction(config, inputdata, region, overwrite) 
        else:
            raise ValueError(f'Unknown land fraction method: {method}')


class LandCoverFractionFactory:
    @staticmethod
    def create_landcover_fraction(method, npft, config, inputdata, region, overwrite):
        if method == 'Poulter':
            if npft == 5:
                return Poulter2015FivePFT(config, inputdata, region, overwrite)
            elif npft == 9: 
                return Poulter2015NinePFT(config, inputdata, region, overwrite)



class InputData:
    def __init__(self, 
                 config, 
                 overwrite=False):

        # TODO check classes 
        # TODO allow user to specify dataset source (perhaps in config?)
        self.landcover = ESACCILC(config, overwrite)
        self.pfts = Poulter2015PFT(config, self.landcover, overwrite)
        self.waterbodies = ESACCIWB(config, overwrite)
        self.soil = SoilGrids(config, overwrite)
        self.elevation = MERITDEM(config, overwrite)
        self.ecoregions = TerrestrialEcoregions(config, overwrite)
        self.c4fraction = C4Fraction(config, overwrite)
        self.overwrite = overwrite

    def initial(self):
        self.landcover.initial()
        self.pfts.initial()
        self.waterbodies.initial()
        self.soil.initial()
        self.elevation.initial()
        self.ecoregions.initial()
        self.c4fraction.initial() 

    def compute(self):
        self.pfts.compute()


class JULESAncillaryData:
    def __init__(self, config, inputdata, region, overwrite):
        self.config = config
        self.inputdata = inputdata 
        self.region = region 
        self.overwrite = overwrite 
        
        # NOTE only one method allowed
        land_fraction_method = self.config['methods']['land_fraction']
        self.landfrac = LandFractionFactory().create_land_fraction(
            land_fraction_method, self.config, self.inputdata, 
            self.region, self.overwrite
        )

        frac_methods = self.config['methods']['frac']
        npft = self.config['methods']['npft']
        self.frac = []
        for method in frac_methods:
            n = 5
            # for n in npft:
            self.frac.append(LandCoverFractionFactory().create_landcover_fraction(
                method, int(n), self.config, self.inputdata, 
                self.region, self.overwrite
            ))

    def _set_landfrac(self):
        # NOTE only one method allowed
        land_fraction_method = self.config['methods']['land_fraction']
        self.landfrac = LandFractionFactory(
            land_fraction_method, self.config, self.inputdata, 
            self.region, self.overwrite
        )

    def _set_frac(self):
        frac_methods = self.config['methods']['frac']
        npft = self.config['methods']['npft']
        self.frac = []
        for method in frac_methods:
            for n in npft:
                self.frac += LandCoverFractionFactory(
                    method, int(n), self.config, self.inputdata, 
                    self.region, self.overwrite
                )

    # def _set_soil_props(self):
    #     # class SoilPropertiesFactory()
    #     self.soil_props = [] 
    #     if 'Cosby' in self.config['methods']['soil_props']:
    #         self.soil_props += CosbySoilProperties()

    #     if 'TomasellaHodnett' in self.config['methods']['soil_props']:
    #         self.soil_props += TomasellaHodnettSoilProperties()

    def compute(self):
        self.landfrac.compute()
        for frac_obj in self.frac: 
            frac_obj.compute()
        # for soil_props_obj in self.soil_props:
        #     soil_props_obj.compute() 

    def write(self):
        pass 