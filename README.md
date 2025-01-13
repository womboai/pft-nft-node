# NFT Node
Post Fiat NFT Node.

## Setting up a Local Node
```bash
# This will prompt you to setup secrets to configure your node
nodetools setup-node
# Pass it an OpenAI key
# OpenRouter key
# No anthropic key
# No remembrance wallet
# And initialize with correct discord and Node wallet credentials

# Initialize the database with the correct tables
# Note this requires a "postfiat" user with the permissions to create DB's
nodetools init-db --create-db


# (OPTIONAL) if you want to update the credentials use
nodetools update-creds
```

## Getting Things Running
0. Before running this you will need to use nodetools to initialize credentials and node configuration on your machine. To do so visit https://github.com/postfiatorg/nodetools/tree/async
1. Create a venv with python version 3.12.0
2. Run `pip install -r requirements.dev.txt`
3. To run the bot you can call `python -m nftnode.chatbots.pft_nft_bot`
