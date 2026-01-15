"""
Database Manager for Cosmos DB
Handles user profiles, conversations, and analytics
"""
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional
from azure.cosmos import CosmosClient, PartitionKey, exceptions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChatBotDatabase:
    """Manages Cosmos DB operations for the chatbot"""

    def __init__(self):
        """Initialize Cosmos DB client and containers"""
        self.client = None
        self.database = None
        self.users_container = None
        self.conversations_container = None
        self.analytics_container = None

        try:
            endpoint = os.getenv('COSMOS_DB_ENDPOINT')
            key = os.getenv('COSMOS_DB_KEY')
            database_name = os.getenv('COSMOS_DB_DATABASE', 'askcatalyst')

            if not endpoint or not key:
                logger.warning("Cosmos DB credentials not found, database features disabled")
                return

            # Initialize client
            self.client = CosmosClient(endpoint, key)

            # Create or get database
            self.database = self.client.create_database_if_not_exists(id=database_name)

            # Create or get containers
            self.users_container = self.database.create_container_if_not_exists(
                id='users',
                partition_key=PartitionKey(path='/user_id'),
                offer_throughput=400
            )

            self.conversations_container = self.database.create_container_if_not_exists(
                id='conversations',
                partition_key=PartitionKey(path='/user_id'),
                offer_throughput=400
            )

            self.analytics_container = self.database.create_container_if_not_exists(
                id='analytics',
                partition_key=PartitionKey(path='/date'),
                offer_throughput=400
            )

            logger.info("Cosmos DB initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Cosmos DB: {e}")
            self.client = None

    def is_enabled(self) -> bool:
        """Check if database is properly configured"""
        return self.client is not None

    def create_or_update_user(self, user_id: str, user_data: Dict) -> bool:
        """
        Create or update user profile

        Args:
            user_id: User identifier
            user_data: User profile data

        Returns:
            True if successful, False otherwise
        """
        if not self.is_enabled():
            return False

        try:
            # Get existing user or create new
            try:
                existing_user = self.users_container.read_item(
                    item=user_id,
                    partition_key=user_id
                )
                # Update interaction count and timestamp
                existing_user['last_interaction'] = datetime.utcnow().isoformat()
                existing_user['interaction_count'] = existing_user.get('interaction_count', 0) + 1
                existing_user.update(user_data)
                user_doc = existing_user
            except exceptions.CosmosResourceNotFoundError:
                # Create new user
                user_doc = {
                    'id': user_id,
                    'user_id': user_id,
                    'created_at': datetime.utcnow().isoformat(),
                    'last_interaction': datetime.utcnow().isoformat(),
                    'interaction_count': 1,
                    **user_data
                }

            self.users_container.upsert_item(user_doc)
            logger.info(f"Updated user profile for {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to create/update user: {e}")
            return False

    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """
        Get user profile

        Args:
            user_id: User identifier

        Returns:
            User profile dict or None
        """
        if not self.is_enabled():
            return None

        try:
            user = self.users_container.read_item(
                item=user_id,
                partition_key=user_id
            )
            return user
        except exceptions.CosmosResourceNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Failed to get user profile: {e}")
            return None

    def log_conversation(self, user_id: str, conversation_data: Dict) -> bool:
        """
        Log a conversation entry

        Args:
            user_id: User identifier
            conversation_data: Conversation data including message, response, etc.

        Returns:
            True if successful, False otherwise
        """
        if not self.is_enabled():
            return False

        try:
            doc = {
                'id': f"{user_id}_{datetime.utcnow().timestamp()}",
                'user_id': user_id,
                'timestamp': datetime.utcnow().isoformat(),
                **conversation_data
            }

            self.conversations_container.create_item(doc)
            logger.info(f"Logged conversation for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to log conversation: {e}")
            return False

    def get_user_conversation_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """
        Get user conversation history

        Args:
            user_id: User identifier
            limit: Maximum number of conversations to retrieve

        Returns:
            List of conversation dicts
        """
        if not self.is_enabled():
            return []

        try:
            query = """
                SELECT TOP @limit * FROM c
                WHERE c.user_id = @user_id
                ORDER BY c.timestamp DESC
            """

            items = list(self.conversations_container.query_items(
                query=query,
                parameters=[
                    {'name': '@user_id', 'value': user_id},
                    {'name': '@limit', 'value': limit}
                ],
                enable_cross_partition_query=False,
                partition_key=user_id
            ))

            return items

        except Exception as e:
            logger.error(f"Failed to get conversation history: {e}")
            return []

    def log_analytics_event(self, event_type: str, event_data: Dict) -> bool:
        """
        Log an analytics event

        Args:
            event_type: Type of event (e.g., 'query', 'error', 'upload')
            event_data: Event data

        Returns:
            True if successful, False otherwise
        """
        if not self.is_enabled():
            return False

        try:
            now = datetime.utcnow()
            date_key = now.strftime('%Y-%m-%d')

            doc = {
                'id': f"{event_type}_{now.timestamp()}",
                'date': date_key,
                'event_type': event_type,
                'timestamp': now.isoformat(),
                **event_data
            }

            self.analytics_container.create_item(doc)
            logger.debug(f"Logged analytics event: {event_type}")
            return True

        except Exception as e:
            logger.error(f"Failed to log analytics event: {e}")
            return False

    def get_daily_analytics(self, date: str = None) -> List[Dict]:
        """
        Get analytics for a specific date

        Args:
            date: Date in YYYY-MM-DD format (defaults to today)

        Returns:
            List of analytics dicts
        """
        if not self.is_enabled():
            return []

        try:
            if not date:
                date = datetime.utcnow().strftime('%Y-%m-%d')

            query = """
                SELECT * FROM c
                WHERE c.date = @date
                ORDER BY c.timestamp DESC
            """

            items = list(self.analytics_container.query_items(
                query=query,
                parameters=[{'name': '@date', 'value': date}],
                enable_cross_partition_query=False,
                partition_key=date
            ))

            return items

        except Exception as e:
            logger.error(f"Failed to get daily analytics: {e}")
            return []

    def get_analytics_summary(self, start_date: str, end_date: str) -> Dict:
        """
        Get analytics summary for a date range

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            Dict with analytics summary
        """
        if not self.is_enabled():
            return {}

        try:
            query = """
                SELECT c.event_type, COUNT(1) as count
                FROM c
                WHERE c.date >= @start_date AND c.date <= @end_date
                GROUP BY c.event_type
            """

            items = list(self.analytics_container.query_items(
                query=query,
                parameters=[
                    {'name': '@start_date', 'value': start_date},
                    {'name': '@end_date', 'value': end_date}
                ],
                enable_cross_partition_query=True
            ))

            summary = {item['event_type']: item['count'] for item in items}
            return summary

        except Exception as e:
            logger.error(f"Failed to get analytics summary: {e}")
            return {}

    def delete_user_data(self, user_id: str) -> bool:
        """
        Delete all data for a user (GDPR compliance)

        Args:
            user_id: User identifier

        Returns:
            True if successful, False otherwise
        """
        if not self.is_enabled():
            return False

        try:
            # Delete user profile
            try:
                self.users_container.delete_item(
                    item=user_id,
                    partition_key=user_id
                )
            except exceptions.CosmosResourceNotFoundError:
                pass

            # Delete conversations
            query = "SELECT c.id FROM c WHERE c.user_id = @user_id"
            conversations = list(self.conversations_container.query_items(
                query=query,
                parameters=[{'name': '@user_id', 'value': user_id}],
                partition_key=user_id
            ))

            for conv in conversations:
                self.conversations_container.delete_item(
                    item=conv['id'],
                    partition_key=user_id
                )

            logger.info(f"Deleted all data for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete user data: {e}")
            return False


# Global instance
db = ChatBotDatabase()
