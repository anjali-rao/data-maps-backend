from flask import request

from Common.views import RestApiBuilder
from MapGenerator.schemas import FileUploaderSchema


class FileUploader(RestApiBuilder):
    schema = dict(
        v1=dict(
            post=FileUploaderSchema()
        )
    )
    def v1_post(self, api_version):
        self.schematized_request = self.load_request(
            schema=self.schema[api_version][self.request_type],
            request=request,
            look_for_files = True,
            auth=False
        )
        import pdb; pdb.set_trace()
        #read file
        #convert to json
        #structure file
        #save to db
        pass
