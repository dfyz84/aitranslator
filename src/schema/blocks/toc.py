from src.schema import BlockTypes
from src.schema.blocks.basetable import BaseTable


class TableOfContents(BaseTable):
    block_type: str = BlockTypes.TableOfContents
    block_description: str = "A table of contents."
