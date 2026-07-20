#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "1. Installing Python Dependencies..."
pip install -r backend/requirements.txt

echo "2. Compiling C++ Core Engine to Linux Shared Object (libengine.so)..."
g++ -O3 -shared -fPIC -std=c++17 -o core/libengine.so core/engine.cpp

echo "Build Completed Successfully!"
