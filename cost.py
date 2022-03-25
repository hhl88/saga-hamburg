class Cost:
    def __init__(self, base_rent=None, operating_cost=None, other_cost=None, heating_cost=None, total_rent=None,
                 deposit=None):
        self.base_rent = base_rent
        self.operating_cost = operating_cost
        self.heating_cost = heating_cost
        self.total_rent = total_rent
        self.deposit = deposit

    def __str__(self):
        if self.base_rent is not None and self.total_rent is not None and self.deposit is not None:
            return "Base: {self.base_rent}, Total: {self.total_rent}, Deposit: {self.deposit}".format(self=self)
        return "{self.base_rent}".format(self=self)

    def dump(self):
        return {
            'base_rent': self.base_rent,
            'operating_cost': self.operating_cost,
            'heating_cost': self.heating_cost,
            'total_rent': self.total_rent,
            "deposit": self.deposit
        }
