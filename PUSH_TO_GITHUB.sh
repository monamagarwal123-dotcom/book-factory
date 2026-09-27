#!/bin/bash
# Run this in your terminal after downloading book-factory folder

cd book-factory

# 1. Init git
git init
git add .
git commit -m "feat: v0.1 Image Director Agent - locking, no-stretch resize, KDP export"

# 2. Create repo on GitHub first (https://github.com/new)
# Name it: book-factory
# Then:

git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/book-factory.git
git push -u origin main

echo "Pushed!"
