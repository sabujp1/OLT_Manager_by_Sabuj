import logging
from typing import List, Optional
from scrapli import AsyncScrapli
from scrapli.exceptions import ScrapliException

logger = logging.getLogger(__name__)

class CliHelper:
    """Async wrapper for SSH/Telnet CLI command execution on OLTs using Scrapli."""
    
    def __init__(
        self, 
        host: str, 
        username: str, 
        password: str, 
        port: int = 22, 
        platform: str = "generic"
    ):
        self.device_config = {
            "host": host,
            "auth_username": username,
            "auth_password": password,
            "port": port,
            "auth_strict_key": False,  # Commonly disabled on internal ISP management networks
            "platform": platform,
            "transport": "asyncssh",
            "timeout_socket": 5.0,
            "timeout_transport": 5.0,
        }

    async def test_ssh_connection(self) -> bool:
        """Verifies if SSH connection can be established successfully."""
        try:
            async with AsyncScrapli(**self.device_config) as conn:
                return conn.isalive()
        except Exception as e:
            logger.warning(f"SSH ping failed on {self.device_config['host']}: {str(e)}")
            return False

    async def execute_command(self, command: str) -> Optional[str]:
        """Runs a single CLI command and returns the string output."""
        try:
            async with AsyncScrapli(**self.device_config) as conn:
                response = await conn.send_command(command)
                if response.failed:
                    logger.error(f"Command '{command}' failed on {self.device_config['host']}")
                    return None
                return response.result
        except ScrapliException as e:
            logger.error(f"Scrapli error executing '{command}' on {self.device_config['host']}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error executing CLI on {self.device_config['host']}: {str(e)}")
            return None

    async def execute_commands(self, commands: List[str]) -> Optional[List[str]]:
        """Runs a list of CLI commands sequentially in the same session."""
        try:
            async with AsyncScrapli(**self.device_config) as conn:
                response = await conn.send_commands(commands)
                return [r.result for r in response]
        except ScrapliException as e:
            logger.error(f"Scrapli error executing config on {self.device_config['host']}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error executing CLI list on {self.device_config['host']}: {str(e)}")
            return None
