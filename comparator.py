from article import Article
import datetime
import log
import json
from config import Config

logger = log.setup_logger(__name__)


class SupportedComparator:
    def __init__(self, min_rooms: float = None, min_living_space: float = None, max_base_rent: float = None,
                 max_total_rent: float = None, is_house: bool = None, max_floor: int = None,
                 available_from: datetime.date = None, has_elevator: bool = None, required_wbs: bool = None):
        self.min_rooms = min_rooms
        self.min_living_space = min_living_space
        self.max_base_rent = max_base_rent
        self.max_total_rent = max_total_rent
        self.is_house = is_house
        self.max_floor = max_floor
        self.available_from = available_from
        self.has_elevator = has_elevator
        self.required_wbs = required_wbs

    def is_match(self, article: Article):
        if Config.DEBUG:
            logger.debug("{0}: {1}".format(article.id, json.dumps(article.dump())))
            logger.debug("comparator: {0}".format(self.__str__()))
        if self.min_rooms is not None:
            if self.min_rooms > article.no_rooms:
                if Config.DEBUG:
                    logger.debug(
                        "Not valid, required min {0} rooms, actual: {1} rooms".format(self.min_rooms, article.no_rooms))
                return False

        if self.min_living_space is not None:
            if self.min_living_space > article.living_space:
                if Config.DEBUG:
                    logger.debug("Not valid, required min {0} m2, actual: {1} m2".format(self.min_living_space,
                                                                                         article.living_space))
                return False

        if self.max_base_rent is not None:
            if self.max_base_rent < article.costs.base_rent:
                if Config.DEBUG:
                    logger.debug("Not valid, required max base {0} euro, actual: {1} euro".format(self.max_base_rent,
                                                                                                  article.costs.base_rent))
                return False

        if self.max_total_rent is not None:
            if self.max_total_rent < article.costs.total_rent:
                if Config.DEBUG:
                    logger.debug("Not valid, required max total {0} euro, actual: {1} euro".format(self.max_total_rent,
                                                                                                   article.costs.total_rent))
                return False

        if self.is_house is not None:
            if self.is_house != article.is_house:
                if Config.DEBUG:
                    logger.debug(
                        "Not valid, required House {0}, actual: House {1} ".format(self.is_house, article.is_house))
                return False

        if self.max_floor is not None:
            if self.max_floor < article.floor:
                if Config.DEBUG:
                    logger.debug("Not valid, required max floor {0}, actual: current floor {1} ".format(self.max_floor,
                                                                                                        article.floor))
                return False

        if self.has_elevator is not None:
            if self.has_elevator != article.has_elevator:
                if Config.DEBUG:
                    logger.debug(
                        "Not valid, required elevator {0}, actual: elevator {1} ".format(self.has_elevator,
                                                                                         article.has_elevator))
                return False

        if self.required_wbs is not None:
            if self.required_wbs != article.required_wbs:
                if Config.DEBUG:
                    logger.debug(
                        "Not valid, required wbs {0}, actual: wbs {1} ".format(self.required_wbs, article.required_wbs))
                return False
        return True

    def __str__(self):
        arr = []

        if self.is_house is not None:
            arr.append("House: {0}".format(self.is_house))

        if self.min_rooms is not None:
            arr.append("Min rooms: {0}".format(self.min_rooms))

        if self.min_living_space is not None:
            arr.append("Min living space: {0}".format(self.min_living_space))

        if self.max_base_rent is not None:
            arr.append("Max base rent: {0}".format(self.max_base_rent))

        if self.max_total_rent is not None:
            arr.append("Max total rent: {0}".format(self.max_total_rent))

        if self.max_floor is not None:
            arr.append("Max floor: {0}".format(self.max_floor))

        if self.available_from is not None:
            arr.append("Available from: {0}".format(self.available_from.strftime("%d.%m.%Y")))

        if self.has_elevator is not None:
            arr.append("Elevator: {0}".format(self.has_elevator))

        if self.required_wbs is not None:
            arr.append("wbs: {0}".format(self.required_wbs))

        return "Comparator {0}".format(",".join(arr))
