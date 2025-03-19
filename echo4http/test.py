import argparse
import json
import requests

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Test HTTP echo server')
    parser.add_argument('--port', type=int, default=5550, help='Port to test')
    args = parser.parse_args()

    response = requests.get(
        url=f'http://localhost:{args.port}/user',
        headers={'User-Agent': 'test-agent'},
        params={'id': '123456'}
    )
    print(json.dumps(response.json(), indent=2))

    response = requests.post(
        url=f'http://localhost:{args.port}/user',
        headers={'User-Agent': 'test-agent'},
        params={'id': '123456'},
        data={"name": "test"},
    )
    print(json.dumps(response.json(), indent=2))

    response = requests.post(
        url=f'http://localhost:{args.port}/raw',
        data="%$<>?@#^&*[]{}\;'",
    )
    print(json.dumps(response.json(), indent=2))

    response = requests.post(
        url=f'http://localhost:{args.port}/user/json',
        headers={'User-Agent': 'test-agent'},
        params={'id': '123456'},
        json={'name': 'test'},
    )
    print(json.dumps(response.json(), indent=2))

    response = requests.post(
        url=f'http://localhost:{args.port}/upload/file',
        headers={'User-Agent': 'test-agent'},
        files={'uploadFile': ('test.txt', 'test content')},
        data={'version': '1.0'},
        params={'ext': 'txt'}
    )

    print(json.dumps(response.json(), indent=2))