from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from discogs_rec_api.schemas import UserCreate
from discogs_rec_api.models import Users
from discogs_rec_api.security import get_password_hash, verify_password
from discogs_rec_api.exceptions import UserNotFound, UserAlreadyExists
from discogs_rec_api.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    """
    Operations for User entities.

    Provides methods for creating, reading, updating, and deleting users
    from the database. Handles password hashing and user authentication.
    """

    def __init__(self):
        super().__init__()
        self.model: type[Users] = Users

    async def create_user(self, db: AsyncSession, user: UserCreate) -> Users:
        """
        Create a new user in the database.

        Checks for existing user with the same email before creation.
        Hashes the password before storing.

        Args:
            db: Database session
            user: User data for creation (username, email, password)

        Returns:
            Users: Created user object with generated ID

        Raises:
            UserAlreadyExists: If user with the same email already exists
        """
        try:
            user_exists = await self.get_user(db, identifier="email", value=user.email)
        except UserNotFound:
            user_exists = None
        if user_exists:
            raise UserAlreadyExists("User already exists!")

        hashed_password = get_password_hash(password=user.password)

        db_user = self.model(
            username=user.username,
            email=user.email,
            hashed_password=hashed_password,
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user

    async def get_user(self, db: AsyncSession, identifier: str, value: str) -> Users:
        """
        Retrieve a user by email, username, or ID.

        Args:
            db: Database session
            identifier: Field to search by ("email", "username", or "id")
            value: Value to search for

        Returns:
            Users: User object if found

        Raises:
            ValueError: If identifier is not "email", "username", or "id"
            UserNotFound: If no user found with the given criteria
        """
        if identifier == "email":
            query = select(self.model).where(self.model.email == value)
        elif identifier == "username":
            query = select(self.model).where(self.model.username == value)
        elif identifier == "id":
            query = select(self.model).where(self.model.id == value)
        else:
            raise ValueError("Must be email or username")

        user = await self._execute_query(query=query, db=db)
        print(user)
        if not user:
            raise UserNotFound("User not found")
        return user

    async def authenticate_user(
        self, db: AsyncSession, username: str, password: str
    ) -> Users | bool:
        """
        Authenticate a user with username and password.

        Verifies the user exists and the password is correct.

        Args:
            db: Database session
            username: Username to authenticate
            password: Plain text password to verify

        Returns:
            Users: User object if authentication successful
            False: If authentication fails (user not found or wrong password)
        """
        user = await self.get_user(db=db, identifier="username", value=username)
        if not user:
            return False
        if not verify_password(
            plain_password=password, hashed_password=user.hashed_password
        ):
            return False
        return user

    async def update_user_status(
        self, db: AsyncSession, user_id: str, action: str = "deactivate"
    ) -> Users:
        """
        Update user account status.

        Args:
            db: Database session
            user_id: ID of user to update
            action: Action to perform ("deactivate" or "activate")

        Returns:
            Users: Updated user object

        Raises:
            UserNotFound: If user with given ID not found
        """
        user = await self.get_user(db=db, identifier="id", value=user_id)
        if not user:
            raise UserNotFound("User not found")
        user.is_active = False if action == "deactivate" else True
        return await self._execute_query_with_refresh(obj=user, db=db)

    async def update_user_privilege(
        self, db: AsyncSession, user_id: str, action: str = "promote"
    ) -> Users:
        """
        Update user privleges.

        Args:
            db: Database session
            user_id: ID of user to update
            action: Action to perform ("promote" or "demote")

        Returns:
            Users: Updated user object

        Raises:
            UserNotFound: If user with given ID not found
        """
        user = await self.get_user(db=db, identifier="id", value=user_id)
        if not user:
            raise UserNotFound("User not found")
        user.is_superuser = True if action == "promote" else False
        return await self._execute_query_with_refresh(obj=user, db=db)

    async def list_all_users(self, db: AsyncSession, page: int, limit: int) -> dict:
        """
        Retrieve a paginated list of all users.

        Args:
            db: Database session
            page: Page number for pagination
            limit: Maximum number of users to return

        Returns:
            dict: Paginated list of user objects
        """
        query = select(
            self.model.id,
            self.model.email,
            self.model.username,
            self.model.created_at,
            self.model.updated_at,
            self.model.is_active,
            self.model.is_superuser,
        )
        count_query = select(func.count(self.model.id))
        return await self._execute_paginated_query(
            query=query, count_query=count_query, page=page, limit=limit, db=db
        )

    async def delete_user(self, db: AsyncSession, user_id: str) -> None:
        """
        Delete user from the databse.

        Args:
            db: Database session
            user_id: ID of user to delete
        Returns:
            int: Number of rows deleted
        Raises:
            UserNotFound: If no user found to delete
        """
        query = delete(self.model).where(self.model.id == user_id)
        row_count = await self._execute_query_with_rowcount(query=query, db=db)

        if row_count == 0:
            raise UserNotFound("User not found")
