from marshmallow import Schema, fields


class FileUploaderSchema(Schema):
    files = fields.Raw()
