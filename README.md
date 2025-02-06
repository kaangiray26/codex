# codex :octocat:

Question Answering on PDF Documents

![](images/app.png)

## About

This is a local web application that allows users to upload PDF documents and ask questions about the document to a voice assistant. The voice assistant will then answer the question based on the contents of the document.

## Setup

Here are the steps to run the application locally, on a Linux machine:

```bash
git clone git@github.com:kaangiray26/codex.git
cd codex
python3 -m venv .env
source .env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Usage

Once the setup is complete, you can run the application inside the virtual environment:

```bash
fastapi run
```

This will start the web server and the web application will be available at [localhost:8000/app](http://localhost:8000/app). Open the link in your browser to access the application.

Once the application is running, click on the "Upload" or "Browse files" button to upload a PDF document. This will spawn a bot in your browser that will start taking questions from you. You can ask questions by simply dictating them to the bot. Answers will be spoken back to you with subtitles and citations on the screen.

## Development

This project is built with **pipecat** and **LlamaIndex** mainly. Other components of this project include the [MarkItDown](https://github.com/microsoft/markitdown) library to convert PDF documents to markdown format real fast. The assistant uses several online services for STT, TTS and LLM inference. These services are listed as follows:

- [Deepgram](https://deepgram.com/) for STT
- [OpenAI](https://openai.com/) for LLM
- [ElevenLabs](https://elevenlabs.io/) for TTS

## Resources:

- [pipecat](https://github.com/pipecat-ai/pipecat)
- [LlamaIndex](https://docs.llamaindex.ai/en/stable/)
