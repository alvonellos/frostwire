'''
Telluride Cloud Video Downloader.
Copyright 2020-2022 FrostWire LLC.
Author: @gubatron

A portable and easy to use yt_dlp wrapper by FrostWire.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''
import os
import signal
import urllib
import yt_dlp
from flask import Flask
from flask import jsonify
from flask import request

DEFAULT_HTTP_PORT = 47999

def query_video(page_url):
    '''
    query_video: queries metadata for the video in page_url using yt_dlp
    '''
    ydl_opts = {'nocheckcertificate' : True,
                'quiet': True,
                'restrictfilenames': True,
                'format': 'bestaudio/best'
               }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(urllib.parse.unquote(page_url), download=False)
        return jsonify(info_dict)

def shutdown_process():
    '''Tries to shutdown the telluride server process with a SIGTERM signal'''
    try:
        os.kill(os.getpid(), signal.SIGTERM)
    except OSError as error:
        print(f"telluride::server::shutdown_process() os.kill failed. Error={error.errno} {error.strerror}")

def start(build_number, http_port_number=DEFAULT_HTTP_PORT):
    '''
    starts the web server.
    Parameters:
    build_number: telluride build number
    http_port_number
    workers_number
    '''
    app = Flask(f'TellurideWebServer_{build_number}')

    def reject_remote_requests():
        #pylint: disable=unused-variable
        if request.remote_addr not in ('127.0.0.1', 'localhost'):
            print(f"telluride::server::start::reject_remote_request: rejecting request from remote_addr={request.remote_addr}")
            return jsonify({'build': build_number, 'message': 'gtfo'}), 403
        return None
    @app.route('/')
    def root_handler():
        '''
        http handler, rejects connections not coming from localhost|127.0.0.1
        url parameters:
        url=<url encoded video page url to obtain json metadata from>
        [shutdown=1] if passed it will shutdown the server
        '''
        gtfo = reject_remote_requests()
        if gtfo is not None:
            return gtfo

        query = request.args.to_dict()
        print(query)
        if 'shutdown' in query and (query['shutdown'] == '1' or query['shutdown'].lower() == 'true'):
            shutdown_process()
            return jsonify({'message':'shutdown'})
        if 'url' in query:
            return query_video(query['url']), 200
        return jsonify({'build' : build_number, 'message': 'no valid parameters received'})

    @app.route('/ping')
    def ping_handler():
        '''
        http ping handler, use this to determine if the server is up.
        rejects connections not coming from localhost|127.0.0.1
        '''
        gtfo = reject_remote_requests()
        if gtfo is not None:
            return gtfo
        return jsonify({'build' : build_number, 'message': 'pong'})

    app.run(host='127.0.0.1', port=http_port_number, threaded=True)
