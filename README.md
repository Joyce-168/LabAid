---
title: LabAid
emoji: ⚡
colorFrom: green
colorTo: indigo
sdk: docker
app_port: 5000
---

# LabAid - HPLC Instrument Troubleshooting Assistant

A smart assistant that helps researchers troubleshoot HPLC instrument issues using AI-powered knowledge retrieval.

## Quick Start 🚀

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your environment:
- Create a `.env` file with your `TOGETHER_API_KEY`
- Place your PDF manuals in the `input` directory

3. Initialize the knowledge base:
```bash
python setup_knowledge_base.py
```

4. Run the app:
```bash
python app.py
```

The app will be available at `http://localhost:5000`

## Features ✨
- AI-powered HPLC troubleshooting
- PDF manual integration
- Interactive chat interface
- Smart knowledge retrieval

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference
