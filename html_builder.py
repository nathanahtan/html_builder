from __future__ import annotations
from typing import Optional, Dict, List, Set
import textwrap


class HTMLAttribute:
    """
    Represents and html attribute, such as 'class' or 'style'.
    Values are a set(), so unicity is guaranteed.
    """

    def __init__(self, name: str, separator: str = " ") -> None:
        self.name = name
        self.values: Set[str] = set()
        self.separator = separator

    def add_value(self, value: str):
        self.values.add(value)

    def text(self) -> str:
        """Generates text for the attribute with separator"""
        attr_text = self.separator.join(self.values)
        return f'{self.name}="{attr_text}"'


class HTMLNode:
    """
    Represents an HTML node.
    Can have child nodes.
    Renders html text.
    """

    # special node types
    void_element_names = [
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "keygen",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    ]

    def __init__(self, tag: str) -> None:
        self.tag = tag
        self.attrs: Dict[str, HTMLAttribute] = {}
        self.children: List[HTMLNode] = []
        self.only_text_or_comments: bool = True

    def add_attr(self, name: str, value: str, separator: str = " ") -> HTMLNode:
        """
        Adds an attribute for a name.
        Duplicates are ignored.
        If attribute is new, then the separator is passed to the Attr object
        """
        if name not in self.attrs:
            self.attrs[name] = HTMLAttribute(name, separator)

        self.attrs[name].add_value(value)

        return self  # for chaining

    def remove_attr(self, name: str, value: str) -> HTMLNode:
        """
        Removes an attribute value, if it exists.
        """
        attr: Optional[HTMLAttribute] = self.attrs.get(name)
        if attr:
            try:
                attr.values.remove(value)
            except KeyError:
                pass

        return self  # for chaining

    def add_class(self, value: str) -> HTMLNode:
        """
        Helper function to add to the 'class' attr, since it is used frequently.
        """
        return self.add_attr("class", value)

    def remove_class(self, value: str) -> HTMLNode:
        """
        Helper function that removes a value from the class attr.
        """
        return self.remove_attr("class", value)

    def add_style(self, key: str, value: str) -> HTMLNode:
        """
        Helper function for adding to the 'style' attr.
        """
        return self.add_attr("style", f"{key}:{value}", ";")

    def add_text(self, text: str) -> HTMLNode:
        """
        Adds a text node to the children.
        This is 'inner' text.
        Note it will be rendered in append order.
        """
        text_node = HTMLText(text)
        self.append(text_node)

        return self  # for chaining

    def add_comment(self, comment: str) -> HTMLNode:
        """
        Adds a comment node to the children.
        Note it will be rendered in append order.
        """
        comment_node = HTMLComment(comment)
        self.append(comment_node)

        return self  # for chaining

    def append(self, child: HTMLNode) -> HTMLNode:
        """
        Appends a node to self.children
        Allows for fancy append()/append_to() chaining.
        """
        
        # Do not allow anything but HTMLNodes to be appended.
        if not isinstance(child, HTMLNode):
            return self  # for chaining
        
        if not any((isinstance(child, HTMLText), isinstance(child, HTMLComment))):
            # Set flag to know this node contains more than just comments or text.
            # Used for rendering.
            self.only_text_or_comments = False
        self.children.append(child)

        return self  # for chaining

    def append_to(self, parent: HTMLNode) -> HTMLNode:
        """
        Appends this node to parent's children.
        Allows for fancy append()/append_to() chaining.
        """
        parent.append(self)

        return parent  # for chaining

    def _start(self) -> str:
        """
        Renders the start of the html.
        """
        attr_texts = [attr.text() for attr in self.attrs.values()]
        if attr_texts:
            name = f"{self.tag} "
        else:
            name = self.tag
        if self.tag in self.void_element_names:
            return f'<{name}{" ".join(attr_texts)}'
        return f'<{name}{" ".join(attr_texts)}>'

    def _mid(self, indent: str) -> str:
        """
        Renders the middle of the html.  Basically gathering up the children html.
        """
        if self.children:
            if not self.only_text_or_comments:
                return "\n" + "\n".join(
                    [
                        textwrap.indent(child.render_text(), indent)
                        for child in self.children
                    ]
                )
            else:
                # if only text and comments then we don't want newlines, just a space; we want to inline it
                return " ".join([child.render_text() for child in self.children])
        return ""

    def _end(self) -> str:
        """
        Renders the end of the html.
        """
        # void elements can't have children, but we aren't enforcing this.
        if not self.children or self.only_text_or_comments:
            if not self.tag in self.void_element_names:
                return f"</{self.tag}>"
            else:
                return ">"
        return f"\n</{self.tag}>"

    def preprocess(self):
        """
        This is called before text is rendered.
        You can hook in here when subclassing.
        Typically used to append children at the last second...
        """
        pass

    def render_text(self, indent: str = "    ") -> str:
        """
        Renders the html text for this node and its children.
        Indent can be specified.
        """
        self.preprocess()
        return f"{self._start()}{self._mid(indent)}{self._end()}"


