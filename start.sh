#!/bin/bash

set -x

# Server starten
ollama serve&

# Modelle installieren
ollama pull llama3.1:8b-instruct-q5_K_M
ollama pull llama3.2

wait