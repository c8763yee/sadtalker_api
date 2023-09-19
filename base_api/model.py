from flask_restx import fields
from werkzeug.datastructures import FileStorage
from . import api_ns

upload_parser = api_ns.parser()
upload_parser.add_argument(
    'source_image', location='files', type=FileStorage, required=True)

upload_parser.add_argument(
    'driven_audio', location='files', type=FileStorage, required=True)


class BaseModel:
    base_content_model = api_ns.model(
        "base_content",
        {
            "message": fields.String(required=True, description="message"),
        },
    )
    base_output_model = api_ns.model(
        "base_output",
        {
            "status": fields.String(required=True, description="status"),
        },
    )
    error_model = api_ns.model(
        "bad_request",
        {
            "status": fields.String(required=True, description="error", default="error"),
            "content": fields.Nested(
                base_content_model,
                required=True,
                description="content of error message",
            ),
        }
    )


class APIModel(BaseModel):
    upload_content_model = api_ns.model('UploadContent', {
        "task_id": fields.String(required=False, description="ID of the request"),
    })

    upload_output_model = api_ns.clone(
        "UploadOutput", BaseModel.base_output_model, {
            "content": fields.Nested(
                upload_content_model,
                required=True,
                description="content of upload result",
            ),
        }
    )

    inference_input_model = api_ns.model('InferenceInput', {
        "task_id": fields.String(required=True, description="ID of the request"),
    })
    inference_content_model = api_ns.clone(
        "InferenceContent", BaseModel.base_content_model,
    )
    inference_output_model = api_ns.clone(
        "InferenceOutput", BaseModel.base_output_model, {
            "content": fields.Nested(
                inference_content_model,
                required=True,
                description="content of inference result",
            ),
        }
    )

    status_input_model = api_ns.model(
        "status_input",
        {
            "task_id": fields.String(required=True, description="task_id"),
        },
    )

    task_info_model = api_ns.model(
        "info",
        {
            "current": fields.Integer(required=True, description="current", default=0),
            "total": fields.Integer(required=True, description="total", default=0),
        },
    )
    status_input_model = api_ns.model(
        "status_input",
        {
            "task_id": fields.String(required=True, description="task_id"),
        },
    )
    status_output_content = api_ns.clone(
        "status_output_content",
        BaseModel.base_content_model,
        {
            "task_status": fields.String(description="task_status"),
            "info": fields.Nested(
                task_info_model,
                description="task_info",
            ),
            "task_result": fields.String(
                required=False, description="task_result", default=""
            ),
        },
    )
    status_output_model = api_ns.clone(
        "status_output",
        BaseModel.base_output_model,
        {
            "content": fields.Nested(
                status_output_content,
                required=True,
                description="content of /api/status",
            ),
        },
    )
