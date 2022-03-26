import os
from typing import get_type_hints, Union
from dotenv import load_dotenv

load_dotenv()


class AppConfigError(Exception):
    pass


def _parse_bool(val: Union[str, bool]) -> bool:  # pylint: disable=E1136
    return val if type(val) == bool else val.lower() in ['true', 'yes', '1']


def _parse_int(val: Union[str, int]) -> int:  # pylint: disable=E1136
    if type(val) == int:
        return val
    try:
        return int(val)
    except ValueError:
        raise "Not integer value"


class AppConfig:
    DEBUG: bool = False
    BASE_URL: str
    BASE_APPLY_URL: str
    BASE_DETAIL_URL: str
    MQTT_BROKER_URL: str
    MQTT_BROKER_PORT: int = 1883
    MQTT_USER: str
    MQTT_PASS: str

    """
    Map environment variables to class fields according to these rules:
      - Field won't be parsed unless it has a type annotation
      - Field will be skipped if not in all caps
      - Class field and environment variable name are the same
    """

    def __init__(self, env):
        for field in self.__annotations__:
            if not field.isupper():
                continue

            # Raise AppConfigError if required field not supplied
            default_value = getattr(self, field, None)

            if default_value is None and env.get(field) is None:
                raise AppConfigError('The {} field is required'.format(field))

            # Cast env var value to expected type and raise AppConfigError on failure
            try:
                var_type = get_type_hints(AppConfig)[field]
                if var_type == bool:
                    value = _parse_bool(env.get(field, default_value))
                elif var_type == int:
                    value = _parse_int(env.get(field, default_value))
                else:
                    value = var_type(env.get(field, default_value))

                self.__setattr__(field, value)
            except ValueError:
                raise AppConfigError('Unable to cast value of "{}" to type "{}" for "{}" field'.format(
                    env[field],
                    var_type,
                    field
                ))

    def __repr__(self):
        return str(self.__dict__)


Config = AppConfig(os.environ)
