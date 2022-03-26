import datetime
from address import Address
from cost import Cost
from config import Config


class Article:
    def __init__(self, article_id: str, title: str, img_path: str = None, street: str = None, total_rent: float = None,
                 no_rooms: float = None, living_space: float = None):
        self.id = article_id
        self.title = title
        self.img_link = "{0}{1}".format(Config.BASE_URL, img_path)
        self.link = "{0}/objekt/wohnungen/{1}".format(Config.BASE_URL, article_id)
        self.apply_link = "{0}/de/apply/{1}".format(Config.BASE_APPLY_URL, article_id)
        self.address = Address(street=street)
        self.costs = Cost(total_rent=total_rent)
        self.no_rooms = no_rooms
        self.living_space = living_space
        self.available = True
        self.available_from: datetime.date = None

        self.is_house = False
        self.floor = 0
        self.no_floor = 0
        self.has_elevator = False
        self.required_wbs = False

    def dump(self):
        return {
            'id': self.id,
            'title': self.title,
            'img_link': self.img_link,
            'link': self.link,
            'apply_link': self.apply_link,
            'address': self.address.dump(),
            'costs': self.costs.dump(),
            'no_rooms': self.no_rooms,
            'living_space': self.living_space,
            'available': self.available,
            'available_from': self.available_from.strftime("%d.%m.%Y") if self.available_from is not None else None,
            'is_house': self.is_house,
            'floor': self.floor,
            'no_floor': self.no_floor,
            'has_elevator': self.has_elevator,
            'required_wbs': self.required_wbs,

        }

    def _type(self):
        if self.is_house:
            return "House"
        return "Apartment, Floor: {0}, No of Floors: {1}, Elevator: {2}".format(self.floor, self.no_floor,
                                                                                self.has_elevator)

    def __str__(self):
        return "Article '{self.title}': {self.address} " \
               "\n     Type: {type}" \
               "\n     Rooms: {self.no_rooms} - Size: {self.living_space} m2" \
               "\n     Costs: {self.costs}" \
               "\n     Available: {self.available}, from: {self.availableFrom}" \
               "\n     Image: {self.img_link}" \
               "\n     Link: {self.link}" \
               "\n     Apply link: {self.apply_link}".format(self=self, type=self._type())
