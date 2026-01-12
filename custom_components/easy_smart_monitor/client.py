from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
from aiohttp import ClientTimeout, ClientResponseError

from .const import TEST_MODE

_LOGGER = logging.getLogger(__name__)


class EasySmartMonitorApiClient:
    """
    Cliente HTTP assíncrono da API Easy Smart Monitor.

    Responsabilidades:
    - Autenticação (login / refresh)
    - Envio de eventos
    - Consulta de status
    - Respeitar TEST_MODE
    """

    def __init__(
        self,
        *,
        base_url: str,
        username: str,
        password: str,
        session: aiohttp.ClientSession,
        timeout: int = 10,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._username = username
        self._password = password
        self._session = session
        self._timeout = ClientTimeout(total=timeout)

        self._access_token: str | None = None
        self._token_expires_at: float | None = None

        self._lock = asyncio.Lock()

    # =========================================================
    # AUTH
    # =========================================================

    async def async_login(self) -> None:
        """
        Realiza login na API e obtém token.
        Em TEST_MODE, simula login com sucesso.
        """
        if TEST_MODE:
            self._access_token = "test-token"
            self._token_expires_at = None
            _LOGGER.warning(
                "Easy Smart Monitor rodando em TEST_MODE (login simulado)"
            )
            return

        url = f"{self._base_url}/auth/login"
        payload = {
            "username": self._username,
            "password": self._password,
        }

        async with self._lock:
            async with self._session.post(
                url,
                json=payload,
                timeout=self._timeout,
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()

                self._access_token = data["access_token"]
                self._token_expires_at = data.get("expires_at")

                _LOGGER.info("Login realizado com sucesso na API")

    async def async_refresh_token(self) -> None:
        """
        Renova o token de acesso.
        Em TEST_MODE, não faz nada.
        """
        if TEST_MODE:
            return

        if not self._access_token:
            await self.async_login()
            return

        url = f"{self._base_url}/auth/refresh"
        headers = {"Authorization": f"Bearer {self._access_token}"}

        async with self._lock:
            async with self._session.post(
                url,
                headers=headers,
                timeout=self._timeout,
            ) as resp:
                if resp.status == 401:
                    _LOGGER.warning(
                        "Token inválido, realizando novo login"
                    )
                    await self.async_login()
                    return

                resp.raise_for_status()
                data = await resp.json()

                self._access_token = data["access_token"]
                self._token_expires_at = data.get("expires_at")

                _LOGGER.info("Token renovado com sucesso")

    # =========================================================
    # REQUEST CORE
    # =========================================================

    async def _get_auth_headers(self) -> dict[str, str]:
        """Garante token válido e retorna headers."""
        if not self._access_token:
            await self.async_login()

        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        *,
        json_data: Any | None = None,
    ) -> Any:
        """
        Executa uma requisição autenticada.
        Trata 401 com refresh automático.
        """
        if TEST_MODE:
            _LOGGER.debug(
                "TEST_MODE ativo: %s %s (requisição simulada)",
                method,
                endpoint,
            )
            return {}

        url = f"{self._base_url}{endpoint}"
        headers = await self._get_auth_headers()

        try:
            async with self._session.request(
                method,
                url,
                json=json_data,
                headers=headers,
                timeout=self._timeout,
            ) as resp:
                if resp.status == 401:
                    _LOGGER.warning(
                        "401 recebido, tentando renovar token"
                    )
                    await self.async_refresh_token()
                    headers = await self._get_auth_headers()

                    async with self._session.request(
                        method,
                        url,
                        json=json_data,
                        headers=headers,
                        timeout=self._timeout,
                    ) as retry_resp:
                        retry_resp.raise_for_status()
                        return await retry_resp.json()

                resp.raise_for_status()
                return await resp.json()

        except ClientResponseError as err:
            _LOGGER.error(
                "Erro HTTP %s em %s: %s",
                err.status,
                endpoint,
                err.message,
            )
            raise

        except asyncio.TimeoutError as err:
            _LOGGER.error("Timeout ao acessar %s", endpoint)
            raise

    # =========================================================
    # PUBLIC API
    # =========================================================

    async def send_events(self, events: list[dict[str, Any]]) -> None:
        """
        Envia eventos para a API.
        Em TEST_MODE, apenas loga.
        """
        if not events:
            return

        if TEST_MODE:
            _LOGGER.info(
                "TEST_MODE ativo: %s eventos simulados (não enviados)",
                len(events),
            )
            return

        payload = {"events": events}

        await self._request(
            method="POST",
            endpoint="/events",
            json_data=payload,
        )

        _LOGGER.info(
            "Envio de %s eventos realizado com sucesso",
            len(events),
        )

    async def get_status(self) -> dict[str, Any]:
        """
        Obtém status da integração na API.
        Em TEST_MODE, retorna status simulado.
        """
        if TEST_MODE:
            return {
                "status": "test_mode",
                "message": "API simulada",
            }

        return await self._request("GET", "/status")

    # =========================================================
    # INFO / DEBUG
    # =========================================================

    @property
    def token_expires_at(self) -> float | None:
        """Retorna timestamp de expiração do token."""
        return self._token_expires_at