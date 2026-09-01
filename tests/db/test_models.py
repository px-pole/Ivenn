from datetime import date

from app.db.models import Category, HouseholdItem, Room, User, Warranty


def test_household_item_relationships(db_session):
    user = User(email="owner@example.com", password_hash="hashed")
    room = Room(name="Kitchen")
    category = Category(name="Appliances")
    db_session.add_all([user, room, category])
    db_session.flush()

    item = HouseholdItem(
        user_id=user.id,
        room_id=room.id,
        category_id=category.id,
        name="Washing Machine",
        serial_number="SN-12345",
        purchase_date=date(2024, 1, 15),
    )
    item.warranty = Warranty(expires_on=date(2027, 1, 15), provider="Acme")
    db_session.add(item)
    db_session.commit()

    saved = db_session.get(HouseholdItem, item.id)
    assert saved.name == "Washing Machine"
    assert saved.warranty.provider == "Acme"
    assert saved.room.name == "Kitchen"
    assert saved.owner.email == "owner@example.com"


def test_household_item_status_defaults_to_active(db_session):
    user = User(email="owner2@example.com", password_hash="hashed")
    room = Room(name="Garage")
    category = Category(name="Tools")
    db_session.add_all([user, room, category])
    db_session.flush()

    item = HouseholdItem(
        user_id=user.id,
        room_id=room.id,
        category_id=category.id,
        name="Drill",
    )
    db_session.add(item)
    db_session.commit()

    assert item.status == "active"
    assert item.warranty is None
