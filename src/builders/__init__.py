from pydantic import BaseModel
from src.logger import get_logger
from src.util import assign_config

logger = get_logger()

class BaseBuilder:
    def __init__(self, config: BaseModel | dict = None):
        assign_config(self, config)

    def __call__(self, data, *args, **kwargs):
        raise NotImplementedError
