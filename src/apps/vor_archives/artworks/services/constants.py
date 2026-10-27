from apps.vor_archives.constants import UserWorkStatusChoices

STATUS_SORT_ORDER = {
    UserWorkStatusChoices.PLANNING: 0,
    UserWorkStatusChoices.IN_PROGRESS: 1,
    UserWorkStatusChoices.COMPLETED: 2,
    UserWorkStatusChoices.DROPPED: 3,
}
