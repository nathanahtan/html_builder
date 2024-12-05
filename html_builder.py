
from textwrap import indent


class HTMLNode:
    def __init__(self, tag: str) -> None:
        self.tag = tag
        self.attributes: dict[str, str] = {}
        self.classes: set[str] = set()
        self.styles: dict[str, str] = {}
        self.inner_text: str = ""
        # use self.append() and .append_to() to manage these automatically
        # and provide chain notation.
        self.children: list[HTMLNode] = []
        self.parent: HTMLNode | None = None

    def add_class(self, classs: str):
        self.classes.add(classs)
        return self

    def add_classes(self, classes: str):
        """
        Expect space separated string of classes.
        """
        for c in classes.split(" "):
            self.classes.add(c)
        return self

    def add_attr(self, k: str, v: str):
        self.attributes[k] = v
        return self

    def add_text(self, text: str):
        self.inner_text=text
        return self
    
    def add_style(self, k: str, v: str):
        self.styles[k] = v
        return self

    def append(self, child):
        """
        Type checks child, sets its parent and returns self for chaining.
        """
        if not isinstance(child, HTMLNode):
            raise TypeError(f"Tried to append a child of type {type(child)}")
        self.children.append(child)
        child.parent = self
        return self

    def append_to(self, parent):
        """
        Type checks parent, sets this parent and returns parent for chaining.
        """
        if not isinstance(parent, HTMLNode):
            raise TypeError(
                f"Tried to append {self} node to parent of typ {type(parent)}"
            )
        self.parent = parent
        parent.children.append(self)
        return parent

    def _check_children(self):
        """
        Double check for self-referencing and non-Node children.
        """
        for child in self.children:
            if child is self:
                raise RecursionError(f"{self} is self referenced.")
            if not isinstance(child, HTMLNode):
                raise ValueError(f"{child} is not a Node")

    def _format_classes(self):
        return " ".join(self.classes)

    def _format_styles(self):
        style_parts = []
        for k, v in self.styles.items():
            style_parts.append(f"{k}: {v}")
        return "; ".join(style_parts)

    def _format_attributes(self):
        attribute_parts = []
        for k, v in self.attributes.items():
            attribute_parts.append(f'{k}="{v}"')
        return " ".join(attribute_parts)

    def _format_inner_text(self):
        """
        If inner text and no children, one liner.
        If inner text has lines, then nest it like a child.
        """
        if not self.children:
            if not "\r\n" in self.inner_text:
                return self.inner_text
            # we need a new line lines before and after
            return f"\r\n{self.inner_text}\r\n"
        # no trailing newwline
        return indent(f"\r\n{self.inner_text}", "  ")

    def render(self):
        self._check_children()
        parts = []

        # turn classes into an attribute
        if self.classes:
            self.attributes["class"] = self._format_classes()

        # turn styles into an attribute
        if self.styles:
            self.attributes["style"] = self._format_styles()

        # build the head depending on attributes or not
        if self.attributes:
            head_parts = [f"<{self.tag} "]
            head_parts.append(self._format_attributes())
        else:
            head_parts = [f"<{self.tag}"]

        # close head
        head_parts.append(">")

        # add head to parts
        parts.append("".join(head_parts))

        if self.inner_text:
            parts.append(self._format_inner_text())

        # is this recursive?
        if self.children:
            parts.append("\r\n")
            child_parts = []
            for child in self.children:
                child_parts.append(indent(text=child.render(), prefix="  "))
            parts.append("\r\n".join(child_parts))
            parts.append("\r\n")

        # close node
        parts.append(f"</{self.tag}>")
        return "".join(parts)

class HTMLDoc():
    """
    HTML documents require the preamble "<!DOCTYPE html>".
    Rather than add preambles to the base node (have not seen any other preambles),
    using it to show a way to use HTMLNode as a base for making more complex HTML.
    """

    def __init__(self, title: str) -> None:
        self.preamble: str = '<!DOCTYPE html>'
        self.root = HTMLNode('html')
        self.head = HTMLNode('head')
        self.title = HTMLNode('title')
        self.title.add_text(title)
        self.body = HTMLNode('body')

    def build_tree(self):
        """
        Append children to form the page.
        """
        self.title.append_to(self.head).append_to(self.root)
        self.body.append_to(self.root)

    def render(self):
        """
        Here we just make a string from the preamble and root render.
        """
        self.build_tree()
        return '\r\n'.join((self.preamble, self.root.render()))


def test():

    doc = HTMLDoc('test doc')

    d = HTMLNode(tag="div")
    d.inner_text = "inner text"
    d.classes.add("class1")
    d.add_classes("class2 class3")
    d.add_style("font", "arial")
    d.add_style("color", "blue")

    doc.body.append(d)
    

    d1 = HTMLNode(tag="div1")
    d1.inner_text = "inner text"

    d2 = HTMLNode(tag="d3")
    d2.inner_text = "line one<br>\r\nline two"
    d2.append(d1)

    d.append(d1)
    d.append(d2)

    print(doc.render())


if __name__ == "__main__":
    test()
