from load_credentials import setup_node
import pexpect
import os
from dotenv import load_dotenv

load_dotenv()


def main():
    encryption_password = setup_node()
    network = "2" if os.getenv("ENV") != "production" else "1"

    child = pexpect.spawn("python -m imagenode.chatbots.pft_image_bot")

    child.expect("Enter your password:")
    child.sendline(encryption_password)

    child.expect(r".*Select network.*")
    child.sendline(network)

    child.interact()


if __name__ == "__main__":
    main()
