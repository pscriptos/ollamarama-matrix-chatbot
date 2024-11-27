#!/bin/bash

# Modelle installieren
ollama pull llama3.1:8b-instruct-q5_K_M
ollama pull llama3.2

# Server starten
ollama serve