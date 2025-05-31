import aiohttp
from typing import List, Dict, Optional
from datetime import datetime
import json

class MoralisAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://deep-index.moralis.io/api/v2"
        self.headers = {
            "accept": "application/json",
            "X-API-Key": api_key
        }

    async def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make a request to Moralis API."""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/{endpoint}",
                headers=self.headers,
                params=params
            ) as response:
                if response.status != 200:
                    raise Exception(f"API error: {response.status} - {await response.text()}")
                return await response.json()

    async def get_token_balances(self, address: str, chain: str = "eth") -> List[Dict]:
        """
        Get token balances for an address.
        chain: eth, bsc, polygon, arbitrum, avalanche
        """
        endpoint = f"{address}/erc20"
        params = {"chain": chain}
        
        try:
            response = await self._make_request(endpoint, params)
            
            # Transform Moralis response to our application format
            tokens = []
            for token in response:
                decimals = int(token.get('decimals', 18))
                amount = float(token['balance']) / (10 ** decimals)
                
                # Get token price
                price_data = await self.get_token_price(token['token_address'], chain)
                price_usd = price_data.get('usdPrice', 0)
                
                tokens.append({
                    'id': token['token_address'],
                    'symbol': token['symbol'],
                    'amount': amount,
                    'price': price_usd,
                    'chain': chain,
                    'decimals': decimals
                })
            
            return tokens
        except Exception as e:
            print(f"Error getting token balances: {str(e)}")
            return []

    async def get_token_price(self, token_address: str, chain: str = "eth") -> Dict:
        """Get token price."""
        endpoint = f"erc20/{token_address}/price"
        params = {"chain": chain}
        
        try:
            return await self._make_request(endpoint, params)
        except Exception:
            return {"usdPrice": 0}

    async def get_token_transfers(self, address: str, chain: str = "eth") -> List[Dict]:
        """Get token transfers."""
        endpoint = f"{address}/erc20/transfers"
        params = {
            "chain": chain,
            "limit": 100
        }
        
        try:
            response = await self._make_request(endpoint, params)
            transfers = []
            
            for transfer in response['result']:
                decimals = int(transfer.get('decimals', 18))
                amount = float(transfer['value']) / (10 ** decimals)
                
                # Determine transaction type (buy/sell)
                tx_type = "buy" if transfer['to_address'].lower() == address.lower() else "sell"
                
                # Get token price at transaction time
                price_data = await self.get_token_price(transfer['token_address'], chain)
                price_usd = price_data.get('usdPrice', 0)
                
                transfers.append({
                    'token_address': transfer['token_address'],
                    'symbol': transfer['symbol'],
                    'amount': amount,
                    'price_usd': price_usd,
                    'total_value_usd': amount * price_usd,
                    'transaction_type': tx_type,
                    'timestamp': int(datetime.fromtimestamp(int(transfer['block_timestamp'])).timestamp()),
                    'chain': chain
                })
            
            return transfers
        except Exception as e:
            print(f"Error getting token transfers: {str(e)}")
            return []

    async def get_gas_price(self, chain: str = "eth") -> Dict:
        """Get current gas price."""
        if chain == "eth":
            endpoint = "web3/gas-price"
            try:
                response = await self._make_request(endpoint)
                wei_to_gwei = 10 ** 9
                return {
                    'safe_low': float(response['safeLow']['wei']) / wei_to_gwei,
                    'standard': float(response['standard']['wei']) / wei_to_gwei,
                    'fast': float(response['fast']['wei']) / wei_to_gwei
                }
            except Exception:
                return {'safe_low': 0, 'standard': 0, 'fast': 0}
        elif chain == "bsc":
            # BSC uses fixed gas price
            return {'safe_low': 5, 'standard': 5, 'fast': 5}
        else:
            return {'safe_low': 0, 'standard': 0, 'fast': 0}

    @staticmethod
    def get_supported_chains() -> List[str]:
        """Get list of supported networks."""
        return ["eth", "bsc", "polygon", "arbitrum", "avalanche"] 