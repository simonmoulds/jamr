
from jamr.process.landfraction import LandFractionFactory
from jamr.process.landcover import LandCoverFractionFactory
from jamr.process.soilprops import SoilPropsFactory


class ProcessData:
    """Data set class to convert raw input data into JULES ancillary data.

    Parameters
    ----------
    config : dict 
        The run configuration.
    inputdata : InputData 
        The raw input data.
    overwrite : bool 
        Whether to overwrite files in the GRASS GIS database.  
    """
    def __init__(self, 
                 config, 
                 inputdata, 
                 overwrite):

        self.config = config
        self.inputdata = inputdata 
        self.overwrite = overwrite 
        
        # NOTE only one method allowed
        land_fraction_method = self.config['methods']['land_fraction']
        self.landfrac = LandFractionFactory().create_land_fraction(
            land_fraction_method, 
            self.config, 
            self.inputdata, 
            self.overwrite
        )

        # More than one method allowed
        frac_methods = self.config['methods']['frac']
        npft = self.config['methods']['npft']
        self.frac = []
        for method in frac_methods:
            for n in npft:
                self.frac.append(LandCoverFractionFactory().create_landcover_fraction(
                    method, int(n), self.config, self.inputdata, 
                    # self.overwrite
                    False
                ))

        # More than one method allowed
        soil_methods = self.config['methods']['soil_props']
        self.soil_props = [] 
        for method in soil_methods:
            self.soil_props.append(SoilPropsFactory().create_soil_props(
                method, self.config, self.inputdata, False
            ))

    def initial(self):
        # for frac_obj in self.frac: 
        #     frac_obj.initial()
        for soil_props_obj in self.soil_props:
            soil_props_obj.initial()
        
    def compute(self):
        self.landfrac.compute()

        for frac_obj in self.frac: 
            frac_obj.compute()

        for soil_props_obj in self.soil_props:
            soil_props_obj.compute()

    def write(self):
        # for frac_obj in self.frac: 
        #     frac_obj.write()
        self.landfrac.write_netcdf()