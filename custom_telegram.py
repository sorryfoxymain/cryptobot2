import os
import logging
from PIL import Image
from typing import Optional, Union, BinaryIO, Dict, Any
import json
import mimetypes
import aiohttp

logger = logging.getLogger(__name__)

class CustomInputFile:
    def __init__(
        self,
        obj: Union[str, BinaryIO],
        filename: Optional[str] = None,
        attach: bool = True,
    ):
        """Initialize a custom input file for Telegram API.
        
        Args:
            obj: File path or file-like object
            filename: Optional custom filename
            attach: Whether to attach the file
        """
        self.attach = attach
        self.filename = None
        self.input_file_content = None

        if isinstance(obj, str):
            if os.path.exists(obj):
                self.filename = os.path.basename(obj) if filename is None else filename
                self.input_file_content = open(obj, 'rb')
                # Try to detect if it's an image using Pillow
                try:
                    with Image.open(obj) as img:
                        self.mimetype = f'image/{img.format.lower()}'
                except:
                    self.mimetype = mimetypes.guess_type(self.filename)[0] or 'application/octet-stream'
            else:
                self.filename = filename or "file.txt"
                self.input_file_content = obj.encode('utf-8')
                self.mimetype = 'text/plain'
        else:
            self.filename = filename or "file"
            self.input_file_content = obj
            self.mimetype = 'application/octet-stream'

    def __del__(self):
        """Clean up file resources."""
        if hasattr(self.input_file_content, 'close'):
            self.input_file_content.close()

class CustomBot:
    def __init__(self, token: str):
        """Initialize the custom Telegram bot.
        
        Args:
            token: Telegram bot API token
        """
        if not token:
            raise ValueError("Bot token cannot be empty")
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        logger.info("CustomBot initialized with base URL: %s", self.base_url)

    async def _make_request(self, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a request to Telegram API with error handling.
        
        Args:
            method: API method name
            data: Request data
            
        Returns:
            API response as dictionary
            
        Raises:
            Exception: If API request fails
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{method}"
                logger.debug("Making request to %s with data: %s", url, data)
                
                async with session.post(url, json=data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error("Telegram API error: %s %s", response.status, error_text)
                        raise Exception(f"Telegram API error: {response.status} {error_text}")
                    
                    result = await response.json()
                    logger.debug("Received response: %s", result)
                    
                    if not result.get('ok'):
                        raise Exception(f"Telegram API error: {result.get('description')}")
                    
                    return result
        except Exception as e:
            logger.error("Error making request to Telegram API: %s", str(e))
            raise

    async def send_message(
        self,
        chat_id: Union[int, str],
        text: str,
        parse_mode: Optional[str] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Send text message with error handling.
        
        Args:
            chat_id: Telegram chat ID
            text: Message text
            parse_mode: Optional message parse mode
            **kwargs: Additional message parameters
            
        Returns:
            API response as dictionary
            
        Raises:
            Exception: If message sending fails
        """
        data = {
            'chat_id': chat_id,
            'text': text,
        }
        if parse_mode:
            data['parse_mode'] = parse_mode
        data.update(kwargs)
        
        try:
            logger.info("Sending message to chat_id %s: %s", chat_id, text[:100])
            return await self._make_request('sendMessage', data)
        except Exception as e:
            logger.error("Error sending message: %s", str(e))
            raise 