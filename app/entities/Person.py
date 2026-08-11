
class Person: 
    age: int # years
    gender: str
    weight: float
    height: float = None
    naf: str # liviana, moderada, intensa
    naf_index: float = None

    def __init__(self, age, gender, weight, naf=None, height=None):
        self.age = age
        self.gender = gender
        self.weight = weight
        self.naf = naf
        self.height = height
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
    


    

    

        