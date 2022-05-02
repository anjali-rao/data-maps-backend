import json
from datetime import datetime
from flask import request, make_response, jsonify

from bson import ObjectId
from flask.views import MethodView

from config import Config


class MongoCollectionsInterface:

    @staticmethod
    def query_builder(keys, base):
        """
        only exception to the concept defined above
        this is used to build queries which are then used to query collections
        for documents
        """
        query = dict()
        for k in keys:
            query[k] = base[k]
        return query

    @staticmethod
    def insert_or_404(collection_name, error_message, post_obj, query, api_version):
        doc_exist = collection_name.find_one(query)
        if doc_exist:
            raise Exception(error_message)
        post_obj["api_version"] = api_version
        post_obj["cd"] = datetime.now()
        post_obj['_id'] = collection_name.insert_one(post_obj).inserted_id
        return post_obj

    @staticmethod
    def find_or_404(collection_name, error_message, query, exclude=None, **kwargs):
        doc = collection_name.find_one(query, exclude)
        if not doc:
            raise Exception(error_message)
        return doc

    @staticmethod
    def find_all_paginated(collection_name, query, exclude=None, sort=None, skip=0, limit=0):
        documents = list()
        if sort:
            '''
            Eg: sort = [("cd", "1")]
            '''
            docs = collection_name.find(query, exclude).sort(sort).skip(skip).limit(limit)
        else:
            docs = collection_name.find(query, exclude).skip(skip).limit(limit)
        for doc in docs:
            documents.append(doc)

        return documents

    @staticmethod
    def get_count(collection_name, query):
        docs_count = collection_name.count_documents(query)
        return docs_count

    @staticmethod
    def find_all(collection_name, query, exclude=None, sort=None):
        documents = list()
        if sort:
            '''
            Eg: sort = [("cd", 1)]
            '''
            docs = collection_name.find(query, exclude).sort(sort)
        else:
            docs = collection_name.find(query, exclude)

        for doc in docs:
            documents.append(doc)

        return documents

    @staticmethod
    def find_one_and_replace(collection_name, query, obj):
        return collection_name.find_one_and_replace(query, obj)

    @staticmethod
    def find_or_none(collection_name, query, exclude=None, sort=None):
        if sort:
            return collection_name.find_one(query, exclude, sort=sort)
        return collection_name.find_one(query, exclude)

    @staticmethod
    def insert(collection_name, post_obj, api_version):
        post_obj["cd"] = datetime.now()
        post_obj["api_version"] = api_version
        obj_id = collection_name.insert_one(post_obj).inserted_id
        return collection_name.find_one({"_id": ObjectId(obj_id)})

    @staticmethod
    def insert_or_return_id(collection_name, query, post_obj, api_version):
        doc_exist = collection_name.find_one(query)
        if doc_exist:
            return str(doc_exist["_id"])
        post_obj["api_version"] = api_version
        post_obj["cd"] = datetime.now()
        post_obj['_id'] = collection_name.insert_one(post_obj).inserted_id
        return str(post_obj["_id"])

    @staticmethod
    def quick_insert(collection_name, post_obj):
        post_obj["cd"] = datetime.now()
        return collection_name.insert(post_obj, w=0, j=False)

    @staticmethod
    def delete(collection_name, query):
        return collection_name.delete_one(query)

    @staticmethod
    def delete_many(collection_name, query):
        return collection_name.delete_many(query)

    @staticmethod
    def text_search(collections_name, query):
        return collections_name.find({"$text": {"$search": query}})

    @staticmethod
    def update_dict_list(collection_name, query, update_data, query_type):
        if query_type == 'push':
            return collection_name.update_one(query, {"$push": update_data}, upsert=True)
        elif query_type == 'set':
            return collection_name.update_one(query, {"$set": update_data}, upsert=True)
        else:
            raise Exception("Incorrect update dict query type")

    @staticmethod
    def insert_or_update(collection_name, query, update_data, query_type):
        upsert = True
        if query_type not in ["$set", "$push"]:
            raise Exception("Incorrect update dict query type")

        return collection_name.update_one(query, {query_type: update_data}, upsert=upsert)


