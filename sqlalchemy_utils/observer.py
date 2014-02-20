"""


::


    class Document(Base):
        __tablename__ = 'document'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))
        locale = sa.Column(sa.String(10))

    class Section(Base):
        __tablename__ = 'section'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))
        locale = sa.Column(sa.String(10))

        document_id = sa.Column(
            sa.Integer, sa.ForeignKey(Document.id)
        )

        document = sa.orm.relationship(Document, backref='sections')

    class SubSection(Base):
        __tablename__ = 'subsection'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))
        locale = sa.Column(sa.String(10))

        section_id = sa.Column(
            sa.Integer, sa.ForeignKey(Section.id)
        )

        section = sa.orm.relationship(Section, backref='subsections')

        @observes('section.document.locale')
        def locale_observer(self, value):
            self.locale = value

"""

class PropertyObserver(object):
    def __init__(self, property, observed_property_path):
        pass

    def generate_property_observer(self, path, attr, property_key):
        """
        Generate SQLAlchemy listener that observes given attr within given
        path space.
        """
        index = path.index(attr)

        @sa.event.listens_for(attr, 'set')
        def receive_attr_set(target, value, oldvalue, initiator):
            if not index:
                setattr(
                    target,
                    property_key,
                    getdotattr(value, str(path[1:]))
                )
            else:
                inversed_path = ~path[0:-1]
                if index == len(path) - 1:
                    entities = getdotattr(
                        target,
                        str(inversed_path)
                    )
                    assigned_value = value
                else:
                    entities = getdotattr(
                        target,
                        str(inversed_path[index:])
                    )
                    assigned_value = getdotattr(value, str(path[(index + 1):]))
                if entities:
                    if not isinstance(entities, list):
                        entities = [entities]
                    for entity in entities:
                        if isinstance(entity, list):
                            for e in entity:
                                setattr(
                                    e,
                                    property_key,
                                    assigned_value
                                )
                        else:
                            setattr(
                                entity,
                                property_key,
                                assigned_value
                            )

        @sa.event.listens_for(attr, 'append')
        def receive_append(target, value, initiator):
            if not index:
                assigned_value = getdotattr(value, str(path[1:]))

                if assigned_value:
                    assigned_value = assigned_value[0]

                if assigned_value:
                    setattr(
                        target,
                        property_key,
                        assigned_value
                    )
            else:
                inversed_path = ~path[0:-1]
                if index == len(path) - 1:
                    entities = getdotattr(
                        target,
                        str(inversed_path)
                    )
                    assigned_value = value
                else:
                    entities = getdotattr(
                        target,
                        str(inversed_path[index:])
                    )
                    assigned_value = getdotattr(value, str(path[(index + 1):]))

                if isinstance(assigned_value, list):
                    assigned_value = assigned_value[0]

                if entities:
                    if not isinstance(entities, list):
                        entities = [entities]
                    for entity in entities:
                        if isinstance(entity, list):
                            for e in entity:
                                setattr(
                                    e,
                                    property_key,
                                    assigned_value
                                )
                        else:
                            setattr(
                                entity,
                                property_key,
                                assigned_value
                            )

    def __call__(self, path):
        path = AttrPath(self.model, path)
        attr = getdotattr(self.model, str(path))

        if isinstance(attr.property, sa.orm.ColumnProperty):
            for attr in path:
                self.generate_property_observer(
                    path,
                    attr,
                    column_key
                )
