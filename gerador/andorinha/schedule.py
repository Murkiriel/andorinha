"""Quando gerar de novo: a geração publicada tem uma data (`built_at` do catalogo.json), e o agendamento só segue
para o build quando ela completa o intervalo. A linha de comando fica em scripts/due.py."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Tuple


def catalog_built_at(catalog: Path) -> Optional[str]:
    """O `built_at` do catálogo publicado; None se o catálogo não existe, não é JSON ou não tem a data."""
    try:
        built_at = json.loads(catalog.read_text(encoding="utf-8")).get("built_at")
    except (OSError, ValueError, AttributeError):
        return None
    return built_at if isinstance(built_at, str) else None


def generation_due(built_at: Optional[str], now: datetime, interval_days: int,
                   manual: bool = False) -> Tuple[bool, str]:
    """(gera?, motivo). Os dias são arredondados, para o horário do build não empurrar a geração para o dia
    seguinte: uma geração que terminou às 06:40 conta 29 dias no agendamento das 06:00 do 29º dia."""
    if manual:
        return True, "disparado à mão: gera"
    try:
        built = datetime.strptime(built_at or "", "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return True, "sem a data da geração publicada: gera"
    days = (now - built + timedelta(hours=12)) // timedelta(days=1)
    if days >= interval_days:
        return True, f"geração publicada em {built_at} ({days} dias): gera"
    return False, f"geração publicada em {built_at} ({days} dias): ainda não, gera ao completar {interval_days} dias"
