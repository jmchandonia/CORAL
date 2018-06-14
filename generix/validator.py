
class TermValidationService:
    def __init__(self):
        self.__validators = {
            'nucleotide_sequence': self.nucleotide_sequence,
            'protein_sequence': self.protein_sequence
        }

    def validator(self, name):
        return self.__validators.get(name)

    def nucleotide_sequence(self, val):
        return True

    def protein_sequence(self, val):
        print('--- check protine sequence ---', val)
        return True
