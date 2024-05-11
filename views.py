from typing import Optional

from sqladmin import ModelView
from models.db import *


class UserView(ModelView, model=User):
    can_create = False
    can_edit = False
    can_delete = False

    name = "Соискатель"
    name_plural = "Соискатели"
    icon = "fa fa-user"

    column_exclude_list = [User.password, User.exp, User.cv, User.contacts, User.responses]
    column_details_exclude_list = [User.password]
    column_searchable_list = [User.name, User.cv, User.phone]
    column_sortable_list = [User.id, User.birthdate, User.reg_date, User.exp, User.salary, User.status]

    column_labels = {
        User.id: "ID",
        User.name: "Имя",
        User.birthdate: "Дата рождения",
        User.gender: "Пол",
        User.reg_date: "Дата регистрации",
        User.exp: "Опыт работы, лет",
        User.cv: "Резюме",
        User.salary: "Желаемая зарплата",
        User.phone: "Номер телефона",
        User.status: "Ищет работу",
        User.contacts: "Другие контакты",
        User.address: "Адрес",
        User.login: "Логин",
        User.password: "Пароль",
        User.responses: "Отклики",
    }


class EmployerView(ModelView, model=Employer):
    name = "Работодатель"
    name_plural = "Работодатели"
    icon = "fa fa-user-tie"

    column_exclude_list = [Employer.description, Employer.contacts, Employer.vacancies, Employer.slogan]
    column_details_list = "__all__"
    column_searchable_list = [Employer.company_name]
    column_sortable_list = [Employer.company_name, Employer.id]

    form_excluded_columns = [Employer.id, Employer.vacancies]

    column_labels = {
        Employer.id: "ID",
        Employer.company_name: "Название компании",
        Employer.website: "Официальный сайт",
        Employer.description: "Описание",
        Employer.contacts: "Контакты",
        Employer.vacancies: "Вакансии",
        Employer.slogan: "Слоган",
        Employer.short_description: "Краткое описание"
    }


class VacancyView(ModelView, model=Vacancy):
    name = "Вакансия"
    name_plural = "Вакансии"
    icon = "fa fa-briefcase"

    column_list = [Vacancy.id, Vacancy.salary, "profession.profession", "employer.company_name"]
    column_details_list = "__all__"
    column_searchable_list = [Vacancy.content]
    column_sortable_list = [Vacancy.id, Vacancy.salary, Vacancy.pub_date, "profession.profession", "employer.company_name"]

    form_excluded_columns = [Vacancy.id, Vacancy.responses, Vacancy.pub_date]

    column_labels = {
        Vacancy.id: "ID",
        Vacancy.salary: "Зарплата",
        Vacancy.exp: "Требуемый опыт работы",
        Vacancy.content: "Текст вакансии",
        Vacancy.address: "Адрес",
        Vacancy.pub_date: "Дата публикации",
        Vacancy.profession_id: "ID специальности",
        Vacancy.employer_id: "ID работодателя",
        Vacancy.profession: "Специальность",
        Vacancy.employer: "Работодатель",
        Vacancy.responses: "Отклики",
        Vacancy.short_text: "Краткое описание",
        "profession.profession": "Специальность",
        "employer.company_name": "Работодатель"
    }


class ResponseView(ModelView, model=Response):
    can_create = False
    can_delete = False

    name = "Отклик"
    name_plural = "Отклики"
    icon = "fa fa-reply"

    column_list = [Response.id, "user.name", "vacancy.profession.profession", "vacancy.employer.company_name", "status.status", Response.employer_response, Response.response_at]
    column_details_list = "__all__"
    column_searchable_list = [Response.cover_letter, Response.employer_response]
    column_sortable_list = [Response.id, Response.response_at, "status.status", "user.name", "vacancy.profession.profession"]

    form_excluded_columns = [Response.id, Response.cover_letter, Response.response_at, Response.vacancy, Response.user]

    column_labels = {
        Response.id: "ID",
        Response.cover_letter: "Сопроводительное письмо",
        Response.response_at: "Время отклика",
        Response.employer_response: "Ответ работодателя",
        Response.vacancy_id: "ID вакансии",
        Response.vacancy: "Вакансия",
        Response.user_id: "ID соискателя",
        Response.user: "Соискатель",
        Response.status: "Статус",
        Response.status_id: "ID статуса",
        "user.name": "Соискатель",
        "vacancy.profession.profession": "Вакансия",
        "vacancy.employer.company_name": "Работодатель",
        "status.status": "Статус"
    }


class StatusView(ModelView, model=Status):
    can_view_details = False

    name = "Статус"
    name_plural = "Статусы"
    icon = "fa fa-star"

    column_exclude_list = [Status.responses]
    column_details_list = "__all__"
    column_searchable_list = [Status.status]
    column_sortable_list = [Status.id, Status.status]

    form_excluded_columns = [Status.responses]

    column_labels = {
        Status.id: "ID",
        Status.status: "Статус",
        Status.responses: "Отклики"
    }


class ProfessionView(ModelView, model=Profession):
    can_view_details = False

    name = "Специальность"
    name_plural = "Специальности"
    icon = "fa fa-users"

    column_exclude_list = [Profession.vacancies]
    column_details_list = "__all__"
    column_searchable_list = [Profession.id]
    column_sortable_list = [Profession.id, Profession.profession]

    form_excluded_columns = [Profession.vacancies]

    column_labels = {
        Profession.id: "ID",
        Profession.profession: "Специальность"
    }

class AdminView(ModelView, model=Admin):
    name = "Админ"
    name_plural = "Админы"
    icon = "fa fa-user-gear"

    column_exclude_list = [Admin.password, Admin.tokens]
    column_details_exclude_list = [Admin.password, Admin.tokens]
    column_searchable_list = [Admin.name]
    column_sortable_list = [Admin.id]

    form_excluded_columns = [Admin.id, Admin.tokens]

    column_labels = {
        Admin.id: "ID",
        Admin.name: "Имя",
        Admin.login: "Логин"
    }


