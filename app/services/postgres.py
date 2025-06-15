# """
# Сервис для работы с PostgreSQL базой данных
# """
# from typing import List, Dict, Any, Optional
# from loguru import logger
# import asyncpg
# from contextlib import asynccontextmanager


# class PostgresService:
#     """Сервис для работы с PostgreSQL базой данных"""
    
#     def __init__(self, database_url: str):
#         """
#         Инициализация сервиса PostgreSQL
        
#         Args:
#             database_url: URL подключения к базе данных
#         """
#         self.database_url = database_url
#         self.pool = None
#         logger.info("PostgresService initialized")
    
#     async def connect(self) -> None:
#         """Создание пула соединений с PostgreSQL"""
#         try:
#             self.pool = await asyncpg.create_pool(self.database_url)
#             logger.info("Connected to PostgreSQL")
#         except Exception as e:
#             logger.error(f"Failed to connect to PostgreSQL: {e}")
#             raise
    
#     async def close(self) -> None:
#         """Закрытие пула соединений"""
#         if self.pool:
#             await self.pool.close()
#             logger.info("PostgreSQL connection pool closed")
    
#     @asynccontextmanager
#     async def get_connection(self):
#         """Контекстный менеджер для получения соединения из пула"""
#         if not self.pool:
#             raise RuntimeError("Database pool not initialized. Call connect() first.")
        
#         async with self.pool.acquire() as connection:
#             yield connection
    
#     async def execute_query(self, query: str, *args) -> List[Dict[str, Any]]:
#         """
#         Выполнение SELECT запроса
        
#         Args:
#             query: SQL запрос
#             *args: Параметры запроса
            
#         Returns:
#             List[Dict[str, Any]]: Результаты запроса
#         """
#         try:
#             async with self.get_connection() as conn:
#                 rows = await conn.fetch(query, *args)
#                 return [dict(row) for row in rows]
#         except Exception as e:
#             logger.error(f"Failed to execute query: {e}")
#             raise
    
#     async def execute_command(self, command: str, *args) -> str:
#         """
#         Выполнение INSERT/UPDATE/DELETE команды
        
#         Args:
#             command: SQL команда
#             *args: Параметры команды
            
#         Returns:
#             str: Статус выполнения команды
#         """
#         try:
#             async with self.get_connection() as conn:
#                 result = await conn.execute(command, *args)
#                 logger.info(f"Command executed: {result}")
#                 return result
#         except Exception as e:
#             logger.error(f"Failed to execute command: {e}")
#             raise
    
#     async def create_tables(self) -> None:
#         """Создание необходимых таблиц"""
#         try:
#             # TODO: Добавить SQL для создания таблиц
#             create_tables_sql = """
#             -- Здесь будут SQL команды для создания таблиц
#             -- CREATE TABLE IF NOT EXISTS users (...);
#             -- CREATE TABLE IF NOT EXISTS blood_tests (...);
#             """
            
#             async with self.get_connection() as conn:
#                 await conn.execute(create_tables_sql)
#                 logger.info("Database tables created successfully")
#         except Exception as e:
#             logger.error(f"Failed to create tables: {e}")
#             raise
    
#     async def save_blood_test_result(self, user_id: str, test_data: Dict[str, Any]) -> int:
#         """
#         Сохранение результата анализа крови
        
#         Args:
#             user_id: ID пользователя
#             test_data: Данные анализа
            
#         Returns:
#             int: ID созданной записи
#         """
#         try:
#             # TODO: Реализовать сохранение результата анализа
#             logger.info(f"Saving blood test result for user {user_id}")
#             return 1  # Заглушка
#         except Exception as e:
#             logger.error(f"Failed to save blood test result: {e}")
#             raise
    
#     async def get_user_history(self, user_id: str) -> List[Dict[str, Any]]:
#         """
#         Получение истории анализов пользователя
        
#         Args:
#             user_id: ID пользователя
            
#         Returns:
#             List[Dict[str, Any]]: История анализов
#         """
#         try:
#             # TODO: Реализовать получение истории
#             logger.info(f"Getting history for user {user_id}")
#             return []  # Заглушка
#         except Exception as e:
#             logger.error(f"Failed to get user history: {e}")
#             raise


# # Глобальный экземпляр сервиса (будет инициализирован в main.py)
# postgres_service: Optional[PostgresService] = None 