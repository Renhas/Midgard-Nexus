from .types import CollectionSpec, WorkRef

COLLECTIONS = (
    CollectionSpec(
        name="Фантастика и антиутопии",
        items=(
            WorkRef("1984", "book"),
            WorkRef("Дюна", "book"),
            WorkRef("Нейромант", "book"),
            WorkRef("Мессия Дюны", "book"),
        ),
        children=(
            CollectionSpec(
                name="Космоопера",
                items=(
                    WorkRef("Дюна", "book"),
                    WorkRef("Мессия Дюны", "book"),
                ),
            ),
            CollectionSpec(name="Киберпанк", items=(WorkRef("Нейромант", "book"),)),
        ),
    ),
    CollectionSpec(
        name="Экранизации и близкое",
        items=(
            WorkRef("Бегущий по лезвию 2049", "film"),
            WorkRef("Интерстеллар", "film"),
        ),
    ),
    CollectionSpec(
        name="Игры на вечер",
        items=(
            WorkRef("Hades", "game"),
            WorkRef("Bastion", "game"),
            WorkRef("Hollow Knight", "game"),
        ),
        children=(
            CollectionSpec(
                name="Короткие",
                items=(
                    WorkRef("Hades", "game"),
                    WorkRef("Bastion", "game"),
                ),
            ),
        ),
    ),
    CollectionSpec(
        name="FromSoftware",
        items=(
            WorkRef("Dark Souls", "game"),
            WorkRef("Elden Ring", "game"),
        ),
    ),
    CollectionSpec(
        name="Пересмотреть",
        items=(
            WorkRef("Начало", "film"),
            WorkRef("Интерстеллар", "film"),
            WorkRef("Унесённые призраками", "film"),
            WorkRef("Чернобыль", "film"),
        ),
    ),
)
