# migrations/env.py
# ===============================================================
# ПОЛНЫЙ РАБОЧИЙ ASYNC env.py ДЛЯ Alembic (PostgreSQL + asyncpg)
# ПОМЕТКИ %%%%% УКАЗЫВАЮТ, ЧТО И ЗАЧЕМ ИЗМЕНЕНО
# ===============================================================

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# %%%%% ИЗМЕНЕНО: вместо sync engine используем async вариант
# %%%%% ПОЧЕМУ: у нас драйвер postgresql+asyncpg, sync-движок вызывает ошибку greenlet
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
from sqlalchemy.ext.asyncio import async_engine_from_config  # было: engine_from_config (sync)

# Это объект конфигурации Alembic (чтение alembic.ini)
config = context.config

# Настройка логирования из alembic.ini (стандартно)
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# %%%%% ДОБАВЛЕНО: импортируем Base и settings из нашего приложения
# %%%%% ПОЧЕМУ: Alembic должен "видеть" модели (Base.metadata), а URL берём из .env
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
from src.database.models import Base           # <<< наши модели; нужно для autogenerate
from src.conf.config import settings           # <<< DB_URL из .env через pydantic-settings

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# %%%%% ИЗМЕНЕНО: сообщаем Alembic метаданные моделей
# %%%%% ПОЧЕМУ: чтобы autogenerate создавал/изменял таблицы согласно моделям
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
target_metadata = Base.metadata

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# %%%%% ДОБАВЛЕНО: подставляем реальный URL из .env
# %%%%% ПОЧЕМУ: чтобы не использовать заглушку из alembic.ini (driver://...), иначе падение
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
config.set_main_option("sqlalchemy.url", settings.DB_URL)

def run_migrations(connection: Connection) -> None:
    """
    Синхронная функция, которую Alembic вызовет внутри async-подключения.
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        # %%%%% ДОБАВЛЕНО: сравнение типов/дефолтов
        # %%%%% ПОЧЕМУ: чтобы Alembic замечал изменения типа колонок и server_default
        # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    """
    Создаём ASYNC engine и выполняем миграции.
    """
    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # %%%%% ИЗМЕНЕНО: создаём async engine из конфигурации
    # %%%%% ПОЧЕМУ: asyncpg требует асинхронный движок; sync engine → ошибка greenlet
    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        # echo=True,  # можно включить при отладке
    )

    async with connectable.connect() as connection:
        # Внутри async-подключения вызываем синхронную функцию run_migrations
        await connection.run_sync(run_migrations)

    await connectable.dispose()

def run_migrations_offline() -> None:
    """
    OFFLINE-режим (без реального подключения к базе): Alembic сгенерирует SQL.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # те же флаги сравнения, что и в online-режиме
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """
    ONLINE-режим: запускаем асинхронные миграции через asyncio.
    """
    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # %%%%% ИЗМЕНЕНО: вместо sync-кода — asyncio.run(...)
    # %%%%% ПОЧЕМУ: весь конвейер переведён на async; это ключ к совместимости с asyncpg
    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    asyncio.run(run_async_migrations())

# Стандартный выбор режима Alembic
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
