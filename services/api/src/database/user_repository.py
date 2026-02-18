"""Repository for user CRUD operations."""
from sqlalchemy import func
from sqlmodel import Session, select

from services.api.src.database.db_models import ExerciseTable, UserTable


class UserRepository:
    """Repository for user database operations.

    Attributes:
        session: SQLModel database session
    """

    def __init__(self, session: Session):
        self.session = session

    def get_by_google_id(self, google_id: str) -> UserTable | None:
        """Find a user by their Google subject ID.

        Args:
            google_id: Google OAuth subject identifier

        Returns:
            User if found, None otherwise.
        """
        statement = select(UserTable).where(UserTable.google_id == google_id)
        return self.session.exec(statement).first()

    def get_by_id(self, user_id: int) -> UserTable | None:
        """Find a user by primary key.

        Args:
            user_id: User's database ID

        Returns:
            User if found, None otherwise.
        """
        return self.session.get(UserTable, user_id)

    def create(
        self,
        google_id: str,
        email: str,
        name: str,
        picture_url: str | None = None,
    ) -> UserTable:
        """Create a new user.

        Args:
            google_id: Google OAuth subject identifier
            email: User email
            name: User display name
            picture_url: Profile picture URL

        Returns:
            The newly created user.
        """
        user = UserTable(
            google_id=google_id,
            email=email,
            name=name,
            picture_url=picture_url,
        )
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def find_or_create(
        self,
        google_id: str,
        email: str,
        name: str,
        picture_url: str | None = None,
        admin_emails: list[str] | None = None,
    ) -> tuple[UserTable, bool]:
        """Find an existing user by Google ID, or create a new one.

        Args:
            google_id: Google OAuth subject identifier
            email: User email
            name: User display name
            picture_url: Profile picture URL
            admin_emails: List of emails that should be auto-promoted to admin

        Returns:
            Tuple of (user, is_new) where is_new is True if the user was just created.
        """
        existing = self.get_by_google_id(google_id)
        if existing:
            # Update profile info on every login
            self.update_profile(existing, email=email, name=name, picture_url=picture_url)
            # Auto-promote to admin if in admin_emails list
            if admin_emails and email.lower() in admin_emails and existing.role != "admin":
                existing.role = "admin"
                self.session.add(existing)
                self.session.commit()
            return existing, False

        # Check if an email/password account already exists for this email
        by_email = self.get_by_email(email)
        if by_email:
            # Link Google credentials to the existing account
            by_email.google_id = google_id
            self.update_profile(by_email, email=email, name=name, picture_url=picture_url)
            # Auto-promote to admin if in admin_emails list
            if admin_emails and email.lower() in admin_emails and by_email.role != "admin":
                by_email.role = "admin"
                self.session.add(by_email)
                self.session.commit()
            return by_email, False

        new_user = self.create(
            google_id=google_id,
            email=email,
            name=name,
            picture_url=picture_url,
        )
        # Auto-promote to admin if in admin_emails list
        if admin_emails and email.lower() in admin_emails:
            new_user.role = "admin"
            self.session.add(new_user)
            self.session.commit()
        return new_user, True

    def get_by_email(self, email: str) -> UserTable | None:
        """Find a user by email address (case-insensitive).

        Args:
            email: User email address

        Returns:
            User if found, None otherwise.
        """
        statement = select(UserTable).where(
            func.lower(UserTable.email) == email.lower()
        )
        return self.session.exec(statement).first()

    def create_email_user(
        self,
        email: str,
        name: str,
        password_hash: str,
    ) -> UserTable:
        """Create a new user with email/password credentials.

        Args:
            email: User email address
            name: User display name
            password_hash: Bcrypt password hash

        Returns:
            The newly created user.
        """
        user = UserTable(
            email=email.lower(),
            name=name,
            password_hash=password_hash,
        )
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def update_profile(
        self,
        user: UserTable,
        email: str | None = None,
        name: str | None = None,
        picture_url: str | None = None,
    ) -> UserTable:
        """Update a user's profile fields.

        Args:
            user: User to update
            email: New email (if changed)
            name: New display name (if changed)
            picture_url: New picture URL (if changed)

        Returns:
            The updated user.
        """
        if email is not None:
            user.email = email
        if name is not None:
            user.name = name
        if picture_url is not None:
            user.picture_url = picture_url
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def get_all(self) -> list[UserTable]:
        """Return all users ordered by id.

        Returns:
            List of all users.
        """
        statement = select(UserTable).order_by(UserTable.id)
        return list(self.session.exec(statement).all())

    def count_admins(self) -> int:
        """Count the number of admin-role users.

        Returns:
            Number of users with the admin role.
        """
        return self.session.execute(
            select(func.count()).select_from(UserTable).where(UserTable.role == "admin")
        ).scalar() or 0

    def delete_by_id(self, user_id: int) -> bool:
        """Delete a user and their exercises by ID.

        Args:
            user_id: ID of the user to delete

        Returns:
            True if deleted, False if not found.
        """
        user = self.session.get(UserTable, user_id)
        if not user:
            return False

        # Delete all exercises belonging to this user
        exercises = self.session.exec(
            select(ExerciseTable).where(ExerciseTable.user_id == user_id)
        ).all()
        for exercise in exercises:
            self.session.delete(exercise)

        self.session.delete(user)
        self.session.commit()
        return True
