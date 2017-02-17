"""
war card game client and server
"""
import asyncio
from collections import namedtuple
from enum import Enum
import logging
import random
import socket
import socketserver
import threading
import sys

Game = namedtuple("Game", ["p1", "p2"])


class Command(Enum):
    """
    The byte values sent as the first byte of any message in the war protocol.
    """
    WANTGAME = 0
    GAMESTART = 1
    PLAYCARD = 2
    PLAYRESULT = 3


class Result(Enum):
    """
    The byte values sent as the payload byte of a PLAYRESULT message.
    """
    WIN = 0
    DRAW = 1
    LOSE = 2

# k = 0


def kill_game(writers):
    # logging.error('{}'.format(str(writers)))
    # global k
    # k += 1
    # logging.error('Exited game {} times.'.format(str(k)))
    writers[0][0].close()
    writers[0][1].close()
    writers[1][0].close()
    writers[1][1].close()
    return


def compare_cards(card1, card2):
    if card1 > 51 or card2 > 51:
        return 3
    if card1 < 0 or card2 < 0:
        return 3
    if card1 == card2:
        return 3

    # logging.error('Player 1 played: {}'.format(card1))
    # logging.error('Player 2 played: {}'.format(card2))
    card1 = card1 % 13
    card2 = card2 % 13
    if (card1 > card2):
        return 0
    elif (card1 < card2):
        return 2
    else:
        return 1


def deal_cards():
    deck = [0]
    for x in range(1, 52):
        deck.append(x)
    random.shuffle(deck)
    a = deck[26:]
    b = deck[:26]
    del deck[:]
    deck.append(a)
    deck.append(b)
    return deck

gamelist = []


def serve_game(host, port):
    loop = asyncio.get_event_loop()
    coroutine = asyncio.start_server(init_game, host, port, loop=loop)
    server = loop.run_until_complete(coroutine)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()


@asyncio.coroutine
def init_game(reader, writer):

    pair = socket.socketpair()

    if not gamelist:
        # logging.error('Client 1 has connected.')
        # logging.error("{}".format(pair[1]))
        gamelist.append((reader, writer, pair[1]))
        return
    else:
        # logging.error('Client 2 has connected.')
        player2 = gamelist.pop()
        yield from play_game((reader, writer, pair[1]), player2)
        return


@asyncio.coroutine
def play_game(player1, player2):
    # logging.error('Starting a game...')
    # z = 1
    # y = 1
    data1 = yield from player1[0].read(2)
    data2 = yield from player2[0].read(2)
    game = [(player1[1], player1[2]), (player2[1], player2[2])]
    # logging.error("Read from player 1 {} times.".format(str(z)))
    # logging.error("{}".format(str(data1)))
    # logging.error("Read from player 2 {} times.".format(str(y)))
    # logging.error("{}".format(str(data2)))
    # z += 1
    # y += 1
    if data1 != b'\0\0' or data2 != b'\0\0':
        logging.error('Improper command was given, exiting game.')
        kill_game(game)
        return
    deck = deal_cards()
    hand1 = [1] + deck[0]
    hand2 = [1] + deck[1]
    hand1 = bytes(hand1)
    hand2 = bytes(hand2)
    player1[1].write(hand1)
    player2[1].write(hand2)

    # logging.error('Sending to player 1: ', hand1)
    # logging.error('Sending to player 2: ', hand2)

    for x in range(1, 27):
        score = [0, 0]
        data1 = yield from player1[0].read(2)
        data2 = yield from player2[0].read(2)
        # logging.error("Read from player 1 {} times.".format(str(z)))
        # logging.error("Read from player 2 {} times.".format(str(y)))
        # z += 1
        # y += 1
        if data1[0] != 2 or data2[0] != 2:
            logging.error('Improper command was given, exiting game.')
            kill_game(game)
            return
            # CHECK LEGAL CARDS USING HAND1/2
        result = compare_cards(int(data1[1]), int(data2[1]))
        if result > 2:
            kill_game(game)
            return
        elif result == 0:
            data1 = b'\3\0'
            data2 = b'\3\2'
            player1[1].write(data1)
            player2[1].write(data2)
            score[0] += 1
            # logging.error('Player 1 won the round.')
        elif result == 1:
            data1 = b'\3\1'
            data2 = b'\3\1'
            player1[1].write(data1)
            player2[1].write(data2)
            # logging.error('This round was a draw.')
        else:
            data1 = b'\3\2'
            data2 = b'\3\0'
            player1[1].write(data1)
            player2[1].write(data2)
            score[1] += 1
            # logging.error('Player 2 won the round.')
    if score[0] > score[1]:
        # logging.error("Player 1 won!")
        kill_game(game)
    elif score[0] < score[1]:
        # logging.error("Player 2 won!")
        kill_game(game)
    else:
        # logging.error("This game was a draw.")
        kill_game(game)
    return


async def limit_client(host, port, loop, sem):
    """
    Limit the number of clients currently executing.
    You do not need to change this function.
    """
    async with sem:
        return await client(host, port, loop)


async def client(host, port, loop):
    """
    Run an individual client on a given event loop.
    You do not need to change this function.
    """
    try:
        reader, writer = await asyncio.open_connection(host, port, loop=loop)
        # send want game
        writer.write(b"\0\0")
        card_msg = await reader.readexactly(27)
        myscore = 0
        for card in card_msg[1:]:
            writer.write(bytes([Command.PLAYCARD.value, card]))
            result = await reader.readexactly(2)
            if result[1] == Result.WIN.value:
                myscore += 1
            elif result[1] == Result.LOSE.value:
                myscore -= 1
        if myscore > 0:
            result = "won"
        elif myscore < 0:
            result = "lost"
        else:
            result = "drew"
        logging.debug("Game complete, I %s", result)
        writer.close()
        return 1
    except ConnectionResetError as exc:
        logging.error("ConnectionResetError: {}".format(exc))
        return 0
    except asyncio.streams.IncompleteReadError:
        logging.error("asyncio.streams.IncompleteReadError")
        return 0
    except OSError as exc:
        logging.error("OSError: {}".format(exc))
        return 0


def main(args):
    """
    launch a client/server
    """
    host = args[1]
    port = int(args[2])
    if args[0] == "server":
        try:
            # your server should serve clients until the user presses ctrl+c
            serve_game(host, port)
        except KeyboardInterrupt:
            pass
        return
    else:
        loop = asyncio.get_event_loop()

    if args[0] == "client":
        loop.run_until_complete(client(host, port, loop))
    elif args[0] == "clients":
        sem = asyncio.Semaphore(1000)
        num_clients = int(args[3])
        clients = [limit_client(host, port, loop, sem)
                   for x in range(num_clients)]
        async def run_all_clients():
            """
            use `as_completed` to spawn all clients simultaneously
            and collect their results in arbitrary order.
            """
            completed_clients = 0
            for client_result in asyncio.as_completed(clients):
                completed_clients += await client_result
            return completed_clients
        res = loop.run_until_complete(
            asyncio.Task(run_all_clients(), loop=loop))
        logging.info("%d completed clients", res)

    loop.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main(sys.argv[1:])
