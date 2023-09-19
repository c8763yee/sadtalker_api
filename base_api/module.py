import os
from base64 import b64encode
from shutil import rmtree
from subprocess import run
from uuid import uuid4

from flask import current_app as app
from moviepy.editor import (CompositeVideoClip, TextClip, VideoFileClip,
                            concatenate_videoclips)
from moviepy.video.tools.subtitles import SubtitlesClip
from pydub import AudioSegment
from werkzeug.datastructures import FileStorage

from config import Config
from inference import args, infer
from model import Status


def merge_video(task_id: str):
    work_dir = os.path.join('upload', task_id)
    output_dir = 'output'

    os.makedirs(output_dir, exist_ok=True)

    output_filepath = os.path.join(output_dir, f"{task_id}.mp4")
    splited_video_path = os.path.join(
        work_dir,
        "splited",
        "video",
    )

    video_list = list(
        filter(lambda x: x.endswith(".mp4"), os.listdir(splited_video_path))
    )
    if video_list == []:
        app.logger.error(f"Video list is empty. (ID: {task_id})")
        return False

    video_list.sort(key=lambda x: int(x.split(".")[0]))
    output = map(
        lambda x: os.path.join(splited_video_path, x),
        video_list,
    )
    concat_list = list(map(VideoFileClip, output))
    result_video = concatenate_videoclips(concat_list)
    try:
        result_video.write_videofile(
            output_filepath,
            threads=1,
            codec="libx264")

    except IndexError:
        result_video = result_video.subclip(
            0, result_video.duration - 1 / result_video.fps)

        result_video.write_videofile(
            output_filepath,
            threads=1,
            codec="libx264")
    for video in concat_list:
        video.close()
    return True


def split_audio(
    input_audio: str,  # input_path: /xxx/.../xxx.mp3
    output_dir: str = "splited/audio",  # output_dir: xxx/<audio_id>
    interval: int = Config.INTERVAL,
    func: callable = None,
):
    # output_path: /<root_path>/<output_dir>/<counter>.mp3
    audio = AudioSegment.from_mp3(input_audio)
    counter = 0
    start_ms = 0
    interval_ms = interval * 1000

    while start_ms < len(audio):
        splited_audio = audio[start_ms: start_ms + interval_ms]
        output_path = os.path.join(output_dir, f"{counter}.mp3")
        splited_audio.export(output_path, format="mp3")

        if func:
            func(output_path)

        start_ms += interval_ms
        counter += 1
    return counter


def generate_lipsync(task_id: str, source_image: str, driven_audio: str):
    app.logger.info(source_image)
    app.logger.info(driven_audio)
    app.logger.info(f"Generating video...(ID: {task_id})")
    for splited in ("audio", "video"):
        rmtree(os.path.join('upload', task_id,
               "splited", splited), ignore_errors=True)
        os.makedirs(os.path.join('upload', task_id,
                    "splited", splited), exist_ok=True)

    audio_pieces_nums = split_audio(
        input_audio=driven_audio,
        output_dir=os.path.join('upload', task_id, "splited", "audio"),
        interval=Config.INTERVAL,
    )

    args.driven_audio = driven_audio
    args.source_image = source_image

    app.logger.info(f"Generating video...(ID: {task_id})")
    args.result_dir = os.path.join('upload', task_id, "splited", "video")
    for index in range(audio_pieces_nums):
        args.driven_audio = os.path.join(
            'upload', task_id, "splited", "audio", f"{index}.mp3")
        os.replace(infer(args).replace(os.sep, "/"),
                   os.path.join(args.result_dir, f"{index}.mp4"))

    return merge_video(task_id)


class APIModule:
    @staticmethod
    def upload_file(source_image: FileStorage, driven_audio: FileStorage, **kwargs):
        task_id = str(uuid4())
        valid_extension = {'jpg', 'jpeg', 'png', 'mp3'}
        if not (source_image.filename or driven_audio.filename):
            return dict(status="error", content=dict(message="no all files are uploaded"))

        image_extension = source_image.filename.split('.')[-1]
        audio_extension = driven_audio.filename.split('.')[-1]
        if image_extension not in valid_extension or audio_extension not in valid_extension:
            return dict(status="error", content=dict(message="invalid file type"))

        try:
            os.makedirs(f"upload/{task_id}")
        except FileExistsError:
            task_id = str(uuid4())
            os.makedirs(f"upload/{task_id}")

        Status.register_data(
            dict(task_id=task_id),
            task_id=task_id,
            status="PENDING",
        )
        source_image.save(f"upload/{task_id}/source_image.{image_extension}")
        driven_audio.save(f"upload/{task_id}/driven_audio.{audio_extension}")
        return dict(status="success", content=dict(message="success", task_id=task_id))

    @staticmethod
    def inference(task_id: str, **kwargs):
        if not os.path.exists(f"upload/{task_id}"):
            return dict(status="error", content=dict(message="invalid task id"))
        for extension in ['jpg', 'jpeg', 'png']:
            image_filename = f"upload/{task_id}/source_image.{extension}"
            if os.path.exists(image_filename):
                break
        else:
            return dict(status="error", content=dict(message="no source image found"))

        audio_filename = f"upload/{task_id}/driven_audio.mp3"
        if not os.path.exists(audio_filename):
            return dict(status="error", content=dict(message="no driven audio found"))
        Status.register_data(
            {},
            task_id=task_id,
            status="PROGRESS",
        )

        if generate_lipsync(
                task_id=task_id,
                source_image=image_filename,
                driven_audio=audio_filename) is False:
            Status.register_data(
                dict(task_id=task_id),
                status="ERROR",
                error="failed to generate video",
            )
            return dict(status="error", content=dict(message="failed to generate video"))

        Status.register_data(
            dict(task_id=task_id),
            status="SUCCESS",
            result=f"output/{task_id}.mp4",
        )

        return dict(status="success", content=dict(message="success"))

    @staticmethod
    def status(task_id: str, **kwargs):
        task = Status.query.filter_by(task_id=task_id).first()
        if task is None:
            return dict(status="error", content=dict(message="invalid task id"))
        info = dict(
            current=task.current,
            total=task.total
        )
        content = dict(task_status=task.status, info=info)
        if task.status == "SUCCESS":
            content["result"] = task.result

        return dict(status="success", content=content)
