from typing import Tuple

from src.builders.document import DocumentBuilder
from src.builders.line import LineBuilder
from src.builders.ocr import OcrBuilder
from src.converters.pdf import PdfConverter
from src.processors import BaseProcessor
from src.processors.equation import EquationProcessor
from src.providers.registry import provider_from_filepath
from src.renderers.ocr_json import OCRJSONRenderer


class OCRConverter(PdfConverter):
    default_processors: Tuple[BaseProcessor, ...] = (EquationProcessor,)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.config:
            self.config = {}

        self.config["force_ocr"] = True
        self.renderer = OCRJSONRenderer

    def build_document(self, filepath: str):
        provider_cls = provider_from_filepath(filepath)
        layout_builder = self.resolve_dependencies(self.layout_builder_class)
        line_builder = self.resolve_dependencies(LineBuilder)
        ocr_builder = self.resolve_dependencies(OcrBuilder)
        document_builder = DocumentBuilder(self.config)

        provider = provider_cls(filepath, self.config)
        document = document_builder(provider, layout_builder, line_builder, ocr_builder)

        for processor in self.processor_list:
            processor(document)

        return document

    def __call__(self, filepath: str):
        document = self.build_document(filepath)
        self.page_count = len(document.pages)
        renderer = self.resolve_dependencies(self.renderer)
        return renderer(document)
