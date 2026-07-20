from django.urls import path
from .views import (
    session_list, start_session, session_detail, close_session,
    create_expense, expense_list,
    cash_register_list, open_cash_register, close_cash_register, register_detail,
    day_end_list, run_day_end,
    select_floor,
)

urlpatterns = [
    path("", session_list, name="session_list"),
    path("select-floor/", select_floor, name="select_floor"),
    path("start/<uuid:table_id>/", start_session, name="start_session"),
    path("<uuid:session_id>/", session_detail, name="session_detail"),
    path("<uuid:session_id>/close/", close_session, name="close_session"),
    path("expenses/create/", create_expense, name="create_expense"),
    path("expenses/", expense_list, name="expense_list"),
    path("cash-registers/open/", open_cash_register, name="open_register"),
    path("cash-registers/<uuid:register_id>/close/", close_cash_register, name="close_register"),
    path("cash-registers/<uuid:register_id>/", register_detail, name="register_detail"),
    path("cash-registers/", cash_register_list, name="cash_register_list"),
    path("day-end/run/", run_day_end, name="run_day_end"),
    path("day-end/", day_end_list, name="day_end_list"),
]
