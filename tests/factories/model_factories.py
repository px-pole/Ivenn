from sqlalchemy.orm import Session

from app.db.models import Category, Room, User


def make_user(db: Session, *, email: str = "owner@example.com") -> User:
    user = User(email=email, password_hash="hashed")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def make_room(db: Session, *, name: str = "Kitchen") -> Room:
    room = Room(name=name)
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


def make_category(db: Session, *, name: str = "Appliances") -> Category:
    category = Category(name=name)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category
