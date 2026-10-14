from .types import CollectionSpec, WorkRef

COLLECTIONS = (
    CollectionSpec(
        name="Фантастика и антиутопии",
        items=(
            WorkRef("1984", "book"),
            WorkRef("Дюна", "book"),
            WorkRef("Нейромант", "book"),
        ),
        children=(
            CollectionSpec(name="Космоопера", items=(WorkRef("Дюна", "book"),)),
            CollectionSpec(name="Киберпанк", items=(WorkRef("Нейромант", "book"),)),
        ),
    ),
    CollectionSpec(
        name="Экранизации и близкое",
        items=(
            WorkRef("Бегущий по лезвию 2049", "film"),
            WorkRef("Тёмный город", "film"),
        ),
    ),
    CollectionSpec(
        name="Игры на вечер",
        items=(
            WorkRef("Hades", "game"),
            WorkRef("Hollow Knight", "game"),
        ),
        children=(CollectionSpec(name="Короткие", items=(WorkRef("Hades", "game"),)),),
    ),
    CollectionSpec(
        name="Пересмотреть",
        items=(
            WorkRef("Начало", "film"),
            WorkRef("Унесённые призраками", "film"),
            WorkRef("Чернобыль", "film"),
        ),
    ),
)
