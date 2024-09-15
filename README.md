AI Assistant on Local Device
------

This is a project to deploy a local AI assistant. This combines [FunAsr](https://github.com/modelscope/FunASR),[ Ollama](https://github.com/ollama/ollama) and [ChatTTS](https://github.com/2noise/ChatTTS).

## Deploy in Windows

### WSL

You need to guarantee the WSL and Windows host can share the docker, this can be opened WSL in the docker desktop.

![](/imgs/docker.png)

Follow this tutorial to deploy FunAsr: [FunASR Realtime Transcribe Service](https://github.com/modelscope/FunASR/blob/main/runtime/docs/SDK_tutorial_online.md).

Download workspace and run the local Asr server:

```bash
$ curl -O https://isv-data.oss-cn-hangzhou.aliyuncs.com/ics/MaaS/ASR/shell/install_docker.sh
$ sudo bash funasr-runtime-deploy-online-cpu-zh.sh install --workspace ./funasr-runtime-resources

# Restart the container
$ sudo bash funasr-runtime-deploy-online-cpu-zh.sh restart
```

In the container, it will download models from the modelscope. After that you should see:

```bash
$ docker ps -a
$ docker exec -it <contianer ID> bash

# In container:
$ watch -n 0.1 "cat FunASR/runtime/log.txt | tail -n 10"
I20240915 21:57:20.544512    56 ct-transformer-online.cpp:21] Successfully load model from /workspace/models/damo/punc_ct-transformer_zh-cn-common-vad_realtime-vocab272727-onnx/model_quant.onnx
I20240915 21:57:20.647238    56 itn-processor.cpp:33] Successfully load model from /workspace/models/thuduj12/fst_itn_zh/zh_itn_tagger.fst
I20240915 21:57:20.648470    56 itn-processor.cpp:35] Successfully load model from /workspace/models/thuduj12/fst_itn_zh/zh_itn_verbalizer.fst
I20240915 21:57:20.648491    56 websocket-server-2pass.cpp:580] initAsr run check_and_clean_connection
I20240915 21:57:20.648558    56 websocket-server-2pass.cpp:583] initAsr run check_and_clean_connection finished
I20240915 21:57:20.648564    56 funasr-wss-server-2pass.cpp:565] decoder-thread-num: 16
I20240915 21:57:20.648567    56 funasr-wss-server-2pass.cpp:566] io-thread-num: 4
I20240915 21:57:20.648571    56 funasr-wss-server-2pass.cpp:567] model-thread-num: 2
I20240915 21:57:20.648572    56 funasr-wss-server-2pass.cpp:568] asr model init finished. listen on port:10095
```

### Ollama

Download and install ollama in windows. After that, run `ollama run llama3.1` in the Powershell to download the model. Then start the ollama server:

```bash
$ ollama serve
...
time=2024-09-15T18:25:35.068+08:00 level=INFO source=images.go:753 msg="total blobs: 5"
time=2024-09-15T18:25:35.069+08:00 level=INFO source=images.go:760 msg="total unused blobs removed: 0"
time=2024-09-15T18:25:35.070+08:00 level=INFO source=routes.go:1172 msg="Listening on 127.0.0.1:11434 (version 0.3.10)"
time=2024-09-15T18:25:35.070+08:00 level=INFO source=payload.go:44 msg="Dynamic LLM libraries [cpu cpu_avx cpu_avx2 cuda_v11 cuda_v12 rocm_v6.1]"
time=2024-09-15T18:25:35.070+08:00 level=INFO source=gpu.go:200 msg="looking for compatible GPUs"
time=2024-09-15T18:25:35.251+08:00 level=INFO source=gpu.go:292 msg="detected OS VRAM overhead" id=GPU-e2aae3a3-4bf5-4f72-0920-b864cb97001c library=cuda compute=8.9 driver=12.6 name="NVIDIA GeForce RTX 4060" overhead="124.9 MiB"
time=2024-09-15T18:25:35.259+08:00 level=INFO source=types.go:107 msg="inference compute" id=GPU-e2aae3a3-4bf5-4f72-0920-b864cb97001c library=cuda variant=v12 compute=8.9 driver=12.6 name="NVIDIA GeForce RTX 4060" total="8.0 GiB" available="6.9 GiB"
```

You can easily follow the Ollama PyPi tutorial to use ollam APIs.

```py
import ollama

# Response streaming can be enabled by setting stream=True, modifying function
# calls to return a Python generator where each part is an object in the stream.
stream = ollama.chat(
    model='llama3.1',
    messages=[{'role': 'user', 'content': 'Why is the sky blue?'}],
    stream=True,
)

for chunk in stream:
    print(chunk['message']['content'], end='', flush=True)
```

### Usage

Run the script:

```bash
$ pip3 install websockets pyaudio ollama
$ python3 funasr_client.py --host "127.0.0.1" --port 10095 --hotword hotword.txt --powershell 1
```

![](/imgs/demo.png)

## Deploy in WSL

The ollama server should start from WSL. Otherwise, the requests from WSL cannot access ollama server. Install ollama in Ubuntu:

```bash
$ curl -fsSL https://ollama.com/install.sh | sh
$ ollama run llama3.1
$ ollama serve
```

> The audio may not work due to the audio card. A way to solve the problem:

```bash
sudo apt-get install python3-pyaudio pulseaudio portaudio19-dev
```

Run the scripts:

```bash
$ python3 funasr_client.py --host "127.0.0.1" --port 10095 --hotword hotword.txt
```

## References

- [Ollama PyPI](https://pypi.org/project/ollama/)
- [Ollama API](https://github.com/ollama/ollama/blob/main/docs/api.md)
