
class Person: 
    age: int # years
    gender: str
    weight: float
    height: float = None
    naf: str # liviana, moderada, intensa
    naf_index: float = None
    is_pregnant: bool
    pregnancy_month:int 
    in_lactancy: bool
    has_postpregnancy_fat: bool

    def __init__(self, age, gender, weight, naf=None, height=None, 
                 is_pregnant=False, pregnancy_month=None, has_postpregnancy_fat=False,
                  in_lactancy=False ):

        if not gender in ['men', 'women']: 
            raise ValueError('Gender must be either men or women ')

        if gender=='men': 
            if is_pregnant or in_lactancy: 
                raise ValueError('Cannot instanciate men pregnant or in lactancy.')

        else:
            if is_pregnant:
                if not pregnancy_month is None:
                    if not (pregnancy_month < 10 and  pregnancy_month >= 0 ):
                        raise ValueError(f'Pregnancy month not a valid value, must be a number between 0-9 ()')
                else: 
                    raise ValueError('Must define pregnancy in case women is pregnant') 


        
        self.age = age
        self.gender = gender
        self.weight = weight
        self.naf = naf
        self.height = height
        self.is_pregnant = is_pregnant
        self.pregnancy_month = pregnancy_month
        self.in_lactancy = in_lactancy
        self.has_postpregnancy_fat = has_postpregnancy_fat

        self.calculate_naf_index()


    def calculate_naf_index(self): 
        if self.naf is None: 
            self.naf_index = None
            return 

        if self.naf == 'low': 
            self.naf_index = 1.55
            return 
        
        if self.gender == 'women': 
            self.naf_index = 1.75 if self.naf == 'moderate' else 2.1 
            return
        # Hombre
        self.naf_index = 1.85 if self.naf == 'moderate' else 2.2 
        return
