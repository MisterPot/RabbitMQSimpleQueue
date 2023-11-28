import json
import pprint
import sys
import logging

import pika
import os

import requests
from dotenv import load_dotenv


load_dotenv()


API_URL = os.getenv('EXTERNAL_API_URL')
username = os.getenv('AMQP_USER')
password = os.getenv('AMQP_PASSWORD')
credentials = pika.ConnectionParameters._DEFAULT


if username or password:
    credentials = pika.PlainCredentials(
        username=username, password=password
    )


connection_params = pika.ConnectionParameters(
    host=os.getenv('AMQP_ADDRESS') or pika.ConnectionParameters._DEFAULT,
    virtual_host=os.getenv('AMQP_VHOST') or pika.ConnectionParameters._DEFAULT,
    port=os.getenv('AMQP_PORT') or pika.ConnectionParameters._DEFAULT,
    credentials=credentials
)


def process_send(data: dict) -> None:
    response = requests.post(API_URL, json=data)
    print(f"Message was sent to API. Response code `{response.status_code}`")


def process_print(data: dict) -> None:
    print('--------------------')
    print('Processing print command...')
    pprint.pprint(data)


def main() -> None:

    connection = pika.BlockingConnection(connection_params)
    channel = connection.channel()
    channel.queue_declare(queue='0')

    def callback(ch, method, properties, body: bytes) -> None:
        message = json.loads(body)
        command = message['command']
        executor = {
            'print': process_print,
            'send': process_send
        }[command]

        executor((message['data']))

    channel.basic_consume(
        queue='0',
        on_message_callback=callback,
        auto_ack=True
    )

    channel.start_consuming()


if __name__ == '__main__':
    try:
        logging.basicConfig(level=logging.DEBUG)
        main()

    except KeyboardInterrupt:
        print('Interrupting ...')

        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)