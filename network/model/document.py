from neomodel import StructuredNode, StringProperty, RelationshipTo, RelationshipFrom, IntegerProperty


class Classification(StructuredNode):
    short = StringProperty()
    name = StringProperty()
    source = StringProperty(default='web')
    project_id = StringProperty(default='')
    documents = RelationshipFrom('Document', "DEALS_WITH")


class Institution(StructuredNode):
    affiliation_id = StringProperty(unique_index=True)
    name = StringProperty()
    short = StringProperty()
    project_id = StringProperty(default='')
    document = RelationshipFrom('Document', 'WRITTEN_AT')


class Document(StructuredNode):
    eid = StringProperty(unique_index=True)
    year = IntegerProperty()
    citation_count = IntegerProperty(default=0)
    title = StringProperty()
    doi = StringProperty(unique_index=True)
    project_id = StringProperty(default='')
    institution = RelationshipTo(Institution, 'WRITTEN_AT')
    topic = RelationshipTo(Classification, "DEALS_WITH")



