from weakref import WeakKeyDictionary

from pytest import raises
import six
import sqlalchemy as sa
from sqlalchemy.ext.hybrid import hybrid_property
from tests import TestCase


copied_attributes = WeakKeyDictionary()


class ColumnCopy(object):
    def __init__(self, path, column_name=None):
        self.path = path
        self.column_name = column_name


@sa.event.listens_for(sa.orm.mapper, 'mapper_configured')
def save_column_copies(mapper, class_):
    for key, value in six.iteritems(class_.__dict__):
        if isinstance(value, ColumnCopy):
            copied_attributes[class_] = value
            if not value.column_name:
                value.column_name = key
            value.column_key = key


@sa.event.listens_for(sa.orm.mapper, 'after_configured')
def configure_column_copies():
    for class_, value in six.iteritems(copied_attributes):
        path = value.path
        if isinstance(path, six.string_types):
            parts = path.split('.')
            attr = getattr(class_, parts[0])
            prop = attr.property
            columns = prop.mapper.columns

            if len(parts) > 1:
                column_name = parts[1]
            else:
                column_name = value.column_name

            if column_name not in columns:
                raise Exception(
                    'Unknown column name %s given.' % column_name
                )

            column_key = value.column_key

            if isinstance(getattr(class_, column_key), ColumnCopy):
                setattr(class_, column_key, columns[column_name].copy())

                @sa.event.listens_for(attr, 'set')
                def receive_attr_set(target, value, oldvalue, initiator):
                    setattr(
                        target,
                        column_key,
                        getattr(value, column_key)
                    )

                if prop.backref:
                    rel_class = attr.property.mapper.class_
                    backref_attr = getattr(
                        rel_class,
                        column_name
                    )
                    if isinstance(prop.backref, tuple):
                        backref_name = prop.backref[0]
                    else:
                        backref_name = prop.backref

                    @sa.event.listens_for(backref_attr, 'set')
                    def receive_backref_column_set(
                        target,
                        value,
                        oldvalue,
                        initiator
                    ):
                        for entity in getattr(target, backref_name):
                            setattr(entity, column_name, value)


@sa.event.listens_for(sa.orm.mapper, 'init')
def receive_init(target, args, kwargs):
    if target.__class__ in copied_attributes:
        column = copied_attributes[target.__class__]
        path = column.path
        if isinstance(path, six.string_types):
            parts = path.split('.')
            if parts[0] in kwargs:
                relation_entity = kwargs[parts[0]]
                if len(parts) > 1:
                    column_name = parts[1]
                else:
                    column_name = value.column_name
                value = getattr(relation_entity, column_name)
                kwargs.setdefault(column.column_key, value)


class SimpleColumnCopyTestCase(TestCase):
    def test_copies_column_definition(self):
        table = self.Article.__table__
        assert 'locale' in table.c
        assert table.c.locale.default
        assert isinstance(table.c.locale.type, sa.Unicode)

    def test_copies_column_value(self):
        category = self.Category(locale='en')
        article = self.Article(category=category)
        assert article.locale == 'en'

    def test_attr_setter_listener(self):
        category = self.Category(locale='en')
        article = self.Article()
        article.category = category
        assert article.locale == 'en'

    def test_attr_setter_backref_listener(self):
        category = self.Category(locale='en')
        article = self.Article()
        article.category = category
        category.locale = 'fi'
        assert article.locale == 'fi'

    def test_init_without_kwargs(self):
        article = self.Article()
        assert article.locale is None


class TestColumnCopyWithStringBackref(SimpleColumnCopyTestCase):
    def create_models(self):
        class Category(self.Base):
            __tablename__ = 'category'
            id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
            description = sa.Column(sa.UnicodeText)
            locale = sa.Column(sa.Unicode(10), default=u'en')

        class Article(self.Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
            description = sa.Column(sa.UnicodeText)
            locale = ColumnCopy('category.locale')
            category_id = sa.Column(sa.Integer, sa.ForeignKey(Category.id))

            category = sa.orm.relationship(
                Category,
                backref='articles'
            )

        self.Article = Article
        self.Category = Category


class TestColumnCopyWithObjectBackref(SimpleColumnCopyTestCase):
    def create_models(self):
        class Category(self.Base):
            __tablename__ = 'category'
            id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
            description = sa.Column(sa.UnicodeText)
            locale = sa.Column(sa.Unicode(10), default=u'en')

        class Article(self.Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
            description = sa.Column(sa.UnicodeText)
            locale = ColumnCopy('category.locale')
            category_id = sa.Column(sa.Integer, sa.ForeignKey(Category.id))

            category = sa.orm.relationship(
                Category,
                backref=sa.orm.backref('articles')
            )


        self.Article = Article
        self.Category = Category
