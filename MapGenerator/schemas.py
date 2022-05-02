from marshmallow import Schema, fields


class FileUploaderSchema(Schema):
    file = fields.Raw(required = True)