from decimal import Decimal

from .types import UserWorkSpec, WorkRef

D = Decimal

# Uneven distribution: completed / in_progress / planning / dropped = 13 / 3 / 2 / 2.
# Low ratings only for fictional works (see `is_fictional=True` in works.py).

USER_WORKS = (
    # ── Books ────────────────────────────────────────────────────────────────
    UserWorkSpec(WorkRef("Дюна", "book"), "completed", 10, D("100"), 1, 980),
    UserWorkSpec(WorkRef("1984", "book"), "completed", 9, D("100"), 1, 900),
    UserWorkSpec(
        WorkRef("Мастер и Маргарита", "book"), "completed", 10, D("100"), 2, 800
    ),
    UserWorkSpec(
        WorkRef("Пикник на обочине", "book"), "completed", 8, D("100"), 1, 650
    ),
    UserWorkSpec(WorkRef("Нейромант", "book"), "in_progress", None, D("40"), 0, 120),
    UserWorkSpec(WorkRef("Хроники Пепла", "book"), "completed", 3, D("100"), 1, 540),
    UserWorkSpec(WorkRef("Тень над Морхеймом", "book"), "dropped", 2, D("20"), 0, 300),
    UserWorkSpec(
        WorkRef("Сад расходящихся троп", "book"), "completed", 5, D("100"), 1, 60
    ),
    # ── Films ────────────────────────────────────────────────────────────────
    UserWorkSpec(WorkRef("Начало", "film"), "completed", 10, D("100"), 2, 720),
    UserWorkSpec(
        WorkRef("Унесённые призраками", "film"), "completed", 10, D("100"), 3, 480
    ),
    UserWorkSpec(
        WorkRef("Бегущий по лезвию 2049", "film"), "in_progress", None, D("50"), 0, 200
    ),
    UserWorkSpec(WorkRef("Тёмный город", "film"), "planning", None, D("0"), 0, 30),
    UserWorkSpec(WorkRef("Чернобыль", "film"), "completed", 10, D("100"), 1, 400),
    UserWorkSpec(WorkRef("Восточный экспресс", "film"), "dropped", 3, D("15"), 0, 260),
    UserWorkSpec(WorkRef("Пустошь", "film"), "completed", 2, D("100"), 1, 90),
    # ── Games ────────────────────────────────────────────────────────────────
    UserWorkSpec(
        WorkRef("The Witcher 3: Wild Hunt", "game"),
        "in_progress",
        None,
        D("60"),
        0,
        350,
    ),
    UserWorkSpec(WorkRef("Hades", "game"), "completed", 9, D("100"), 1, 150),
    UserWorkSpec(WorkRef("Disco Elysium", "game"), "completed", 10, D("100"), 1, 500),
    UserWorkSpec(WorkRef("Hollow Knight", "game"), "planning", None, D("0"), 0, 40),
    UserWorkSpec(
        WorkRef("Тени Морхейма: Пробуждение", "game"), "completed", 3, D("100"), 1, 25
    ),
)
