from flask_restx import Resource

from . import api_ns
from .model import upload_parser, APIModel
from .module import APIModule


@api_ns.route('/upload')
class UploadFile(Resource):
    @api_ns.expect(upload_parser)
    @api_ns.marshal_with(APIModel.upload_output_model)
    def post(self):
        return APIModule.upload_file(**upload_parser.parse_args())


@api_ns.route('/inference')
class Inference(Resource):
    @api_ns.expect(APIModel.inference_input_model)
    @api_ns.marshal_with(APIModel.inference_output_model)
    def post(self):
        return APIModule.inference(**api_ns.payload)


@api_ns.route('/status')
class Status(Resource):
    @api_ns.expect(APIModel.status_input_model)
    @api_ns.marshal_with(APIModel.status_output_model)
    def post(self):
        return APIModule.status(**api_ns.payload)
