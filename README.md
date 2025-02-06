# codex :octocat:

Question Answering on PDF Documents

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

This will start the FASTAPI server on `http://localhost:8000`. 

## Resources:

- [pipecat](https://github.com/pipecat-ai/pipecat)
- [LlamaIndex](https://docs.llamaindex.ai/en/stable/)
