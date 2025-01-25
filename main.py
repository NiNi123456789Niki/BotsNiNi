from bot.main import main
from threading import Thread

import keep_alive


if __name__ == "__main__":
    flask_thread = Thread(target=keep_alive.keep_Alive)

    flask_thread.daemon = True
    flask_thread.start()
    main()

