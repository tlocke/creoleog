from google.appengine.ext import ndb
from xml.dom import Node
from creole import creole2html
import xml.parsers.expat
import xml.dom.minidom
from django.core.exceptions import ValidationError

allowed_elements = {
    'a': ['href'], 'br': [], 'p': [], 'h1': [], 'h2': [], 'h3': [],
    'h4': [], 'h5': [], 'ul': [], 'li': [], 'em': [], 'strong': [],
    'dl': [], 'dt': [], 'dd': [], 'pre': [], 'kbd': []}

tag_map = (('i', 'em'), ('tt', 'kbd'))
conv = []
for old, new in tag_map:
    conv.append(('<' + old + '>', '<' + new + '>'))
    conv.append(('</' + old + '>', '</' + new + '>'))

NODE_TYPES = {
    Node.ELEMENT_NODE: 'element',
    Node.ATTRIBUTE_NODE: 'attribute',
    Node.TEXT_NODE: 'text',
    Node.CDATA_SECTION_NODE: 'cdata_section',
    Node.ENTITY_NODE: 'entity',
    Node.PROCESSING_INSTRUCTION_NODE: 'processing_instruction',
    Node.COMMENT_NODE: 'comment_node',
    Node.DOCUMENT_NODE: 'document',
    Node.DOCUMENT_TYPE_NODE: 'document_type',
    Node.NOTATION_NODE: 'notation'}


def creole_as_html(creole_txt):
    html = creole2html(creole_txt)
    for old, new in conv:
        html = html.replace(old, new)
    return html


def check_node(node):
    if node.nodeType == node.TEXT_NODE:
        pass
    elif node.nodeType == node.ELEMENT_NODE:
        if node.tagName not in allowed_elements.keys():
            raise ValidationError(
                "The element '" + node.tagName + """' is not allowed. The
                allowed elements are """ + str(allowed_elements.keys()))
        allowed_attrs = allowed_elements[node.tagName]
        attrs = node.attributes
        for i in range(attrs.length):
            attr = attrs.item(i)
            if attr.name not in allowed_attrs:
                raise ValidationError(
                    "The only allowed attributes of the '" +
                    node.tagName + "' element are " +
                    str(allowed_attrs) + ".")
        for sub_node in node.childNodes:
            check_node(sub_node)
    else:
        raise ValidationError(
            "The document can't contain a node of type " +
            NODE_TYPES[node.nodeType] + ".")


def check_creole(creole_str):
    try:
        dom = xml.dom.minidom.parseString(
            '<creoleog>' + creole_as_html(creole_str).encode('utf_8') +
            '</creoleog>')
    except xml.parsers.expat.ExpatError as e:
        raise ValidationError('Problem parsing the post' + e.message)
    for node in dom.documentElement.childNodes:
        check_node(node)


class Blog(ndb.Model):
    title = ndb.StringProperty(required=True)


class Entry(ndb.Model):
    body = ndb.StringProperty(indexed=False)
    creation_date = ndb.DateTimeProperty(auto_now_add=True)

    def body_as_html(self):
        return creole_as_html(self.body)
