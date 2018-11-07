import markdown2
from abc import abstractmethod

class Markup:
    @abstractmethod
    def compile(self, source: str) -> str:
        pass
    

class Markdown(Markup):
    def convert(self, source: str) -> str:
        return markdown2.markdown(source.strip(), extras=["fenced-code-blocks"])
    
    def css_class(self) -> str:
        return 'markup-markdown'


class Pre(Markup):
    def convert(self, source: str) -> str:
        return '<pre>' + source + '</pre>'
    
    def css_class(self) -> str:
        return 'markup-pre'
