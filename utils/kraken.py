import base64
import hashlib
import hmac
import http.client
import json
import time
import urllib.parse
import urllib.request
import uuid

from dotenv import load_dotenv

ORDER_TYPES = ["buy", "sell"]


class KrakenClient:
    BASE_URL = "https://api.kraken.com"

    def __init__(self):
        pass

    def __init__(self, public_key: str, private_key: str) -> None:
        self.load_keys(public_key, private_key)

    def load_keys(self, public_key: str, private_key: str) -> None:
        self.__public_key = public_key
        self.__private_key = private_key

    def get_asset_pairs(self):
        path = "/0/public/AssetPairs"
        response = self.__request(path=path)
        if response.status != 200:
            raise Exception(f"Error fetching asset pairs: {response.status}")
        data = json.loads(response.read())
        if "error" in data and len(data["error"]) > 0:
            raise Exception(f"Error in response: {data['error']}")
        return data["result"]

    def get_account_balance(self):
        response = self.__request(
            method="POST",
            path="/0/private/Balance",
        )
        if response.status != 200:
            raise Exception(f"Error fetching account balance: {response.status}")
        return json.loads(response.read()).get("result", {})

    def get_ticker_ask_price(self, pair: str) -> float:
        """
        Get the current ticker ask price for a specific asset pair.
        Returns the ask price.
        """
        resp = self.__request(
            method="GET",
            path=f"/0/public/Ticker?pair={pair}",
        )

        data = json.loads(resp.read())

        if resp.status != 200:
            raise Exception(f"Error fetching ticker ask price: {resp.status} {data}")

        if data.get("error"):
            raise Exception(
                f"Error fetching ticker ask price for {pair}: {data['error']}"
            )

        return float(data["result"][pair]["a"][0])

    def buy_limit_order(self, pair: str, flat_amount: float, buffer: float) -> dict:
        """
        Place a buy limit order.
        """
        try:
            ask_price = self.get_ticker_ask_price(pair)
        except Exception as e:
            raise Exception(e)

        limit_price = round(ask_price * (1 + buffer), 1)
        volume = flat_amount / limit_price

        return self.place_order(
            ordertype="limit",
            type_="buy",
            volume=str(volume),
            pair=pair,
            price=str(limit_price),
        )

    def place_order(
        self,
        pair: str,
        type_: str,
        ordertype: str,
        volume: float,
        price: float = None,
        cl_ord_id: str = None,
        **kwargs,
    ) -> dict:
        """
        Places an order on Kraken.
        pair: str -> e.g. 'XXBTZEUR'
        type_: str -> 'buy' or 'sell'
        ordertype: str -> 'market', 'limit', etc.
        volume: str/float -> amount to buy/sell
        price: str/float -> needed for limit orders
        kwargs: extra params (stop price, leverage, etc.)
        """
        if not cl_ord_id:
            # Generate a unique client order ID if not provided
            cl_ord_id = uuid.uuid4()

        data = {
            "pair": pair,
            "type": type_,
            "ordertype": ordertype,
            "volume": str(volume),
            "cl_ord_id": str(cl_ord_id),
        }
        if price:
            data["price"] = str(price)

        data.update(kwargs)
        resp = self.__request(
            method="POST",
            path="/0/private/AddOrder",
            body=data,
        )
        res_data = json.loads(resp.read())
        if resp.status != 200:
            raise Exception(f"Error placing order: {resp.status} {res_data}")

        if res_data.get("error"):
            raise Exception(f"Error placing order: {res_data['error']}")

        return res_data

    def __request(
        self,
        method: str = "GET",
        path: str = "",
        query: dict | None = None,
        body: dict | None = None,
    ) -> http.client.HTTPResponse:

        url = self.BASE_URL + path

        query_str = ""
        if query is not None and len(query) > 0:
            query_str = urllib.parse.urlencode(query)
            url += "?" + query_str
        nonce = ""
        if len(self.__public_key) > 0:
            if body is None:
                body = {}
            nonce = body.get("nonce")
            if nonce is None:
                nonce = self.__get_nonce()
                body["nonce"] = nonce
        headers = {}
        body_str = ""
        if body is not None and len(body) > 0:
            body_str = json.dumps(body)
            headers["Content-Type"] = "application/json"
        if len(self.__public_key) > 0:
            headers["API-Key"] = self.__public_key
            headers["API-Sign"] = self.__get_signature(
                query_str + body_str, nonce, path
            )
        req = urllib.request.Request(
            method=method,
            url=url,
            data=body_str.encode(),
            headers=headers,
        )
        return urllib.request.urlopen(req)

    def __get_nonce(self) -> str:
        return str(int(time.time() * 1000))

    def __get_signature(self, data: str, nonce: str, path: str) -> str:
        return self.__sign(
            private_key=self.__private_key,
            message=path.encode() + hashlib.sha256((nonce + data).encode()).digest(),
        )

    def __sign(self, private_key: str, message: bytes) -> str:
        return base64.b64encode(
            hmac.new(
                key=base64.b64decode(private_key),
                msg=message,
                digestmod=hashlib.sha512,
            ).digest()
        ).decode()