class SchematizedAPIInterface:

    @staticmethod
    def load_obj(schema, input_dict):

        errors = schema.validate(input_dict)
        if errors:
            raise Exception(json.dumps(errors))
        try:
            return schema.load(input_dict)
        except:
            message = 'A Raw field in %s is acting funny. Please contact admin' % str(schema)
            raise Exception(message)

    def parse_request(self, request, look_for_files=False, auth=False, de_tokenize=False, auth_key=None):
        """
        we use parsed request to parse all incoming requests
        parse_request is designed to be flexible in nature
        but it also enforces some rules on request methods
        GET
            1. cannot send a body, only query strings
            2. tokenized data can only be sent in get as query string with ?tokenized_data=
            as the variable
        POST / PUT
            1. can only send a body, no query strings
            2. can send a form or a application/json object
            3. allows for a single file upload, the file is returned a
            filetype object which the user can handle accordingly
        """
        parsed_request = dict()

        if request.method == 'GET':
            parsed_request = dict(request.args)
        elif request.method in ['POST', 'PUT']:
            parsed_request = dict(request.form)
            if look_for_files:
                if len(request.files) >= 1:
                    parsed_request['files'] = request.files.to_dict(flat=False)
                else:
                    parsed_request['files'] = list()
        else:
            message = '%s method is not allowed on %s' % (str(request.method), str(request.path))
            raise Exception(message)

        return parsed_request

    def load_request(self, schema, request, look_for_files=False, auth=False, de_tokenize=False, auth_key=None):
        """
        we are loading a request through this function

        you will find the use of this function throughout the codebase
        """
        parsed_request = self.parse_request(
            request=request,
            look_for_files=look_for_files,
            auth=auth,
            de_tokenize=de_tokenize,
            auth_key=auth_key,
        )
        return self.load_obj(
            schema=schema,
            input_dict=parsed_request)


    def single_schema_response(self, schema, request):
        load_request = self.load_request(
            schema=schema,
            request=request)
        response = self.dump_response(
            schema=schema,
            obj=load_request,
            message="Schematized response for %s using %s" % (str(request.path), str(schema))
        )
        return response

    @staticmethod
    def dump_response(message, success, schema=None, obj=None, error_code=None):
        """
        just like schema de serializes an object using load, it uses dump
        to serialize an object into a json

        pre_dump, post_dump functionalities are available along with validations
        just like load
        """
        response = dict(
            success=success,
            message=message)
        if error_code is not None:
            response['error_code'] = error_code
        else:
            response['data'] = schema.dump(obj)
        return response

    @staticmethod
    def schemaless_response(message, success, obj=None, error_code=None):
        """
        this function is developed as a failsafe..this should be avoided
        this allows you to return a json to api
        without dumping through a schema

        this should be avoided as a hygiene engineering practice
        lazy engineering should be avoided
        """
        response = dict(
            success=success,
            message=message)
        if error_code is not None:
            response['error_code'] = error_code
        else:
            response['data'] = obj
        return response


class RestApiBuilder(MethodView, SchematizedAPIInterface, MongoCollectionsInterface):

    def __init__(self):
        self.request_type = str(request.method).lower()
        self.schematized_request = None
        self.response = None
        self.api_version = request.url.split("/")[len(request.url.split("/")) - 2]
        self.look_for_files = vars(self).get("look_for_files", False)
        self.de_tokenize = vars(self).get("de_tokenize", False)

        try:
            self.schema[self.api_version][self.request_type]
        except Exception as e:
            raise Exception(
                "Please configure schema.api_version.request_method. None, if not required.")
        self.schema_class = self.schema[self.api_version][self.request_type]
        self.auth = self.schema[self.api_version].get("auth", False)
        if self.auth is not False:
            self.auth_key = self.schema[self.api_version]["auth"].get("key", Config.APP_SECRET)
        self.schema_init()

    def schema_init(self):

        self.schematized_request = self.parse_request(
            request = request,
            look_for_files = self.look_for_files,
            de_tokenize = self.de_tokenize
        )
        if self.schema_class is not None:
            self.schematized_request = self.load_obj(
                input_dict = self.schematized_request,
                schema = self.schema_class
            )
        if self.auth is not False:
            self.schematized_request["user_id"] = self.user_auth(
                request = request,
                parsed_request = self.schematized_request,
                auth_key = self.auth_key
            )

        self.response = self.schemaless_response(
            message = "data.request is the response from the version function. default data.request == self.schematized_request.",
            success = True,
            obj = dict(
                request = self.schematized_request
            )
        )


    def dispatcher(self):
        response, status_code = getattr(self, self.api_version + "_" + self.request_type)(
            api_version = self.api_version)
        if response is None:
            response = self.response
            status_code = 200

        if type(status_code) == str and status_code == "pdf":
            resp = make_response(response.getvalue())
            resp.mimetype = 'application/pdf'
            resp.headers['Content-Disposition'] = 'attachment; filename=invoice.pdf'
            return resp
        return make_response(
            jsonify(response),
            status_code
        )

    def get(self, api_version):
        return self.dispatcher()

    def post(self, api_version):
        return self.dispatcher()

    def put(self, api_version):
        return self.dispatcher()

    def delete(self, api_version):
        return self.dispatcher()

    def patch(self, api_version):
        return self.dispatcher()

