import aiohttp
from typing import List, Dict, Optional
from datetime import datetime
import json
import asyncio
from functools import lru_cache
import time
import logging

logger = logging.getLogger(__name__)

class MoralisAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://deep-index.moralis.io/api/v2"
        self.session = None
        self._cache = {}
        self._cache_ttl = 60  # 1 minute cache

    async def _get_session(self):
        """Get aiohttp session with proper headers."""
        if not self.session:
            self.session = aiohttp.ClientSession(headers={
                'accept': 'application/json',
                'X-API-Key': self.api_key
            })
        return self.session

    async def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make API request with proper error handling and rate limiting."""
        session = await self._get_session()
        url = f"{self.base_url}/{endpoint}"
        
        print(f"\n=== Making API request ===")
        print(f"URL: {url}")
        print(f"Params: {params}")
        print(f"Headers: {session.headers}")
        
        try:
            async with session.get(url, params=params) as response:
                print(f"Response status: {response.status}")
                response_text = await response.text()
                print(f"Response text: {response_text}")
                
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"API request failed: {response.status} - {response_text}")
                    return {}
        except Exception as e:
            print(f"Error making API request: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return {}

    async def get_wallet_balance(self, address: str, chain: str = "eth") -> List[Dict]:
        """Get wallet balance including native token and ERC20 tokens."""
        print(f"\n=== Getting wallet balance for {address} on {chain} ===")
        try:
            # Get native token balance
            print("1. Getting native token balance...")
            native_balance_response = await self._make_request(f"{address}/balance", {
                "chain": chain,
                "format": "decimal"
            })
            print(f"Native balance response: {native_balance_response}")
            
            if not native_balance_response or not isinstance(native_balance_response, dict):
                print(f"Error: Invalid response for native balance: {native_balance_response}")
                return []
                
            native_balance = float(native_balance_response.get('balance', '0'))
            print(f"Calculated native balance: {native_balance}")
            
            if native_balance <= 0:
                print("No native token balance")
                native_token = None
            else:
                # Get native token price
                print("\n2. Getting native token price...")
                native_price = await self.get_native_price(chain)
                print(f"Native price response: {native_price}")
                native_price_usd = float(native_price.get('usdPrice', 0))
                print(f"Native token price USD: {native_price_usd}")
                
                # Create native token balance entry
                native_token = {
                    'symbol': chain.upper() if chain != "eth" else "ETH",
                    'amount': native_balance,
                    'price': native_price_usd,
                    'total_value_usd': native_balance * native_price_usd,
                    'chain': chain
                }
                print(f"\nNative token entry: {native_token}")
            
            # Get ERC20 token balances
            print("\n3. Getting ERC20 token balances...")
            token_balances = await self.get_token_balances(address, chain)
            print(f"Found {len(token_balances)} ERC20 tokens")
            
            # Combine native and token balances
            all_balances = []
            if native_token:
                all_balances.append(native_token)
            all_balances.extend(token_balances)
            
            # Sort by USD value
            all_balances.sort(key=lambda x: x.get('total_value_usd', 0), reverse=True)
            print(f"\nTotal balances found: {len(all_balances)}")
            
            return all_balances
            
        except Exception as e:
            print(f"Error getting wallet balance: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return []

    async def get_native_price(self, chain: str = "eth") -> Dict:
        """Get native token price for the specified chain."""
        try:
            native_token_contracts = {
                "eth": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",  # WETH
                "bsc": "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c",  # WBNB
                "polygon": "0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270",  # WMATIC
            }
            
            native_token_address = native_token_contracts.get(chain, native_token_contracts["eth"])
            return await self._make_request(f"erc20/{native_token_address}/price", {"chain": chain})
        except Exception as e:
            print(f"Error getting native token price: {str(e)}")
            return {"usdPrice": 0}

    async def get_token_balances(self, address: str, chain: str = "eth") -> List[Dict]:
        """Get ERC20 token balances for a wallet."""
        print(f"\n=== Getting token balances for {address} on {chain} ===")
        try:
            # Get ERC20 token balances
            print("1. Requesting ERC20 balances...")
            response = await self._make_request(f"{address}/erc20", {
                "chain": chain,
                "format": "decimal"  # Запрашиваем значения в десятичном формате
            })
            print(f"ERC20 response: {response}")
            
            tokens = []
            if not response or not isinstance(response, list):
                print(f"No valid ERC20 tokens response. Response type: {type(response)}")
                return tokens
                
            print(f"\nProcessing {len(response)} tokens...")
            for token in response:
                try:
                    print(f"\nProcessing token: {token}")
                    if not isinstance(token, dict):
                        print(f"Invalid token data format: {token}")
                        continue
                        
                    decimals = int(token.get('decimals', 18))
                    raw_balance = token.get('balance', '0')
                    
                    if not raw_balance:
                        print(f"No balance for token: {token.get('symbol')}")
                        continue
                        
                    amount = float(raw_balance) / (10 ** decimals)
                    print(f"Token amount after decimal conversion: {amount}")
                    
                    if amount <= 0:
                        print(f"Zero balance for token: {token.get('symbol')}")
                        continue
                    
                    # Get token price
                    token_address = token.get('token_address')
                    print(f"Getting price for token {token_address}")
                    price_data = await self.get_token_price(token_address, chain)
                    print(f"Price data: {price_data}")
                    price_usd = float(price_data.get('usdPrice', 0))
                    print(f"USD price: {price_usd}")
                    
                    if price_usd <= 0:
                        print(f"No valid price for token: {token.get('symbol')}")
                        continue
                    
                    token_info = {
                        'id': token_address,
                        'symbol': token.get('symbol', 'UNKNOWN'),
                        'amount': amount,
                        'price': price_usd,
                        'chain': chain
                    }
                    print(f"Adding token info: {token_info}")
                    tokens.append(token_info)
                except Exception as e:
                    print(f"Error processing token {token.get('symbol', 'UNKNOWN')}: {str(e)}")
                    continue
            
            print(f"\nSuccessfully processed {len(tokens)} tokens")
            return tokens
        except Exception as e:
            print(f"Error getting token balances: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return []

    @lru_cache(maxsize=100)
    async def get_token_price(self, token_address: str, chain: str = "eth") -> Dict:
        """Get token price with caching."""
        try:
            return await self._make_request(f"erc20/{token_address}/price", {"chain": chain})
        except Exception:
            return {"usdPrice": 0}

    async def get_gas_price(self, chain: str = "eth") -> Dict:
        """Get current gas price for the specified chain."""
        try:
            response = await self._make_request("gas-price", {"chain": chain})
            return {
                'safe_low': float(response.get('safeLow', {}).get('value', 0)),
                'standard': float(response.get('standard', {}).get('value', 0)),
                'fast': float(response.get('fast', {}).get('value', 0))
            }
        except Exception as e:
            print(f"Error getting gas price: {str(e)}")
            return {
                'safe_low': 0,
                'standard': 0,
                'fast': 0
            }

    async def get_token_transfers(self, address: str, chain: str = "eth") -> List[Dict]:
        """Get token transfers with optimized processing."""
        endpoint = f"{address}/erc20/transfers"
        params = {
            "chain": chain,
            "limit": 100
        }
        
        try:
            response = await self._make_request(endpoint, params)
            
            async def process_transfer(transfer):
                decimals = int(transfer.get('decimals', 18))
                amount = float(transfer['value']) / (10 ** decimals)
                tx_type = "buy" if transfer['to_address'].lower() == address.lower() else "sell"
                price_data = await self.get_token_price(transfer['token_address'], chain)
                price_usd = price_data.get('usdPrice', 0)
                
                return {
                    'token_address': transfer['token_address'],
                    'symbol': transfer['symbol'],
                    'amount': amount,
                    'price_usd': price_usd,
                    'total_value_usd': amount * price_usd,
                    'transaction_type': tx_type,
                    'timestamp': int(datetime.fromtimestamp(int(transfer['block_timestamp'])).timestamp()),
                    'chain': chain
                }
            
            # Process transfers concurrently
            tasks = [process_transfer(transfer) for transfer in response['result']]
            transfers = await asyncio.gather(*tasks)
            
            return transfers
        except Exception as e:
            print(f"Error getting token transfers: {str(e)}")
            return []

    @staticmethod
    def get_supported_chains() -> List[str]:
        """Get list of supported networks."""
        return ["eth", "bsc", "polygon", "arbitrum", "avalanche"] 