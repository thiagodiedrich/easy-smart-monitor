from __future__ import annotations

import asyncio
import logging
from typing import Any, List, Optional

from aiohttp import ClientSession, ClientResponseError, ClientTimeout

_LOGGER = logging.getLogger(__name__)


class EasySmartMonitorClient:
    """
    Cliente HTTP assíncrono para comunicação com a API Easy Smart Monitor.

    Responsabilidades:
    - Login (usuário/senha)
    - Gerenciamento de token
    - Reautenticação automática
    - Envio de eventos em lote
    """

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        timeout: int = 10,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._username = username
        self._password = password

        self._token: Optional[str] = None
        self._timeout = ClientTimeout(total=timeout)

        # Lock para evitar múltiplos logins simultâneos
        self._auth_lock = asyncio.Lock()

    # ==========================================================
    # AUTENTICAÇÃO
    # ==========================================================

    async def async_login(self, session: ClientSession) -> None:
        """
        Realiza login na API e armazena o token.
        """
        async with self._auth_lock:
            # Outro coroutine pode ter feito login enquanto aguardávamos
            if self._token:
                return

            _LOGGER.debug("Realizando login na API Easy Smart Monitor")

            async with session.post(
                f"{self._base_url}/login",
                json={
                    "username": self._username,
                    "password": self._password,
                },
                timeout=self._timeout,
            ) as response:
                response.raise_for_status()
                data = await response.json()

                self._token = data.get("token")
                if not self._token:
                    raise RuntimeError("Token não retornado pela API")

                _LOGGER.info("Login realizado com sucesso na API")

    def _auth_headers(self) -> dict[str, str]:
        if not self._token:
            return {}
        return {"Authorization": f"Bearer {self._token}"}

    def invalidate_token(self) -> None:
        """
        Invalida o token atual (força novo login).
        """
        _LOGGER.warning("Invalidando token da API")
        self._token = None

    # ==========================================================
    # ENVIO DE EVENTOS
    # ==========================================================

    async def async_send_events(
        self,
        session: ClientSession,
        events: List[dict[str, Any]],
    ) -> None:
        """
        Envia um lote de eventos para a API.

        - Faz login automaticamente se necessário
        - Reautentica em caso de 401
        - Lança exceção se falhar (para retry externo)
        """
        if not events:
            return

        if not self._token:
            await self.async_login(session)

        try:
            await self._post_events(session, events)

        except ClientResponseError as err:
            if err.status == 401:
                _LOGGER.warning("Token expirado ou inválido (401), refazendo login")
                self.invalidate_token()
                await self.async_login(session)
                await self._post_events(session, events)
            else:
                raise

    async def _post_events(
        self,
        session: ClientSession,
        events: List[dict[str, Any]],
    ) -> None:
        """
        POST real para a API.
        """
        _LOGGER.debug("Enviando %d eventos para a API", len(events))

        async with session.post(
            f"{self._base_url}/events",
            json={"events": events},
            headers=self._auth_headers(),
            timeout=self._timeout,
        ) as response:
            response.raise_for_status()

            _LOGGER.info(
                "Eventos enviados com sucesso para a API (%d itens)",
                len(events),
            )