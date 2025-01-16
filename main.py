from load_credentials import setup_node
import pexpect
import os
from dotenv import load_dotenv

load_dotenv()


def main():
    encryption_password = setup_node()
    ENV = os.getenv("ENV")

    network = "2" if ENV != "production" else "1"

    child = pexpect.spawn("python -m nftnode.chatbots.pft_nft_bot")

    child.expect("Enter your password:")
    child.sendline(encryption_password)

    child.expect(r".*Select network.*")
    child.sendline(network)

    # NOTE: for now no local node
    if ENV == "production":
        child.expect(r".*Do you have a local node.*")
        child.sendline("n")

    child.interact()


if __name__ == "__main__":
    main()
