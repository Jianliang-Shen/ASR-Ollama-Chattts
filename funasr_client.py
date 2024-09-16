# -*- encoding: utf-8 -*-
import os
import websockets, ssl
import asyncio
import argparse
import json
from ollama import Client
import logging
from multiprocessing import Process

logging.basicConfig(level=logging.ERROR)

parser = argparse.ArgumentParser()
parser.add_argument("--host", type=str, default="localhost", required=False, help="host ip, localhost, 0.0.0.0")
parser.add_argument("--port", type=int, default=10095, required=False, help="grpc server port")
parser.add_argument("--chunk_size", type=str, default="5, 10, 5", help="chunk")
parser.add_argument("--chunk_interval", type=int, default=10, help="chunk")
parser.add_argument("--hotword", type=str, default="", help="hotword file path, one hotword perline (e.g.:阿里巴巴 20)")
parser.add_argument("--words_max_print", type=int, default=10000, help="chunk")
parser.add_argument("--use_itn", type=int, default=1, help="1 for using itn, 0 for not itn")
parser.add_argument("--powershell", type=int, default=0, help="work under powershell")
parser.add_argument("--llamahost", type=str, default="0.0.0.0:11434", help="Ollama server")
parser.add_argument("--llm_model", type=str, default="llama3.1", help="Ollama model")

args = parser.parse_args()
args.chunk_size = [int(x) for x in args.chunk_size.split(",")]

msg_cnt = 0
msg_end = False
text_print = ""
text_print_2pass_online = ""
text_print_2pass_offline = ""
messages = []

async def record_microphone():
    is_finished = False
    import pyaudio
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    chunk_size = 60 * args.chunk_size[1] / args.chunk_interval
    CHUNK = int(RATE / 1000 * chunk_size)

    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    # hotwords
    fst_dict = {}
    hotword_msg = ""
    if args.hotword.strip() != "":
        f_scp = open(args.hotword, encoding='utf-8')
        hot_lines = f_scp.readlines()
        for line in hot_lines:
            words = line.strip().split(" ")
            if len(words) < 2:
                print("Please checkout format of hotwords")
                continue
            try:
                fst_dict[" ".join(words[:-1])] = int(words[-1])
            except ValueError:
                print("Please checkout format of hotwords")
        hotword_msg=json.dumps(fst_dict)

    use_itn=True
    if args.use_itn == 0:
        use_itn=False
    
    message = json.dumps({"mode": "2pass", "chunk_size": args.chunk_size, "chunk_interval": args.chunk_interval,
                          "wav_name": "microphone", "is_speaking": True, "hotwords":hotword_msg, "itn": use_itn})
    await websocket.send(message)
    
    if args.powershell:
        os.system('powershell -command "Clear-Host"')
    else:
        os.system('clear')

    print('---------------------------------------------------------------')
    print('Welcome to use local AI assistant. You can say: Tell me a joke!')
    print('---------------------------------------------------------------')
    print("User: ")

    while True:
        data = stream.read(CHUNK)
        message = data
        await websocket.send(message)
        await asyncio.sleep(0.005)

async def wait_end_and_send_to_ollama():
    while True:
        global msg_cnt, msg_end, text_print, text_print_2pass_online, text_print_2pass_offline

        cur_cnt = msg_cnt
        await asyncio.sleep(2)
        if (msg_cnt == cur_cnt and text_print):
            prompt = text_print
            assistant_log = ""

            # Clear ASR texts
            text_print_2pass_online = ""
            text_print_2pass_offline = ""
            text_print = ""

            print("\n\nAssistant: ")
            messages.append({'role': 'user', 'content': prompt})
            client = Client(host='http://' + args.llamahost)
            stream = client.chat(model=args.llm_model, messages=messages, stream=True)
            for chunk in stream:
                assistant_log += chunk['message']['content']
                print(chunk['message']['content'], end='', flush=True)
            messages.append({'role': 'assistant', 'content': assistant_log})
            assistant_log = ""
            print("\n-------------------------------------------------------------")
            print("User: ")


async def message(id):
    global websocket

    try:
       while True:
            global msg_cnt, msg_end, text_print, text_print_2pass_online, text_print_2pass_offline

            meg = await websocket.recv()
            msg_cnt += 1

            meg = json.loads(meg)
            text = meg["text"]

            if 'mode' not in meg:
                continue
            else:
                if meg["mode"] == "2pass-online":
                    text_print_2pass_online += "{}".format(text)
                    text_print = text_print_2pass_offline + text_print_2pass_online
                else:
                    text_print_2pass_online = ""
                    text_print = text_print_2pass_offline + "{}".format(text)
                    text_print_2pass_offline += "{}".format(text)
                text_print = text_print[-args.words_max_print:]

                # Fix: Delete the laster punctuation mark in the laster sentence
                if (text_print[0] in ["。", "，", "？", "！"]):
                    text_print = text_print[1:]

                print("\r" + text_print, end='')

    except Exception as e:
            print("Exception:", e)

async def ws_client(id, chunk_begin, chunk_size):
    chunk_begin=0
    chunk_size=1
    global websocket
    
    for i in range(chunk_begin,chunk_begin+chunk_size):

        ssl_context = ssl.SSLContext()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        uri = "wss://{}:{}".format(args.host, args.port)

        print("connect to", uri)
        async with websockets.connect(uri, subprotocols=["binary"], ping_interval=None, ssl=ssl_context) as websocket:
            task1 = asyncio.create_task(record_microphone())
            task2 = asyncio.create_task(message(str(id)+"_"+str(i))) #processid+fileid
            task3 = asyncio.create_task(wait_end_and_send_to_ollama())
            await asyncio.gather(task1, task2, task3)
    exit(0)

def one_thread(id, chunk_begin, chunk_size):
    asyncio.get_event_loop().run_until_complete(ws_client(id, chunk_begin, chunk_size))
    asyncio.get_event_loop().run_forever()

if __name__ == '__main__':
    p = Process(target=one_thread, args=(0, 0, 0))
    p.start()
    p.join()
    print('end')
