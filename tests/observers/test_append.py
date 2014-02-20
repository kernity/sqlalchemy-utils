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

            @generates(locale, source='sections.subsections.locale')
            def copy_locale(self, value):
                return value

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

        self.Document = Document
        self.Section = Section
        self.SubSection = SubSection

    def test_append_direct_child(self):
        document = self.Document(name=u'Document 1')
        section = self.Section(name=u'Section 1')
        subsection = self.SubSection(
            name=u'Section 1',
            section=section,
            locale='fi'
        )
        document.sections.append(section)
        assert document.locale == 'fi'

    def test_append_second_level_child(self):
        document = self.Document(name=u'Document 1')
        section = self.Section(name=u'Section 1', document=document)
        subsection = self.SubSection(
            name=u'Section 1',
            locale='fi'
        )
        section.subsections.append(subsection)
        assert document.locale == 'fi'
