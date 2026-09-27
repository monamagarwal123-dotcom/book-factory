#!/bin/bash
echo "Installing Book Factory..."
pip install -r requirements.txt
echo ""
echo "For real image generation, set:"
echo "export REPLICATE_API_TOKEN=r8_xxx"
echo "Get token at https://replicate.com/account/api-tokens"
echo ""
echo "Then run: python cli.py init --title 'My Book'"
