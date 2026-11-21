import sqlite3
from datetime import datetime, timezone

import pytest

from src.arquivos_salvos import (
    RepositorioArtigosSalvosSQLite,
    ServicoArtigosSalvos,
)
