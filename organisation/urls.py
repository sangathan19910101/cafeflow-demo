from django.urls import path
from . import views

urlpatterns = [
    path("branches/", views.branch_list, name="branch_list"),
    path("branches/create/", views.create_branch, name="create_branch"),
    path("branches/<uuid:branch_id>/edit/", views.edit_branch, name="edit_branch"),
    path("branches/<uuid:branch_id>/toggle/", views.toggle_branch, name="toggle_branch"),
    path("floors/", views.floor_list, name="floor_list"),
    path("floors/create/", views.create_floor, name="create_floor"),
    path("floors/<uuid:floor_id>/edit/", views.edit_floor, name="edit_floor"),
    path("floors/<uuid:floor_id>/toggle/", views.toggle_floor, name="toggle_floor"),
    path("floors/<uuid:floor_id>/layout/", views.floor_layout, name="floor_layout"),
    path("tables/", views.table_list, name="table_list"),
    path("tables/create/", views.create_table, name="create_table"),
    path("tables/<uuid:table_id>/edit/", views.edit_table, name="edit_table"),
    path("tables/<uuid:table_id>/toggle/", views.toggle_table, name="toggle_table"),
    path("tables/<uuid:table_id>/available/", views.mark_table_available, name="mark_table_available"),
    path("tables/assign-position/", views.assign_table_position, name="assign_table_position"),
    path("tables/<uuid:table_id>/details/", views.get_table_details, name="get_table_details"),
    path("tables/<uuid:table_id>/update/", views.update_table_ajax, name="update_table_ajax"),
]
