from dotenv import load_dotenv
from nftnode.chatbots.pft_nft_bot import main

from load_creds import setup_node_auto

load_dotenv()

if __name__ == "__main__":
    setup_node_auto()
    main()
