## AWS bedrock model access quick test

After cloning the repo, make sure you have a .env with the access key data

Then
```
 uv venv --python=3.12.10
 uv pip install -r requirements.txt
```

Then activate the env with `source .venv/bin/activate` or run directly with
```
 uv run ./testrock.py -D -p 'who are you' -m 'us.anthropic.claude-3-7-sonnet-20250219-v1:0'
```
