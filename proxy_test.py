import requests


def test_proxy(proxy):
    try:
        response = requests.get("http://httpbin.org/ip", proxies={"http": proxy, "https": proxy}, timeout=5)
        if response.ok:
            print(f"Proxy {proxy} is working. Your IP: {response.json()['origin']}")
        else:
            print(f"Proxy {proxy} returned status code {response.status_code}")
    except Exception as e:
        print(f"Error occurred while testing proxy {proxy}: {e}")


def main():
    proxy = "http://8c5906b99fbd1c0bcd0f916d545c565a34bd2d11958d3822cf700eb57ff905e6ba35654f79abf9bec3e69bc77e36312a1635bf09928c1598e2cd5a5f480d97c9:f4f7e68yzdih@proxy.toolip.io:31111"
    test_proxy(proxy)


if __name__ == "__main__":
    main()
