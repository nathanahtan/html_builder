# html_builder
## What
A simple, pure python3 html builder (or generator).

## What is not
* DOM editor
* HTML Parser
* Extremely performant
* Tested extensively for compliance against any specification

## Why
While working on server-side-rendered web apps, I find changing from 'python mode' to 'html mode' or 'template mode' involves quite a bit of cognitive ovehead.  I wanted a way to compose html without leaving 'python mode'.  `html_builder` is the result.  It won't replace the knowledge needed to work with html.  You still need to know/understand what your html needs to be, but it does enable generating that html in a more pythonic way.

## How

### Install
Just copy html_builder.py and import: `import html_builder`.

I like to import as a shorter alias, which is used in the below examples:

`import html_builder as hb`

### Usage

#### Nodes
Create a div:

`div_node = hb.HTMLNode('div')`

Most 'editing' type of functions of HTMLNode return `self` so they can be chained.

One reason for chaining is it flows well while building the html tree.  HTMLNodes can have children, and can be children.  This is accomplished with `.append()` and `.append_to()`.  Note that `.append_to()` returns the parent, not self.  This allows things like:

```python
# one way to make a node and add text
parent = hb.HTMLNode('div')
parent.add_text('parent')
# another way
child = hb.HTMLNode('div').add_text('child')
# make grandchild node and append to child and append child to parent, all in one line
hb.HTMLNode('div').add_text('grandchild').append_to(child).append_to(parent)
```
One could also append from the top down to achieve the same tree:
```python
parent.append(child.append(hb.HTMLNode('div').add_text('grandchild')))
```
Or mix and match; Whatever fits well with how you generated, or are thinking about, the nodes.
```python
parent.append(hb.HTMLNode('div').add_text('grandchild').append_to(child))
```

Another reason for chaining is grouping attribute assignments together.  The `.add_class()`, `.add_style()`, and the more general `.add_attr()`functions also return `self`.
Say you are using a css framework and have a subtitle paragraph that needs three classes applied in order to set the font size, a muted color, and transform to lower case.  You also need to set some responsive width classes.  You could group all classes dealing with fonts to one line, and layout classes on another:
```python
subtitle = hb.HTMLNode('p')
subtitle.add_classes('font-size-sm').add_classes('font-color-muted').add_classes('font-transform-lower')
subtitle.add_classes('width-400 max-width-full')
```

Other functions that support chaining are:

* add_text()
* add_comment()

After the nodes are built, call `render()` on the top or root node to get a string representation.  Use this as the body in your html response.


#### Inheritence

`HTMLNode` can be inherited from if you need to customize it, or more commonly, package up functionality in an object to make a more complex html entity.  In the source, `HTMLDoc` does just this.  `HTMLDoc` is an object that is an `HTMLNode`, but also:
* Has a 'head' `HTMLNode`
* Has a 'body' `HTMLNode`
* Has other properties like language_code, title.

After instantiating an `HTMLDoc`, you can set its proprties.  If you need to add something to the html head, then just `HTMLDoc.head.append(...)`.  Similarly with the body.
These properties and children are independent until it comes time to render the html.

`HTMLNode` has a function called `preprocess()` which is meant to be overriden (if needed).  It is the first thing called in the base `render_text()` function.  This is where you 'build' the node.  So for `HTMLDoc`, the properties are added as attributes, and the head and body are appended.

You can also override `render_text()` if needed.  `HTMLDoc`, `HTMLComment`, and `HTMLText` all do this.  For `HTMLDoc`, the doctype needs to be 'stuck on' the beginning of the text.

The result of a fresh `HTMLDoc` is:
```html
<!DOCTYPE html>
<html lang="en">
    <head></head>
    <body></body>
</html>
```
"en" is the default language.  Lets add a title, a meta node to the head, and a paragraph to the body:
```python
doc = hb.HTMLDoc()
doc.title = 'Document Title'
# add a meta to the head
hb.HTMLNode('meta').add_attr('meta_key', 'meta_value').append_to(doc.head)
# add a paragraph to the body
hb.HTMLNode('p').add_text('Paragraph text').append_to(doc.body)
print(doc.render_text())
```
Which results in:
```html
<!DOCTYPE html>
<html lang="en">
    <head>
        <meta meta_key="meta_value">
        <title>Document Title</title>
    </head>
    <body>
        <p>Paragraph text</p>
    </body>
</html>
```
Lets take a look at `preprocess()` in `HTMLDoc`:
```python
def preprocess(self):
    # add language attribute, which is 'en' by default
    self.add_attr('lang', self.language_code)
    # if a title then add to head
    if self.title:
        HTMLNode('title').add_text(self.title).append_to(self.head)
    # add the head node to the doc children
    self.append(self.head)
    # add the body node to the doc children
    self.append(self.body)   
```
Note that if you run `render_text()` more than once, `self.head` and `self.body` will be appended more than once.  `HTMLDoc` is a one-shot object.  Since `html_builder` is meant for generation, not editing, most of the time, this is fine. If you need to re-render for some reason, you will have to implement a way to prevent duplication.

Also for an example of overriding `render_text()`, from `HTMLDoc`:
```python
def render_text(self):
# Override this to add the doctype.
return f"{self.doctype}\n{super().render_text(indent=self.indent)}"
```
All we did was insert `super().render_text()` into an fstring that has the doctype.

## Summary
`html_builder` is intended to be a base for generating html entities in a pythonic way.  If you find a problem or have a solution, submit an issue or pull request.