class HTMLText(HTMLNode):
    """
    Special node that renders out as text.
    
    Use for 'inner' text that needs to be in the append list.
    """

    def __init__(self, text: str) -> None:
        super().__init__("text_node")  # this isn't rendered
        self.text = text

    def render_text(self, indent: Optional[str] = "    ") -> str:
        return self.text


class HTMLComment(HTMLNode):
    """
    Special node that renders out as a single line comment.
    """

    def __init__(self, comment: str) -> None:
        super().__init__("comment_node")  # this isn't rendered
        self.comment = comment

    def render_text(self, indent: Optional[str] = "    ") -> str:
        return f"<-- {self.comment} -->"


class HTMLDoc(HTMLNode):
    """
    An HTMLNode with a doctype and some convienence functions.
    """

    def __init__(self, indent: Optional[str] = "    ") -> None:
        super().__init__(tag="html")
        self.indent = indent
        self.doctype = "<!DOCTYPE html>"
        self.head = HTMLNode("head")
        self.body = HTMLNode("body")
        self.title: str = None
        self.language_code: str = "en"

    def preprocess(self):
        # add language attribute, which is 'en' by default
        # HTMLNode won't allow duplicate attributes so don't have to clear.
        self.add_attr("lang", self.language_code)
        # if a title then add to head
        if self.title:
            HTMLNode("title").add_text(self.title).append_to(self.head)
        # add the head node to the doc children
        self.append(self.head)
        # add the body node to the doc children
        self.append(self.body)

    def render_text(self) -> str:
        # Override this to add the doctype.
        return f"{self.doctype}\n{super().render_text(indent=self.indent)}"


if __name__ == "__main__":

    # div example
    div_node = HTMLNode("div")
    print(div_node.render_text())

    # append chain example
    # one way to make a node and add text
    parent = HTMLNode("div")
    parent.add_text("parent")
    # another way
    child = HTMLNode("div").add_text("child")
    # make gandchild node and append to child and append child to parent in one line
    HTMLNode("div").add_text("grandchild").append_to(child).append_to(parent)

    # same appending done from top down:
    # parent.append(child.append(hb.HTMLNode('div').add_text('grandchild')))

    # mix and match:
    # parent.append(hb.HTMLNode('div').add_text('grandchild').append_to(child))

    # you could even render the text on the above line but for clarity...
    print(parent.render_text())
    # change the indent string to two spaces
    print(parent.render_text(indent="  "))

    # class chaining example
    subtitle = HTMLNode("p")
    subtitle.add_class("font-size-sm").add_class("font-color-muted").add_class(
        "font-transform-lower"
    )
    subtitle.add_class("width-400").add_class("max-width-full")

    # HTMLDoc is a subclass of HTMLNode
    doc = HTMLDoc()
    # Edit the doc
    # add a title
    doc.title = "Document Title"
    # add a meta to the head
    HTMLNode("meta").add_attr("meta_key", "meta_value").append_to(doc.head)
    HTMLComment('This is a comment').append_to(doc.head)
    # add a paragraph to the body
    HTMLNode("p").add_text("Paragraph text").append_to(doc.body)
    print(doc.render_text())
    # HTMLDoc is a one-shot object!  Re-rendering will cause duplicate children.
