"""Lightweight management commands for use inside Docker containers.

Usage:
    docker exec workout-tracker-api python -m services.api.src.manage promote user@example.com
    docker exec workout-tracker-api python -m services.api.src.manage promote user@example.com --role readonly
    docker exec workout-tracker-api python -m services.api.src.manage list-users
"""
import argparse
import sys

from services.api.src.database.database import init_db, get_session
from services.api.src.database.user_repository import UserRepository


def promote(email: str, role: str = "admin") -> None:
    """Promote a user to a given role."""
    if role not in ("admin", "user", "readonly"):
        print(f"Error: invalid role '{role}'. Must be admin, user, or readonly.")
        sys.exit(1)

    init_db()
    with next(get_session()) as session:
        repo = UserRepository(session)
        user = repo.get_by_email(email)
        if not user:
            print(f"Error: user '{email}' not found.")
            sys.exit(1)

        old_role = user.role
        if old_role == role:
            print(f"User '{email}' already has role '{role}'.")
            return

        user.role = role
        session.add(user)
        session.commit()
        print(f"Done! {user.name} ({user.email}): {old_role} -> {role}")


def list_users() -> None:
    """List all users with their roles."""
    init_db()
    with next(get_session()) as session:
        repo = UserRepository(session)
        users = repo.get_all()
        if not users:
            print("No users found.")
            return
        print(f"{'ID':<6} {'Role':<10} {'Email':<35} {'Name'}")
        print("-" * 80)
        for u in users:
            flag = " (disabled)" if u.disabled else ""
            print(f"{u.id:<6} {u.role:<10} {u.email:<35} {u.name}{flag}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Workout Tracker management commands")
    sub = parser.add_subparsers(dest="command")

    p_promote = sub.add_parser("promote", help="Change a user's role")
    p_promote.add_argument("email", help="User email")
    p_promote.add_argument("--role", "-r", default="admin", help="Role to assign (default: admin)")

    sub.add_parser("list-users", help="List all users")

    args = parser.parse_args()
    if args.command == "promote":
        promote(args.email, args.role)
    elif args.command == "list-users":
        list_users()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
