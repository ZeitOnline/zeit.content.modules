from zope.cachedescriptors.property import Lazy as cachedproperty
import UserDict
import grokcore.component as grok
import lxml.objectify
import zeit.cms.content.property
import zeit.cms.content.reference
import zeit.content.modules.interfaces
import zeit.edit.block
import zope.formlib.form
import zope.interface
import zope.security


class RawText(zeit.edit.block.Element):

    zope.interface.implements(zeit.content.modules.interfaces.IRawText)

    text_reference = zeit.cms.content.reference.SingleResource(
        '.text_reference', 'related')
    text = zeit.cms.content.property.ObjectPathProperty(
        '.text', zeit.content.modules.interfaces.IRawText['text'])

    @property
    def raw_code(self):
        if self.text_reference:
            return self.text_reference.text
        if self.text:
            return self.text
        return ''

    @cachedproperty
    def params(self):
        return zeit.content.modules.interfaces.IEmbedParameters(self)


class EmbedParameters(
        grok.Adapter,
        UserDict.DictMixin,
        zeit.cms.content.xmlsupport.Persistent):
    # 99% copy&paste from z.c.author.author.BiographyQuestions, changed the tag
    # name to `param` from `question` and added type conversion.

    grok.context(zeit.content.modules.interfaces.IRawText)
    grok.implements(zeit.content.modules.interfaces.IEmbedParameters)

    def __init__(self, context):
        # The really correct way to do this would be the "trusted adapter"
        # pattern, i.e. unwrap context but then wrap ourselves. But then we
        # would need a security declaration that covers arbitrary attributes
        # (since the parameters are user-defined), which is not feasible.
        context = zope.security.proxy.getObject(context)
        object.__setattr__(self, 'context', context)
        object.__setattr__(self, 'xml', context.xml)

        embed = self.context.text_reference
        fields = {}
        if (zeit.content.text.interfaces.IEmbed.providedBy(embed) and
                embed.parameter_definition):
            for name, field in embed.parameter_fields.items():
                fields[name] = field.bind(embed)
        object.__setattr__(self, 'fields', fields)

        # Set parent last so we don't accidentally trigger _p_changed.
        object.__setattr__(self, '__parent__', context)

    def __getitem__(self, key):
        node = self.xml.xpath('//param[@id="%s"]' % key)
        if not node:
            field = self.fields.get(key, zope.schema.TextLine())
            return field.default
        return self._converter(key).fromProperty(unicode(node[0]))

    def __setitem__(self, key, value):
        node = self.xml.xpath('//param[@id="%s"]' % key)
        if node:
            self.xml.remove(node[0])
        if value:  # XXX Use field.missing_value?
            value = self._converter(key).toProperty(value)
            node = lxml.objectify.E.param(value, id=key)
            lxml.objectify.deannotate(node[0], cleanup_namespaces=True)
            self.xml.append(node)
        super(EmbedParameters, self).__setattr__('_p_changed', True)

    def _converter(self, name):
        props = zeit.cms.content.property.DAVConverterWrapper.DUMMY_PROPERTIES
        field = self.fields.get(name, zope.schema.TextLine())
        return zope.component.queryMultiAdapter(
            (field, props),
            zeit.cms.content.interfaces.IDAVPropertyConverter)

    def keys(self):
        return [x.get('id') for x in self.xml.xpath('//param')]

    # Attribute-style access is meant only for zope.formlib.

    def __getattr__(self, key):
        return self.get(key)

    def __setattr__(self, key, value):
        self[key] = value


class EmbedParameterForm(object):

    _form_fields = NotImplemented
    _omit_fields = ()

    def __init__(self, context, request):
        super(EmbedParameterForm, self).__init__(context, request)
        self.form_fields = self._form_fields.omit(*self._omit_fields)

        embed = self.context.text_reference
        if (zeit.content.text.interfaces.IEmbed.providedBy(embed) and
                embed.parameter_definition):
            self.form_fields = self.form_fields.omit('text')
            # There really is no point in security declarations for fields.
            parameters = zope.security.proxy.getObject(embed.parameter_fields)
            for field in parameters.values():
                self.form_fields += zope.formlib.form.FormFields(field)
