from decimal import Decimal

from .types import UserWorkSpec, WorkRef

D = Decimal

# Uneven distribution across 24 works.
# Low ratings (≤5) are reserved for fictional works tagged "Вымышленное".

USER_WORKS = (
    # ── Books (8) ───────────────────────────────────────────────────────────
    UserWorkSpec(WorkRef("Дюна", "book"), "completed", 8, D("100"), 1, 980),
    UserWorkSpec(WorkRef("Мессия Дюны", "book"), "completed", 7, D("100"), 1, 850),
    UserWorkSpec(WorkRef("1984", "book"), "completed", 9, D("100"), 1, 900),
    UserWorkSpec(WorkRef("Скотный двор", "book"), "completed", 9, D("100"), 2, 700),
    UserWorkSpec(
        WorkRef("Мастер и Маргарита", "book"), "completed", 10, D("100"), 2, 800
    ),
    UserWorkSpec(
        WorkRef("Пикник на обочине", "book"), "completed", 10, D("100"), 1, 650
    ),
    UserWorkSpec(WorkRef("Нейромант", "book"), "in_progress", None, D("40"), 0, 120),
    UserWorkSpec(WorkRef("Хроники Пепла", "book"), "dropped", 3, D("20"), 0, 540),
    # ── Films (6) ───────────────────────────────────────────────────────────
    UserWorkSpec(WorkRef("Начало", "film"), "completed", 10, D("100"), 2, 720),
    UserWorkSpec(WorkRef("Интерстеллар", "film"), "completed", 10, D("100"), 2, 600),
    UserWorkSpec(
        WorkRef("Унесённые призраками", "film"), "completed", 10, D("100"), 3, 480
    ),
    UserWorkSpec(
        WorkRef("Бегущий по лезвию 2049", "film"), "in_progress", None, D("50"), 0, 200
    ),
    UserWorkSpec(WorkRef("Чернобыль", "film"), "completed", 10, D("100"), 1, 400),
    UserWorkSpec(WorkRef("Восточный экспресс", "film"), "dropped", 3, D("15"), 0, 260),
    # ── Games (10) ──────────────────────────────────────────────────────────
    UserWorkSpec(
        WorkRef("The Witcher 3: Wild Hunt", "game"), "completed", 10, D("100"), 2, 900
    ),
    UserWorkSpec(
        WorkRef("Cyberpunk 2077", "game"), "in_progress", None, D("60"), 0, 350
    ),
    UserWorkSpec(WorkRef("Hades", "game"), "completed", 9, D("100"), 1, 150),
    UserWorkSpec(WorkRef("Bastion", "game"), "completed", 8, D("100"), 1, 500),
    UserWorkSpec(WorkRef("Disco Elysium", "game"), "completed", 10, D("100"), 1, 550),
    UserWorkSpec(WorkRef("Hollow Knight", "game"), "planning", None, D("0"), 0, 40),
    UserWorkSpec(WorkRef("Dark Souls", "game"), "completed", 9, D("100"), 1, 700),
    UserWorkSpec(WorkRef("Elden Ring", "game"), "in_progress", None, D("70"), 0, 300),
    UserWorkSpec(
        WorkRef("Тени Морхейма: Пробуждение", "game"), "completed", 3, D("100"), 1, 25
    ),
    UserWorkSpec(WorkRef("Врата Пепла", "game"), "dropped", 2, D("10"), 0, 90),
)
