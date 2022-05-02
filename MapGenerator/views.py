from Common.views import RestApiBuilder
from MapGenerator.schemas import FileUploaderSchema


class FileUploader(RestApiBuilder):
    schema = dict(
        v1=dict(
            post=FileUploaderSchema()
        )
    )
    def v1_post(self, api_version):
        #read file
        #convert to json
        #structure file
        #save to db
        pass
