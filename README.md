# AWS Elemental MediaTailor - Automatic Ads Profiling - Black Frames

This repository supports the Media Blog article [Monetizing your Media Content with AWS Elemental MediaTailor and Computer Vision](https://aws.amazon.com/blogs/media/monetizing-your-media-content-with-media-tailor).
  
The goal of this repository is to deploy a minima pipeline to ingest, analyze
stream, and automatically insert ads in media contents.


## Repository Structure
```bash
.
├── assets/
├── cloudformation/
│ ├── dynamodb.yml
│ ├── fanout-lambda.yml
│ ├── inputs.yml
│ ├── main.yml
│ ├── media-lambda.yml
│ ├── tasks.yml
│ └── vpc.yml
├── functions/
│ ├── fanout-lambda/
│ │ ├── fanout-lambda.py
│ │ ├── jobTemplate.json
│ │ └── Makefile
│ └── media-lambda/
│     ├── Makefile
│     └── media-lambda.py
├── player/
│ └── index.template.html
│ └── deploy.sh
│ └── env.example
│ └── README.md
├── tasks/
│ └── black-frames/
│     ├── config.env
│     ├── deploy.env
│     ├── Dockerfile
│     ├── Makefile
│     ├── README.md
│     ├── task/
│     │ ├── task.py
│     │ └── utils.py
│     └── version.sh
├── install.sh
└── README.md

```

**assets/** includes some static files that are used by the deployment script or to run tests.

**cloudformation/** includes all of the templates needed to deploy the solution.  The stack is configured as a nested-stack. All of the components are deployed via the **main.yml** template.

**functions/** includes the code for the lambda functions deployed with the solution:

* **fanout-lambda/** is the function that starts the MediaConvert job, registers the media asset in DynamoDB, and bootstraps the analysis task on Fargate. **fanout-lambda.py** is the script that includes the Lambda handler, while **jobTemplate.json** is the MediaConvert job template that is used by the Lambda Function.
* **media-lambda/** is the function that creates a MediaTailor Campaign and adds the relative metadata to the DynamoDB table.

**player/** includes a minimal html page that allows the user to stream a sample ads-featured HLS stream.  

**tasks/** is the folder that hosts the analysis tasks. At the time of writing, the repositorie only includes **black-frames/**, the task which finds long sequences of black frames within the media asset.

* **config.env** is used by the Makefile to configure the task at runtime. This can be useful to test the task locally.
* **deploy.env** is used by the deployment script to configure the Fargate Task at deployment time. 
* **README.md** provides further information about the task.
* **Dockerfile** configures the Docker container that will be deployed to ECR and used by ECS Fargate to perform the analysis.
* **task/task.py** is the container entrypoint while **task/utils.py** includes utility functions for the task.

**install.sh** is the script that orchestrates the deployment of the AWS infrastructure.


## Deployment
To deploy the stack, create a file named `.env` in the root folder.  
Populate the file with the following 

```bash
STACK_NAME=automatic-ads-profiling-dev
CFN_BUCKET=<insert-cfn-bucket-here>
AWS_DEFAULT_REGION=eu-west-1

```
In a shell, run 
```bash
./install.sh
```

## Acknowledgements

**Big Buck Bunny** is a 2008 short, open-source film made by the Blender Institute.  
A short clip of this video has been used to test the end-to-end processing and
it's available in the `./assets` folder.  
Big Buck Bunny is a 2008 &copy; copyright of [Blender Foundation](http://www.bigbuckbunny.org/).

## License
The content of this repository is released under MIT-0 license, exception made for what described in the paragraph **Legal Notice about the usage of FFmpeg**.  
You can find more details in the `LICENSE` file.  

## Legal Notice about the usage of FFmpeg

This software uses code of <a href=http://ffmpeg.org>FFmpeg</a> licensed under
the <a href=http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html>LGPLv2.1</a>
and its source can be downloaded <a href="/tasks/black-frames/ffmpeg/ffmpeg-4.2.2.tar.bz2">here</a>.   

A copy of the LGPLv2.1 is also available in this repository [here](/tasks/black-frames/ffmpeg/LICENSE).  

### Compilation Process
FFmpeg source code has **NOT** been modified for this software.  
FFmpeg has been compiled with the following configuration.  

```
ffmpeg version 4.2.2 Copyright (c) 2000-2019 the FFmpeg developers
  built with gcc 7 (Ubuntu 7.5.0-3ubuntu1~18.04)
  configuration: --disable-debug --disable-doc --disable-ffplay --prefix=/opt/ffmpeg --extra-cflags=-I/opt/ffmpeg/include --extra-ldflags=-L/opt/ffmpeg/lib
  libavutil      56. 31.100 / 56. 31.100
  libavcodec     58. 54.100 / 58. 54.100
  libavformat    58. 29.100 / 58. 29.100
  libavdevice    58.  8.100 / 58.  8.100
  libavfilter     7. 57.100 /  7. 57.100
  libswscale      5.  5.100 /  5.  5.100
  libswresample   3.  5.100 /  3.  5.100
```
FFmpeg has been compiled **without** `--enable-gpl` and `--enable-nonfree` in order to comply with the terms of [LGPLv2.1](/tasks/black-frames/ffmpeg/LICENSE).  
You can have further details on the compilation process in the [Dockerfile](/tasks/black-frames/Dockerfile)  

### How does this software make use of FFmpeg?
FFmpeg is dynamically linked to the software in this repository.  
The `ffmpeg` cli tool is invoked via a python script to analyse a video file to find black frames.  
The exact filter used in the analysis is [vf_blackdetect.c](https://github.com/FFmpeg/FFmpeg/blob/release/4.2/libavfilter/vf_blackdetect.c) covered by [LGPLv2.1](tasks/black-frames/ffmpeg/LICENSE).
FFmpeg is therfore used to decode the video and run the mentioned filter on the decoded frames.  

The exact spot in which the command is invoked is `tasks/black-frames/task/task.py`, lines 38-54. 
The output of the invocation of `ffmpeg` is then parsed to produce a VMAP file.