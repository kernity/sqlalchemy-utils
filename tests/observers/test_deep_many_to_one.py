import sqlalchemy as sa
from sqlalchemy_utils import generates
from tests import TestCase


class TestPropertyObserversWithDeepManyToOneRelationships(TestCase):
    def create_models(self):
        class Document(self.Base):
            __tablename__ = 'document'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            locale = sa.Column(sa.String(10))

        class Section(self.Base):
            __tablename__ = 'section'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            locale = sa.Column(sa.String(10))

            document_id = sa.Column(
                sa.Integer, sa.ForeignKey(Document.id)
            )

            document = sa.orm.relationship(Document, backref='sections')

        class SubSection(self.Base):
            __tablename__ = 'subsection'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            locale = sa.Column(sa.String(10))

            section_id = sa.Column(
                sa.Integer, sa.ForeignKey(Section.id)
            )

            section = sa.orm.relationship(Section, backref='subsections')

            @generates(locale, source='section.document.locale')
            def copy_locale(self, value):
                return value

        self.Document = Document
        self.Section = Section
        self.SubSection = SubSection

    def test_change_parent_attribute(self):
        document = self.Document(name=u'Document 1', locale='en')
        section = self.Section(name=u'Section 1', document=document)
        subsection = self.SubSection(name=u'Section 1', section=section)
        document.locale = 'fi'
        assert subsection.locale == 'fi'

    def test_simple_assignment(self):
        document = self.Document(name=u'Document 1', locale='en')
        section = self.Section(name=u'Section 1', document=document)
        subsection = self.SubSection(name=u'Section 1', section=section)
        assert subsection.locale == 'en'

    def test_intermediate_object_reference(self):
        document = self.Document(name=u'Document 1', locale='en')
        section = self.Section(name=u'Section 1', document=document)
        subsection = self.SubSection(name=u'Section 1', section=section)
        section.document = self.Document(name=u'Document 2', locale='sv')
        assert subsection.locale == 'sv'
