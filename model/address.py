class Address:
    def __init__(self, street, plz=None, city=None):
        self.street = street
        self.plz = plz
        self.city = city

    def __str__(self):
        if self.plz is not None and self.city is not None:
            return "{self.street}, {self.plz} {self.city}".format(self=self)
        return "{self.street}".format(self=self)

    def dump(self):
        return {
            'street': self.street,
            'zip': self.plz,
            'city': self.city
        }
